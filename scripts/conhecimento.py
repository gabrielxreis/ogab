"""Conhecimento da comunidade do Gab (regra do Gabriel, 05/11/2026): toda instalação alimenta o Gab com o que aprende
no trabalho; a lição vai ANÔNIMA para a fila da VPS, o criador aprova no chat e ela entra na base da nuvem, que todo
Gab com licença válida baixa no próximo uso. Nada chega aos outros sem a aprovação do criador.

Quem usa (automático, sem perguntar; vale pelo aceite dos termos, `"relatos": true` no config):
  python3 conhecimento.py registrar --area video --titulo "..." --texto "..."   # manda 1 lição (anônima) para a fila
  python3 conhecimento.py baixar          # baixa a base aprovada (o inicio.py chama; imprime CONHECIMENTO: se mudou)
  python3 conhecimento.py ler [--area X]  # o que a comunidade ensinou (área + geral); o Gab lê no começo da área

Criador (`/ogab conhecimento`, só a key de criador):
  python3 conhecimento.py fila            # lições que chegaram, numeradas, com a mais parecida da base
  python3 conhecimento.py aprovar N [--titulo T] [--texto X] [--area A]   # entra na base (com edição) e sai da fila
  python3 conhecimento.py recusar N       # só tira da fila
  python3 conhecimento.py remover <id>    # tira da base uma lição já aprovada
Áreas: video, design, trafego, comercial, negocio, geral.
"""
import difflib, hashlib, json, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import licenca, relatar   # noqa: E402

AREAS = ("video", "design", "trafego", "comercial", "negocio", "geral")
BASE = os.path.expanduser("~/.claude/ogab_conhecimento.json")
FILA_LOCAL = os.path.expanduser("~/.claude/ogab_relatos/conhecimento_fila.json")   # numeração da última `fila`
ENVIADAS = os.path.expanduser("~/.claude/ogab_relatos/conhecimento_enviadas.json")
PEND = os.path.expanduser("~/.claude/ogab_relatos/conhecimento_pendentes")        # sem internet: manda depois


def _cred():
    d = licenca._ler()
    return (d["key"], licenca.maquina()) if d.get("key") else (None, None)


def _json(arq, padrao):
    try:
        return json.load(open(arq, encoding="utf-8"))
    except Exception:
        return padrao


def _gravar(arq, obj):
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    json.dump(obj, open(arq + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(arq + ".tmp", arq)


def _area(a):
    a = (a or "geral").lower().replace("í", "i").replace("é", "e").replace("á", "a")
    a = {"trafego pago": "trafego", "negocios": "negocio", "videos": "video"}.get(a, a)
    if a not in AREAS:
        sys.exit(f"área inválida: {a} (use {', '.join(AREAS)})")
    return a


# ------------------------------------------------------------------ quem usa
def registrar(area, titulo, texto):
    cfg = relatar._config()
    if cfg.get("dono_biblioteca"):   # o criador não manda para a fila: aprova direto
        return aprovar_licao({"area": area, "titulo": titulo, "texto": texto})
    if cfg.get("relatos") is not True:
        print("CONHECIMENTO_DESLIGADO: relatos anônimos desligados no config (nada enviado)"); return 0
    nomes = relatar._nomes_privados(cfg)
    li = {"area": _area(area), "titulo": relatar.anonimizar(titulo, nomes)[:200].strip(),
          "texto": relatar.anonimizar(texto, nomes)[:4000].strip(), "versao": relatar._versao(),
          "quando": time.strftime("%Y-%m-%d")}
    if not li["titulo"] or len(li["texto"]) < 20:
        sys.exit("lição curta demais: título e um texto de pelo menos 20 caracteres")
    assin = hashlib.sha1((li["titulo"] + li["texto"]).lower().encode()).hexdigest()[:10]
    env = _json(ENVIADAS, [])
    if assin in env:
        print("CONHECIMENTO: essa lição já foi enviada"); return 0
    os.makedirs(PEND, exist_ok=True)
    _gravar(os.path.join(PEND, f"{assin}.json"), li)
    n = enviar_pendentes()
    print("CONHECIMENTO: lição enviada para a comunidade (o criador aprova antes de ir para todos)" if n
          else "CONHECIMENTO: lição guardada; vai na próxima conexão")
    return 0


def enviar_pendentes():
    key, maq = _cred()
    if not key or not os.path.isdir(PEND):
        return 0
    usuario = str((relatar._config().get("comunidade") or {}).get("nome") or "anon")[:60]
    env, n = _json(ENVIADAS, []), 0
    for nome in sorted(os.listdir(PEND)):
        arq = os.path.join(PEND, nome)
        li = _json(arq, None)
        if not li:
            continue
        r = licenca._post("/v1/preset", {"key": key, "maquina": maq, "usuario": usuario, "tipo": "conhecimento",
                                         "preset": f"{li['area']}_{li['titulo']}"[:80],
                                         "pacote": json.dumps(li, ensure_ascii=False)})
        if r is None:
            break   # sem internet
        if r.get("status") == "ok":
            env.append(nome[:-5]); os.remove(arq); n += 1
    _gravar(ENVIADAS, env[-500:])
    return n


def baixar(calado=False):
    key, maq = _cred()
    if not key:
        return 0
    try:
        enviar_pendentes()
    except Exception:
        pass
    atual = _json(BASE, {"versao": "", "licoes": []})
    r = licenca._post("/v1/conhecimento", {"key": key, "maquina": maq, "versao": atual.get("versao", "")})
    if not r or r.get("status") != "ok" or r.get("igual"):
        return 0
    velhas = {x["id"] for x in atual.get("licoes", [])}
    novas = [x for x in r.get("licoes", []) if x.get("id") not in velhas]
    _gravar(BASE, {"versao": r.get("versao", ""), "licoes": r.get("licoes", [])})
    if novas and not calado:
        areas = sorted({x["area"] for x in novas})
        print(f"CONHECIMENTO: {len(novas)} lição(ões) nova(s) da comunidade ({', '.join(areas)})")
    return len(novas)


def ler(area=None):
    b = _json(BASE, {"licoes": []})
    ls = [x for x in b.get("licoes", []) if not area or x["area"] in (_area(area), "geral")]
    if not ls:
        print("(a comunidade ainda não ensinou nada para esta área)"); return
    print(f"# Conhecimento da comunidade ({len(ls)} lição(ões), aprovadas pelo criador)\n")
    for a in AREAS:
        grupo = [x for x in ls if x["area"] == a]
        if grupo:
            print(f"## {a}")
            for x in grupo:
                print(f"- **{x['titulo']}** ({x.get('quando', '')}): {x['texto']}")
            print()


# ------------------------------------------------------------------ criador
def _parecida(li, base):
    alvo = (li.get("titulo", "") + " " + li.get("texto", "")).lower()
    melhor, nota = None, 0.0
    for x in base:
        s = difflib.SequenceMatcher(None, alvo, (x["titulo"] + " " + x["texto"]).lower()).ratio()
        if s > nota:
            melhor, nota = x, s
    return melhor, nota


def fila():
    key, maq = _cred()
    r = licenca._post("/v1/criador/presets", {"key": key, "maquina": maq}) if key else None
    if not r or r.get("status") != "ok":
        sys.exit(f"não consegui ler a fila: {(r or {}).get('msg', 'sem conexão')}")
    paths = [x["path"] for x in r["presets"] if "/conhecimento/" in x["path"]]
    baixar(calado=True)
    base = _json(BASE, {"licoes": []}).get("licoes", [])
    itens = []
    for p in paths:
        c = licenca._post("/v1/criador/baixar", {"key": key, "maquina": maq, "path": p}) or {}
        try:
            li = json.loads(c.get("conteudo", ""))
        except Exception:
            li = {"area": "geral", "titulo": "(ilegível)", "texto": str(c.get("conteudo", ""))[:400]}
        li["path"] = p
        itens.append(li)
    _gravar(FILA_LOCAL, itens)
    if not itens:
        print("FILA_VAZIA: nenhuma lição esperando aprovação"); return
    print(f"{len(itens)} lição(ões) esperando aprovação:\n")
    for i, li in enumerate(itens, 1):
        par, nota = _parecida(li, base)
        aviso = f"\n   PARECIDA ({nota:.0%}) com [{par['id']}] {par['titulo']}" if par and nota >= 0.55 else ""
        print(f"{i}. [{li.get('area')}] {li.get('titulo')}\n   {li.get('texto')}\n   (versão {li.get('versao', '?')}, "
              f"{li.get('quando', '?')}){aviso}\n")


def _item(n):
    itens = _json(FILA_LOCAL, [])
    if not (1 <= n <= len(itens)):
        sys.exit("número fora da última fila: rode `conhecimento.py fila` de novo")
    return itens[n - 1]


def aprovar_licao(li, path=None):
    key, maq = _cred()
    corpo = {"key": key, "maquina": maq, "licao": {"area": _area(li.get("area")), "titulo": li.get("titulo", ""),
                                                   "texto": li.get("texto", "")}}
    if path:
        corpo["path"] = path
    r = licenca._post("/v1/criador/conhecimento/aprovar", corpo) if key else None
    if not r or r.get("status") != "ok":
        sys.exit(f"não aprovou: {(r or {}).get('msg', 'sem conexão')}")
    baixar(calado=True)
    print(f"APROVADA [{r['licao']['id']}] {r['licao']['titulo']} (base com {r['total']}; chega a todos no próximo uso)")
    return 0


def recusar(n):
    key, maq = _cred(); li = _item(n)
    r = licenca._post("/v1/criador/apagar", {"key": key, "maquina": maq, "path": li["path"]})
    print("RECUSADA: saiu da fila" if r and r.get("status") == "ok" else f"falhou: {(r or {}).get('msg', 'sem conexão')}")


def remover(id_):
    key, maq = _cred()
    r = licenca._post("/v1/criador/conhecimento/remover", {"key": key, "maquina": maq, "id": id_})
    if r and r.get("status") == "ok":
        baixar(calado=True); print(f"REMOVIDA da base ({r['total']} ficam)")
    else:
        print(f"falhou: {(r or {}).get('msg', 'sem conexão')}")


def _opt(a, nome):
    return a[a.index(nome) + 1] if nome in a and a.index(nome) + 1 < len(a) else None


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd = a[0]
    if cmd == "registrar":
        if not (_opt(a, "--titulo") and _opt(a, "--texto")):
            sys.exit("uso: conhecimento.py registrar --area A --titulo T --texto X")
        return registrar(_area(_opt(a, "--area")), _opt(a, "--titulo"), _opt(a, "--texto"))
    if cmd == "baixar":
        baixar(calado="--calado" in a); return 0
    if cmd == "ler":
        ler(_opt(a, "--area")); return 0
    if cmd == "fila":
        fila(); return 0
    if cmd == "aprovar" and len(a) >= 2 and a[1].isdigit():
        li = dict(_item(int(a[1])))
        for k in ("titulo", "texto", "area"):
            if _opt(a, "--" + k):
                li[k] = _opt(a, "--" + k)
        return aprovar_licao(li, li.get("path"))
    if cmd == "recusar" and len(a) >= 2 and a[1].isdigit():
        recusar(int(a[1])); return 0
    if cmd == "remover" and len(a) >= 2:
        remover(a[1]); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
