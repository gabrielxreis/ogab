#!/usr/bin/env python3
"""Upscale de imagem com IA, local e grátis (Real-ESRGAN ncnn-vulkan, xinntao, licença BSD-3). Roda no Mac (Apple
Silicon e Intel), Windows e Linux, na GPU pela Vulkan/Metal. Pedido do usuário em 29/10/2026: foto do Gemini saía em
1376 px e ficava borrada em tela cheia.

  python3 upscale.py <imagem ou pasta> [--escala 2|3|4] [--modelo foto|anime] [--saida <arquivo ou pasta>] [--largura N]

  --escala   2, 3 ou 4 (padrão 4). O modelo de foto é sempre 4x; 2x e 3x saem do 4x reduzido em Lanczos (fica melhor
             que o Lanczos direto).
  --modelo   foto (realesrgan-x4plus, padrão: gente, produto, paisagem) | anime (ilustração, desenho, 2D)
  --largura  reduz o resultado até essa largura (ex.: 2400 para web), mantendo a proporção.
  --saida    padrão: <nome>_up.png ao lado do original (pasta: <pasta>/upscale/).

Na primeira vez baixa o programa do GitHub oficial (versão fixada abaixo, ~52 MB) para ~/.cache/ogab/realesrgan
(Windows: %LOCALAPPDATA%/ogab/realesrgan). Nada fica dentro da skill.
Não usar para "recuperar" o rosto de uma pessoa real em foto pequena demais (a IA inventa detalhe): abaixo de ~400 px
de rosto, avisar antes.
"""
import argparse, os, shutil, subprocess, sys, tempfile, urllib.request, zipfile

VERSAO = "v0.2.5.0"
ZIPS = {"darwin": "realesrgan-ncnn-vulkan-20220424-macos.zip",
        "win32": "realesrgan-ncnn-vulkan-20220424-windows.zip",
        "linux": "realesrgan-ncnn-vulkan-20220424-ubuntu.zip"}
URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/{v}/{z}"
MODELOS = {"foto": "realesrgan-x4plus", "anime": "realesrgan-x4plus-anime"}
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def pasta_bin():
    base = os.environ.get("LOCALAPPDATA") if os.name == "nt" else os.path.expanduser("~/.cache")
    return os.path.join(base, "ogab", "realesrgan")


def programa():
    """Caminho do executável; baixa e descompacta na primeira vez."""
    d = pasta_bin()
    exe = os.path.join(d, "realesrgan-ncnn-vulkan" + (".exe" if os.name == "nt" else ""))
    if os.path.exists(exe):
        return exe
    plat = "darwin" if sys.platform == "darwin" else ("win32" if os.name == "nt" else "linux")
    url = URL.format(v=VERSAO, z=ZIPS[plat])
    os.makedirs(d, exist_ok=True)
    print(f"baixando o Real-ESRGAN {VERSAO} (~52 MB) de {url}", file=sys.stderr)
    tmp = os.path.join(d, "_download.zip")
    urllib.request.urlretrieve(url, tmp)
    with zipfile.ZipFile(tmp) as z:
        z.extractall(d)
    os.remove(tmp)
    if not os.path.exists(exe):   # alguns zips vêm com uma pasta dentro
        for raiz, _, arqs in os.walk(d):
            if os.path.basename(exe) in arqs:
                for a in os.listdir(raiz):
                    shutil.move(os.path.join(raiz, a), d)
                break
    if os.name != "nt":
        os.chmod(exe, 0o755)
        if sys.platform == "darwin":   # sem a quarentena o macOS deixa rodar
            subprocess.run(["xattr", "-dr", "com.apple.quarantine", d], capture_output=True)
    return exe


def um(exe, ent, sai, escala, modelo, largura):
    from PIL import Image
    ent, sai = os.path.abspath(ent), os.path.abspath(sai)   # o programa roda com cwd na pasta dele
    with tempfile.TemporaryDirectory() as tmp:
        src = ent
        if not ent.lower().endswith((".jpg", ".jpeg", ".png")):   # webp etc.: o programa lê só jpg/png
            src = os.path.join(tmp, "in.png"); Image.open(ent).convert("RGB").save(src)
        x4 = os.path.join(tmp, "x4.png")
        r = subprocess.run([exe, "-i", src, "-o", x4, "-n", MODELOS[modelo], "-s", "4"],
                           cwd=os.path.dirname(exe), capture_output=True, text=True)
        if r.returncode or not os.path.exists(x4):
            raise SystemExit(f"UPSCALE_FALHOU {ent}: {(r.stderr or r.stdout)[-300:]}")
        im = Image.open(x4)
        w0, h0 = Image.open(ent).size
        alvo = (w0 * escala, h0 * escala)
        if largura and alvo[0] > largura:
            alvo = (largura, round(alvo[1] * largura / alvo[0]))
        if im.size != alvo:
            im = im.resize(alvo, Image.LANCZOS)
        os.makedirs(os.path.dirname(os.path.abspath(sai)), exist_ok=True)
        if sai.lower().endswith((".jpg", ".jpeg")):
            im.convert("RGB").save(sai, quality=92)
        else:
            im.save(sai)
    print(f"ok {os.path.basename(ent)} {w0}x{h0} -> {alvo[0]}x{alvo[1]} {sai}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("entrada")
    ap.add_argument("--escala", type=int, default=4, choices=[2, 3, 4])
    ap.add_argument("--modelo", default="foto", choices=list(MODELOS))
    ap.add_argument("--saida")
    ap.add_argument("--largura", type=int)
    a = ap.parse_args()
    exe = programa()
    if os.path.isdir(a.entrada):
        arqs = sorted(f for f in os.listdir(a.entrada) if f.lower().endswith(EXTS))
        dest = a.saida or os.path.join(a.entrada, "upscale")
        for f in arqs:
            um(exe, os.path.join(a.entrada, f), os.path.join(dest, os.path.splitext(f)[0] + "_up.png"), a.escala, a.modelo, a.largura)
    else:
        sai = a.saida or os.path.splitext(a.entrada)[0] + "_up.png"
        um(exe, a.entrada, sai, a.escala, a.modelo, a.largura)


if __name__ == "__main__":
    main()
