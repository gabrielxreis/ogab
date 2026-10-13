"""Relatos de erro que chegaram das instalações (lado do DONO: /ogab relatos).

Os relatos caem na planilha de respostas do Formulário Google do dono (relatos/destino.json > planilha_id). Ninguém
além do dono vê a planilha. O Gab do dono lê pelo Chrome logado (Claude in Chrome), na versão HTML:

  python3 relatos.py url [--editar]            # planilha em HTML para ler (ou em edição, para apagar o resolvido)
  python3 relatos.py resolvidos                # assinaturas já resolvidas (ficam só no Mac do dono)
  python3 relatos.py resolver <assinatura> <commit> ["nota"]   # marcar como resolvido depois do commit+push

Fluxo: abrir a URL, ler as linhas, IGNORAR as assinaturas já resolvidas, agrupar pela assinatura (vezes e máquinas =
coluna instalacao), e para cada erro: ler causa, correção e diff, reproduzir, aplicar a correção (ou uma melhor) no
repo, linha em docs/PROCESSO.md e no CHANGELOG, commit+push, `resolver` e APAGAR da planilha as linhas desse erro
(`relatos.py url --editar`, clique direito no número da linha > Excluir linha). Os usuários recebem no auto-update.
"""
import json, os, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOLVIDOS = os.path.expanduser("~/.claude/ogab_relatos/resolvidos.json")


def url(editar=False):
    d = json.load(open(os.path.join(SKILL, "relatos", "destino.json"), encoding="utf-8"))
    base = f"https://docs.google.com/spreadsheets/d/{d['planilha_id']}"
    return base + ("/edit" if editar else f"/htmlview/sheet?headers=true&gid={d.get('aba_gid', '0')}")   # sem gid não abre


def resolvidos():
    try:
        return json.load(open(RESOLVIDOS, encoding="utf-8"))
    except Exception:
        return {}


def resolver(assinatura, commit, nota=""):
    r = resolvidos(); r[assinatura] = {"commit": commit, "nota": nota, "quando": time.strftime("%Y-%m-%d")}
    os.makedirs(os.path.dirname(RESOLVIDOS), exist_ok=True)
    json.dump(r, open(RESOLVIDOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return r[assinatura]


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["url"]:
        print(url("--editar" in a))
    elif a[:1] == ["resolvidos"]:
        print(json.dumps(resolvidos(), ensure_ascii=False, indent=1))
    elif a[:1] == ["resolver"] and len(a) >= 3:
        print(resolver(a[1], a[2], a[3] if len(a) > 3 else ""))
    else:
        raise SystemExit(__doc__)
