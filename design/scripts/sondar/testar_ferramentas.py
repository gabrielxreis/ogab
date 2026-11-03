"""Testa TODAS as ferramentas nativas do agente do Photoshop num documento de teste e grava o veredito.

    python3 ~/.claude/skills/ogab/design/scripts/sondar/testar_ferramentas.py [--imagem foto_com_pessoa.png] [--so nome1,nome2]

- Monta um documento com foto, texto, forma, prancheta e as 14 camadas de ajuste.
- Gera parâmetros mínimos válidos a partir do JSON Schema de cada ferramenta (com ajustes conhecidos em AJUSTES).
- Depois de cada ferramenta volta o documento pelo histórico (history_set_state), então uma não estraga a outra.
- Pula as que gastam crédito generativo (gen_tech_*) e as que mexem em arquivo (abrir/salvar/fechar).
Resultado: docs/catalogo/local/teste_ferramentas.json (+ resumo na tela). Precisa catalogar.py rodado antes.
"""
import argparse
import base64
import json
import os
import struct
import sys
import time
import zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import ps_lib as PS  # noqa: E402

LOCAL = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "docs", "catalogo", "local")
T = {x["name"]: x for x in json.load(open(os.path.join(LOCAL, "agente_ferramentas.json")))}
F = PS.ferramenta

PULAR = {"application_document_close", "application_document_save", "application_document_open"}
PULAR |= {n for n in T if n.startswith("gen_tech")}
# rodam por último (mudam o documento inteiro)
DESTRUTIVAS = ["application_document_duplicate", "document_delete_layers", "layer_merge_visible", "document_resize",
               "document_rotate_image", "document_flip_image", "document_resize_canvas", "document_content_aware_expand",
               "document_delete_artboard", "layer_cleanup_delete_empty_layers", "document_promote_background_layer"]
PRECISA_SELECAO = {"document_erase_selected_pixels", "document_remove_selection", "layer_set_mask_from_selection",
                   "layer_new_via_copy", "selection_contract", "selection_expand", "selection_feather",
                   "selection_smooth", "selection_invert_selection"}
RET = {"top": 100, "left": 100, "bottom": 400, "right": 500}


def png_mascara(w, h):
    """PNG em tons de cinza com um quadrado branco no meio (para selection_set_selection_from_mask)."""
    linhas = b"".join(b"\x00" + bytes(255 if (w // 4 < x < 3 * w // 4 and h // 4 < y < 3 * h // 4) else 0 for x in range(w))
                      for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(linhas)) + chunk(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagem", help="foto com uma pessoa (para selecionar assunto / remover fundo)")
    ap.add_argument("--so", help="testar só estas ferramentas (separadas por vírgula)")
    a = ap.parse_args()

    PS.js("while(app.documents.length) app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); 'ok'")
    D = F("application_new_document", {"width": {"value": 1080, "unit": "pixels"}, "height": {"value": 1350, "unit": "pixels"},
                                       "resolution": {"value": 72, "unit": "pixels_per_inch"}, "mode": "RGBColor",
                                       "fill": "white", "name": "orick_testador"})["data"]["doc_id"]
    if a.imagem:
        img = os.path.abspath(a.imagem).replace("\\", "/")
        PS.js(f"""function s(x){{return stringIDToTypeID(x);}} var a=new ActionDescriptor(); a.putPath(s("null"), new File("{img}"));
executeAction(s("placeEvent"),a,DialogModes.NO); app.activeDocument.activeLayer.rasterize(RasterizeType.ENTIRELAYER);
app.activeDocument.activeLayer.name="FOTO"; 'ok'""")
    else:
        PS.js("""var d=app.activeDocument; var l=d.artLayers.add(); l.name="FOTO"; d.selection.select([[200,300],[880,300],[880,1100],[200,1100]]);
var c=new SolidColor(); c.rgb.hexValue="3366CC"; d.selection.fill(c); d.selection.deselect(); 'ok'""")
    ids = {}
    ids["text"] = F("document_create_text_layer", {"doc_id": D, "text": "TESTE", "font_postscript_name": "Montserrat-Bold",
                    "font_size": {"value": 80, "unit": "pixels"}, "position_x": 50, "position_y": 10, "position": "top"})["data"]["layer_id"]
    ids["shape"] = F("shape_layer_create_shape_layer", {"doc_id": D, "shape_type": "rectangle", "appearance": {"corner_radius": 20,
                     "fill_color": {"r": 10, "g": 10, "b": 10}, "fill_enabled": True},
                     "transform": {"top_left": {"x": 100, "y": 1100}, "width": 400, "height": 100}})["data"]["layer_id"]
    F("layer_effect_add_stroke", {"doc_id": D, "layer_id": ids["text"], "size": 3, "stroke_color": {"r": 0, "g": 0, "b": 0}})
    resultados = {}

    def registra(n, p, r, ms):
        resultados[n] = {"ok": r.get("status") == "success", "ms": ms, "params": p,
                         "resposta": json.dumps(r, ensure_ascii=False)[:800]}
        print(("OK   " if resultados[n]["ok"] else "FALHA"), n, "" if resultados[n]["ok"] else resultados[n]["resposta"][:200], flush=True)

    art = F("document_create_artboard", {"doc_id": D, "name": "AB", "anchor": {"x": 1200, "y": 0}, "size": {"width": 500, "height": 500}})
    registra("document_create_artboard", {}, art, 0)
    ids["artboard"] = (art.get("data") or {}).get("layer_id")
    adj = {}
    for n in sorted(T):
        if n.startswith("document_create_") and n.endswith("_layer") and n not in (
                "document_create_text_layer", "document_create_pixel_layer", "document_create_group_layer", "document_create_solid_color_layer"):
            p = {"doc_id": D, "position": "top"}
            if n == "document_create_photo_filter_layer":
                p["color"] = {"r": 255, "g": 160, "b": 60}
            t0 = time.time(); r = F(n, p); registra(n, p, r, int((time.time() - t0) * 1000))
            if r.get("status") == "success":
                adj[n[len("document_create_"):-len("_layer")]] = r["data"]["layer_id"]
    est = F("document_get_structure", {"doc_id": D})["data"]["layers"]
    def acha(ls, nome):
        for l in ls:
            if l["name"] == nome: return l["id"]
            x = acha(l.get("children", []), nome)
            if x: return x
    ids["pixel"] = acha(est, "FOTO")
    mascara = base64.b64encode(png_mascara(1080, 1350)).decode()

    def layer_para(n):
        if n.startswith("text_layer") or "stroke" in n: return ids["text"]
        if n.startswith("shape_layer"): return ids["shape"]
        if "artboard" in n: return ids["artboard"]
        for k, v in adj.items():
            if f"_{k}_" in f"_{n}_": return v
        return ids["pixel"]

    FIXOS = {"doc_id": D, "prompt": "o retângulo azul", "text": "Novo texto", "name": "orick", "preset_id": "P02",
             "mask_data": mascara, "use_generative_ai": False, "bounds": RET, "area_frame": RET}

    def gera(sch, nome, ferr):
        if nome in FIXOS: return FIXOS[nome]
        if nome == "layer_id": return layer_para(ferr)
        if nome == "layer_ids": return [ids["text"], ids["shape"]]
        if nome == "relative_to_layer_id": return ids["text"]
        if nome == "history_id": return None
        if not isinstance(sch, dict): return None
        if "allOf" in sch:
            junto = {"type": "object", "properties": {}, "required": []}
            for s in sch["allOf"] + [sch]:
                junto["properties"].update(s.get("properties") or {}); junto["required"] += s.get("required") or []
            return gera(junto, nome, ferr)
        for alt in ("oneOf", "anyOf"):
            if alt in sch:
                base = {k: v for k, v in sch.items() if k != alt}
                op = sch[alt][0]
                if "properties" in base or "required" in base:
                    op = {"type": "object", "properties": {**(base.get("properties") or {}), **(op.get("properties") or {})},
                          "required": (base.get("required") or []) + (op.get("required") or [])}
                return gera(op, nome, ferr)
        if "enum" in sch: return sch["enum"][0]
        tp = sch.get("type")
        if isinstance(tp, list): tp = tp[0]
        if tp == "object" or "properties" in sch:
            req = sch.get("required") or []
            return {k: gera(v, k, ferr) for k, v in (sch.get("properties") or {}).items() if k in req}
        if tp == "array":
            return [gera(sch.get("items", {}), nome[:-1] if nome.endswith("s") else nome, ferr)]
        if tp == "boolean": return False
        if tp in ("integer", "number"):
            lo = sch.get("minimum", sch.get("exclusiveMinimum", 0)); hi = sch.get("maximum", 100)
            v = max(lo + (1 if "exclusiveMinimum" in sch else 0), min(hi, 10))
            return int(v) if tp == "integer" else float(v)
        if tp == "string": return "orick"
        return None

    AJUSTES = {
        "shape_layer_create_shape_layer": {"transform": {"top_left": {"x": 100, "y": 100}, "width": 200, "height": 100}},
        "layer_fill_with_color": {"color": {"r": 200, "g": 30, "b": 30}},
        "document_resize_canvas": {"bounds": {"top": -50, "left": -50, "bottom": 1400, "right": 1130}},
        "document_content_aware_expand": {"bounds": {"top": -50, "left": -50, "bottom": 1400, "right": 1130}},
        "layer_resize": {"width": 50, "height": 50},
        "text_layer_set_frame_type": {"frame_type": "area"},
    }
    nomes = [n for n in sorted(T) if n not in PULAR and n not in resultados and n not in DESTRUTIVAS] + DESTRUTIVAS
    if a.so:
        nomes = [n for n in nomes if n in a.so.split(",")]
    for n in nomes:
        p = gera(T[n]["input_schema"], "", n)
        p = p if isinstance(p, dict) else {}
        p.update(AJUSTES.get(n, {}))
        if n == "history_set_state":
            p["history_id"] = F("history_get_list", {"doc_id": D})["data"]["current_entry"]["id"]
        if n in PRECISA_SELECAO:
            F("selection_rectangular_marquee", {"doc_id": D, "bounds": {"top": 400, "left": 300, "bottom": 900, "right": 800}})
        antes = F("history_get_list", {"doc_id": D})["data"]["current_entry"]["id"]
        docs_antes = {d["doc_id"] for d in F("application_list_open_documents")["data"]["open_documents"]}
        t0 = time.time()
        try:
            r = F(n, p)
        except Exception as e:
            r = {"status": "exception", "data": str(e)[:300]}
        registra(n, p, r, int((time.time() - t0) * 1000))
        for d in F("application_list_open_documents")["data"]["open_documents"]:
            if d["doc_id"] not in docs_antes:
                registra("application_document_close", {"doc_id": d["doc_id"]},
                         F("application_document_close", {"doc_id": d["doc_id"], "force_save": False}), 0)
        F("history_set_state", {"doc_id": D, "history_id": antes})
        F("selection_deselect_all", {"doc_id": D})
    saida = os.path.join(LOCAL, "teste_ferramentas.json")
    json.dump({"photoshop": PS.js("app.version"), "data": time.strftime("%Y-%m-%d %H:%M"), "alertas": PS.ALERTAS,
               "resultados": resultados}, open(saida, "w"), indent=1, ensure_ascii=False)
    ok = sum(v["ok"] for v in resultados.values())
    print(f"\n{ok}/{len(resultados)} ok. Alertas fechados: {len(PS.ALERTAS)}. Resultado em {saida}")


if __name__ == "__main__":
    main()
