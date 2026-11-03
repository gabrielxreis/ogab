"""Gera várias artes de um mesmo arte.jsx trocando variáveis (carrossel, variações A/B, série de posts).

    python3 lote.py arte.jsx dados.json MARCA=... [SAIDA=pasta]

dados.json = lista de objetos; cada um vira uma montagem com essas variáveis (strings) + NUM (1, 2, ...).
Ex.: [{"TITULO": "ERRO 1", "FOTO": "/caminho/a.jpg"}, {"TITULO": "ERRO 2", "FOTO": "/caminho/b.jpg"}]
No arte.jsx: Y.texto({txt: TITULO, ...}); Y.trocarConteudo(camadaFoto, FOTO); Y.salvar(SAIDA + "/post-" + NUM + ".psd", ...)
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    arte, dados = sys.argv[1], json.load(open(sys.argv[2])); extras = sys.argv[3:]
    for i, d in enumerate(dados, 1):
        vs = [f"{k}={v}" for k, v in d.items()] + [f"NUM={i:02d}"]
        r = subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), arte, *extras, *vs], capture_output=True, text=True)
        print(f"{i:02d}/{len(dados)}", (r.stdout.strip().splitlines() or ["?"])[-1] if r.returncode == 0 else "ERRO " + r.stderr.strip()[-300:], flush=True)


if __name__ == "__main__":
    main()
