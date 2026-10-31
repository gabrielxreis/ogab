"""Separa as faixas (stems) de uma música com o Open-Unmix (github.com/sigsep/open-unmix-pytorch): voz, bateria,
baixo e outros. Instala sozinho na primeira vez (openunmix + pesos do modelo ~140 MB em ~/.cache/torch/hub).

  python3 separar.py musica.mp3                       # 4 faixas: voz, bateria, baixo, outros
  python3 separar.py clipe.mp4 --so-voz               # 2 faixas: voz e instrumental (karaokê, tirar a voz da trilha)
  python3 separar.py musica.wav --faixas vocals,drums --saida /pasta
  python3 separar.py --instalar                       # só instala/confere (doctor)

Quando usar: trilha com voz cantada brigando com a fala (tirar a voz e ficar só o instrumental), pegar só a bateria
para cortar no ritmo, abaixar um instrumento, música de referência do cliente com voz. Aceita áudio ou vídeo (o ffmpeg
extrai o áudio). Saída: WAV 24 bit 44,1 kHz em <nome>_faixas/ ao lado do arquivo, nomes novos a cada rodada (_v2...).

Modelo: umxhq (pesos MIT, pode usar em trabalho de cliente). O umxl separa melhor, mas os pesos são CC BY-NC-SA (só uso
pessoal, sem cliente): --modelo umxl só se a pessoa pedir e o uso não for comercial.
Não é para limpar a fala de ruído (o modelo de fala dele é 16 kHz mono): isso é o isolamento de voz do editor/ElevenLabs.
Sem torchaudio de propósito: a versão no pip prende uma torch mais velha e rebaixaria a torch da máquina (CLAP, upscale);
o openunmix só usa o torchaudio para reamostrar, e quem reamostra aqui é o ffmpeg.
"""
import argparse, importlib.util, os, subprocess, sys, time, types

TAXA = 44100
FAIXAS = {"vocals": "voz", "drums": "bateria", "bass": "baixo", "other": "outros"}
TROCO = 60     # segundos por pedaço (memória); emenda com cruzamento de 1 s
CRUZA = 1


def _pip(*pacs):
    base = [sys.executable, "-m", "pip", "install", "--user", "--progress-bar", "off", *pacs]
    if subprocess.run(base).returncode == 0:
        return True
    return subprocess.run(base + ["--break-system-packages"]).returncode == 0


def garantir():
    """Instala o que falta. torch só se não existir (~800 MB); openunmix sem deps para não puxar o torchaudio."""
    if importlib.util.find_spec("torch") is None:
        print("instalando torch (~800 MB, só na primeira vez)...", flush=True)
        if not _pip("torch"):
            raise SystemExit(f"não consegui instalar a torch: {sys.executable} -m pip install --user torch")
    falta = [p for m, p in (("openunmix", "openunmix==1.3.0"), ("tqdm", "tqdm")) if importlib.util.find_spec(m) is None]
    if falta:
        print("instalando Open-Unmix (só na primeira vez)...", flush=True)
        if not _pip("--no-deps", *falta):
            raise SystemExit(f"não consegui instalar: {sys.executable} -m pip install --user --no-deps {' '.join(falta)}")
        importlib.invalidate_caches()
    if importlib.util.find_spec("torchaudio") is None:
        sys.modules["torchaudio"] = types.ModuleType("torchaudio")   # import no topo do openunmix; não é usado aqui


def ler(arq):
    """Áudio (ou o áudio do vídeo) em float32 estéreo 44,1 kHz, formato (canais, amostras)."""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-vn", "-ac", "2", "-ar", str(TAXA), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode or not r.stdout:
        raise SystemExit(f"ffmpeg não leu o áudio de {arq}: {r.stderr.decode(errors='ignore')[-400:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2).T.copy()


def gravar(arq, audio):
    import numpy as np
    dados = np.ascontiguousarray(np.clip(audio.T, -1, 1).astype(np.float32)).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(TAXA), "-i", "-",
                    "-c:a", "pcm_s24le", arq], input=dados, check=True)


def separar(audio, modelo, faixas, residual):
    import numpy as np, torch, openunmix
    sep = getattr(openunmix, modelo)(targets=faixas, residual=residual, device="cpu")
    sep.freeze()
    n = audio.shape[1]
    passo, cruza = TROCO * TAXA, CRUZA * TAXA
    saida, peso = None, np.zeros(n, dtype=np.float32)
    ini = 0
    while ini < n:
        fim = min(n, ini + passo + cruza)
        with torch.no_grad():
            est = sep(torch.from_numpy(audio[None, :, ini:fim])).numpy()[0]    # (faixas, canais, amostras)
        if saida is None:
            saida = np.zeros((est.shape[0], 2, n), dtype=np.float32)
        janela = np.ones(fim - ini, dtype=np.float32)
        if ini > 0:
            janela[:cruza] = np.linspace(0, 1, cruza, dtype=np.float32)
        if fim < n:
            janela[-cruza:] = np.linspace(1, 0, cruza, dtype=np.float32)
        saida[:, :, ini:fim] += est * janela
        peso[ini:fim] += janela
        print(f"  {min(fim, n) / TAXA:.0f}/{n / TAXA:.0f} s", flush=True)
        ini += passo
    return saida / np.maximum(peso, 1e-6)


def pasta_nova(base):
    p, v = base, 1
    while os.path.exists(p):
        v += 1
        p = f"{base}_v{v}"
    return p


def main():
    ap = argparse.ArgumentParser(description="Separa as faixas de uma música (Open-Unmix).")
    ap.add_argument("arquivo", nargs="?")
    ap.add_argument("--so-voz", action="store_true", help="só voz + instrumental")
    ap.add_argument("--faixas", default="vocals,drums,bass,other", help="vocals,drums,bass,other")
    ap.add_argument("--modelo", default="umxhq", choices=["umxhq", "umxl", "umx"])
    ap.add_argument("--saida", help="pasta de saída (padrão: <nome>_faixas ao lado do arquivo)")
    ap.add_argument("--instalar", action="store_true", help="só instala e confere")
    a = ap.parse_args()
    garantir()
    if a.instalar:
        import openunmix
        print(f"OK: Open-Unmix pronto ({os.path.dirname(openunmix.__file__)})")
        return
    if not a.arquivo or not os.path.isfile(a.arquivo):
        raise SystemExit("passe o arquivo de áudio ou vídeo")
    faixas = ["vocals"] if a.so_voz else [f.strip() for f in a.faixas.split(",") if f.strip()]
    if any(f not in FAIXAS for f in faixas):
        raise SystemExit(f"faixas válidas: {', '.join(FAIXAS)}")
    residual = a.so_voz or len(faixas) < len(FAIXAS)
    nome = os.path.splitext(os.path.basename(a.arquivo))[0]
    pasta = a.saida or pasta_nova(os.path.join(os.path.dirname(os.path.abspath(a.arquivo)), f"{nome}_faixas"))
    t0 = time.time()
    audio = ler(a.arquivo)
    print(f"separando {audio.shape[1] / TAXA:.0f} s com {a.modelo} (primeira vez baixa os pesos)...", flush=True)
    est = separar(audio, a.modelo, faixas, residual)
    os.makedirs(pasta, exist_ok=True)
    rotulos = [FAIXAS[f] for f in faixas] + (["instrumental" if a.so_voz else "resto"] if residual else [])
    for i, r in enumerate(rotulos):
        arq = os.path.join(pasta, f"{nome}_{r}.wav")
        gravar(arq, est[i])
        print(arq)
    print(f"OK: {len(rotulos)} faixas em {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
