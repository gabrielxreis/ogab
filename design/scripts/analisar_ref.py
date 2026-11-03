"""Lê o SISTEMA de design de uma referência (post/capa): paleta com proporções e grade de texto.

    .venv/bin/python analisar_ref.py ref.png [--largura 1080] [--k 7]

PALETA (k-médias em Lab): cores dominantes com % de área, papel provável (dominante 60 / secundária 30 /
destaque 10) e se o destaque é saturado. Use para tokens da marca e para conferir o remake (--comparar remake.png
dá a diferença de cor ΔE por papel).
GRADE: acha as linhas de texto (pixels claros sobre escuro ou escuros sobre claro, em faixas horizontais) e infere
alinhamento (esquerda/centro/direita pelo desvio das bordas), margens, eixo, ritmo vertical (passo entre linhas)
e escala tipográfica (razão entre alturas de linha: 1,25 terça maior, 1,5 quinta, 1,618 áurea...).
"""
import argparse
import json

import numpy as np
from PIL import Image


def lab(rgb):
    c = rgb / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883]); f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)


def kmeans(X, k, it=25, seed=1):
    rng = np.random.default_rng(seed); C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(it):
        d = ((X[:, None] - C[None]) ** 2).sum(2); L = d.argmin(1)
        C = np.array([X[L == j].mean(0) if (L == j).any() else C[j] for j in range(k)])
    return C, L


def paleta(img, k):
    a = np.asarray(img.convert("RGB").resize((240, int(240 * img.height / img.width)))).reshape(-1, 3).astype(float)
    C, L = kmeans(lab(a), k); res = []
    for j in range(k):
        m = L == j
        if m.sum() == 0: continue
        rgb = np.median(a[m], 0); croma = float(np.hypot(*lab(rgb[None])[0][1:]))
        res.append({"hex": "#%02X%02X%02X" % tuple(int(v) for v in rgb), "area": round(100 * m.mean(), 1), "croma": round(croma)})
    res.sort(key=lambda r: -r["area"])
    if res:
        res[0]["papel"] = "dominante (60)"
        if len(res) > 1: res[1]["papel"] = "secundária (30)"
        dest = max(res[2:] or res[1:], key=lambda r: r["croma"] * (1 if r["area"] < 20 else 0.3))
        dest["papel"] = dest.get("papel", "") or "destaque (10)"
    return res


def grade(img, W, destaque=None, regiao=None):
    g = np.asarray(img.convert("L"), float); k = W / img.width
    fundo = np.median(g); claro = fundo < 128
    m = (g > 200) if claro else (g < 60)
    if destaque:   # palavra destacada na cor da marca também é texto
        rgb = np.asarray(img.convert("RGB"), float); alvo = np.array([int(destaque[i:i + 2], 16) for i in (1, 3, 5)], float)
        m |= np.sqrt(((rgb - alvo) ** 2).sum(2)) < 45
    if regiao:
        x1, y1, x2, y2 = [round(v / k) for v in regiao]; z = np.zeros_like(m); z[y1:y2, x1:x2] = m[y1:y2, x1:x2]; m = z
    on = m.sum(1) > max(3, m.shape[1] * 0.01)
    linhas, ini = [], None
    for y, v in enumerate(list(on) + [False]):
        if v and ini is None: ini = y
        elif not v and ini is not None:
            if y - ini >= 4:
                cols = np.where(m[ini:y].sum(0) > 0)[0]
                if len(cols) and (cols.max() - cols.min()) > img.width * 0.08:
                    linhas.append([round(cols.min() * k), round(ini * k), round(cols.max() * k), round(y * k)])
            ini = None
    if not linhas:
        return {"linhas": []}
    L = np.array(linhas, float); esq, dir_ = L[:, 0], W - L[:, 2]; cen = (L[:, 0] + L[:, 2]) / 2 - W / 2
    disp = {"esquerda": np.std(esq), "direita": np.std(dir_), "centro": np.std(cen)}
    # agrupa: cada linha entra no alinhamento em que tem mais vizinhas (borda/eixo a <= 10 px)
    grupos = []
    for i in range(len(L)):
        op = {"esquerda": esq, "centro": cen, "direita": dir_}
        melhor = max(op, key=lambda n: (np.abs(op[n] - op[n][i]) <= 10).sum() + (0.5 if n == "centro" and abs(cen[i]) < 12 else 0))
        grupos.append(melhor)
    resumo = {}
    for i, gname in enumerate(grupos):
        v = {"esquerda": esq, "centro": cen + W / 2, "direita": W - dir_}[gname][i]
        resumo.setdefault(gname, []).append((i, int(v)))
    alinh = "; ".join(f"{n} em ~{int(np.median([v for _, v in lst]))} px: linhas {[i + 1 for i, _ in lst]}" for n, lst in resumo.items())
    alturas = L[:, 3] - L[:, 1]; passos = np.diff(L[:, 1]) if len(L) > 1 else np.array([])
    tams = sorted(set(round(h / 4) * 4 for h in alturas), reverse=True)
    razoes = [round(tams[i] / tams[i + 1], 2) for i in range(len(tams) - 1) if tams[i + 1] > 0]
    return {"alinhamento": alinh, "dispersao_px": {k_: round(v, 1) for k_, v in disp.items()},
            "margem_esq": int(np.median(esq)), "margem_dir": int(np.median(dir_)), "linhas": linhas,
            "passos_verticais": [int(p) for p in passos], "alturas": [int(h) for h in alturas], "escala_tipografica": razoes}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("--largura", type=int, default=1080)
    ap.add_argument("--k", type=int, default=7); ap.add_argument("--comparar")
    ap.add_argument("--regiao", type=int, nargs=4, help="só procura texto nessa área (px do documento)")
    a = ap.parse_args(); im = Image.open(a.ref)
    p = paleta(im, a.k)
    def h2l_(h): return lab(np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)]], float))[0]
    dest = next((c["hex"] for c in p if "destaque" in c.get("papel", "") and c["area"] < 8 and c["croma"] > 30
                 and np.linalg.norm(h2l_(c["hex"]) - h2l_(p[0]["hex"])) > 40), None)   # só destaque de verdade (pequeno, saturado, longe do fundo)
    gr = grade(im, a.largura, dest, a.regiao)
    print("PALETA:"); [print(f"  {c['hex']}  {c['area']:5.1f}%  croma {c['croma']:3d}  {c.get('papel', '')}") for c in p]
    print(f"GRADE: alinhamento {gr.get('alinhamento')}  margens {gr.get('margem_esq')}/{gr.get('margem_dir')}  dispersão {gr.get('dispersao_px')}")
    print(f"  linhas (x1,y1,x2,y2): {gr.get('linhas')}")
    print(f"  alturas {gr.get('alturas')}  passos {gr.get('passos_verticais')}  escala {gr.get('escala_tipografica')}")
    if a.comparar:
        q = paleta(Image.open(a.comparar), a.k)
        def h2l(h): return lab(np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)]], float))[0]
        print("COMPARAR (ΔE76 por cor da referência -> cor mais próxima do remake; < 5 ok, > 12 visível):")
        for c in p[:5]:
            d = min(float(np.linalg.norm(h2l(c["hex"]) - h2l(r["hex"]))) for r in q)
            print(f"  {c['hex']} ({c['area']}%) ΔE {d:.1f}")


if __name__ == "__main__":
    main()
