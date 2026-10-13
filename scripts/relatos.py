"""Relatos de erro que chegaram das instalações (lado do DONO: /ogab relatos).

  python3 relatos.py ligar                    # 1ª vez, logo depois de publicar o receptor: pega a chave de admin
  python3 relatos.py listar [--todos]          # abertos, agrupados por erro (vezes, máquinas, versão, editor)
  python3 relatos.py ver <assinatura>          # tudo de um erro, com o diff da correção feita na máquina do usuário
  python3 relatos.py resolver <assinatura> <commit> ["nota"]   # marca resolvido (depois do commit+push da correção)

Fluxo do dono (SKILL.md, "Relatos de erro"): listar -> para cada erro: ler causa e correção, reproduzir, aplicar a
correção (ou uma melhor) no repo, registrar em docs/PROCESSO.md e no CHANGELOG, commit+push, `resolver`.
A URL do receptor fica em relatos/destino.json (no git); a chave de admin só no config.json do dono ("relatos_admin").
"""
import json, os, sys, urllib.parse, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SKILL, "config.json")


def _url():
    try:
        return json.load(open(os.path.join(SKILL, "relatos", "destino.json"), encoding="utf-8")).get("url", "")
    except Exception:
        return ""


def _cfg():
    return json.load(open(CONFIG, encoding="utf-8"))


def _get(**p):
    u = _url() + "?" + urllib.parse.urlencode(p)
    return json.loads(urllib.request.urlopen(u, timeout=30).read().decode("utf-8"))


def _post(d):
    req = urllib.request.Request(_url(), data=json.dumps(d).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))


def ligar():
    if not _url():
        raise SystemExit("falta a URL do receptor em relatos/destino.json (ver relatos/LEIA.md)")
    r = _get(acao="chave")
    if not r.get("ok"):
        raise SystemExit(f"o receptor já entregou a chave antes ({r}). Se perdeu: apague ADMIN_KEY nas propriedades do script e rode de novo.")
    c = _cfg(); c["relatos_admin"] = r["chave"]; c["relatos_planilha"] = r.get("planilha", "")
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return r.get("planilha", "")


def listar(todos=False, diff=False):
    r = _get(acao="listar", chave=_cfg().get("relatos_admin", ""), **({"todos": 1} if todos else {}), **({"diff": 1} if diff else {}))
    if not r.get("ok"):
        raise SystemExit(f"receptor recusou: {r} (rode `relatos.py ligar` na 1ª vez)")
    return r["relatos"]


def resolver(assinatura, commit, nota=""):
    return _post({"acao": "resolver", "chave": _cfg().get("relatos_admin", ""), "assinatura": assinatura, "commit": commit, "nota": nota})


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "ligar":
        print("ligado. planilha:", ligar())
    elif a[0] == "listar":
        rs = sorted(listar("--todos" in a), key=lambda r: -int(r.get("vezes") or 1))
        if not rs:
            print("nenhum relato aberto")
        for r in rs:
            maqs = len([x for x in str(r.get("instalacoes", "")).split(",") if x])
            print(f"[{r['assinatura']}] {r['titulo']}\n   {r.get('vezes', 1)}x em {maqs} máquina(s) | v{r.get('versao')} | {r.get('sistema')} | "
                  f"{r.get('editor')}/{r.get('motion')} | {r.get('status')}\n   erro: {str(r.get('erro'))[:160]}")
    elif a[0] == "ver" and len(a) >= 2:
        for r in listar(True, diff=True):
            if r["assinatura"] == a[1]:
                for k in ("titulo", "erro", "causa", "correcao", "diff", "versao", "sistema", "python", "editor", "motion",
                          "vezes", "instalacoes", "status", "commit", "nota"):
                    print(f"--- {k}\n{r.get(k, '')}")
    elif a[0] == "resolver" and len(a) >= 3:
        print(resolver(a[1], a[2], a[3] if len(a) > 3 else ""))
    else:
        raise SystemExit(__doc__)
