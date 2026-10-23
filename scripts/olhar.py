#!/usr/bin/env python3
"""Imagem leve para o Claude olhar (economia de tokens).

Mac: sips (nativo). Windows/Linux: Pillow. Sem nenhum dos dois, o Read segue normal.
Uma imagem de 1920x1080 custa ~1.800 tokens; com 1024 px no lado maior, ~700.
Para conferir rosto, enquadramento, legenda e cor, 1024 px basta.

Modos:
  hook (PreToolUse do Read, registrado em ~/.claude/settings.json):
      python3 olhar.py hook          lê o JSON do Claude Code no stdin e, se a imagem
                                     passar de 1024 px, troca o caminho por uma cópia
                                     reduzida em ~/.cache/olhar/ (o original fica intacto).
      Não reduz: folhas de contato/grades (nome com folha, sheet, grade, grid, tile,
      contato, mapa), arquivo com _full no nome, ou com OLHAR=0 no ambiente.
  recorte (ver um detalhe em resolução cheia, barato):
      python3 olhar.py recorte <img> <x> <y> <larg> <alt> [saida.jpg]
  reduzir à mão:
      python3 olhar.py <img> [--max 1024]
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

LIMITE = 1024
CACHE = os.path.expanduser("~/.cache/olhar")
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff", ".bmp"}
NAO_REDUZ = re.compile(r"folha|sheet|grade|grid|tile|contato|mapa|_full", re.I)


def _pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


SIPS = sys.platform == "darwin" and shutil.which("sips")


def dims(p):
    if SIPS:
        o = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", p],
                           capture_output=True, text=True).stdout
        w = re.search(r"pixelWidth: (\d+)", o)
        h = re.search(r"pixelHeight: (\d+)", o)
        return (int(w.group(1)), int(h.group(1))) if w and h else (0, 0)
    Image = _pillow()
    if not Image:
        return (0, 0)          # sem sips nem Pillow: não reduz (o Read segue normal)
    with Image.open(p) as im:
        return im.size


def reduzir(p, limite=LIMITE):
    st = os.stat(p)
    chave = hashlib.sha1(f"{p}|{st.st_mtime_ns}|{st.st_size}|{limite}".encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    nome = re.sub(r"[^\w.-]", "_", os.path.splitext(os.path.basename(p))[0])[:40]
    saida = os.path.join(CACHE, f"{nome}_{chave}.jpg")
    if not os.path.exists(saida):
        if SIPS:
            subprocess.run(["sips", "-Z", str(limite), "-s", "format", "jpeg", "-s", "formatOptions", "82",
                            p, "--out", saida], capture_output=True, check=True)
        else:                  # Windows/Linux: Pillow (o windows\install.ps1 já instala)
            Image = _pillow()
            with Image.open(p) as im:
                im = im.convert("RGB")
                im.thumbnail((limite, limite), Image.LANCZOS)
                im.save(saida, "JPEG", quality=82)
    return saida


def hook():
    try:
        dado = json.load(sys.stdin)
    except Exception:
        return
    entrada = dado.get("tool_input") or {}
    p = entrada.get("file_path") or ""
    if os.environ.get("OLHAR") == "0" or not p or p.startswith(CACHE):
        return
    if os.path.splitext(p)[1].lower() not in EXTS or NAO_REDUZ.search(os.path.basename(p)):
        return
    if not os.path.isfile(p):
        return
    try:
        w, h = dims(p)
        if max(w, h) <= LIMITE:
            return
        novo = reduzir(p)
    except Exception:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": f"olhar.py: {w}x{h} reduzida para {LIMITE} px (detalhe: olhar.py recorte)",
        "updatedInput": {**entrada, "file_path": novo},
    }}))


def recorte(args):
    img, x, y, lw, lh = args[0], *map(int, args[1:5])
    saida = args[5] if len(args) > 5 else os.path.join(
        CACHE, f"recorte_{os.path.splitext(os.path.basename(img))[0]}_{x}_{y}_{lw}x{lh}.jpg")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", img, "-vf", f"crop={lw}:{lh}:{x}:{y}",
                    "-q:v", "3", saida], check=True)
    print(saida)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["hook"]:
        hook()
    elif a[:1] == ["recorte"] and len(a) >= 5:
        recorte(a[1:])
    elif a:
        lim = int(a[a.index("--max") + 1]) if "--max" in a else LIMITE
        print(reduzir(os.path.abspath(a[0]), lim))
    else:
        print(__doc__)
