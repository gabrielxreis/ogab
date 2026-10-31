"""Relatos de erro e motions que chegaram das instalações (lado do DONO: /ogab relatos).

SÓ VPS (regra do usuário, 26/10/2026): relatos e presets da comunidade chegam APENAS pela fila da VPS do autor
(`/v1/preset`, enviada pelo `relatar.py enviar`). A planilha/Formulário Google e o Drive foram DESATIVADOS: não ler,
não recriar e não inventar outro destino (planilha, formulário, Drive, gws, webhook, e-mail). O dono lê a fila com a
key de criador pelo `presets_vps.py` (só no Mac do dono, fora do git):

  python3 relatos.py fila                      # lista a fila da VPS (relatos/ e presets/ de cada usuário)
  python3 presets_vps.py puxar                 # baixa e reconstrói tudo em ~/.claude/ogab_presets_vps para tratar
  python3 presets_vps.py apagar <path>         # tira da VPS o que já foi tratado (ou `limpar` = tudo da fila atual)
  python3 relatos.py resolvidos                # assinaturas já resolvidas (ficam só no Mac do dono)
  python3 relatos.py resolver <assinatura> <commit> ["nota"]   # marcar como resolvido depois do commit+push
  python3 relatos.py lido                      # marca "fila lida agora" (libera commits por LEITURA_VALE horas)
  python3 relatos.py checar                    # sai com erro se a última leitura é velha (usado pelo hook do git)
  python3 relatos.py hook                      # instala o pre-commit no repo do dono (commit só depois de ler)

Regra do dono (13/10/2026): ANTES de qualquer commit na skill, ler a fila inteira: erros (relatos/) E motions novos
(presets/). Para cada erro: reproduzir, corrigir no repo, linha em docs/PROCESSO.md e no CHANGELOG, commit+push,
`resolver` e `presets_vps.py apagar` daquele item. Preset bom: `biblioteca_motions.py salvar` ("autor": "comunidade");
preset fraco ou repetido: só apagar da fila.
Itens com nome RICK_ são do /orick (Rick, mesma fila): tratar no repo do Rick com `orick/scripts/relatos_rick.py`
(fila | puxar | resolver | apagar), não aqui.
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


PLANILHA_DESATIVADA = ("A planilha/Formulário dos relatos foi DESATIVADA em 26/10/2026: tudo chega pela VPS.\n"
                       "Ler a fila: python3 scripts/relatos.py fila (ou presets_vps.py listar|puxar). Não recriar planilha.")


def fila():
    """Lista a fila da VPS pelo presets_vps.py (ferramenta só do dono, fora do git)."""
    p = os.path.join(SKILL, "scripts", "presets_vps.py")
    if not os.path.exists(p):
        raise SystemExit("presets_vps.py não está nesta máquina: a fila da VPS só é lida no Mac do dono (key de criador).")
    import subprocess
    return subprocess.call([sys.executable, p, "listar"])


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
              f"  (ler a fila da VPS: `python3 scripts/relatos.py fila` / `presets_vps.py puxar`, tratar tudo, depois `python3 scripts/relatos.py lido`)\n"
              f"  última leitura: {'nunca' if h is None else f'há {h:.1f} h'} (vale {LEITURA_VALE} h)")
        return False
    return True


def hook():
    destino = os.path.join(SKILL, ".git", "hooks", "pre-commit")
    open(destino, "w").write(HOOK); os.chmod(destino, 0o755)
    return destino


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["fila"]:
        sys.exit(fila())
    elif a[:1] == ["url"]:
        raise SystemExit(PLANILHA_DESATIVADA)
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
