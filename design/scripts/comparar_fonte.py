"""Comparador de fonte local: descobre qual fonte instalada/ativada mais se parece com uma linha de texto da referência.

    ~/.claude/skills/ogab/design/.venv/bin/python comparar_fonte.py imagem.png X1 Y1 X2 Y2 "TEXTO EXATO" [--filtro Good,Anton,Bebas] [--top 12]

- Renderiza o MESMO texto em cada fonte (sistema, ~/Library/Fonts e fontes ativadas pelo Adobe Fonts) e compara
  com o recorte da referência: forma (IoU dos pixels depois de igualar altura e largura) + proporção largura/altura.
- Devolve o ranking (PostScript name, nota) e salva uma folha `*.comparacao.png` com a referência em cima e as
  melhores candidatas embaixo (conferir com Read).
- Use junto com o reconhecer_fonte.py (Adobe): o Adobe sugere, ative as sugeridas da nuvem, e este aqui decide pela largura.
- `--filtro`: só fontes cujo nome contém algum dos termos (mais rápido). Sem filtro varre tudo (~1-3 min).
Dica: TEXTO EXATO tem que ser o que aparece no recorte (maiúsculas/minúsculas e acentos iguais).
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "fontes_indice.json")
PASTAS = ["/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts"),
          os.path.expanduser("~/Library/Application Support/Adobe/CoreSync/plugins/livetype")]
if os.name == "nt":  # Windows: sistema, fontes do usuário e Adobe Fonts (lá os arquivos vêm sem extensão: livetype/r/12560)
    PASTAS = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
              os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CoreSync", "plugins", "livetype")]


def indice():
    """Mapa PostScript name -> (arquivo, índice dentro do .ttc). Fica em cache; refaz se aparecerem arquivos novos."""
    arquivos = []
    for p in PASTAS:
        for raiz, _, nomes in os.walk(p):  # os.walk enxerga as pastas ocultas do Adobe Fonts (.r/.12345.otf)
            for n in nomes:
                f = os.path.join(raiz, n)
                if f.lower().endswith((".ttf", ".otf", ".ttc")) or (os.name == "nt" and p == PASTAS[-1] and "." not in n):
                    arquivos.append(f)
    try:
        c = json.load(open(CACHE))
        if c.get("n") == len(arquivos):
            return c["fontes"]
    except Exception:
        pass
    fontes = {}
    for f in arquivos:
        try:
            with open(f, "rb") as fb:
                ttc = fb.read(4) == b"ttcf"
            faces = TTCollection(f).fonts if ttc else [TTFont(f, lazy=True)]
        except Exception:
            continue
        for i, ft in enumerate(faces):
            try:
                ps = ft["name"].getDebugName(6)
                if ps and ps not in fontes and not ps.startswith("."):
                    cm = ft.getBestCmap() or {}
                    cob = "".join(chr(c) for c in cm if 32 <= c < 0x180)
                    fontes[ps] = [f, i, cob]
            except Exception:
                pass
    json.dump({"n": len(arquivos), "fontes": fontes}, open(CACHE, "w"))
    return fontes


def binarizar(im):
    """Texto vira branco (255) sobre preto. Decide a cor do texto pela minoria de pixels."""
    g = np.asarray(ImageOps.grayscale(im), dtype=np.float32)
    borda = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]).mean()   # o fundo é a cor das bordas
    lim = (g.max() + g.min()) / 2
    claro = g > lim
    return ~claro if borda > lim else claro


def faixa_principal(m):
    """Fica só a faixa de linhas de tinta principal (+ acentos/descendentes a até 15% da altura): pedaços da linha
    vizinha no recorte mudavam a proporção (12,6 -> 8,6) e faziam a fonte condensada vencer."""
    linhas = m.any(1); runs, ini = [], None
    for y, v in enumerate(list(linhas) + [False]):
        if v and ini is None: ini = y
        elif not v and ini is not None: runs.append((ini, y)); ini = None
    if len(runs) <= 1:
        return m
    peso = [m[a:b].sum() for a, b in runs]; i0 = int(np.argmax(peso)); a0, b0 = runs[i0]; h0 = b0 - a0; ok = [runs[i0]]
    for j, (a, b) in enumerate(runs):
        if j == i0: continue
        gap = a - b0 if a >= b0 else a0 - b
        if gap <= max(2, h0 * 0.15) and (b - a) < h0 * 0.45: ok.append((a, b))
    out = np.zeros_like(m)
    for a, b in ok: out[a:b] = m[a:b]
    return out


def apertar(m):
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def render(caminho, idx, texto, alt=120, ar=None):
    """Renderiza o texto. Com `ar` (largura/altura da referência), ajusta o espaço entre letras (tracking) até a
    proporção bater: assim a nota compara o DESENHO das letras, já que o tracking a gente ajusta no Photoshop."""
    try:
        fnt = ImageFont.truetype(caminho, alt, index=idx)
    except Exception:
        return None
    if ar:
        base = render(caminho, idx, texto, alt)
        if base is None or len(texto) < 2:
            return base
        extra = (ar * base.shape[0] - base.shape[1]) / (len(texto) - 1)
        if abs(extra) > alt * 0.25:   # precisaria de tracking absurdo: devolve sem ajuste (a nota de largura pune)
            return base
        try:
            larg = [fnt.getlength(c) for c in texto]
            W = int(sum(larg) + extra * len(texto) + alt * 2); im = Image.new("L", (max(8, W), alt * 3), 0); d = ImageDraw.Draw(im)
            x = alt / 2
            for c, w in zip(texto, larg):
                d.text((x, alt), c, font=fnt, fill=255); x += w + extra
            return apertar(np.asarray(im) > 128)
        except Exception:
            return base
    try:
        bx = fnt.getbbox(texto)
    except Exception:
        return None
    w, h = bx[2] - bx[0] + 20, bx[3] - bx[1] + 20
    if w <= 0 or h <= 0 or w > 8000:
        return None
    im = Image.new("L", (w, h), 0)
    try:
        ImageDraw.Draw(im).text((10 - bx[0], 10 - bx[1]), texto, font=fnt, fill=255)
    except Exception:
        return None
    return apertar(faixa_principal(np.asarray(im) > 128))   # mesma régua da referência


def nota(ref, cand, H=96):
    if cand is None or cand.shape[0] < 4:
        return 0, 0
    ar_ref, ar_c = ref.shape[1] / ref.shape[0], cand.shape[1] / cand.shape[0]
    larg = min(ar_ref, ar_c) / max(ar_ref, ar_c)          # 1 = mesma proporção (largura)
    W = max(8, int(H * ar_ref))
    a = np.asarray(Image.fromarray(ref.astype(np.uint8) * 255).resize((W, H))) > 128
    b = np.asarray(Image.fromarray(cand.astype(np.uint8) * 255).resize((W, H))) > 128
    iou = (a & b).sum() / max(1, (a | b).sum())
    # correlação das máscaras desfocadas: tolera 1-2 px de deslocamento (fonte fina/Light, onde o IoU despenca)
    def borra(m):
        return np.asarray(Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(H / 40)), dtype=np.float32)
    x, y = borra(a), borra(b); x -= x.mean(); y -= y.mean()
    corr = float((x * y).sum() / max(1e-6, np.sqrt((x * x).sum() * (y * y).sum())))
    forma = max(iou, corr) if a.mean() < 0.25 else iou   # traço fino ocupa pouco do recorte
    return forma * 0.65 + larg * 0.35, larg


def peso(ref, cand, H=96):
    """Proporção de tinta na mesma caixa: separa pesos da mesma família (Thin, Light, Regular, Bold)."""
    if cand is None:
        return 0
    W = max(8, int(H * ref.shape[1] / ref.shape[0]))
    a = (np.asarray(Image.fromarray(ref.astype(np.uint8) * 255).resize((W, H))) > 128).mean()
    b = (np.asarray(Image.fromarray(cand.astype(np.uint8) * 255).resize((W, H))) > 128).mean()
    return min(a, b) / max(a, b, 1e-6)


def intensidade(crop, cores, tol):
    """Mapa 0..1 de 'quanto é tinta' por pixel (antisserrilhado preservado): 1 - distância à cor do texto / tol."""
    px = np.asarray(crop, dtype=np.float32); d = np.full(px.shape[:2], 1e9, np.float32)
    for c in cores:
        al = np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.float32); d = np.minimum(d, np.sqrt(((px - al) ** 2).sum(2)))
    return np.clip(1 - d / (tol * 2.2), 0, 1)


def render_fino(caminho, idx, texto, alvo):
    """Renderiza em escala de cinza no tamanho do alvo (altura da caixa de tinta) com o espaçamento ajustado à largura."""
    H, W = alvo.shape
    try:
        fnt0 = ImageFont.truetype(caminho, 100, index=idx); bx = fnt0.getbbox(texto)
        if bx[3] - bx[1] <= 0: return None
        tam = 100 * H / (bx[3] - bx[1]); fnt = ImageFont.truetype(caminho, max(4, int(round(tam))), index=idx)
        larg = [fnt.getlength(ch) for ch in texto]; bx = fnt.getbbox(texto); natural = bx[2] - bx[0]
        extra = (W - natural) / max(1, len(texto) - 1)
        im = Image.new("L", (int(W + H * 4), int(H * 3)), 0); d = ImageDraw.Draw(im); x = H
        for ch, w in zip(texto, larg):
            d.text((x, H), ch, font=fnt, fill=255); x += w + extra
        a = np.asarray(im, np.float32) / 255; ys, xs = np.where(a > 0.5)
        if len(xs) == 0: return None
        a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
    except Exception:
        return None


def meia_espessura(m, maxit=20):
    """Meia-espessura média do traço em px: soma das áreas que sobrevivem a erosões sucessivas / área inicial."""
    cur = Image.fromarray((m * 255).astype(np.uint8)); tot = m.sum(); acc = 0
    for _ in range(maxit):
        cur = cur.filter(ImageFilter.MinFilter(3)); n = (np.asarray(cur) > 0).sum(); acc += n
        if n == 0: break
    return acc / max(1, tot)


def corr_desloc(a, b, raio=2):
    """Maior correlação normalizada entre a e b com deslocamento de até `raio` px (alinhamento sub-caixa)."""
    melhor = -1
    for dy in range(-raio, raio + 1):
        for dx in range(-raio, raio + 1):
            bb = np.roll(np.roll(b, dy, 0), dx, 1); x = a - a.mean(); y = bb - bb.mean()
            c = float((x * y).sum() / max(1e-6, np.sqrt((x * x).sum() * (y * y).sum()))); melhor = max(melhor, c)
    return melhor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("x1", type=int); ap.add_argument("y1", type=int)
    ap.add_argument("x2", type=int); ap.add_argument("y2", type=int); ap.add_argument("texto")
    ap.add_argument("--filtro", default="")
    ap.add_argument("--cor", default="", help="cor do texto na referência (#RRGGBB): pega só os pixels perto dessa cor (use quando há foto/objeto atrás ou na frente)")
    ap.add_argument("--tol", type=int, default=70); ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--sem-fino", action="store_true", help="pula a 2ª etapa (render no tamanho real + correlação)")
    a = ap.parse_args()
    crop = Image.open(a.img).convert("RGB").crop((a.x1, a.y1, a.x2, a.y2))
    if a.cor:
        px = np.asarray(crop, dtype=np.float32); m = np.zeros(px.shape[:2], dtype=bool)
        for c in a.cor.split(","):  # várias cores: "#FFFFFF,#3ED6A6" (linha com palavra destacada)
            c = c.strip(); alvo = np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)
            m |= np.sqrt(((px - alvo) ** 2).sum(axis=2)) < a.tol
        ref = apertar(faixa_principal(m))
    else:
        ref = apertar(faixa_principal(binarizar(crop)))
    fontes = indice()
    termos = [t.strip().lower() for t in a.filtro.split(",") if t.strip()]
    res = []
    precisa = {c for c in a.texto if c.isprintable() and c not in " \n"}   # caracteres de controle (\x03 quebra) não contam
    for ps, (f, i, cob) in fontes.items():
        if termos and not any(t in ps.lower() for t in termos):
            continue
        if not precisa.issubset(set(cob)):
            continue
        cand = render(f, i, a.texto)
        if cand is None:
            continue
        _, larg = nota(ref, cand)                       # largura natural (sem tracking)
        ajust = render(f, i, a.texto, ar=ref.shape[1] / ref.shape[0])
        forma, _ = nota(ref, ajust)
        dens = peso(ref, ajust)                          # espessura do traço (Thin x Light x Regular)
        # largura natural pesa de novo (sem isso fonte condensada + tracking enorme ganhava: Radiologia em GoodPro XCond)
        n = (forma - 0.35) / 0.65 * 0.5 + dens * 0.2 + larg ** 2 * 0.3
        if n > 0:
            res.append((n, larg, ps, f, i))
    res.sort(reverse=True)
    # 2ª etapa (fina): as 15 melhores renderizadas no tamanho REAL da referência, em cinza, comparadas por correlação
    if a.cor and len(res) > 1 and not a.sem_fino:
        crop_rgb = Image.open(a.img).convert("RGB").crop((a.x1, a.y1, a.x2, a.y2))
        it = intensidade(crop_rgb, [c.strip() for c in a.cor.split(",")], a.tol)
        ys, xs = np.where(it > 0.5)
        if len(xs) > 20:
            it = it[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            novos = []
            for n, larg, ps, f, i in res[:15]:
                r = render_fino(f, i, a.texto, it)
                fino = corr_desloc(it, r) if r is not None else 0
                novos.append((fino * 0.7 + n * 0.3, larg, ps, f, i))   # testados e piores: + tinta (52%), + espessura (55%)
            res = sorted(novos, reverse=True) + res[15:]
    top = res[:a.top]
    for n, larg, ps, f, i in top:
        print(f"{n:.3f}  largura {larg:.2f}  {ps}")
    # folha de comparação
    linhas = [Image.fromarray(ref.astype(np.uint8) * 255)]
    for n, larg, ps, f, i in top[:8]:
        linhas.append(Image.fromarray(render(f, i, a.texto, ar=ref.shape[1] / ref.shape[0]).astype(np.uint8) * 255))
    H = 60; ims = [im.resize((max(1, int(im.width * H / im.height)), H)) for im in linhas]
    W = max(im.width for im in ims) + 360
    folha = Image.new("L", (W, (H + 14) * len(ims)), 0); d = ImageDraw.Draw(folha)
    rot = ["REFERÊNCIA"] + [f"{t[0]:.2f} {t[2]}" for t in top[:8]]
    for k, im in enumerate(ims):
        folha.paste(im, (350, k * (H + 14))); d.text((6, k * (H + 14) + 20), rot[k], fill=200)
    saida = os.path.splitext(a.img)[0] + ".comparacao.png"
    folha.save(saida); print(saida)


if __name__ == "__main__":
    main()
