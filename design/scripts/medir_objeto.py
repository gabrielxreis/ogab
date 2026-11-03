"""Mede a caixa de um objeto/pessoa na referência (para o remake encaixar a foto no mesmo lugar e tamanho).

    .venv/bin/python medir_objeto.py ref.png --regiao x1 y1 x2 y2 [--limiar 45] [--largura 1080]

- `--ps "the camera"` (RECOMENDADO para objeto/pessoa): abre a referência no Photoshop, seleciona por IA
  (selection_select_by_prompt, prompt em inglês; vários separados por "|") e devolve a caixa da seleção.
  Pega partes escuras do objeto e ignora brilho/sombra em volta, onde o limiar de cor falha.
- Sem --ps: o fundo é estimado pela cor da borda da região; pixels que se afastam dele mais que --limiar viram objeto.
  Fica só o maior bloco conectado (sem partículas, brilhos soltos, textos pequenos).
- Saída em pixels do documento: {"x","y","w","h"} + prévia *.objeto.png. No arte.jsx:
  Y.colocar(foto, nome, grupo, {x,y,w,h}, "cobrir"|"conter") e depois Y.recortar; ou medir o remake também e
  corrigir escala/posição pela diferença (o recorte do remake tem a mesma lógica de caixa).
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def maior_bloco(m):
    from collections import deque
    h, w = m.shape; vis = np.zeros_like(m); melhor = None; tam = 0
    ys, xs = np.where(m)
    for y0, x0 in zip(ys[::7], xs[::7]):
        if vis[y0, x0]:
            continue
        q = deque([(y0, x0)]); vis[y0, x0] = True; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not vis[yy, xx]:
                    vis[yy, xx] = True; q.append((yy, xx))
        if len(pts) > tam:
            tam = len(pts); melhor = pts
    return melhor


def retangulo(mm, k):
    """Objeto de borda reta (celular, tela, quadro, livro) segurado/ocluído: ajusta as bordas ESQUERDA e DIREITA
    linha a linha só onde a largura é estável (sem dedo/mão), por regressão. Devolve ângulo verdadeiro, largura,
    topo (centro da borda de cima) e base visível, em pixels do documento. O PCA da máscara inteira erra
    alguns graus quando a mão entra na seleção."""
    linhas = [y for y in range(mm.shape[0]) if mm[y].any()]
    ys, xl, xr = [], [], []
    for y in linhas:
        xx = np.where(mm[y])[0]; ys.append(y); xl.append(xx.min()); xr.append(xx.max())
    ys, xl, xr = map(np.array, (ys, xl, xr)); w = xr - xl; n = len(ys)
    meio = slice(int(n * 0.12), int(n * 0.88))                    # sem os cantos arredondados
    wm = np.median(w[meio]); ok = np.zeros(n, bool); ok[meio] = np.abs(w[meio] - wm) < wm * 0.04
    def reta(x):
        A = np.vstack([ys[ok], np.ones(ok.sum())]).T; c = np.linalg.lstsq(A, x[ok], rcond=None)[0]
        res = x[ok] - A @ c; boa = np.abs(res) < 2.5                # 2ª passada sem os pontos que fogem (dedo)
        return np.linalg.lstsq(A[boa], x[ok][boa], rcond=None)[0]
    (ml, bl), (mr, br) = reta(xl), reta(xr)
    m = (ml + mr) / 2; ang = float(np.degrees(np.arctan(-m)))       # x cresce para cima -> topo para a direita
    cos = np.cos(np.radians(ang)); larg = float(np.median((xr - xl)[ok])) * cos
    # centro da borda de CIMA: ponto da linha central com a maior projeção no eixo do objeto (u aponta para cima)
    b = (bl + br) / 2; yc = float(ys.mean()); O = np.array([m * yc + b, yc]); u = np.array([-m, -1.0]); u /= np.linalg.norm(u)
    py, px = np.where(mm); P = np.vstack([px, py]).T - O; pr = P @ u
    tt, tb = np.percentile(pr, 99.9), np.percentile(pr, 0.1); T = O + u * tt; Bv = O + u * tb
    return {"angulo": round(ang, 1), "largura": round(larg * k), "topo": [round(T[0] * k, 1), round(T[1] * k, 1)],
            "base_visivel": [round(Bv[0] * k, 1), round(Bv[1] * k, 1)], "comprimento_visivel": round((tt - tb) * k),
            "faixas_limpas": int(ok.sum())}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("img"); ap.add_argument("--regiao", type=int, nargs=4)
    ap.add_argument("--limiar", type=float, default=45); ap.add_argument("--largura", type=int, default=1080)
    ap.add_argument("--escala-doc", action="store_true", help="regiao já em pixels do documento (1080)")
    ap.add_argument("--retangulo", action="store_true", help="objeto de borda reta: ajusta as bordas (ângulo e largura verdadeiros)")
    ap.add_argument("--ps", help='prompt(s) em inglês para a seleção por IA do Photoshop, ex.: "the camera|the lens"')
    a = ap.parse_args()
    im = Image.open(a.img).convert("RGB"); k = a.largura / im.width
    if a.ps:
        import re; slug = re.sub(r"[^a-z0-9]+", "-", a.ps.lower()).strip("-")[:40]
        MASCARA = os.path.splitext(a.img)[0] + f".{slug}.mascara.png"   # uma máscara por prompt (não sobrescreve)
        import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ps_lib as PS
        lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsx", "rick.jsx")
        r = PS.js(f"""$.evalFile({json.dumps(lib)}); var d = app.open(new File({json.dumps(os.path.abspath(a.img))})); Y.usar(d);
var out; try {{ if (d.mode != DocumentMode.RGB) d.changeMode(ChangeMode.RGB); Y.selecionarPorPrompt(d.activeLayer, {json.dumps(a.ps.split("|"))});
  var bb = d.selection.bounds; out = [bb[0].as("px"), bb[1].as("px"), bb[2].as("px"), bb[3].as("px")].join(",");
  var l = d.artLayers.add(); var c = new SolidColor(); c.rgb.hexValue = "FFFFFF"; d.selection.fill(c); d.selection.invert();
  c.rgb.hexValue = "000000"; d.selection.fill(c); d.selection.deselect();
  var o = new PNGSaveOptions(); d.saveAs(new File({json.dumps(MASCARA)}), o, true);
}} catch (e) {{ out = "ERRO " + e; }} d.close(SaveOptions.DONOTSAVECHANGES); out""", timeout=300)
        if r.startswith("ERRO"):
            print(r); return
        bx1, by1, bx2, by2 = [float(v) for v in r.split(",")]
        res = {"x": round(bx1 * k), "y": round(by1 * k), "w": round((bx2 - bx1) * k), "h": round((by2 - by1) * k)}
        # ângulo do eixo principal (PCA da máscara): 0 = em pé; positivo = topo inclinado para a DIREITA
        mm = np.asarray(Image.open(MASCARA).convert("L")) > 128; ys, xs = np.where(mm)
        if len(xs) > 50:
            cov = np.cov(np.vstack([xs - xs.mean(), ys - ys.mean()])); val, vec = np.linalg.eigh(cov); v = vec[:, 1]
            if v[1] > 0: v = -v
            res["angulo"] = round(float(np.degrees(np.arctan2(v[0], -v[1]))), 1)
            res["centro"] = [round(xs.mean() * k), round(ys.mean() * k)]
            if a.retangulo:
                res["retangulo"] = retangulo(mm, k)
        print(json.dumps(res)); print(MASCARA)
        return
    if not a.regiao:
        ap.error("--regiao é obrigatória sem --ps")
    x1, y1, x2, y2 = [round(v / k) for v in a.regiao] if a.escala_doc else a.regiao
    sub = np.asarray(im.crop((x1, y1, x2, y2)).filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    borda = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]); fundo = np.median(borda, axis=0)
    m = np.sqrt(((sub - fundo) ** 2).sum(axis=2)) > a.limiar
    pts = maior_bloco(m)
    if not pts:
        print("{}"); return
    ys = np.array([p[0] for p in pts]); xs = np.array([p[1] for p in pts])
    bx, by, bw, bh = xs.min() + x1, ys.min() + y1, xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    res = {"x": round(bx * k), "y": round(by * k), "w": round(bw * k), "h": round(bh * k)}
    prev = im.copy(); ImageDraw.Draw(prev).rectangle([bx, by, bx + bw, by + bh], outline=(255, 0, 0), width=2)
    saida = os.path.splitext(a.img)[0] + ".objeto.png"; prev.save(saida)
    print(json.dumps(res)); print(saida)


if __name__ == "__main__":
    main()
