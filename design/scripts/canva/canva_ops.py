"""Plano da arte (plano.json) -> operações do edit-design do conector do Canva, página por página.

O script NÃO chama o Canva (quem chama é o Claude, pelas ferramentas do conector): ele só monta a lista de operações
na ordem certa (de baixo para cima), para colar no `edit-design`.

  python3 canva_ops.py plano.json --kit kit.json --midias midias.json [--pagina 1]

kit.json (lido com read-design na cópia do kit da marca): página e caixas de texto por estilo, cada caixa já na fonte
da marca. Ex.: {"page_id": "PB...", "caixas": {"titulo": ["PB...-LBa", "PB...-LBb"], "corpo": ["PB...-LBc"], ...}}
midias.json: {"fundo_p1.png": "MAH...", "logo.png": "MAH..."} (mediaId de cada upload).

No plano, cada texto leva "estilo" (titulo, subtitulo, corpo, destaque, botao...) = a caixa do kit que ele usa (a fonte
vem dela). Texto sem estilo, ou sem caixa sobrando no kit, vira add_text na fonte padrão do Canva (o script avisa).
Trecho de outra cor ("faixas") vira um elemento de texto separado (o Canva formata o elemento inteiro).
Caixas do kit que sobrarem são apagadas no fim.
"""
import argparse, json, os, sys

AVISOS = []


def _caminho_forma(c):
    w, h = float(c["w"]), float(c["h"])
    if c.get("forma") == "elipse":
        rx, ry = w / 2, h / 2
        return f"M0 {ry} A{rx} {ry} 0 1 0 {w} {ry} A{rx} {ry} 0 1 0 0 {ry} Z"
    return f"M0 0 H{w} V{h} H0 Z"


def _texto(c, pid, caixas, usadas):
    ops, estilo = [], c.get("estilo")
    livres = [l for l in caixas.get(estilo or "", []) if l not in usadas]
    txt = c["texto"].upper() if c.get("caixa_alta") else c["texto"]
    fmt = {k: v for k, v in {
        "font_size": int(round(float(c["tamanho"]))) if c.get("tamanho") else None,
        "color": c.get("cor"), "font_weight": ("bold" if c.get("negrito") else None),
        "font_style": ("italic" if c.get("italico") else None),
        "line_height": c.get("entrelinha"),
        "text_align": {"esquerda": "start", "centro": "center", "direita": "end"}.get(c.get("alinhar", ""), None),
    }.items() if v is not None}
    if livres:
        loc = livres[0]; usadas.add(loc)
        ops.append({"type": "replace_text", "locator_id": loc, "text": txt})
        ops.append({"type": "resize_element", "locator_id": loc, "width": float(c["w"])})
        if fmt:
            ops.append({"type": "format_text", "locator_id": loc, "formatting": fmt})
        ops.append({"type": "position_element", "locator_id": loc, "top": float(c["y"]), "left": float(c["x"])})
        ops.append({"type": "layer_element", "locator_id": loc, "position": "front"})
    else:
        if estilo:
            AVISOS.append(f"sem caixa '{estilo}' sobrando no kit para '{txt[:30]}': entra na fonte padrão do Canva")
        else:
            AVISOS.append(f"texto sem 'estilo' ('{txt[:30]}'): entra na fonte padrão do Canva")
        ops.append({"type": "add_text", "page_id": pid, "text": txt, "top": float(c["y"]), "left": float(c["x"]),
                    "width": float(c["w"])})
        ops.append({"type": "format_text", "locator_id": "<<id do texto novo: pegar no documento da resposta>>",
                    "formatting": fmt})
    if c.get("faixas"):
        AVISOS.append(f"'{txt[:30]}' tem trecho colorido: no Canva cada cor é um texto separado (quebrar no plano)")
    return ops


def operacoes(plano, kit, midias, pagina):
    pg = plano["paginas"][pagina - 1]
    pid, caixas, usadas, ops = kit["page_id"], kit.get("caixas", {}), set(), []
    for c in pg["camadas"]:
        t = c["tipo"]
        if t == "imagem":
            mid = midias.get(c["arquivo"]) or midias.get(os.path.basename(c["arquivo"]))
            if not mid:
                AVISOS.append(f"sem mediaId para {c['arquivo']}: subir com create-upload-url antes"); continue
            if c.get("fundo"):
                ops.append({"type": "update_fill", "locator_id": pid, "asset_type": "image", "asset_id": mid,
                            "alt_text": c.get("nome", "fundo")[:250]})
            else:
                ops.append({"type": "insert_fill", "page_id": pid, "asset_type": "image", "asset_id": mid,
                            "alt_text": c.get("nome", os.path.basename(c["arquivo"]))[:250],
                            "left": float(c["x"]), "top": float(c["y"]), "width": float(c["w"]), "height": float(c["h"]),
                            **({"opacity": float(c["opacidade"])} if c.get("opacidade") is not None else {})})
        elif t == "forma":
            op = {"type": "insert_shape", "page_id": pid, "top": float(c["y"]), "left": float(c["x"]),
                  "width": float(c["w"]), "height": float(c["h"]), "path": _caminho_forma(c),
                  "view_box_width": float(c["w"]), "view_box_height": float(c["h"])}
            if c.get("cor"):
                op["color"] = c["cor"].upper()
            if c.get("opacidade") is not None:
                op["opacity"] = float(c["opacidade"])
            if c.get("forma") == "arredondado":
                op["corner_rounding"] = float(c.get("raio", 24))
            if c.get("borda"):
                op["stroke_color"] = c["borda"].get("cor", "#000000").upper(); op["stroke_weight"] = float(c["borda"].get("px", 1))
            ops.append(op)
        elif t == "texto":
            ops += _texto(c, pid, caixas, usadas)
    for estilo, locs in caixas.items():
        for loc in locs:
            if loc not in usadas:
                ops.append({"type": "delete_element", "locator_id": loc})
    return ops


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plano"); ap.add_argument("--kit", required=True); ap.add_argument("--midias", required=True)
    ap.add_argument("--pagina", type=int, default=1)
    a = ap.parse_args()
    ops = operacoes(json.load(open(a.plano, encoding="utf-8")), json.load(open(a.kit, encoding="utf-8")),
                    json.load(open(a.midias, encoding="utf-8")), a.pagina)
    print(json.dumps(ops, ensure_ascii=False, indent=1))
    for av in AVISOS:
        print("AVISO:", av, file=sys.stderr)
