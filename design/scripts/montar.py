"""Roda um script de arte (.jsx que usa a biblioteca Y de jsx/rick.jsx) no Photoshop, com caminhos injetados.
    python3 montar.py arte.jsx VAR=valor VAR2=valor ...
As variáveis viram `var VAR="valor";` antes do script. Devolve o que o script devolver e mostra alertas fechados.
Fecha os documentos que o script abriu (já salvos pelo Y.salvar) para não lotar a RAM/disco de trabalho em
testes repetidos (21 documentos abertos = "discos de trabalho cheios"). ABRIR=1 deixa o resultado aberto."""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ps_lib as PS
arte = os.path.abspath(sys.argv[1])
vars_ = dict(a.split("=", 1) for a in sys.argv[2:])
cab = f'$.evalFile({json.dumps(os.path.join(AQUI, "jsx", "rick.jsx"))});\n' + "".join(f"var {k}={json.dumps(v)};\n" for k, v in vars_.items())
ANTES = 'var s=[];for(var i=0;i<app.documents.length;i++)s.push(app.documents[i].id);s.join(",")'
antes = set(PS.js(ANTES).split(","))
try:
    r = PS.js(cab + open(arte, encoding="utf-8").read(), timeout=900)
finally:
    if vars_.get("ABRIR") != "1":
        PS.js("var a=%s;for(var i=app.documents.length-1;i>=0;i--){var d=app.documents[i];"   # ExtendScript: sem Array.indexOf
              "if(a.indexOf(','+d.id+',')<0)d.close(SaveOptions.DONOTSAVECHANGES);}'ok'" % json.dumps("," + ",".join(sorted(antes)) + ","))
print(r)
if PS.ALERTAS: print("ALERTAS:", PS.ALERTAS)
