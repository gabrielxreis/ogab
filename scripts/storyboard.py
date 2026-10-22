"""Storyboard ANTES do render (regra do usuário, 16/10/2026): roteiro cena a cena + 3 quadros parados para aprovar.
Ajuste vem por número de cena e só aquela cena muda; render só depois do "pode renderizar".

  python3 storyboard.py <pasta_do_motion> [--tempos 1.2,6,13.5] [--cena 3] [--plano plano.json]

<pasta_do_motion> é a pasta HyperFrames (index.html com data-composition-id). Sem --tempos, escolhe 3 momentos:
o gancho, a cena principal e o fecho, cada um depois da entrada dos elementos (65% da cena). --cena N fotografa só
a cena N (depois de um ajuste). Lê as cenas do plano.js (presets) ou do --plano.

Saída na própria pasta:
  storyboard.md    tabela de batidas: cena, tempo, tipo, mensagem e som (vai para o usuário)
  storyboard.jpg   os quadros lado a lado, com o número da cena e o tempo
O Gab manda os dois e PARA. Nada de render antes da aprovação.
"""
import json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from navegador import rodar


def composicao(pasta):
    html = open(os.path.join(pasta, "index.html"), encoding="utf-8").read()
    pega = lambda k, p: float((re.search(r'data-%s="([\d.]+)"' % k, html) or [0, p])[1])
    return int(pega("width", 1080)), int(pega("height", 1920)), pega("duration", 10)


def _txt(x):
    """Texto da cena em uma linha, aceite string, lista, lista de listas ou itens {t: ...}."""
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return str(x.get("t") or x.get("texto") or "")
    if isinstance(x, (list, tuple)):
        return " / ".join(p for p in (_txt(i) for i in x) if p)
    return str(x)


def cenas_do_plano(pasta, plano=None):
    try:
        if plano:
            P = json.load(open(plano, encoding="utf-8"))
        else:
            txt = open(os.path.join(pasta, "plano.js"), encoding="utf-8").read()
            P = json.loads(re.sub(r"^\s*window\.PLANO\s*=\s*|;\s*$", "", txt.strip()))
    except Exception:
        return []
    t, out = 0.0, []
    for i, c in enumerate(P.get("cenas", []), 1):
        d = float(c.get("dur", 3))
        texto = _txt(c.get("texto") or c.get("titulo") or c.get("frase") or c.get("nome") or c.get("linhas")
                     or c.get("palavras") or c.get("grupos") or c.get("antes") or c.get("itens") or "")
        out.append({"n": i, "ini": t, "dur": d, "tipo": c.get("tipo", ""), "texto": re.sub(r"[*|]+", " ", texto).replace("  ", " ").strip(),
                    "som": c.get("som", "")})
        t += d
    return out


def escolher(cenas, dur):
    if not cenas:
        return [round(dur * f, 2) for f in (.2, .5, .85)]
    if len(cenas) <= 3:
        alvo = cenas
    else:
        meio = max(cenas[1:-1], key=lambda c: c["dur"])   # a cena principal costuma ser a mais longa
        alvo = [cenas[0], meio, cenas[-1]]
    return [round(c["ini"] + c["dur"] * .65, 2) for c in alvo]


def cena_de(t, cenas):
    for c in cenas:
        if c["ini"] <= t < c["ini"] + c["dur"] + 1e-6:
            return c["n"]
    return "?"


def folha(fotos, rotulos, saida, larg=360):
    """Quadros lado a lado com rótulo (Pillow se tiver; senão ffmpeg sem rótulo)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        ims = [Image.open(f).convert("RGB") for f in fotos]
        ims = [im.resize((larg, round(im.height * larg / im.width))) for im in ims]
        alt = max(im.height for im in ims) + 54
        out = Image.new("RGB", (larg * len(ims) + 16 * (len(ims) + 1), alt + 16), (24, 24, 26))
        try:
            fonte = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except Exception:
            fonte = ImageFont.load_default()
        d = ImageDraw.Draw(out)
        for i, (im, r) in enumerate(zip(ims, rotulos)):
            x = 16 + i * (larg + 16)
            out.paste(im, (x, 16)); d.text((x + 4, 16 + im.height + 14), r, fill=(235, 235, 240), font=fonte)
        out.save(saida, quality=90)
    except ImportError:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + sum([["-i", f] for f in fotos], []) +
                       ["-filter_complex", "".join(f"[{i}]scale={larg}:-1[v{i}];" for i in range(len(fotos))) +
                        "".join(f"[v{i}]" for i in range(len(fotos))) + f"hstack={len(fotos)}", saida], check=True)


def main(a):
    if not a:
        raise SystemExit(__doc__)
    pasta = os.path.abspath(a[0])
    op = lambda k: a[a.index(k) + 1] if k in a else None
    W, H, dur = composicao(pasta)
    cenas = cenas_do_plano(pasta, op("--plano"))
    if op("--tempos"):
        tempos = [float(x) for x in op("--tempos").split(",")]
    elif op("--cena"):
        c = cenas[int(op("--cena")) - 1]; tempos = [round(c["ini"] + c["dur"] * .65, 2)]
    else:
        tempos = escolher(cenas, dur)
    tmp = tempfile.mkdtemp(prefix="storyboard_")
    fotos = rodar("quadros.mjs", [os.path.join(pasta, "index.html"), tmp, ",".join(map(str, tempos)), W, H])
    rot = [(f"Cena {cena_de(t, cenas)} · " if cenas else "") + f"{t:.1f} s" for t in tempos]
    folha(fotos, rot, os.path.join(pasta, "storyboard.jpg"))
    linhas = ["# Storyboard", "", f"{W}x{H}, {dur:g} s. Aprovar antes do render; ajuste por número de cena (só ela muda).", "",
              "| Cena | Tempo | Tipo | Mensagem | Som |", "|---|---|---|---|---|"]
    for c in cenas:
        linhas.append(f"| {c['n']} | {c['ini']:.1f}-{c['ini'] + c['dur']:.1f} s | {c['tipo']} | {c['texto']} | {c['som']} |")
    if not cenas:
        linhas.append("| (sem plano) | | | descrever as cenas à mão | |")
    open(os.path.join(pasta, "storyboard.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    print(os.path.join(pasta, "storyboard.md")); print(os.path.join(pasta, "storyboard.jpg"))


if __name__ == "__main__":
    main(sys.argv[1:])
