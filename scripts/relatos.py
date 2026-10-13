"""Relatos de erro que chegaram das instalações (lado do DONO: /ogab relatos).

Os relatos caem na planilha de respostas do Formulário Google do dono (relatos/destino.json > planilha_id). Ninguém
além do dono vê a planilha. O Gab do dono lê pelo Chrome logado (Claude in Chrome), na versão HTML:

  python3 relatos.py url [--editar]            # planilha em HTML para ler (ou em edição, para apagar o resolvido)
  python3 relatos.py resolvidos                # assinaturas já resolvidas (ficam só no Mac do dono)
  python3 relatos.py resolver <assinatura> <commit> ["nota"]   # marcar como resolvido depois do commit+push
  python3 relatos.py lido                      # marca "planilha lida agora" (libera commits por LEITURA_VALE horas)
  python3 relatos.py checar                    # sai com erro se a última leitura é velha (usado pelo hook do git)
  python3 relatos.py hook                      # instala o pre-commit no repo do dono (commit só depois de ler)

Regra do dono (13/10/2026): ANTES de qualquer commit na skill, ler a planilha inteira: erros (tipo bug ou vazio) E
motions novos (tipo preset). O pre-commit do git trava o commit se a leitura tiver mais de LEITURA_VALE horas.
Preset bom: renderizar a prévia com as cores de um cliente de exemplo, salvar com `biblioteca_motions.py salvar`
(no dono publica), "autor": "comunidade"; preset fraco ou repetido: só apagar a linha.

Fluxo: abrir a URL, ler as linhas, IGNORAR as assinaturas já resolvidas, agrupar pela assinatura (vezes e máquinas =
coluna instalacao), e para cada erro: ler causa, correção e diff, reproduzir, aplicar a correção (ou uma melhor) no
repo, linha em docs/PROCESSO.md e no CHANGELOG, commit+push, `resolver` e APAGAR da planilha as linhas desse erro
(`relatos.py url --editar`, clique direito no número da linha > Excluir linha). Os usuários recebem no auto-update.
"""
import json, os, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOLVIDOS = os.path.expanduser("~/.claude/ogab_relatos/resolvidos.json")
LIDO = os.path.expanduser("~/.claude/ogab_relatos/ultima_leitura.txt")
LEITURA_VALE = 3   # horas
HOOK = """#!/bin/sh
# /ogab (dono): commit só depois de ler os relatos (erros e motions novos). Ver scripts/relatos.py.
python3 "$(git rev-parse --show-toplevel)/scripts/relatos.py" checar || exit 1
"""


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


def lido():
    os.makedirs(os.path.dirname(LIDO), exist_ok=True); open(LIDO, "w").write(str(time.time()))


def checar():
    try:
        h = (time.time() - float(open(LIDO).read().strip())) / 3600
    except Exception:
        h = None
    if h is None or h > LEITURA_VALE:
        print("COMMIT BLOQUEADO: antes de commitar na skill, ler os relatos (erros e motions novos): /ogab relatos\n"
              f"  (abrir `python3 scripts/relatos.py url` no Chrome, tratar tudo, depois `python3 scripts/relatos.py lido`)\n"
              f"  última leitura: {'nunca' if h is None else f'há {h:.1f} h'} (vale {LEITURA_VALE} h)")
        return False
    return True


def hook():
    destino = os.path.join(SKILL, ".git", "hooks", "pre-commit")
    open(destino, "w").write(HOOK); os.chmod(destino, 0o755)
    return destino


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["url"]:
        print(url("--editar" in a))
    elif a[:1] == ["resolvidos"]:
        print(json.dumps(resolvidos(), ensure_ascii=False, indent=1))
    elif a[:1] == ["lido"]:
        lido(); print("leitura marcada; commits liberados por", LEITURA_VALE, "h")
    elif a[:1] == ["checar"]:
        sys.exit(0 if checar() else 1)
    elif a[:1] == ["hook"]:
        print("pre-commit instalado:", hook())
    elif a[:1] == ["resolver"] and len(a) >= 3:
        print(resolver(a[1], a[2], a[3] if len(a) > 3 else ""))
    else:
        raise SystemExit(__doc__)
