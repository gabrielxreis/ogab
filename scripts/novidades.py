"""Novidades da skill desde a última vez que ESTE usuário viu (passo zero do SKILL.md, depois do git pull).

  python3 novidades.py            # imprime as novidades novas (nada se não houver) e marca como vistas
  python3 novidades.py --todas    # imprime tudo, sem marcar

Lê CHANGELOG.md (versões "## <versão> (<data>)", mais nova em cima) e guarda a última versão vista em
config.json > "versao_vista" (fica só na máquina do usuário). Na primeira vez mostra só a versão atual.
"""
import json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG = os.path.join(RAIZ, "CHANGELOG.md")
CONFIG = os.path.join(RAIZ, "config.json")


def versoes():
    texto = open(CHANGELOG, encoding="utf-8").read()
    partes = re.split(r"^## ", texto, flags=re.M)[1:]
    saida = []
    for p in partes:
        cab, _, corpo = p.partition("\n")
        m = re.match(r"(\S+)\s*(\(.*\))?", cab.strip())
        if m:
            saida.append((m.group(1), cab.strip(), corpo.strip()))
    return saida


def main(a):
    vs = versoes()
    if not vs:
        return
    if "--todas" in a:
        for _, cab, corpo in vs:
            print(f"### {cab}\n{corpo}\n")
        return
    cfg = json.load(open(CONFIG, encoding="utf-8")) if os.path.exists(CONFIG) else {}
    vista = cfg.get("versao_vista")
    nomes = [v for v, _, _ in vs]
    if vista in nomes:
        novas = vs[:nomes.index(vista)]
    else:
        novas = vs[:1]                     # primeira vez: só a versão atual, não o histórico inteiro
    if novas:
        print(f"Novidades do Gab (versão {vs[0][0]}):")
        for _, cab, corpo in novas:
            print(f"\n{corpo}")
    if os.path.exists(CONFIG) and cfg.get("versao_vista") != vs[0][0]:
        cfg["versao_vista"] = vs[0][0]
        json.dump(cfg, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(sys.argv[1:])
