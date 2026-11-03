"""Gera o catálogo local do Photoshop desta máquina em docs/catalogo/local/ (fora do git).

    python3 ~/.claude/skills/ogab/design/scripts/sondar/catalogar.py

- agente_ferramentas.json: ferramentas nativas do agente do Photoshop (listTools), com JSON Schema
- batchplay_exemplos_adobe.json: comandos batchPlay usados pelos painéis da própria Adobe (com exemplo)
- descritores/: descritor completo do app, do documento da frente e das camadas
Rodar de novo quando o Photoshop atualizar. Precisa do Photoshop aberto.
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import ps_lib as PS  # noqa: E402

LOCAL = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "docs", "catalogo", "local")
os.makedirs(os.path.join(LOCAL, "descritores"), exist_ok=True)
LIB = os.path.join(PS.JSX, "agente_lib.jsx").replace("\\", "/").replace("'", "\\'")


def limpa(x):
    if isinstance(x, dict):
        return {k: limpa(v) for k, v in x.items() if k != "_obj"}
    if isinstance(x, list):
        return [limpa(v) for v in x]
    return x


# 1) ferramentas do agente
bruto = PS.js(f"""$.evalFile('{LIB}');
var a=new ActionDescriptor(); a.putReference(s("null"),_refAgente()); a.putBoolean(s("expanded"),true);
d2j(executeAction(s("listTools"),a,DialogModes.NO));""")
tools = limpa(json.loads(bruto.replace(",}", "}"))["tools"])
json.dump(tools, open(os.path.join(LOCAL, "agente_ferramentas.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(tools), "ferramentas do agente")

# 2) batchPlay dos painéis internos
if os.name == "nt":  # Windows: a pasta do programa vem do próprio Photoshop
    uxp = os.path.join(PS.js("app.path.fsName"), "Required", "UXP")
else:
    app_dir = subprocess.run(["mdfind", "kMDItemCFBundleIdentifier == 'com.adobe.Photoshop'"],
                             capture_output=True, text=True).stdout.split("\n")[0]
    uxp = os.path.join(app_dir, "Contents", "Required", "UXP")
if os.path.isdir(uxp):
    subprocess.run([sys.executable, "-I", os.path.join(AQUI, "extrai_bp.py"), uxp,
                    os.path.join(LOCAL, "batchplay_exemplos_adobe.json")])

# 3) descritores (app sempre; documento e camadas se houver documento aberto)
for nome, alvo in [("app", "application"), ("documento", "document")]:
    try:
        bruto = PS.js(f"""$.evalFile('{LIB}'); var r=new ActionReference();
r.putEnumerated(s("{alvo}"),s("ordinal"),s("targetEnum")); d2j(executeActionGet(r));""")
        d = json.loads(bruto.replace(",}", "}"))
        json.dump(d, open(os.path.join(LOCAL, "descritores", nome + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("descritor", nome, len(d), "chaves")
    except Exception as e:
        print("descritor", nome, "pulado:", str(e)[:80])
print("pronto em", LOCAL)
