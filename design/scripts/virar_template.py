"""Transforma uma reconstrução (pasta do reconstruir.py) num TEMPLATE da marca: troca o texto, mantém o estilo.

    python3 virar_template.py pasta_reconstrucao
    python3 montar.py pasta/template.jsx PASTA=pasta SAIDA=pasta/saida TEXTOS='{"L02": "ENFERMAGEM", "L03": "Uma das **profissões** mais..."}'

Lê o editavel.psd: para cada camada de texto guarda fonte, tamanho real (px), tracking, entrelinha, cor, alinhamento
(centro/esquerda/direita pela posição no documento) e a âncora (eixo, margem, linha de base). O template.jsx
recria o post com o FUNDO LIMPO e os textos novos; marcação no texto:
  **palavras**  -> negrito da linha (fonte de negrito informada no reconstruir ou a do original)
  {{palavras}}  -> cor de destaque usada no original (a primeira faixa colorida)
Linhas sem texto novo ficam como no original; "" apaga a linha.
"""
import json
import os
import sys

from psd_tools import PSDImage


def main():
    pasta = os.path.abspath(sys.argv[1]); psd = PSDImage.open(os.path.join(pasta, "editavel.psd")); W = psd.width
    arte = open(os.path.join(pasta, "arte.jsx")).read()
    linhas = []
    decl = {c["nome"]: c for c in json.load(open(os.path.join(pasta, "camadas.json")))} if os.path.exists(os.path.join(pasta, "camadas.json")) else {}
    for l in psd.descendants():
        if l.kind != "type":
            continue
        ed = l.engine_dict; runs = ed["StyleRun"]["RunArray"]; ss = runs[0]["StyleSheet"]["StyleSheetData"]
        k = l.transform[3] if hasattr(l, "transform") else 1
        fontes = [f["Name"] for f in l.resource_dict["FontSet"]]
        def fonte_run(r): return str(fontes[r["StyleSheet"]["StyleSheetData"].get("Font", 0)]).strip("\x27\x22")
        def cor_run(r):
            v = r["StyleSheet"]["StyleSheetData"].get("FillColor", {}).get("Values", [1, 1, 1, 1]); return "#%02X%02X%02X" % tuple(round(x * 255) for x in v[1:4])
        tam = ed["StyleRun"]["RunLengthArray"]; conta = {}
        for r, n in zip(runs, tam): conta[(fonte_run(r), cor_run(r))] = conta.get((fonte_run(r), cor_run(r)), 0) + n
        base_f, base_c = max(conta, key=conta.get)   # estilo da MAIORIA dos caracteres
        neg = next((fonte_run(r) for r in runs if fonte_run(r) != base_f), None)
        dest = next((cor_run(r) for r in runs if cor_run(r) != base_c), None)
        chave = l.name.split(" ")[0]
        if chave in decl or l.name in decl:   # estilo declarado pelo reconstruir (mais confiável que os trechos do PSD)
            dd = decl.get(chave) or decl[l.name]; base_f, base_c, neg, dest = dd["fonte"], dd["cor"], dd["negrito"], dd["destaque"]
        x1, y1, x2, y2 = l.bbox; cx = (x1 + x2) / 2
        alinh = "centro" if abs(cx - W / 2) < W * 0.04 else ("esq" if x1 < W - x2 else "dir")
        linhas.append({"id": l.name.split(" ")[0], "nome": l.name, "texto": l.text.replace("\r", "\\n"), "fonte": base_f,
                       "px": round(float(ss.get("FontSize", 40)) * k, 2), "tracking": int(ss.get("Tracking", 0)),
                       "entrelinha": round(float(ss.get("Leading", 0)) * k, 2) if not ss.get("AutoLeading", True) else None,
                       "cor": base_c, "negrito": neg, "destaque": dest, "alinh": alinh,
                       "x": {"centro": round(cx), "esq": x1, "dir": x2}[alinh], "topo": y1})
    dest_g = next((x["destaque"] for x in linhas if x["destaque"]), None)   # cor de destaque da peça vale para todas as linhas
    for x in linhas: x["destaque"] = x["destaque"] or dest_g
    json.dump(linhas, open(os.path.join(pasta, "template.json"), "w"), ensure_ascii=False, indent=1)
    # fundo do template = mesmo início do arte.jsx (doc + fundo limpo + caixas)
    corpo = arte.split('var gT = Y.grupo("TEXTOS");')[0]
    caixas = [ln for ln in arte.splitlines() if "CAIXA MARCA-TEXTO" in ln]
    js = [corpo.replace('var ALV = Y.lerJSON(PASTA + "/alvos.json");', ""), 'var gT = Y.grupo("TEXTOS");', *caixas,
          "var T = Y.lerJSON(PASTA + \"/template.json\"), NOVOS = (typeof TEXTOS !== \"undefined\") ? eval(\"(\" + TEXTOS + \")\") : {};",
          "for (var i = 0; i < T.length; i++) { var t = T[i], txt = NOVOS.hasOwnProperty(t.id) ? NOVOS[t.id] : t.texto; if (txt === \"\") continue;",
          "  var m = Y.marcacao(txt.replace(/\\\\n/g, \"\\n\"), t.negrito, t.destaque);",
          "  var anc = t.alinh === \"centro\" ? \"tc\" : (t.alinh === \"dir\" ? \"tr\" : \"tl\");",
          "  Y.texto({ txt: m.txt, nome: t.nome, fonte: t.fonte, px: t.px, cor: t.cor, tracking: t.tracking, entrelinha: t.entrelinha || undefined,",
          "    alinh: t.alinh === \"centro\" ? \"centro\" : (t.alinh === \"dir\" ? \"dir\" : \"esq\"), faixas: m.faixas.length ? m.faixas : undefined, x: t.x, y: t.topo, ancora: anc }, gT); }",
          "Y.salvar(SAIDA + \"/post\" + (typeof NUM !== \"undefined\" ? \"-\" + NUM : \"\") + \".psd\", SAIDA + \"/post\" + (typeof NUM !== \"undefined\" ? \"-\" + NUM : \"\") + \".png\");", "\"ok\";"]
    open(os.path.join(pasta, "template.jsx"), "w").write("\n".join(js) + "\n")
    for ln in linhas:
        print(f"{ln['id']:<4} {ln['alinh']:<6} {ln['fonte']:<26} {ln['px']:>6}px  neg={ln['negrito']} dest={ln['destaque']}  '{ln['texto'][:40]}'")
    print("template.json + template.jsx em", pasta)


if __name__ == "__main__":
    main()
