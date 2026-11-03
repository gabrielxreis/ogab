"""Ciclo fechado "idêntico": mede a referência, monta, MEDE O REMAKE com a mesma regra e corrige os alvos até bater.

    python3 ciclo.py pasta_da_arte MARCA=... [--voltas 3]

A pasta tem `arte.jsx` e `medidas.json`:
    {"ref": "caminho/ref.png",
     "itens": [{"nome": "TITULO 1", "cor": "#FFFFFF,#3ED6A6", "regiao": [x1, y1, x2, y2]}, ...]}
  - regiao em pixels da REFERÊNCIA (a mesma usada no medir_texto.py), uma linha de texto por item.
  - "texto": o conteúdo da linha (decide se confere pelo corpo da maiúscula ou pela faixa do x).
O ciclo grava `alvos.json` ({nome: {x,y,w,h,cy,ch,xy,xh,cor}}) que o arte.jsx lê com
    var ALV = Y.lerJSON(PASTA + "/alvos.json");   ...  alvo: ALV["TITULO 1"]
Volta 1: alvos = medida da referência. Depois de montar, mede o remake (mesma cor, mesma região convertida) e
corrige cada alvo pelo erro (alvo += ref - remake), cancelando vieses do Photoshop (borda antisserrilhada na caixa
da camada, métrica da fonte). Para quando o erro máximo fica <= 1 px ou acabam as voltas.
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(AQUI, "..", ".venv", "bin", "python")
CAMPOS = ("x", "y", "w", "h", "cy", "ch", "xy", "xh")


def usados(texto, r):
    """Campos que o Y.encaixarTexto usa: caixa alta encaixa pelo corpo (cy/ch), minúscula pela faixa do x (xy/xh)."""
    if texto and texto == texto.upper():
        return ("x", "w", "cy", "ch") if "ch" in r else ("x", "w", "y", "h")
    if texto:
        return ("x", "w", "xy", "xh") if "xh" in r else ("x", "w", "y", "h")
    return ("x", "w", "cy", "ch", "xy", "xh")


def medir(img, cor, regiao, juntar=3, centro_y=None):
    out = subprocess.run([PY, os.path.join(AQUI, "medir_texto.py"), img, "--cor", cor, "--regiao", *map(str, regiao), "--juntar", str(juntar)],
                         capture_output=True, text=True).stdout.splitlines()
    linhas = json.loads(out[0]) if out else []
    if not linhas:
        return None
    if centro_y is not None:   # a linha cujo meio está mais perto do centro esperado (caixa do OCR invade a vizinha)
        return min(linhas, key=lambda d: abs(d["y"] + d["h"] / 2 - centro_y) - (0 if d["h"] > 8 else -999))
    return max(linhas, key=lambda d: d["w"] * d["h"])   # a linha principal da região


def main():
    pasta = os.path.abspath(sys.argv[1]); extras = [a for a in sys.argv[2:] if "=" in a and not a.startswith("--")]
    voltas = int(sys.argv[sys.argv.index("--voltas") + 1]) if "--voltas" in sys.argv else 3
    cfg = json.load(open(os.path.join(pasta, "medidas.json")))
    from PIL import Image
    wref = Image.open(cfg["ref"]).width
    ref = {}
    for it in cfg["itens"]:
        m = medir(cfg["ref"], it["cor"], it["regiao"], it.get("juntar", 3), it.get("centro_y"))
        if not m:
            print("sem medida na referência:", it["nome"]); continue
        # sanidade: altura-x/maiúscula incoerente com a caixa (linhas vizinhas coladas, fragmento) -> encaixa pela caixa
        if "xh" in m and not (0.35 * m["h"] <= m["xh"] <= 0.8 * m["h"] and m["y"] <= m["xy"] <= m["y"] + m["h"]): m.pop("xh"); m.pop("xy", None)
        if "ch" in m and not (0.5 * m["h"] <= m["ch"] <= 1.0 * m["h"] and m["y"] <= m["cy"] <= m["y"] + m["h"]): m.pop("ch"); m.pop("cy", None)
        ref[it["nome"]] = m
    alvos = {n: dict(v) for n, v in ref.items()}
    melhor = {n: (9e9, dict(v)) for n, v in ref.items()}   # melhor erro e o alvo que o produziu, por item
    for volta in range(1, voltas + 1):
        json.dump(alvos, open(os.path.join(pasta, "alvos.json"), "w"), ensure_ascii=False, indent=1)
        r = subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), os.path.join(pasta, "arte.jsx"),
                            f"SAIDA={pasta}", f"PASTA={pasta}", *extras], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-800:], r.stderr[-800:]); return
        png = [f for f in os.listdir(pasta) if f.endswith(".png") and not any(s in f for s in (".medidas", "sobrepos", ".objeto", ".mascara"))]
        png = max((os.path.join(pasta, f) for f in png), key=os.path.getmtime)
        wrm = Image.open(png).width; k = wrm / wref
        pior = 0; print(f"volta {volta}:")
        for it in cfg["itens"]:
            n = it["nome"]
            if n not in ref:
                continue
            # no remake mede só em volta da caixa da referência (+14 px): foto/mão diferente perto não contamina
            R_ = ref[n]; mg = max(4, min(14, round(R_["h"] * 0.3)))   # folga proporcional: linhas pequenas empilhadas não se misturam
            rg = [max(0, round(R_["x"] - mg)), max(0, round(R_["y"] - mg)), round(R_["x"] + R_["w"] + mg), round(R_["y"] + R_["h"] + mg)]
            m = medir(png, it.get("cor_remake", it["cor"]), rg, it.get("juntar", 1 if not it.get("bloco") else 30), ref[n]["y"] + ref[n]["h"] / 2)   # junção mínima: linhas coladas não se fundem
            if not m:
                print(f"  {n}: não achei no remake"); continue
            usa = ("x", "w", "y") if it.get("bloco") else (usados(it.get("texto", ""), ref[n]) if ref[n]["h"] >= 34 else ("x", "w", "y", "h"))   # bloco: largura + topo; minúsculo: caixa inteira
            err = {c: ref[n][c] - m[c] for c in usa if c in m and c in ref[n]}
            e = max(abs(v) for v in err.values()); pior = max(pior, e)
            print(f"  {n:<22} erro máx {e:>3} px  " + " ".join(f"{c}{v:+d}" for c, v in err.items() if v))
            if e < melhor[n][0]:
                melhor[n] = (e, dict(alvos[n]))
            elif e > melhor[n][0]:   # piorou: volta ao melhor alvo e não corrige mais este item
                alvos[n] = dict(melhor[n][1]); continue
            for c, v in err.items():   # trava: no máximo 25% do valor da referência, nunca <= 0 em tamanho
                lim = max(3, abs(ref[n][c]) * 0.25 if c in ("w", "h", "ch", "xh") else 40)
                novo = alvos[n][c] + max(-lim, min(lim, v))
                if c in ("w", "h", "ch", "xh"): novo = max(ref[n][c] * 0.6, min(ref[n][c] * 1.6, novo))
                alvos[n][c] = round(novo)
        if pior <= 1:
            print("bateu (<= 1 px)"); break
    ultimo = json.load(open(os.path.join(pasta, "alvos.json")))
    alvos = {n: melhor[n][1] if melhor[n][0] < 9e9 else alvos[n] for n in alvos}   # fica o melhor de cada item
    if alvos != ultimo:   # o PSD final tem que sair com os MELHORES alvos, não com os da última volta
        json.dump(alvos, open(os.path.join(pasta, "alvos.json"), "w"), ensure_ascii=False, indent=1)
        subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), os.path.join(pasta, "arte.jsx"), f"SAIDA={pasta}", f"PASTA={pasta}", *extras], capture_output=True, text=True)
        print("montagem final com os melhores alvos")
    json.dump(alvos, open(os.path.join(pasta, "alvos.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
