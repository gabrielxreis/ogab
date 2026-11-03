"""Prova de fogo automática numa reconstrução: para cada linha de TÍTULO com candidatas empatadas (diferença de
nota < --margem), monta o PSD com cada candidata naquela linha e fica com a que mais se sobrepõe à referência.

    python3 refinar_fontes.py pasta_reconstrucao [--margem 0.06] [--max 3]

Usa camadas.json (candidatas do reconstruir) e alvos.json (o encaixe vale para qualquer fonte). Nota = bordas a
até 2 px (sobrepor.py) só na caixa da linha. Grava a escolha no arte.jsx e remonta.
"""
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__)); PY = os.path.join(AQUI, "..", ".venv", "bin", "python")


def main():
    pasta = os.path.abspath(sys.argv[1]); marg = float(sys.argv[sys.argv.index("--margem") + 1]) if "--margem" in sys.argv else 0.06
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 3
    cam = json.load(open(os.path.join(pasta, "camadas.json"))); alv = json.load(open(os.path.join(pasta, "alvos.json")))
    ref = json.load(open(os.path.join(pasta, "medidas.json")))["ref"]; arte = os.path.join(pasta, "arte.jsx"); js = open(arte).read()
    for c in cam:
        cs, ns = c.get("candidatas") or [], c.get("notas") or []
        if c.get("pequeno") or len(cs) < 2 or ns[0] - ns[1] > marg or c["nome"] not in alv: continue
        a = alv[c["nome"]]; reg = [str(max(0, a["x"] - 6)), str(max(0, a["y"] - 6)), str(a["x"] + a["w"] + 6), str(a["y"] + a["h"] + 6)]
        padrao = re.compile(r'(nome: "' + re.escape(c["nome"]) + r'[^"]*", fonte: )"[^"]*"')
        notas = {}
        it_ = lambda s: "Italic" in s or "Oblique" in s
        if not it_(cs[0]): cs = [f for f in cs if not it_(f)]   # itálico só entra se a 1ª candidata já for itálica
        if len(cs) < 2: continue
        for f in cs[:mx]:
            open(arte, "w").write(padrao.sub(lambda m: m.group(1) + json.dumps(f), js))
            subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), arte, f"SAIDA={pasta}", f"PASTA={pasta}"], capture_output=True, text=True)
            out = subprocess.run([PY, os.path.join(AQUI, "sobrepor.py"), ref, os.path.join(pasta, "editavel.png"), os.path.join(pasta, "_prova.png"), "--regiao", *reg],
                                 capture_output=True, text=True).stdout
            try: notas[f] = float(out.split(":")[1].split()[0])
            except Exception: notas[f] = 0
        venc = max(notas, key=notas.get)
        print(f"{c['nome']}: " + "  ".join(f"{f} {v:.3f}" for f, v in sorted(notas.items(), key=lambda x: -x[1])) + f"  -> {venc}", flush=True)
        js = padrao.sub(lambda m: m.group(1) + json.dumps(venc), js); c["fonte"] = venc
    open(arte, "w").write(js); json.dump(cam, open(os.path.join(pasta, "camadas.json"), "w"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), arte, f"SAIDA={pasta}", f"PASTA={pasta}"], capture_output=True, text=True)
    if os.path.exists(os.path.join(pasta, "_prova.png")): os.remove(os.path.join(pasta, "_prova.png"))


if __name__ == "__main__":
    main()
