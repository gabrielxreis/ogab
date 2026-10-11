"""Conferência automática antes de entregar.

  python3 qc.py <pasta_do_video> [--cliente <pasta_cliente>] [--plataforma instagram|meta_ads|youtube_shorts]

Confere:
  1. Pastas e arquivos obrigatórios (roteiro.txt, links.txt, narracoes/, musica/, brolls/, videos/, legendas/).
  2. Vídeo final: resolução, duração dentro da regra da plataforma, quadros pretos (blackdetect), loudness (LUFS).
  3. Legendas: uma linha só, tamanho máximo, grafias proibidas do cliente (erros de transcrição), palavra fraca no fim.
  4. Takes: green screen, arquivos pesados (4K/ProRes) que travam o playback.
  5. Gera folha de contato (qc_folha.jpg) com 6 quadros do vídeo final.
Saída: lista de OK / AVISO / ERRO. Corrigir os ERROs antes de entregar.
"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from midia import info, green, pesado
from legendas import fraca

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cfg():
    for n in ("config.json", "config.example.json"):
        p = os.path.join(AQUI, n)
        if os.path.exists(p): return json.load(open(p))
    return {}


def main(pasta, cliente=None, plataforma="instagram"):
    C = cfg(); R = C.get("regras", {}); res = []
    ok = lambda m: res.append(("OK", m)); av = lambda m: res.append(("AVISO", m)); er = lambda m: res.append(("ERRO", m))

    for item in ("roteiro.txt", "links.txt", "narracoes", "musica", "brolls", "videos", "legendas"):
        (ok if os.path.exists(os.path.join(pasta, item)) else er)(f"estrutura: {item}")

    vids = sorted(glob.glob(os.path.join(pasta, "videos", "*.mp4")), key=os.path.getmtime)
    if not vids: er("nenhum vídeo final em videos/")
    else:
        v = vids[-1]; i = info(v)
        ok(f"vídeo final {os.path.basename(v)}: {i['w']}x{i['h']}, {i['dur']:.1f}s")
        lim = R.get("duracao_segundos", {}).get(plataforma)
        if lim:
            if plataforma == "meta_ads":
                (ok if any(abs(i['dur'] - d) <= 1.5 for d in lim) else er)(f"duração Meta Ads deve ser uma de {lim}s")
            else:
                (ok if lim[0] - 1 <= i['dur'] <= lim[1] + 1 else er)(f"duração {plataforma}: {lim[0]} a {lim[1]} s")
        bd = subprocess.run(["ffmpeg", "-i", v, "-vf", "blackdetect=d=0.03:pix_th=0.05", "-an", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        pretos = re.findall(r"black_start:([\d.]+)", bd)
        (er if pretos else ok)(f"quadros pretos: {', '.join(pretos[:5]) or 'nenhum'}")
        ld = subprocess.run(["ffmpeg", "-i", v, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)
        if m:
            lufs = float(m[-1]); alvo = R.get("loudness_alvo_lufs", -14)
            (ok if abs(lufs - alvo) <= 3 else av)(f"loudness {lufs} LUFS (alvo {alvo})")
        # folha de contato
        d = i['dur']; tmp = []
        for k in range(6):
            o = os.path.join(pasta, f".qc_{k}.jpg"); tmp.append(o)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(d * (k + .5) / 6), "-i", v, "-frames:v", "1",
                            "-vf", "scale=240:-1", o])
        try:
            from PIL import Image
            im = [Image.open(x) for x in tmp]; fl = Image.new("RGB", (240 * 6, im[0].height))
            for k, x in enumerate(im): fl.paste(x, (240 * k, 0))
            fl.save(os.path.join(pasta, "qc_folha.jpg")); ok("folha de contato: qc_folha.jpg")
        finally:
            for x in tmp:
                if os.path.exists(x): os.remove(x)

    srts = sorted(glob.glob(os.path.join(pasta, "legendas", "*.srt")), key=os.path.getmtime)
    if srts:
        L = R.get("legenda", {}); mx = L.get("max_caracteres", 25)
        bl = open(srts[-1]).read().strip().split("\n\n"); linhas = [b.split("\n")[2:] for b in bl]
        if L.get("uma_linha", True):
            multi = [" / ".join(l) for l in linhas if len(l) > 1]
            (er if multi else ok)(f"legenda em uma linha ({len(multi)} com quebra)")
        longas = [l for b in linhas for l in b if len(l) > mx]
        (er if longas else ok)(f"legendas até {mx} caracteres" + (f": {longas[:3]}" if longas else ""))
        fim_fraco = [b[-1] for b in linhas[:-1] if b and not re.search(r'[.?!]$', b[-1]) and fraca(b[-1].split()[-1])]
        (av if fim_fraco else ok)("legenda terminando em palavra fraca" + (f": {fim_fraco[:3]}" if fim_fraco else ""))
        if cliente and os.path.exists(os.path.join(cliente, "pronuncia.json")):
            bruto = " ".join(l for b in linhas for l in b)
            for t in json.load(open(os.path.join(cliente, "pronuncia.json"))).get("termos", []):
                for e in t.get("erros_transcricao", []):
                    so_caixa = e.lower() == t["grafia"].lower()
                    achou = (e in bruto) if so_caixa else (e.lower() in bruto.lower())
                    if so_caixa and L.get("preset_trilha", {}).get("caixa_alta"): achou = False  # legenda vai em caixa alta
                    (er if achou else ok)(f"grafia: '{e}' -> '{t['grafia']}'")
    else: er("nenhum SRT em legendas/")

    for f in sorted(glob.glob(os.path.join(pasta, "brolls", "take_*"))):
        nome = os.path.basename(f)
        if glob.glob(os.path.splitext(f)[0] + "_1080*"): continue  # já tem versão convertida em uso
        try:
            if pesado(f): av(f"{nome} pesado (4K/ProRes): converter com midia.py preparar_take")
            if R.get("evitar_green_screen", True) and green(f) > 0.25: er(f"{nome} parece green screen")
        except Exception as e: av(f"{nome}: não analisado ({e})")

    for tipo, msg in res: print(f"[{tipo}] {msg}")
    print(f"\n{sum(1 for t, _ in res if t == 'ERRO')} erro(s), {sum(1 for t, _ in res if t == 'AVISO')} aviso(s)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    main(a[0], opt("--cliente"), opt("--plataforma", "instagram"))
