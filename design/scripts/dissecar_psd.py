"""Disseca um PSD SEM abrir o Photoshop (psd-tools): árvore de camadas, textos (fonte, tamanho, cor), efeitos,
smart objects, máscaras, recortes, ajustes + prévia em JPG. Serve para o Gab estudar o método de um designer.

    python3 dissecar_psd.py arquivo.psd pasta_saida/
Saída: <pasta>/<nome>.arvore.md (legível), <nome>.arvore.json, <nome>.preview.jpg
Requer: pip install psd-tools (o design usa um venv próprio em design/.venv).
"""
import json
import os
import sys

from psd_tools import PSDImage


def _cor(c):
    try:
        v = c["Values"]
        if v and len(v) == 4:  # [alpha, r, g, b] 0-1
            return "#%02X%02X%02X" % tuple(int(round(float(x) * 255)) for x in v[1:])
    except Exception:
        pass
    return None


def texto(layer):
    info = {"texto": layer.text.replace("\r", "\n")}
    try:
        fontes = [f.get("Name").value if hasattr(f.get("Name"), "value") else str(f.get("Name"))
                  for f in layer.resource_dict["FontSet"]]
        runs = layer.engine_dict["StyleRun"]
        estilos, vistos = [], set()
        texto_total = layer.text
        pos = 0
        for comp, st in zip(runs["RunLengthArray"], runs["RunArray"]):
            d = st["StyleSheet"]["StyleSheetData"]
            fonte = fontes[d["Font"]] if "Font" in d else None
            tam = round(float(d["FontSize"]), 1) if "FontSize" in d else None
            cor = _cor(d.get("FillColor")) if "FillColor" in d else None
            trecho = texto_total[pos:pos + comp].strip()
            pos += comp
            chave = (fonte, tam, cor, d.get("Tracking"), d.get("Leading"))
            e = {"fonte": fonte, "tamanho": tam, "cor": cor, "tracking": d.get("Tracking"),
                 "entrelinha": d.get("Leading"), "trecho": trecho[:60]}
            if chave not in vistos or len(estilos) < 8:
                estilos.append(e); vistos.add(chave)
        info["estilos"] = estilos[:8]
        try:
            m = layer.transform  # escala do texto (texto escalado no Free Transform)
            info["escala"] = round(float(m[0]), 3)
        except Exception:
            pass
        try:
            par = layer.engine_dict["ParagraphRun"]["RunArray"][0]["ParagraphSheet"]["Properties"]
            info["alinhamento"] = ["esquerda", "direita", "centro", "justificado"][int(par.get("Justification", 0)) % 4]
        except Exception:
            pass
    except Exception as e:
        info["erro_estilo"] = str(e)[:80]
    return info


def efeitos(layer):
    out = []
    try:
        if layer.effects and layer.effects.enabled:
            for fx in layer.effects:
                if getattr(fx, "enabled", True):
                    nome = type(fx).__name__
                    d = {"efeito": nome}
                    for k in ("size", "distance", "opacity", "angle", "blend_mode", "position", "choke"):
                        v = getattr(fx, k, None)
                        if v is not None:
                            d[k] = str(v)
                    try:
                        d["cor"] = _cor(fx.color) if fx.color else None
                    except Exception:
                        pass
                    out.append(d)
    except Exception:
        pass
    return out


def no(layer, prof):
    k = layer.kind
    d = {"nome": layer.name, "tipo": k, "visivel": layer.visible, "opacidade": round(layer.opacity / 255 * 100),
         "mesclagem": str(layer.blend_mode).split(".")[-1], "bbox": list(layer.bbox), "prof": prof}
    if getattr(layer, "clipping", False): d["recorte"] = True
    if layer.has_mask(): d["mascara"] = True
    if getattr(layer, "has_vector_mask", lambda: False)(): d["mascara_vetor"] = True
    fx = efeitos(layer)
    if fx: d["efeitos"] = fx
    if k == "type": d.update(texto(layer))
    if k == "smartobject":
        so = layer.smart_object
        d["smart"] = {"arquivo": so.filename, "vinculado": so.kind != "data", "formato": getattr(so, "filetype", None)}
        try:
            if layer.has_filters() if hasattr(layer, "has_filters") else False: d["filtros"] = True
        except Exception:
            pass
    if k in ("shape",):
        try:
            d["cor"] = _cor(layer.tagged_blocks.get_data(b"SoCo").get(b"Clr ")) if layer.tagged_blocks else None
        except Exception:
            pass
    if k == "artboard": d["prancheta"] = True
    if layer.is_group():
        d["filhos"] = [no(c, prof + 1) for c in reversed(list(layer))]  # psd-tools lista de baixo para cima
    return d


def linha_md(n):
    pad = "  " * n["prof"]
    extra = []
    if not n["visivel"]: extra.append("oculta")
    if n["opacidade"] != 100: extra.append(f"{n['opacidade']}%")
    if n["mesclagem"] not in ("NORMAL", "PASS_THROUGH"): extra.append(n["mesclagem"].lower())
    if n.get("recorte"): extra.append("recorte")
    if n.get("mascara"): extra.append("máscara")
    if n.get("mascara_vetor"): extra.append("máscara vetorial")
    if n.get("efeitos"): extra.append("fx: " + ", ".join(e["efeito"] for e in n["efeitos"]))
    if n.get("smart"): extra.append(f"SO {'vinc.' if n['smart']['vinculado'] else 'incorp.'}: {n['smart']['arquivo']}")
    b = n["bbox"]; tam = f"{b[2]-b[0]}x{b[3]-b[1]} @ {b[0]},{b[1]}"
    s = f"{pad}- **{n['nome']}** [{n['tipo']}] {tam}" + (f" ({'; '.join(extra)})" if extra else "")
    out = [s]
    if n["tipo"] == "type":
        t = n["texto"].replace("\n", " / ")[:120]
        out.append(f"{pad}  - texto: \"{t}\"" + (f", alinh. {n['alinhamento']}" if n.get("alinhamento") else ""))
        for e in n.get("estilos", [])[:4]:
            esc = n.get("escala", 1) or 1
            tam_real = round(e["tamanho"] * esc, 1) if e.get("tamanho") else None
            out.append(f"{pad}  - {e['fonte']} {e['tamanho']}pt (≈{tam_real}px) {e['cor']} tracking {e['tracking']}: \"{e['trecho']}\"")
    for c in n.get("filhos", []):
        out += linha_md(c)
    return out


def main(arq, saida):
    os.makedirs(saida, exist_ok=True)
    psd = PSDImage.open(arq)
    base = os.path.splitext(os.path.basename(arq))[0]
    arvore = [no(l, 0) for l in reversed(list(psd))]  # mesma ordem do painel Camadas
    meta = {"arquivo": os.path.basename(arq), "largura": psd.width, "altura": psd.height,
            "modo": str(psd.color_mode).split(".")[-1], "camadas_total": sum(1 for _ in psd.descendants())}
    json.dump({"meta": meta, "arvore": arvore}, open(os.path.join(saida, base + ".arvore.json"), "w"), indent=1, ensure_ascii=False, default=str)
    md = [f"# {meta['arquivo']}", "", f"{psd.width}x{psd.height} px, {meta['modo']}, {meta['camadas_total']} camadas", "", "Árvore (de cima para baixo):", ""]
    for n in arvore:
        md += linha_md(n)
    open(os.path.join(saida, base + ".arvore.md"), "w").write("\n".join(md) + "\n")
    try:
        img = psd.topil()  # imagem composta salva no próprio PSD (rápido)
        if img is None:
            img = psd.composite()
        img = img.convert("RGB"); img.thumbnail((1600, 1600)); img.save(os.path.join(saida, base + ".preview.jpg"), quality=85)
    except Exception as e:
        print("sem prévia:", e)
    print(f"{base}: {meta['camadas_total']} camadas, {psd.width}x{psd.height}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
