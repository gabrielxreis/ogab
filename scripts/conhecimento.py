"""Conhecimento da comunidade do Gab (regra do Gabriel, 05/11/2026): toda instalação alimenta o Gab com o que aprende
no trabalho; a lição vai ANÔNIMA para a fila da VPS, o criador aprova no chat e ela entra na base da nuvem, que todo
Gab com licença válida baixa no próximo uso. Nada chega aos outros sem a aprovação do criador.

Quem usa (automático, sem perguntar; vale pelo aceite dos termos, `"relatos": true` no config):
  python3 conhecimento.py registrar --area video --titulo "..." --texto "..."   # manda 1 lição (anônima) para a fila
  python3 conhecimento.py baixar          # baixa a base aprovada (o inicio.py chama; imprime CONHECIMENTO: se mudou)
  python3 conhecimento.py ler [--area X]  # o que a comunidade ensinou (área + geral); o Gab lê no começo da área

Colheita (uma vez por máquina; o inicio.py avisa com COLHEITA_PERGUNTAR):
  python3 conhecimento.py colher          # anotações de "Inteligência nova" das memórias de marca deste computador
  python3 conhecimento.py colher --feito  # marca a colheita como feita (ou --nao se a pessoa recusou)

Criador (`/ogab conhecimento`, só a key de criador):
  python3 conhecimento.py fila            # lições que chegaram: UMA linha cada (--completa = texto inteiro)
  python3 conhecimento.py contar          # só quantas esperam (o pre-commit do dono lembra em todo commit)
  python3 conhecimento.py aprovar todos [menos 2,5]   # aprova tudo; as do menos são recusadas (números ficam fixos)
  python3 conhecimento.py aprovar N [--titulo T] [--texto X] [--area A]   # entra na base (com edição) e sai da fila
  python3 conhecimento.py recusar N[,M...]   # só tira da fila
  python3 conhecimento.py remover <id>    # tira da base uma lição já aprovada
Áreas: video, design, trafego, comercial, negocio, geral.
"""
import difflib, hashlib, json, os, re, sys, time, unicodedata

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


def _fila_salvar(itens):
    _gravar(FILA_LOCAL, itens)


def fila(completa=False):
    """Fila do criador com NÚMEROS ESTÁVEIS: quem já estava mantém o número, o novo vai para o fim e o que saiu do
    servidor fica marcado. Assim "aprovar todos menos 3" sempre fala da lista que o Gabriel viu."""
    key, maq = _cred()
    r = licenca._post("/v1/criador/presets", {"key": key, "maquina": maq}) if key else None
    if not r or r.get("status") != "ok":
        sys.exit(f"não consegui ler a fila: {(r or {}).get('msg', 'sem conexão')}")
    no_servidor = [x["path"] for x in r["presets"] if "/conhecimento/" in x["path"]]
    baixar(calado=True)
    base = _json(BASE, {"licoes": []}).get("licoes", [])
    velhos = [x for x in _json(FILA_LOCAL, []) if isinstance(x, dict) and x.get("path")]
    if not any(not x.get("feito") and x["path"] in no_servidor for x in velhos):
        velhos = []   # nada pendente da lista anterior: recomeça a numeração do 1
    por_path = {x["path"]: x for x in velhos}
    for x in velhos:
        if x["path"] not in no_servidor and not x.get("feito"):
            x["feito"] = "saiu"
    itens = list(velhos)
    for p in no_servidor:
        c = licenca._post("/v1/criador/baixar", {"key": key, "maquina": maq, "path": p})
        if c is None:
            sys.exit("sem conexão no meio da fila: rode de novo (nada mudou)")
        try:
            li = json.loads(c.get("conteudo", ""))
            if not isinstance(li, dict) or not li.get("titulo") or not li.get("texto"):
                raise ValueError
        except Exception:
            li = {"area": "geral", "titulo": "(ilegível)", "texto": str(c.get("conteudo", ""))[:200], "ilegivel": True}
        li["path"] = p
        if p in por_path:
            antigo = por_path[p]
            if antigo.get("feito") and antigo["feito"] != "saiu":
                continue
            antigo.update({k: v for k, v in li.items() if k != "feito"})   # mesmo número, texto atual
        else:
            itens.append(li)
    _fila_salvar(itens)
    pend = [(i, li) for i, li in enumerate(itens, 1) if not li.get("feito")]
    if not pend:
        print("FILA_VAZIA: nenhuma lição esperando aprovação"); return
    print(f"{len(pend)} lição(ões) esperando (aprovar todos | aprovar todos menos N,M | recusar N):")
    for i, li in pend:
        par, nota = _parecida(li, base)
        aviso = f" [PARECIDA {nota:.0%} com {par['id']}]" if par and nota >= 0.55 else ""
        aviso += " [ILEGÍVEL: fica fora do aprovar todos]" if li.get("ilegivel") else ""
        if completa:
            print(f"\n{i}. [{li.get('area')}] {li.get('titulo')}{aviso}\n   {li.get('texto')}")
        else:
            txt = " ".join(str(li.get("texto", "")).split())
            print(f"{i}. [{li.get('area')}] {li.get('titulo')}: {txt[:110] + ('...' if len(txt) > 110 else '')}{aviso}")


def _item(n):
    itens = _json(FILA_LOCAL, [])
    if not (1 <= n <= len(itens)):
        sys.exit("número fora da última fila: rode `conhecimento.py fila` de novo")
    return itens[n - 1]


def _marcar(path, feito):
    itens = _json(FILA_LOCAL, [])
    for x in itens:
        if x.get("path") == path:
            x["feito"] = feito
    _fila_salvar(itens)


def aprovar_licao(li, path=None, sair=True):
    """Devolve True/False; com sair=True (uso avulso) erro encerra o script."""
    def falhou(msg):
        if sair:
            sys.exit(msg)
        print(msg); return False
    area = str(li.get("area") or "geral").lower()
    area = {"trafego pago": "trafego", "negocios": "negocio", "videos": "video"}.get(area, area)
    if area not in AREAS:
        area = "geral"
    key, maq = _cred()
    corpo = {"key": key, "maquina": maq, "licao": {"area": area, "titulo": li.get("titulo", ""),
                                                   "texto": li.get("texto", "")}}
    if path:
        corpo["path"] = path
    r = licenca._post("/v1/criador/conhecimento/aprovar", corpo) if key else None
    if not r or r.get("status") != "ok":
        if r and r.get("status") == "ja_tratada" and path:
            _marcar(path, "tratada fora")
            print(f"JÁ TRATADA: {li.get('titulo')}"); return "ja"
        return falhou(f"não aprovou \"{li.get('titulo')}\": {(r or {}).get('msg', 'sem conexão')}")
    if path:
        _marcar(path, "aprovada")
    baixar(calado=True)
    print(f"APROVADA [{r['licao']['id']}] {r['licao']['titulo']} (base com {r['total']}; chega a todos no próximo uso)")
    return True


def recusar(n):
    key, maq = _cred(); li = _item(n)
    if li.get("feito"):
        print(f"{n}: já {li['feito']}"); return True
    r = licenca._post("/v1/criador/apagar", {"key": key, "maquina": maq, "path": li["path"]})
    if r and r.get("status") == "ok":
        _marcar(li["path"], "recusada"); print(f"RECUSADA {n}: saiu da fila"); return True
    print(f"falhou {n}: {(r or {}).get('msg', 'sem conexão')}"); return False


def remover(id_):
    key, maq = _cred()
    r = licenca._post("/v1/criador/conhecimento/remover", {"key": key, "maquina": maq, "id": id_})
    if r and r.get("status") == "ok":
        baixar(calado=True); print(f"REMOVIDA da base ({r['total']} ficam)")
    else:
        print(f"falhou: {(r or {}).get('msg', 'sem conexão')}")


def contar():
    """Uma linha para o pre-commit do dono: quantas lições esperam aprovação (silencioso se nada ou sem conexão)."""
    key, maq = _cred()
    r = licenca._post("/v1/criador/presets", {"key": key, "maquina": maq}) if key else None
    n = len([x for x in (r or {}).get("presets", []) if "/conhecimento/" in x.get("path", "")])
    if n:
        print(f"CONHECIMENTO_FILA: {n} lição(ões) esperando sua aprovação. Mostrar a fila curta ao Gabriel: "
              "`conhecimento.py fila` (ele responde: aprovar todos, ou todos menos N,M)")
    return n


def _nums(txt):
    try:
        return sorted({int(x) for x in re.split(r"[,\s]+", str(txt).strip()) if x})
    except ValueError:
        sys.exit(f"não entendi os números \"{txt}\": use 2,5")


def aprovar_todos(menos):
    itens = _json(FILA_LOCAL, [])
    if not itens:
        sys.exit("rode `conhecimento.py fila` antes")
    fora = [n for n in menos if not (1 <= n <= len(itens))]
    if fora:
        sys.exit(f"número fora da fila: {fora} (nada foi feito)")
    for n in menos:
        recusar(n)
    ok, falha, pulou, ja = [], [], [], []
    for i, li in enumerate(_json(FILA_LOCAL, []), 1):
        if i in menos or li.get("feito"):
            continue
        if li.get("ilegivel"):
            pulou.append(i); continue
        res = aprovar_licao(li, li.get("path"), sair=False)
        (ja if res == "ja" else ok if res else falha).append(i)
    print(f"RESUMO: aprovadas {ok or '-'}; recusadas {menos or '-'}" + (f"; já tratadas antes {ja}" if ja else "")
          + (f"; FALHARAM {falha} (rode `aprovar todos` de novo, as feitas não repetem)" if falha else "")
          + (f"; ilegíveis fora {pulou}" if pulou else ""))


# ------------------------------------------------------------------ colheita (o que a máquina já aprendeu)
COLHEITA = os.path.expanduser("~/.claude/ogab_relatos/colheita.json")
NOMES_COLHEITA = os.path.expanduser("~/.claude/ogab_relatos/nomes_colheita.json")   # relatar._nomes_privados lê
SECAO = "## Inteligência nova"
PULAR = {"node_modules", ".git", ".Trash", "__pycache__", ".venv", "venv", ".cache", "ogab"}   # em qualquer nível
PULAR_RAIZ = {"Library", "Applications", "Pictures", "Music", "AppData"}   # só logo abaixo da raiz (pasta de cliente
                                                                           # chamada "Music" ainda entra)
DATA = re.compile(r"^\d{2}/\d{2}/\d{4}: ")


def _norm(x):
    return unicodedata.normalize("NFC", x).casefold()


def _raizes():
    cfg = relatar._config()
    casa = os.path.expanduser("~")
    r = [cfg.get("pasta_saida"), cfg.get("pasta_clientes"), "~/Documents", "~/Desktop", "~/Movies", "~/Videos", "~/Downloads"]
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):   # Windows: Documentos/Área de Trabalho redirecionados
        if os.environ.get(var):
            r += [os.path.join(os.environ[var], x) for x in ("Documents", "Documentos", "Desktop", "Área de Trabalho")]
    out = []
    for x in r:
        if x:
            x = os.path.realpath(os.path.expanduser(x))
            if os.path.isdir(x) and x != casa and not any(x == o or x.startswith(o + os.sep) for o in out):
                out = [o for o in out if not o.startswith(x + os.sep)] + [x]   # raiz dentro de outra: uma só
    return out


def _memorias(limite_s=12):
    """Arquivos de memória da marca (<pasta>/<pasta>.md, criados pelo projeto.py memoria) até 5 níveis abaixo."""
    t0, achados, vistos = time.time(), set(), set()
    for raiz in _raizes():
        base = raiz.rstrip(os.sep).count(os.sep)
        for d, subs, fs in os.walk(raiz):
            if time.time() - t0 > limite_s:
                return sorted(achados)
            real = os.path.realpath(d)
            if real in vistos:
                subs[:] = []; continue
            vistos.add(real)
            raiz_nivel = d.count(os.sep) == base
            subs[:] = [x for x in subs if x not in PULAR and not x.startswith(".") and not (raiz_nivel and x in PULAR_RAIZ)]
            if d.count(os.sep) - base >= 5:
                subs[:] = []
            alvo = _norm(os.path.basename(d) + ".md")
            for f in fs:
                if _norm(f) == alvo:
                    arq = os.path.join(d, f)
                    try:
                        with open(arq, encoding="utf-8", errors="replace") as h:
                            if "memória da marca" in h.readline():
                                achados.add(arq)
                    except Exception:
                        pass
    return sorted(achados)


def _anotacoes(arq):
    out, dentro = [], False
    try:
        linhas = open(arq, encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        return out
    for l in linhas:
        if l.startswith("## "):
            dentro = l.startswith(SECAO)
        elif dentro and l.strip().startswith("- "):
            t = DATA.sub("", l.strip()[2:])
            if len(t) >= 20:
                out.append(t)
    return out


def _nomes_da_marca(arq):
    nomes = {os.path.basename(os.path.dirname(arq))}
    try:
        m = re.match(r"#\s+(.+?):\s*memória da marca", open(arq, encoding="utf-8", errors="replace").readline())
        if m:
            nomes.add(m.group(1).strip())
    except Exception:
        pass
    return {n for n in nomes if len(n) >= 3}


def colher(acao=None):
    if acao not in (None, "--checar", "--feito", "--nao"):
        sys.exit("uso: conhecimento.py colher [--checar | --feito | --nao]")
    est = _json(COLHEITA, {})
    if acao in ("--feito", "--nao"):
        est.update(estado="feito" if acao == "--feito" else "recusado", quando=time.strftime("%Y-%m-%d"))
        _gravar(COLHEITA, est); print("COLHEITA: registrado"); return 0
    cfg = relatar._config()
    if cfg.get("dono_biblioteca") or cfg.get("relatos") is not True or est.get("estado"):
        if acao != "--checar":
            print("COLHEITA: nada a fazer (já decidida, relatos desligados ou máquina do criador)")
        return 0
    if acao == "--checar":
        if time.time() - est.get("checado", 0) < 7 * 86400 and not est.get("total"):
            return 0   # procurou há menos de 7 dias e não achou nada: não varre o disco em toda abertura
        if est.get("total") and time.time() - est.get("checado", 0) < 7 * 86400:
            total, n_marcas = est["total"], est.get("marcas", 1)
        else:
            marcas = [(a, _anotacoes(a)) for a in _memorias(limite_s=5)]
            marcas = [(a, n) for a, n in marcas if n]
            total, n_marcas = sum(len(n) for _, n in marcas), len(marcas)
            est.update(checado=time.time(), total=total, marcas=n_marcas); _gravar(COLHEITA, est)
        if total:
            print(f"COLHEITA_PERGUNTAR: {total} anotação(ões) de aprendizado em {n_marcas} marca(s) neste "
                  "computador. Perguntar em UMA linha: \"Posso mandar para a comunidade do Gab, anônimo e sem nome de "
                  "cliente, o que eu já aprendi nos seus trabalhos? O criador aprova antes.\" Sim: `conhecimento.py "
                  "colher`, registrar só o que serve para outros usuários e depois `conhecimento.py colher --feito`. "
                  "Não: `conhecimento.py colher --nao`.")
        return 0
    marcas = [(a, _anotacoes(a)) for a in _memorias()]
    marcas = [(a, n) for a, n in marcas if n]
    total = sum(len(n) for _, n in marcas)
    if not total:
        print("COLHEITA: nenhuma anotação de aprendizado neste computador"); return 0
    nomes_marcas = set().union(*(_nomes_da_marca(a) for a, _ in marcas))
    guardados = set(_json(NOMES_COLHEITA, []))
    _gravar(NOMES_COLHEITA, sorted(guardados | nomes_marcas))   # o registrar também tira esses nomes
    privados = list(relatar._nomes_privados(cfg)) + sorted(nomes_marcas, key=len, reverse=True)
    est.update(estado="em_andamento", quando=time.strftime("%Y-%m-%d")); _gravar(COLHEITA, est)
    print(f"# {total} anotação(ões) para separar (marcas numeradas, nomes já trocados)\n"
          "Registrar com `conhecimento.py registrar` SÓ o que vale para outros usuários, reescrito como regra geral "
          "(sem cliente, marca, pessoa, cidade, preço ou roteiro); gosto de um cliente só fica de fora. Uma lição por "
          "chamada, juntando repetidas. No fim: `conhecimento.py colher --feito`.\n")
    for i, (_, notas) in enumerate(marcas, 1):
        print(f"## marca {i}")
        for n in notas:
            print(f"- {relatar.anonimizar(n, privados)}")
        print()
    return 0


def _opt(a, nome):
    return a[a.index(nome) + 1] if nome in a and a.index(nome) + 1 < len(a) else None


def main(a):
    try:   # Windows sem PYTHONUTF8: acento ou símbolo na nota não derruba a saída
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
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
        fila("--completa" in a); return 0
    if cmd == "contar":
        contar(); return 0
    if cmd == "colher":
        return colher(a[1] if len(a) > 1 else None)
    if cmd == "aprovar" and len(a) >= 2 and a[1] == "todos":
        resto = a[2:]
        if resto and resto[0].lstrip("-") != "menos":
            sys.exit(f"não entendi {resto}: use `aprovar todos` ou `aprovar todos menos 2,5` (nada foi feito)")
        if resto and not _nums(" ".join(resto[1:])):
            sys.exit("faltou o número depois de \"menos\": `aprovar todos menos 2,5` (nada foi feito)")
        aprovar_todos(_nums(" ".join(resto[1:])) if resto else []); return 0
    if cmd == "aprovar" and len(a) >= 2 and a[1].isdigit():
        li = dict(_item(int(a[1])))
        if li.get("feito"):
            print(f"{a[1]}: já {li['feito']}"); return 0
        for k in ("titulo", "texto", "area"):
            if _opt(a, "--" + k):
                li[k] = _opt(a, "--" + k)
        return 0 if aprovar_licao(li, li.get("path")) else 1
    if cmd == "recusar" and len(a) >= 2:
        for n in _nums(" ".join(a[1:])):
            recusar(n)
        return 0
    if cmd == "remover" and len(a) >= 2:
        remover(a[1]); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
