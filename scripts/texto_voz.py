"""Texto do roteiro -> texto para a voz IA, com a grafia que o eleven_v4 pronuncia certo em português.
Aplica pronuncia_ptbr.json (armadilhas de todo cliente) e depois clientes/<cliente>/pronuncia.json (grafia -> fala).
Regra do usuário, 30/10/2026: "você tem que ter isso salvo na skill como contornar, senão vai apagar com meu dinheiro".

  python3 texto_voz.py <roteiro.txt> [--cliente <pasta do cliente em clientes/>]
Imprime o texto pronto para o creative_generate_speech (model eleven_v4, SEMPRE) e, no stderr, cada troca feita.
"""
import json, os, re, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def termos(cliente=None):
    arqs = [os.path.join(SKILL, "pronuncia_ptbr.json")]
    if cliente: arqs.append(os.path.join(SKILL, "clientes", cliente, "pronuncia.json"))
    out = []
    for a in arqs:
        if os.path.exists(a): out += json.load(open(a, encoding="utf-8")).get("termos", [])
    return out


def converter(texto, cliente=None):
    trocas = []
    for t in termos(cliente):
        g, f = t["grafia"], t["fala"]
        if g == f: continue
        def sub(m):
            w = m.group(0); novo = f[0].upper() + f[1:] if w[0].isupper() else f
            trocas.append(f"{w} -> {novo}"); return novo
        texto = re.sub(r"(?<![\wÀ-ÿ])" + re.escape(g) + r"(?![\wÀ-ÿ])", sub, texto, flags=re.I)
    return texto, trocas


if __name__ == "__main__":
    a = sys.argv[1:]
    cli = a[a.index("--cliente") + 1] if "--cliente" in a else None
    txt, tr = converter(open(a[0], encoding="utf-8").read().strip(), cli)
    for x in tr: print("troca:", x, file=sys.stderr)
    print(txt)
