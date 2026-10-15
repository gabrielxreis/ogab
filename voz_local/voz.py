"""Voz local do Gab: clonar e gerar fala com o motor do VoiceStudio rodando por trás do Claude.

  python3 voz.py motores                                   motores de voz, instalados ou não, com português e licença
  python3 voz.py instalar-motor <id>                       instala um motor (ambiente isolado) com barra ao vivo
  python3 voz.py clonar <audio> "<Nome>" [--inicio S --fim S] [--motor omnivoice]
  python3 voz.py vozes                                     vozes clonadas (nome -> profile_id)
  python3 voz.py gerar "<texto>" --voz "<Nome>" [--saida arquivo.wav] [--motor omnivoice] [--passos 32]
                     [--efeito raw|broadcast|...] [--seed N] [--instrucao "..."] [--velocidade 1.0]

Toda geração e instalação mostra barra de progresso em tempo real (regra do usuário): rode no terminal do app
(mcp__terminal__run_in_terminal) para o usuário acompanhar. A síntese não informa progresso; a barra é estimada
pelo tempo real das gerações anteriores (ritmo.json, por motor e passos), trava em 99% até o áudio chegar.
Precisa do backend no ar: voicestudio.sh start (os comandos sobem sozinhos se estiver parado).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
API = "http://127.0.0.1:3900"
BASE = os.environ.get("OGAB_VOZ_BASE", os.path.expanduser("~/Documents/Gab Voz Local"))
PY_MOTOR = os.path.expanduser("~/Library/Application Support/GabVoz/VoiceStudio/.venv/bin/python")
VOZES = os.path.join(BASE, "vozes.json")
RITMO = os.path.join(BASE, "ritmo.json")

# Motores que clonam voz e falam português (conferido nas docs do VoiceStudio 0.5.6, 15/10/2026).
# IndexTTS e CosyVoice controlam emoção/instrução mas NÃO falam português.
MOTORES_PT = {
    "omnivoice": ("GPU (MPS)", "3,3 GB", "modelo CC-BY-NC: NÃO comercial", "padrão, rápido, 600+ idiomas"),
    "voxcpm2": ("GPU (MPS)", "~5 GB", "Apache-2.0", "48 kHz, voz por descrição, 30 idiomas"),
    "confucius4-tts": ("CPU", "~5 GB", "Apache-2.0", "mantém a voz entre idiomas, 14 idiomas"),
    "moss-tts-nano": ("CPU", "leve", "Apache-2.0", "48 kHz, 20 idiomas"),
    "pockettts": ("CPU", "leve", "código MIT, pesos CC-BY-4.0 (aceitar termo no Hugging Face)", "6 idiomas"),
}


def subir():
    try:
        urllib.request.urlopen(API + "/health", timeout=3)
    except OSError:
        subprocess.run([os.path.join(AQUI, "voicestudio.sh"), "start"], check=True)


def get(caminho, timeout=30):
    with urllib.request.urlopen(API + caminho, timeout=timeout) as r:
        return json.loads(r.read())


def post_json(caminho, corpo=None, timeout=60):
    req = urllib.request.Request(API + caminho, json.dumps(corpo or {}).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def post_form(caminho, campos, timeout=3600):
    """multipart/form-data só com campos de texto (o perfil já carrega o áudio de referência)."""
    b = uuid.uuid4().hex
    partes = []
    for k, v in campos.items():
        if v is None:
            continue
        partes.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    corpo = b"".join(partes) + f"--{b}--\r\n".encode()
    req = urllib.request.Request(API + caminho, corpo, {"Content-Type": f"multipart/form-data; boundary={b}"})
    r = urllib.request.urlopen(req, timeout=timeout)
    return r.read(), dict(r.headers)


def barra(pct, rotulo):
    n = int(pct / 2)
    sys.stdout.write(f"\r[{'#' * n}{'-' * (50 - n)}] {pct:3.0f}%  {rotulo}      ")
    sys.stdout.flush()


def ler(arq, padrao):
    try:
        with open(arq) as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def gravar(arq, dados):
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    with open(arq, "w") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


# ---------- motores ----------
def cmd_motores(_):
    subir()
    inst = {e["id"]: e for e in get("/engines/tts")["backends"]}
    print(f"{'motor':16} {'instalado':10} {'roda em':10} {'tamanho':8} licença / destaque")
    for mid, (onde, tam, lic, extra) in MOTORES_PT.items():
        ok = "sim" if inst.get(mid, {}).get("available") else "não"
        print(f"{mid:16} {ok:10} {onde:10} {tam:8} {lic}; {extra}")


def cmd_instalar_motor(a):
    subir()
    print(post_json(f"/engines/sidecar/{a.id}/install"))
    t0 = time.time()
    while True:
        s = get(f"/engines/sidecar/{a.id}/install/status")
        estado = s.get("state") or s.get("status") or ""
        pct = s.get("progress") or s.get("percent") or 0
        pct = pct * 100 if isinstance(pct, float) and pct <= 1 else pct
        barra(min(float(pct or 0), 100), f"{estado} {s.get('message') or s.get('phase') or ''} {time.time() - t0:.0f} s"[:70])
        if estado in ("done", "installed", "complete", "completed", "succeeded", "ok"):
            barra(100, "instalado")
            print()
            return
        if estado in ("failed", "error"):
            print(f"\nFALHOU: {json.dumps(s, ensure_ascii=False)[:600]}")
            sys.exit(1)
        time.sleep(2)


# ---------- clonar ----------
def melhor_janela(audio, inicio, fim):
    """Escolhe ~18 s que começam e terminam em pausa (o motor usa até 20 s de referência)."""
    if inicio is not None:
        return inicio, fim if fim is not None else inicio + 18
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", "silencedetect=n=-35dB:d=0.35",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    fins = [float(l.split("silence_end: ")[1].split()[0]) for l in log.splitlines() if "silence_end" in l]
    inis = [float(l.split("silence_start: ")[1]) for l in log.splitlines() if "silence_start" in l]
    for s in [0.0] + fins:
        cands = [e for e in inis if 12 <= e - s <= 20]
        if cands:
            return max(0.0, s - 0.1), max(cands) + 0.1
    return 0.0, 18.0


def transcrever(wav):
    cod = ("import mlx_whisper,sys;print(mlx_whisper.transcribe(sys.argv[1],"
           "path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='pt')['text'].strip())")
    r = subprocess.run([PY_MOTOR, "-I", "-c", cod, wav], capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


def cmd_clonar(a):
    sys.path.insert(0, AQUI)
    import vs_mcp
    subir()
    os.makedirs(os.path.join(BASE, "referencias"), exist_ok=True)
    ini, fim = melhor_janela(a.audio, a.inicio, a.fim)
    nome_arq = "".join(c if c.isalnum() else "_" for c in a.nome).strip("_").lower()
    ref = os.path.join(BASE, "referencias", f"{nome_arq}_ref.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.2f}", "-to", f"{fim:.2f}", "-i", a.audio,
                    "-ac", "1", "-ar", "44100", ref], check=True)
    print(f"Referência: {fim - ini:.1f} s ({ini:.1f} a {fim:.1f} s do original) -> {ref}")
    texto = transcrever(ref)
    print(f"Transcrição da referência: {texto}")
    _, sid = vs_mcp.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                       "clientInfo": {"name": "voz", "version": "1"}})
    vs_mcp.rpc("notifications/initialized", sid=sid, rid=None)
    msg, _ = vs_mcp.rpc("tools/call", {"name": "clone_voice", "arguments": {
        "name": a.nome, "ref_audio_path": os.path.relpath(ref, BASE), "ref_text": texto,
        "language": "Portuguese"}}, sid=sid, rid=2)
    info = json.loads(msg["result"]["content"][0]["text"])
    if "profile_id" not in info:
        sys.exit(f"ERRO ao clonar: {info}")
    vozes = ler(VOZES, {})
    vozes[a.nome] = info["profile_id"]
    gravar(VOZES, vozes)
    print(f"Voz '{a.nome}' clonada: profile_id {info['profile_id']}")


def cmd_vozes(_):
    for nome, pid in ler(VOZES, {}).items():
        print(f"{nome}: {pid}")


# ---------- gerar ----------
def cmd_gerar(a):
    subir()
    vozes = ler(VOZES, {})
    pid = vozes.get(a.voz, a.voz)
    chave = f"{a.motor}:{a.passos}"
    ritmos = ler(RITMO, {})
    s_char = ritmos.get(chave, 0.146 * a.passos / 16)  # 1ª medição: OmniVoice no M1 Pro
    estimado = max(5.0, s_char * len(a.texto))
    saida = a.saida or os.path.join(BASE, "saida", time.strftime("fala_%Y%m%d_%H%M%S.wav"))
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    print(f"Gerando {len(a.texto)} caracteres | voz {a.voz} | motor {a.motor} | {a.passos} passos | "
          f"estimativa ~{estimado:.0f} s\n")
    res = {}

    def chamar():
        try:
            res["wav"], res["hdr"] = post_form("/generate", {
                "text": a.texto, "language": "Portuguese", "profile_id": pid, "engine": a.motor,
                "num_step": a.passos, "speed": a.velocidade, "effect_preset": a.efeito, "seed": a.seed,
                "instruct": a.instrucao, "wav_bits": "24"})
        except urllib.error.HTTPError as e:
            res["erro"] = f"HTTP {e.code}: {e.read().decode()[:600]}"
        except Exception as e:  # noqa: BLE001
            res["erro"] = str(e)

    t0 = time.time()
    th = threading.Thread(target=chamar, daemon=True)
    th.start()
    while th.is_alive():
        dec = time.time() - t0
        barra(min(99, dec / estimado * 100), f"{dec:5.1f} s  " + (f"faltam ~{estimado - dec:.0f} s" if dec < estimado else "finalizando..."))
        time.sleep(0.5)
    if "erro" in res:
        sys.exit(f"\nERRO: {res['erro']}")
    total = time.time() - t0
    with open(saida, "wb") as f:
        f.write(res["wav"])
    os.chmod(saida, 0o644)
    barra(100, f"{total:.0f} s")
    h = {k.lower(): v for k, v in res["hdr"].items()}
    gen = float(h.get("x-gen-time") or total)
    ritmos[chave] = round(0.5 * s_char + 0.5 * gen / max(len(a.texto), 1), 4)
    gravar(RITMO, ritmos)
    print(f"\n\nPronto: {float(h.get('x-audio-duration') or 0):.1f} s de áudio em {total:.0f} s "
          f"(seed {h.get('x-seed') or '?'})\n{saida}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("motores")
    p = sub.add_parser("instalar-motor"); p.add_argument("id")
    p = sub.add_parser("clonar"); p.add_argument("audio"); p.add_argument("nome")
    p.add_argument("--inicio", type=float); p.add_argument("--fim", type=float)
    sub.add_parser("vozes")
    p = sub.add_parser("gerar"); p.add_argument("texto"); p.add_argument("--voz", required=True)
    p.add_argument("--saida"); p.add_argument("--motor", default="omnivoice")
    p.add_argument("--passos", type=int, default=32); p.add_argument("--efeito", default="raw")
    p.add_argument("--seed", type=int); p.add_argument("--instrucao"); p.add_argument("--velocidade", type=float, default=1.0)
    a = ap.parse_args()
    {"motores": cmd_motores, "instalar-motor": cmd_instalar_motor, "clonar": cmd_clonar,
     "vozes": cmd_vozes, "gerar": cmd_gerar}[a.cmd](a)


if __name__ == "__main__":
    main()
