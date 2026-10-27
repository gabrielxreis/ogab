#!/usr/bin/env python3
"""Prints grandes de TODAS as cenas antes do render (regra do usuário, 27/10/2026: "você precisa tirar print antes de
renderizar, o cenário tá mega preto, personagens bugados, funções bugadas e muito feio"; "salva isso para nunca mais dar
esses furos").

  python3 prints_cenas.py <pasta_da_composicao> <plano.json> [--em 0.85] [--largura 360] [--saida folha.png]

Tira 1 print por cena no estado quase final (85% da cena, quando tudo já entrou), monta uma folha em tamanho de LEITURA
(360 px por quadro, 4 por linha; nunca miniatura) e faz a conferência automática que dá para fazer sem olho:
  - ESCURO: brilho médio da área do cenário abaixo de 38 (0-255) = cena escura demais;
  - BORDA: conteúdo claro encostando na borda esquerda/direita = objeto cortado ou fora do centro;
  - VAZIO: quase nada além do fundo = objeto não apareceu (material/luz quebrados);
  - TEXTO: objeto 3D encostando no texto do cartão, do CTA ou do carimbo (prints de novo sem o texto e compara).
Sai com código 1 se algum alerta disparar. Depois disso, OLHAR a folha cena a cena com o checklist do SKILL.md
("Prints antes de renderizar") e só então renderizar.
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def hf():
    return subprocess.run([sys.executable, os.path.join(AQUI, "componentes.py"), "hf"], capture_output=True, text=True).stdout.strip() or "hyperframes"


def medir(png):
    """(brilho médio da área do cenário, fração de pixels claros nas bordas laterais, fração de pixels 'de conteúdo')."""
    from PIL import Image
    im = Image.open(png).convert("L"); w, h = im.size
    area = im.crop((0, int(h * .32), w, int(h * .95)))   # abaixo do cartão
    px = list(area.getdata()); media = sum(px) / len(px)
    fundo = sorted(px)[len(px) // 2]
    conteudo = sum(1 for p in px if p > fundo + 40) / len(px)
    faixa = max(2, w // 60)
    bordas = [im.crop((0, int(h * .32), faixa, int(h * .95))), im.crop((w - faixa, int(h * .32), w, int(h * .95)))]
    claro = max(sum(1 for p in b.getdata() if p > fundo + 70) / (b.size[0] * b.size[1]) for b in bordas)
    return media, claro, conteudo


def texto_x_objeto(comp, tempos):
    """Por cena, fração do TEXTO (cartão, CTA, carimbo) que encosta em OBJETO 3D (regra do usuário, 27/10/2026: "os
    objetos estão atrapalhando a escrita, não pode ter isso"). Tira os prints de novo numa cópia sem o texto
    (visibility hidden): texto = o que muda entre as duas; objeto = o que é claro no print sem texto."""
    import shutil, tempfile
    from PIL import Image, ImageChops, ImageFilter
    copia = tempfile.mkdtemp(prefix="sem_texto_")
    shutil.copytree(comp, copia, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".hyperframes"))
    for f in os.listdir(copia):
        if f.endswith(".css"):
            open(os.path.join(copia, f), "a", encoding="utf-8").write("\n#card, #cta, #carimbo, #legenda { visibility: hidden !important; }\n")
    subprocess.run(["npx", "--yes", hf(), "snapshot", copia, "--at", ",".join(map(str, tempos))], capture_output=True, text=True)
    sn = os.path.join(copia, ".hyperframes", "artifacts", "snapshots"); ps = max((os.path.join(sn, d) for d in os.listdir(sn)), key=os.path.getmtime)
    return ps, sorted(f for f in os.listdir(ps) if f.startswith("frame-") and f.endswith(".png"))


def sobrepoe(com, sem):
    from PIL import Image, ImageChops, ImageFilter
    A = Image.open(com).convert("L").resize((270, 480)); Bm = Image.open(sem).convert("L").resize((270, 480))
    texto = ImageChops.difference(A, Bm).point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(9))
    px = list(Bm.getdata()); fundo = sorted(px)[len(px) // 2]
    obj = Bm.point(lambda v: 255 if v > fundo + 45 else 0).filter(ImageFilter.MinFilter(3))   # MinFilter tira a poeira
    t = sum(1 for v in texto.getdata() if v); o = ImageChops.multiply(texto, obj); n = sum(1 for v in o.getdata() if v)
    return (n / t) if t else 0.0


def main(a):
    if len(a) < 2:
        raise SystemExit(__doc__)
    comp, plano = os.path.abspath(a[0]), json.load(open(a[1], encoding="utf-8"))
    frac = float(a[a.index("--em") + 1]) if "--em" in a else .85
    larg = int(a[a.index("--largura") + 1]) if "--largura" in a else 360
    saida = a[a.index("--saida") + 1] if "--saida" in a else os.path.join(comp, "prints_cenas.png")
    cenas = plano["cenas"]; tempos = [round(c["de"] + frac * (c["ate"] - c["de"]), 2) for c in cenas]
    r = subprocess.run(["npx", "--yes", hf(), "snapshot", comp, "--at", ",".join(map(str, tempos))], capture_output=True, text=True)
    snaps = os.path.join(comp, ".hyperframes", "artifacts", "snapshots")
    pasta = max((os.path.join(snaps, d) for d in os.listdir(snaps)), key=os.path.getmtime)
    fs = sorted(f for f in os.listdir(pasta) if f.startswith("frame-") and f.endswith(".png"))[:len(cenas)]
    alertas = []
    for k, (c, f) in enumerate(zip(cenas, fs), 1):
        media, borda, cont = medir(os.path.join(pasta, f))
        nome = f"cena {k} ({c.get('tipo', 'globo')}, {c['de']:.1f}s)"
        if media < 38: alertas.append(f"ESCURO  {nome}: brilho {media:.0f}")
        if borda > .04: alertas.append(f"BORDA   {nome}: conteúdo encostando na lateral ({borda:.0%})")
        if cont < .01 and c.get("tipo"): alertas.append(f"VAZIO   {nome}: quase nada além do fundo")
    if "--sem-texto" not in a:   # objeto encostando no texto (cartão/CTA/carimbo)
        try:
            ps, fs2 = texto_x_objeto(comp, tempos)
            for k, (c, f1, f2) in enumerate(zip(cenas, fs, fs2), 1):
                fr = sobrepoe(os.path.join(pasta, f1), os.path.join(ps, f2))
                if fr > .06: alertas.append(f"TEXTO   cena {k} ({c.get('tipo', 'globo')}, {c['de']:.1f}s): objeto encostando no texto ({fr:.0%} do texto)")
        except Exception as e:
            alertas.append(f"TEXTO   não consegui conferir texto x objeto: {e}")
    # folha: 4 por linha, 360 px por quadro, com o número da cena (Pillow; o ffmpeg nem sempre tem drawtext)
    from PIL import Image, ImageDraw, ImageFont
    qs = []
    for k, f in enumerate(fs, 1):
        im = Image.open(os.path.join(pasta, f)).convert("RGB"); im = im.resize((larg, int(im.size[1] * larg / im.size[0])))
        d = ImageDraw.Draw(im)
        try: fonte = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
        except Exception: fonte = ImageFont.load_default()
        d.rectangle((6, 6, 58, 46), fill=(0, 0, 0)); d.text((14, 10), str(k), fill=(255, 255, 255), font=fonte); qs.append(im)
    alt = qs[0].size[1]; cols = 4; rows = (len(qs) + cols - 1) // cols
    folha = Image.new("RGB", (larg * cols, alt * rows), (0, 0, 0))
    for k, q in enumerate(qs): folha.paste(q, ((k % cols) * larg, (k // cols) * alt))
    folha.save(saida)
    print(f"folha: {saida} ({len(fs)} cenas)")
    for x in alertas:
        print("ALERTA", x)
    print("conferência automática: " + ("OK" if not alertas else f"{len(alertas)} alerta(s)") + " · agora OLHAR a folha com o checklist antes do render")
    return 1 if alertas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
