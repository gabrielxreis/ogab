"""Meu Negócio do O Gab: servidor local (só 127.0.0.1) que imita o Supabase do Frame Zero.

O painel (web/, fork do Frame Zero) usa o supabase-js sem mudança; aqui respondem:
  /rest/v1/<tabela>      PostgREST (filtros, embeds por chave estrangeira, ordem, contagem, upsert)
  /rest/v1/rpc/<função>  RPCs que o painel chama
  /auth/v1/*             login automático de um usuário local (sem senha: roda só na máquina da pessoa)
  /storage/v1/*          arquivos em DADOS/arquivos/<bucket>/
  /functions/v1/*        funções (extrato do banco em OFX/CSV; o resto responde sem IA)
  /api/ogab/*            assinatura do O Gab (key de licença) e resumo para o /ogab
Dados em SQLite (DADOS/negocio.db), cada linha guardada como JSON. Python só com a biblioteca padrão.
"""
import base64, datetime as dt, email.parser, email.policy, functools, json, mimetypes, os, re
import secrets, sqlite3, sys, threading, urllib.parse, urllib.request, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.expanduser(os.environ.get("DADOS", "~/.ogab/negocio"))
WEB = os.environ.get("WEB", os.path.join(AQUI, "..", "web", "dist"))
PORTA = int(os.environ.get("PORTA", "3200"))
UID = "00000000-0000-4000-8000-000000000001"
ESQUEMA = json.load(open(os.path.join(AQUI, "esquema.json"), encoding="utf-8"))
TRAVA = threading.RLock()
os.makedirs(os.path.join(DADOS, "arquivos"), exist_ok=True)

sys.path.insert(0, AQUI)
import contrato  # noqa: E402
import email_envio  # noqa: E402
import extrato  # noqa: E402
import ia  # noqa: E402
import ogab  # noqa: E402

# No Windows o mimetypes lê o registro, que às vezes diz text/plain para .js e o navegador recusa o módulo
for _ext, _tipo in ((".js", "application/javascript"), (".mjs", "application/javascript"), (".css", "text/css"),
                    (".svg", "image/svg+xml"), (".json", "application/json"), (".webp", "image/webp"),
                    (".woff2", "font/woff2"), (".wasm", "application/wasm")):
    mimetypes.add_type(_tipo, _ext)


def agora():
    return dt.datetime.now(dt.timezone.utc).isoformat()


# ---------------------------------------------------------------- banco

class Banco:
    def __init__(self, caminho):
        self.con = sqlite3.connect(caminho, check_same_thread=False)
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("CREATE TABLE IF NOT EXISTS linhas (tabela TEXT, pk TEXT, dados TEXT, PRIMARY KEY (tabela, pk))")
        self.cache = {}

    def tabela(self, t):
        if t not in self.cache:
            cur = self.con.execute("SELECT pk, dados FROM linhas WHERE tabela=? ORDER BY rowid", (t,))
            self.cache[t] = {pk: json.loads(d) for pk, d in cur}
        return self.cache[t]

    def linhas(self, t):
        return list(self.tabela(t).values())

    def gravar(self, t, linha):
        pk = chave(t, linha)
        self.tabela(t)[pk] = linha
        self.con.execute("INSERT OR REPLACE INTO linhas VALUES (?,?,?)", (t, pk, json.dumps(linha, ensure_ascii=False)))

    def apagar(self, t, linha):
        pk = chave(t, linha)
        self.tabela(t).pop(pk, None)
        self.con.execute("DELETE FROM linhas WHERE tabela=? AND pk=?", (t, pk))

    def salvar(self):
        self.con.commit()


def chave(t, linha):
    cols = ESQUEMA.get(t, {}).get("pk") or ["id"]
    return "|".join(str(linha.get(c)) for c in cols)


BANCO = Banco(os.path.join(DADOS, "negocio.db"))


# ---------------------------------------------------------------- tipos e padrões

INTEIROS = {"integer", "bigint", "smallint"}
DECIMAIS = {"numeric", "double precision", "real"}


def coagir(t, col, v):
    info = ESQUEMA.get(t, {}).get("colunas", {}).get(col)
    if info is None or v is None:
        return v
    tipo = info["tipo"]
    try:
        if tipo in INTEIROS and not isinstance(v, bool):
            return None if v == "" else int(float(v))
        if tipo in DECIMAIS and not isinstance(v, bool):
            return None if v == "" else float(v)
        if tipo == "boolean" and isinstance(v, str):
            return v.lower() in ("true", "t", "1", "yes")
        if tipo == "date" and isinstance(v, str) and len(v) > 10:
            return v[:10]
    except (TypeError, ValueError):
        return v
    return v


def padrao(t, col, info):
    p = info.get("padrao")
    if not p:
        return None
    if "gen_random_uuid" in p and "replace" in p:
        return uuid.uuid4().hex
    if "gen_random_uuid" in p:
        return str(uuid.uuid4())
    if "gen_random_bytes" in p:
        return secrets.token_hex(32)
    if "auth.uid()" in p:
        return UID
    if p.startswith("nextval("):
        return max([int(r.get(col) or 0) for r in BANCO.linhas(t)] + [0]) + 1
    m = re.match(r"\(now\(\) \+ '(.+)'::interval\)", p)
    if m:
        txt = m.group(1)
        d = re.match(r"(\d+) days?", txt)
        h = re.match(r"(\d+):(\d+):(\d+)", txt)
        delta = dt.timedelta(days=int(d.group(1))) if d else dt.timedelta(hours=int(h.group(1)), minutes=int(h.group(2))) if h else dt.timedelta()
        return (dt.datetime.now(dt.timezone.utc) + delta).isoformat()
    if p in ("now()", "CURRENT_TIMESTAMP", "timezone('utc'::text, now())"):
        return agora()
    if p == "CURRENT_DATE":
        return dt.date.today().isoformat()
    if p in ("true", "false"):
        return p == "true"
    m = re.match(r"^'(.*)'::([\w ]+)(\[\])?$", p, re.S)
    if m:
        txt, tipo, arr = m.groups()
        if arr or txt.startswith("{") and tipo not in ("jsonb", "json"):
            return [x.strip('"') for x in txt.strip("{}").split(",") if x]
        if tipo in ("jsonb", "json"):
            try:
                return json.loads(txt)
            except ValueError:
                return txt
        if tipo in INTEIROS:
            return int(txt)
        if tipo in DECIMAIS:
            return float(txt)
        return txt
    if p.startswith("ARRAY["):
        return re.findall(r"'([^']*)'", p)
    try:
        return int(p) if re.fullmatch(r"-?\d+", p) else float(p)
    except ValueError:
        return None


def linha_nova(t, item):
    cols = ESQUEMA.get(t, {}).get("colunas", {})
    linha = {}
    for c, info in cols.items():
        if c not in item:
            linha[c] = padrao(t, c, info)
    for c, v in item.items():
        linha[c] = coagir(t, c, v)
    if not cols:  # tabela só do Meu Negócio (crm_tarefas, crm_notas...): id e datas automáticos
        linha.setdefault("id", str(uuid.uuid4()))
        linha.setdefault("created_at", agora())
        linha.setdefault("updated_at", linha["created_at"])
    return linha


# ---------------------------------------------------------------- comparação

def como_data(s):
    if not isinstance(s, str) or not re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def comparar(a, b):
    """-1/0/1 entre o valor da linha (a) e o texto do filtro ou outro valor (b)."""
    if isinstance(a, bool):
        b = b if isinstance(b, bool) else str(b).lower() in ("true", "t", "1")
        return (a > b) - (a < b)
    if isinstance(a, (int, float)):
        try:
            b = float(b)
        except (TypeError, ValueError):
            return -1
        return (a > b) - (a < b)
    da, db = como_data(a), como_data(b)
    if da and db:
        return (da > db) - (da < db)
    a, b = str(a), str(b)
    return (a > b) - (a < b)


def lista_pg(txt):
    """'(a,b,"c d")' ou '{a,b}' -> ['a','b','c d']"""
    txt = txt.strip()
    if txt[:1] in "({" and txt[-1:] in ")}":
        txt = txt[1:-1]
    saida, atual, aspas = [], "", False
    for ch in txt:
        if ch == '"':
            aspas = not aspas
        elif ch == "," and not aspas:
            saida.append(atual)
            atual = ""
        else:
            atual += ch
    if atual or saida:
        saida.append(atual)
    return saida


def valor_pg(v):
    if isinstance(v, str):
        t = v.strip()
        if t.startswith(("[", "{\"", "{}")) or (t.startswith("{") and ":" in t):
            try:
                return json.loads(t)
            except ValueError:
                pass
        if t.startswith("{"):
            return lista_pg(t)
    return v


def casa(a, op, v):
    if op == "is":
        v = v.lower()
        if v == "null":
            return a is None
        if v in ("true", "false"):
            return a is (v == "true")
        if v == "unknown":
            return a is None
        return False
    if op in ("eq", "neq", "gt", "gte", "lt", "lte"):
        if a is None:
            return False
        c = comparar(a, v) if not isinstance(a, (dict, list)) else (0 if json.dumps(a) == v else 1)
        return {"eq": c == 0, "neq": c != 0, "gt": c > 0, "gte": c >= 0, "lt": c < 0, "lte": c <= 0}[op]
    if op == "in":
        if a is None:
            return False
        return any(comparar(a, x) == 0 for x in lista_pg(v))
    if op in ("like", "ilike", "match", "imatch"):
        if a is None:
            return False
        if op in ("match", "imatch"):
            return re.search(v, str(a), re.I if op == "imatch" else 0) is not None
        padrao_re = "^" + re.escape(v).replace(r"\*", ".*").replace("%", ".*").replace(r"\%", ".*").replace("_", ".") + "$"
        return re.match(padrao_re, str(a), re.S | (re.I if op == "ilike" else 0)) is not None
    if op in ("cs", "cd", "ov"):
        if a is None:
            return False
        b = valor_pg(v)
        if isinstance(a, dict) and isinstance(b, dict):
            return all(a.get(k) == x for k, x in b.items()) if op == "cs" else all(b.get(k) == x for k, x in a.items())
        a_l = a if isinstance(a, list) else [a]
        b_l = b if isinstance(b, list) else [b]
        sa, sb = [json.dumps(x) if isinstance(x, (dict, list)) else str(x) for x in a_l], [json.dumps(x) if isinstance(x, (dict, list)) else str(x) for x in b_l]
        if op == "cs":
            return all(x in sa for x in sb)
        if op == "cd":
            return all(x in sb for x in sa)
        return any(x in sb for x in sa)
    if op in ("fts", "plfts", "phfts", "wfts"):
        palavras = re.sub(r"^\w+\(.*?\)\.", "", v).replace("'", " ").replace("&", " ").replace("|", " ").split()
        texto = str(a or "").lower()
        return all(p.lower().strip(":*") in texto for p in palavras)
    return True


def pegar(linha, col):
    """col pode ser 'a->b->>c' (JSON)."""
    if "->" not in col:
        return linha.get(col)
    partes = re.split(r"->>?", col)
    v = linha.get(partes[0])
    for p in partes[1:]:
        if isinstance(v, dict):
            v = v.get(p.strip("'"))
        elif isinstance(v, list) and p.isdigit() and int(p) < len(v):
            v = v[int(p)]
        else:
            return None
    if col.split(partes[-1])[0].endswith("->>") and v is not None and not isinstance(v, str):
        v = json.dumps(v) if isinstance(v, (dict, list)) else str(v).lower() if isinstance(v, bool) else v
    return v


def separar_topo(txt, sep=","):
    partes, nivel, atual, aspas = [], 0, "", False
    for ch in txt:
        if ch == '"':
            aspas = not aspas
        if not aspas:
            if ch == "(":
                nivel += 1
            elif ch == ")":
                nivel -= 1
            elif ch == sep and nivel == 0:
                partes.append(atual)
                atual = ""
                continue
        atual += ch
    if atual:
        partes.append(atual)
    return partes


def condicao(expr):
    """Texto 'col.op.val' ou 'and(...)' / 'or(...)' / 'not.and(...)' -> função(linha)."""
    expr = expr.strip()
    neg = False
    if expr.startswith("not.") and re.match(r"not\.(and|or)\(", expr):
        neg, expr = True, expr[4:]
    m = re.match(r"^(and|or)\((.*)\)$", expr, re.S)
    if m:
        f = grupo(m.group(1), m.group(2))
        return (lambda l: not f(l)) if neg else f
    col, resto = expr.split(".", 1)
    return filtro(col, resto)


def grupo(tipo, txt):
    fs = [condicao(p) for p in separar_topo(txt)]
    return (lambda l: all(f(l) for f in fs)) if tipo == "and" else (lambda l: any(f(l) for f in fs))


def filtro(col, op_val):
    neg = False
    if op_val.startswith("not."):
        neg, op_val = True, op_val[4:]
    op, _, v = op_val.partition(".")
    m = re.match(r"^(\w+)\((.*)\)$", op)  # fts(config) / any/all
    if m and m.group(1) in ("fts", "plfts", "phfts", "wfts"):
        op = m.group(1)
    if len(v) > 1 and v[0] == '"' and v.endswith('"'):
        v = v[1:-1]
    f = lambda l: casa(pegar(l, col), op, v)
    return (lambda l: not f(l)) if neg else f


# ---------------------------------------------------------------- select e embeds

def ler_select(txt):
    itens = []
    for parte in separar_topo(re.sub(r"\s+(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", "", txt or "*")):
        if not parte:
            continue
        alias = None
        m = re.match(r"^([\w-]+):(?!:)(.*)$", parte, re.S)
        if m:
            alias, parte = m.group(1), m.group(2)
        m = re.match(r"^([\w-]+)((?:![\w-]+)*)\((.*)\)$", parte, re.S)
        if m and m.group(1) not in ("count", "sum", "avg", "min", "max"):
            dicas = [d for d in m.group(2).split("!") if d]
            interno = "inner" in dicas
            dicas = [d for d in dicas if d not in ("inner", "left")]
            itens.append({"tipo": "embed", "rel": m.group(1), "alias": alias or m.group(1), "dica": dicas[0] if dicas else None,
                          "inner": interno, "sub": ler_select(m.group(3))})
            continue
        if parte == "*":
            itens.append({"tipo": "tudo"})
            continue
        if parte in ("count()", "count"):
            itens.append({"tipo": "count", "alias": alias or "count"})
            continue
        nome = parte.split("::")[0]
        chave_saida = alias or re.split(r"->>?", nome)[-1].strip("'")
        itens.append({"tipo": "col", "nome": nome, "alias": chave_saida})
    return itens


def relacao(pai, rel, dica):
    """-> (tabela, 'um'|'muitos', coluna_local, coluna_remota) ou None."""
    ep = ESQUEMA.get(pai, {})
    candidatos = []
    for fk in ep.get("fks", []):  # pai.col -> rel.id : objeto
        if fk["ref"] == rel or fk["coluna"] == rel or fk["nome"] == rel:
            candidatos.append((fk["ref"], "um", fk["coluna"], fk["ref_coluna"], fk))
    if rel in ESQUEMA:
        for fk in ESQUEMA[rel].get("fks", []):  # rel.col -> pai.id : lista
            if fk["ref"] == pai:
                unico = [fk["coluna"]] in ESQUEMA[rel].get("unicos", []) or ESQUEMA[rel].get("pk") == [fk["coluna"]]
                candidatos.append((rel, "um" if unico else "muitos", fk["ref_coluna"], fk["coluna"], fk))
    if dica:
        filtrados = [c for c in candidatos if dica in (c[4]["nome"], c[4]["coluna"]) or dica == c[0]]
        if not filtrados and dica in ESQUEMA:  # dica = tabela alvo, rel = coluna
            filtrados = [c for c in candidatos if c[0] == dica]
        candidatos = filtrados or candidatos
    if not candidatos:
        return None
    alvo_direto = [c for c in candidatos if c[0] == rel]
    c = (alvo_direto or candidatos)[0]
    return c[:4]


def aplicar_ordem(linhas, ordem_txt):
    if not ordem_txt:
        return linhas
    regras = []
    for parte in ordem_txt.split(","):
        bits = parte.split(".")
        col, desc, nulos = bits[0], "desc" in bits[1:], None
        if "nullsfirst" in bits:
            nulos = "first"
        elif "nullslast" in bits:
            nulos = "last"
        else:
            nulos = "first" if desc else "last"
        regras.append((col, desc, nulos))

    def cmp(x, y):
        for col, desc, nulos in regras:
            a, b = pegar(x, col), pegar(y, col)
            if a is None and b is None:
                continue
            if a is None or b is None:
                primeiro_nulo = -1 if nulos == "first" else 1
                return primeiro_nulo if a is None else -primeiro_nulo
            c = comparar(a, b)
            if c:
                return -c if desc else c
        return 0
    return sorted(linhas, key=functools.cmp_to_key(cmp))


def montar(t, linha, itens, opcoes, caminho=""):
    """Aplica o select a uma linha. Devolve None se um embed !inner ficar vazio."""
    saida = {}
    cols = ESQUEMA.get(t, {}).get("colunas", {})
    for it in itens:
        if it["tipo"] == "tudo":
            for c in cols:
                saida[c] = linha.get(c)
            for c, v in linha.items():
                saida.setdefault(c, v)
        elif it["tipo"] == "col":
            saida[it["alias"]] = pegar(linha, it["nome"])
    for it in itens:
        if it["tipo"] != "embed":
            continue
        rel = relacao(t, it["rel"], it["dica"])
        sub_caminho = (caminho + "." if caminho else "") + it["alias"]
        if not rel:
            saida[it["alias"]] = None
            continue
        alvo, modo, local, remoto = rel
        filhos = [r for r in BANCO.linhas(alvo) if linha.get(local) is not None and r.get(remoto) is not None
                  and comparar(r.get(remoto), linha.get(local)) == 0]
        for f in opcoes["filtros"].get(sub_caminho, []):
            filhos = [r for r in filhos if f(r)]
        filhos = aplicar_ordem(filhos, opcoes["ordens"].get(sub_caminho))
        lim = opcoes["limites"].get(sub_caminho)
        if lim is not None:
            filhos = filhos[opcoes["inicios"].get(sub_caminho, 0):][:lim]
        montados = [m for m in (montar(alvo, r, it["sub"], opcoes, sub_caminho) for r in filhos) if m is not None]
        if any(s["tipo"] == "count" for s in it["sub"]):
            montados = [{"count": len(montados)}]
        if modo == "um":
            valor = montados[0] if montados else None
            if it["inner"] and valor is None:
                return None
            # filtro no embed de um-para-um sem !inner deixa o objeto nulo
            if not montados and opcoes["filtros"].get(sub_caminho) and not it["inner"]:
                valor = None
            saida[it["alias"]] = valor
        else:
            if it["inner"] and not montados:
                return None
            saida[it["alias"]] = montados
    return saida


# ---------------------------------------------------------------- PostgREST

RESERVADOS = {"select", "order", "limit", "offset", "on_conflict", "columns"}


def ler_consulta(q):
    opcoes = {"filtros": {}, "ordens": {}, "limites": {}, "inicios": {}, "select": "*", "on_conflict": None, "columns": None}
    for k, v in q:
        base, _, ultimo = k.rpartition(".")
        if k == "select":
            opcoes["select"] = v
        elif k == "on_conflict":
            opcoes["on_conflict"] = v
        elif k == "columns":
            opcoes["columns"] = v
        elif ultimo in ("order", "limit", "offset") or k in ("order", "limit", "offset"):
            nome, caminho = (ultimo, base) if ultimo in ("order", "limit", "offset") else (k, "")
            if nome == "order":
                opcoes["ordens"][caminho] = v
            elif nome == "limit":
                opcoes["limites"][caminho] = int(v)
            else:
                opcoes["inicios"][caminho] = int(v)
        elif ultimo in ("or", "and"):
            neg = base == "not" or base.endswith(".not")
            caminho = "" if base in ("", "not") else base[:-4] if neg else base
            f = grupo(ultimo, v[1:-1] if v.startswith("(") else v)
            opcoes["filtros"].setdefault(caminho, []).append((lambda l, f=f: not f(l)) if neg else f)
        else:
            caminho, col = (base, ultimo) if base and "->" not in k else ("", k)
            opcoes["filtros"].setdefault(caminho, []).append(filtro(col, v))
    return opcoes


def filtrar(t, opcoes):
    linhas = BANCO.linhas(t)
    for f in opcoes["filtros"].get("", []):
        linhas = [l for l in linhas if f(l)]
    return linhas


def consultar(t, opcoes, rng=None):
    linhas = aplicar_ordem(filtrar(t, opcoes), opcoes["ordens"].get(""))
    itens = ler_select(opcoes["select"])
    montadas = [m for m in (montar(t, l, itens, opcoes) for l in linhas) if m is not None]
    total = len(montadas)
    ini = opcoes["inicios"].get("", 0)
    lim = opcoes["limites"].get("")
    if rng:
        ini, fim = rng
        lim = fim - ini + 1 if fim is not None else None
    montadas = montadas[ini:]
    if lim is not None:
        montadas = montadas[:lim]
    if any(i["tipo"] == "count" for i in itens) and not any(i["tipo"] in ("col", "tudo") for i in itens):
        montadas = [{"count": total}]
    return montadas, total, ini


def conflito(t, linha, cols_lista):
    for cols in cols_lista:
        if any(linha.get(c) is None for c in cols):
            continue
        for r in BANCO.linhas(t):
            if all(comparar(r.get(c), linha.get(c)) == 0 for c in cols):
                return r
    return None


def inserir(t, corpo, opcoes, prefer):
    itens = corpo if isinstance(corpo, list) else [corpo]
    upsert = "resolution=" in prefer
    ignorar = "ignore-duplicates" in prefer
    alvo = [opcoes["on_conflict"].split(",")] if opcoes["on_conflict"] else [ESQUEMA.get(t, {}).get("pk") or ["id"]]
    unicos = alvo + ESQUEMA.get(t, {}).get("unicos", []) if not upsert else alvo
    feitos = []
    for item in itens:
        if opcoes["columns"]:
            cols = [c.strip('"') for c in opcoes["columns"].split(",")]
            item = {k: v for k, v in item.items() if k in cols}
        if upsert:
            existente = conflito(t, {c: coagir(t, c, item.get(c)) for c in alvo[0]}, alvo)
            if existente is not None:
                if ignorar:
                    continue
                novo = dict(existente)
                for c, v in item.items():
                    novo[c] = coagir(t, c, v)
                if "updated_at" in ESQUEMA.get(t, {}).get("colunas", {}) and "updated_at" not in item:
                    novo["updated_at"] = agora()
                if chave(t, novo) != chave(t, existente):
                    BANCO.apagar(t, existente)
                BANCO.gravar(t, novo)
                feitos.append(novo)
                continue
        linha = linha_nova(t, item)
        if not upsert and conflito(t, linha, unicos) is not None:
            return None, {"code": "23505", "details": None, "hint": None,
                          "message": f'duplicate key value violates unique constraint "{t}_key"'}
        BANCO.gravar(t, linha)
        feitos.append(linha)
    return feitos, None


def rpc(nome, args):
    if nome == "get_effective_dashboard_id":
        ds = sorted([d for d in BANCO.linhas("dashboards") if d.get("user_id") == UID], key=lambda d: d.get("created_at") or "")
        return ds[0]["id"] if ds else None
    if nome in ("get_effective_credit_user_id",):
        return UID
    if nome == "is_admin":
        return False
    if nome in ("get_ai_credits", "consume_ai_credit"):
        return {"user_id": UID, "success": True, "monthly_limit": 999999, "current_usage": 0, "bonus_credits": 0,
                "remaining": 999999, "monthly_remaining": 999999, "bonus_remaining": 0, "consumed": args.get("p_amount", 1)}
    if nome in ("get_document_signers_safe", "get_user_signers_safe"):
        doc = args.get("p_document_id") or args.get("document_id")
        return [s for s in BANCO.linhas("signature_signers") if not doc or s.get("document_id") == doc]
    if nome == "get_or_create_dm_conversation":
        return None
    if nome.startswith("admin_"):
        return []
    return None


# ---------------------------------------------------------------- auth

def jwt():
    cab = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    exp = int(dt.datetime.now().timestamp()) + 10 * 365 * 86400
    corpo = base64.urlsafe_b64encode(json.dumps({"sub": UID, "role": "authenticated", "aud": "authenticated", "exp": exp}).encode()).rstrip(b"=").decode()
    return f"{cab}.{corpo}.local", exp


def usuario():
    p = BANCO.tabela("profiles").get(UID) or {}
    return {"id": UID, "aud": "authenticated", "role": "authenticated", "email": p.get("email") or "voce@ogab.local",
            "email_confirmed_at": "2026-01-01T00:00:00Z", "phone": "", "confirmed_at": "2026-01-01T00:00:00Z",
            "last_sign_in_at": agora(), "app_metadata": {"provider": "email", "providers": ["email"]},
            "user_metadata": {"full_name": p.get("full_name") or "", "username": p.get("username") or ""},
            "identities": [], "created_at": "2026-01-01T00:00:00Z", "updated_at": agora(), "is_anonymous": False}


def sessao():
    token, exp = jwt()
    return {"access_token": token, "token_type": "bearer", "expires_in": 10 * 365 * 86400, "expires_at": exp,
            "refresh_token": "local", "user": usuario()}


def semear():
    """Primeira vez: perfil, painel, workspace e dono, com nome e e-mail da key do O Gab."""
    with TRAVA:
        conta = ogab.conta()
        nome = conta.get("nome") or ""
        if UID not in BANCO.tabela("profiles"):
            usuario_nome = re.sub(r"[^a-z0-9_]", "", (conta.get("email") or "voce").split("@")[0].lower())[:20] or "voce"
            BANCO.gravar("profiles", linha_nova("profiles", {"id": UID, "full_name": nome, "username": usuario_nome,
                                                             "email": conta.get("email") or "voce@ogab.local"}))
        if not [d for d in BANCO.linhas("dashboards") if d.get("user_id") == UID]:
            BANCO.gravar("dashboards", linha_nova("dashboards", {"user_id": UID, "name": "Meu negócio"}))
        painel = rpc("get_effective_dashboard_id", {})
        if not BANCO.linhas("workspaces"):
            ws = linha_nova("workspaces", {"name": "Meu negócio", "created_by": UID, "owner_id": UID, "dashboard_id": painel})
            BANCO.gravar("workspaces", ws)
            BANCO.gravar("workspace_members", linha_nova("workspace_members", {"workspace_id": ws["id"], "user_id": UID, "role": "owner"}))
        for ws in BANCO.linhas("workspaces"):  # sem dashboard_id o app não acha o workspace e espera 8 s
            if not ws.get("dashboard_id"):
                BANCO.gravar("workspaces", {**ws, "dashboard_id": painel})
        BANCO.salvar()


# ---------------------------------------------------------------- funções

IA_FUNCOES = ("ai-generate-budget", "ai-generate-proposal", "ai-chat", "parse-bank-statement", "clean-transaction-names")


def funcao(nome, corpo, arquivos):
    if nome == "generate-contract":  # sem IA: modelo fixo com os dados do formulário, no formato de stream
        if not corpo or not corpo.get("clientName") or not corpo.get("contractValue"):
            return 400, {"error": "Campos obrigatórios não preenchidos"}
        return 200, contrato.sse(contrato.texto(corpo)), "text/event-stream"
    if nome == "check-subscription":
        a = ogab.assinatura()
        return 200, {"subscribed": True, "plan": "premium", "product_id": "ogab", "subscription_end": a.get("ate")}
    if nome in ("calendar-sync", "telegram-send", "whatsapp-send"):
        return 200, {"ok": True, "skipped": True}
    return 501, {"error": "Isso usa IA ou serviço online e ainda não está ligado no Meu Negócio do O Gab. Peça ao Gab no chat."}


# ---------------------------------------------------------------- HTTP

class Pedido(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "OGabNegocio/1"

    def log_message(self, fmt, *args):
        if os.environ.get("LOG"):
            sys.stderr.write("%s\n" % (fmt % args))

    # respostas
    def enviar(self, status, corpo=None, tipo="application/json", extra=None):
        if status >= 400 and not self.path.startswith(("/assets", "/favicon")):
            sys.stderr.write(f"[{status}] {self.command} {self.path[:300]} -> {str(corpo)[:300]}\n")
        dados = b"" if corpo is None else corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", tipo + ("; charset=utf-8" if tipo.startswith(("application/json", "text/")) else ""))
        self.send_header("Content-Length", str(len(dados) if self.command != "HEAD" else len(dados)))
        self.send_header("Cache-Control", "no-store" if tipo == "application/json" else "no-cache")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD" and dados:
            self.wfile.write(dados)

    def corpo_bruto(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def corpo_json(self):
        bruto = self.corpo_bruto()
        if not bruto:
            return None
        try:
            return json.loads(bruto)
        except ValueError:
            return None

    def multipart(self, bruto):
        tipo = self.headers.get("Content-Type", "")
        msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(b"Content-Type: " + tipo.encode() + b"\r\n\r\n" + bruto)
        saida = {}
        for parte in msg.iter_parts():
            nome = parte.get_param("name", header="content-disposition") or ""
            saida[nome] = (parte.get_filename() or "", parte.get_payload(decode=True) or b"", parte.get_content_type())
        return saida

    def local(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        return self.client_address[0] in ("127.0.0.1", "::1") and host in ("127.0.0.1", "localhost", "")

    def do_OPTIONS(self):
        self.enviar(204)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.rotear("GET")

    def do_POST(self):
        self.rotear("POST")

    def do_PATCH(self):
        self.rotear("PATCH")

    def do_PUT(self):
        self.rotear("PUT")

    def do_DELETE(self):
        self.rotear("DELETE")

    def rotear(self, metodo):
        if not self.local():
            return self.enviar(403, {"error": "só abre nesta máquina"})
        url = urllib.parse.urlsplit(self.path)
        caminho = urllib.parse.unquote(url.path)
        q = urllib.parse.parse_qsl(url.query, keep_blank_values=True)
        try:
            if caminho == "/api/ogab/assinatura":  # vai à internet (até 8 s): fora da trava do banco
                status, r = ogab.rota(metodo, "assinatura", self.corpo_json(), BANCO, UID)
                nome = (r.get("nome") or "").split()
                if nome:  # o perfil local ganha o nome do cadastro no ogab.io (aparece em cards, log e comentários)
                    with TRAVA:
                        p = BANCO.tabela("profiles").get(UID)
                        if p and not p.get("first_name"):
                            p.update(first_name=nome[0], last_name=" ".join(nome[1:]) or None, full_name=" ".join(nome))
                            BANCO.gravar("profiles", p)
                            BANCO.salvar()
                return self.enviar(status, r)
            if caminho == "/api/ogab/email":  # SMTP pode levar segundos: fora da trava do banco
                if metodo == "GET":
                    return self.enviar(200, email_envio.status(DADOS))
                try:
                    return self.enviar(200, email_envio.configurar(DADOS, self.corpo_json() or {}))
                except email_envio.Erro as e:
                    sys.stderr.write(f"[e-mail] {e}\n")  # sem senha: só o motivo do servidor de e-mail
                    return self.enviar(400, {"error": str(e)})
            if caminho == "/functions/v1/send-quote-email":
                return self.enviar(*email_envio.enviar_orcamento(DADOS, self.corpo_json() or {}))
            if caminho == "/api/ogab/ia" or caminho[14:] in IA_FUNCOES and caminho.startswith("/functions/v1/"):
                return self.ia_rota(metodo, caminho)  # a IA demora: fora da trava do banco
            with TRAVA:
                if caminho.startswith("/rest/v1/rpc/"):
                    return self.enviar(200, rpc(caminho[13:], self.corpo_json() or dict(q)))
                if caminho.startswith("/rest/v1/"):
                    return self.rest(metodo, caminho[9:], q)
                if caminho.startswith("/auth/v1/"):
                    return self.auth(metodo, caminho[9:])
                if caminho.startswith("/storage/v1/"):
                    return self.storage(metodo, caminho[12:], q)
                if caminho.startswith("/functions/v1/"):
                    bruto = self.corpo_bruto()
                    if "multipart/form-data" in (self.headers.get("Content-Type") or ""):
                        status, r = funcao(caminho[14:], None, self.multipart(bruto))
                    else:
                        try:
                            corpo = json.loads(bruto) if bruto else None
                        except ValueError:
                            corpo = None
                        status, r, *tipo = funcao(caminho[14:], corpo, {})
                        if tipo:
                            return self.enviar(status, r, tipo[0])
                    return self.enviar(status, r)
                if caminho.startswith("/api/ogab/"):
                    return self.enviar(*ogab.rota(metodo, caminho[10:], self.corpo_json(), BANCO, UID))
            return self.estatico(caminho)
        except (BrokenPipeError, ConnectionResetError):
            return None  # o navegador desistiu do pedido (troca de página): nada a responder
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            return self.enviar(500, {"code": "XX000", "message": str(e), "details": None, "hint": None})

    def ia_rota(self, metodo, caminho):
        """Ajustes da IA (/api/ogab/ia) e as funções que usam IA. Erro da IA vira mensagem amigável no painel."""
        try:
            if caminho == "/api/ogab/ia":
                if metodo == "GET":
                    return self.enviar(200, ia.estado())
                corpo = self.corpo_json() or {}
                if corpo.get("desligar"):
                    return self.enviar(200, ia.desligar())
                return self.enviar(200, ia.salvar(corpo.get("provedor"), corpo.get("chave")))
            nome = caminho[14:]
            bruto = self.corpo_bruto()
            if nome == "parse-bank-statement":
                arquivos = self.multipart(bruto)
                arq = arquivos.get("file")
                if not arq:
                    return self.enviar(400, {"error": "Arquivo não fornecido"})
                periodo = (arquivos.get("period_days") or (None, b"all"))[1].decode() or "all"
                if not arq[0].lower().endswith(".pdf"):
                    try:
                        return self.enviar(200, extrato.ler(arq[0], arq[1], periodo))
                    except extrato.Erro as e:
                        return self.enviar(400, {"error": str(e)})
                trans = ia.extrato_pdf(arq[1], periodo)
                if not trans:
                    return self.enviar(422, {"error": "Nenhuma transação encontrada no PDF. Tente o extrato em OFX ou CSV."})
                return self.enviar(200, {"success": True, "transactions": trans, "total": len(trans), "summary": {
                    "income": sum(t["amount"] for t in trans if t["type"] == "income"),
                    "expense": sum(t["amount"] for t in trans if t["type"] == "expense")}})
            corpo = json.loads(bruto) if bruto else {}
            if nome == "clean-transaction-names":
                return self.enviar(200, {"transactions": ia.limpar_nomes(corpo.get("transactions", []))})
            if nome == "ai-generate-budget":
                return self.enviar(200, ia.orcamento(corpo))
            if nome == "ai-generate-proposal":
                with TRAVA:
                    perfil = dict(BANCO.tabela("profiles").get(UID) or {})
                return self.enviar(200, ia.proposta(corpo, perfil))
            if nome == "ai-chat":
                return self.enviar(200, contrato.sse(ia.chat(corpo)), "text/event-stream")
            return self.enviar(404, {"error": "função"})
        except ia.Erro as e:
            return self.enviar(e.status, {"error": str(e), "ia": True})

    def rest(self, metodo, t, q):
        opcoes = ler_consulta(q)
        prefer = self.headers.get("Prefer") or ""
        objeto = "vnd.pgrst.object" in (self.headers.get("Accept") or "")
        contar = re.search(r"count=(exact|planned|estimated)", prefer)
        rng = None
        if self.headers.get("Range"):
            m = re.match(r"(\d+)-(\d*)", self.headers["Range"])
            if m:
                rng = (int(m.group(1)), int(m.group(2)) if m.group(2) else None)
        if metodo == "GET":
            linhas, total, ini = consultar(t, opcoes, rng)
            return self.resposta(linhas, objeto, total if contar else None, ini, 200)
        if metodo == "POST":
            corpo = self.corpo_json()
            if corpo is None:
                return self.enviar(400, {"code": "PGRST102", "message": "corpo vazio"})
            feitos, erro = inserir(t, corpo, opcoes, prefer)
            if erro:
                return self.enviar(409, erro)
            BANCO.salvar()
            return self.escrita(t, feitos, opcoes, prefer, objeto, 201)
        if metodo == "PATCH":
            corpo = self.corpo_json() or {}
            alvo = filtrar(t, opcoes)
            feitos = []
            tem_updated = "updated_at" in ESQUEMA.get(t, {}).get("colunas", {})
            for l in alvo:
                novo = dict(l)
                for c, v in corpo.items():
                    novo[c] = coagir(t, c, v)
                if tem_updated and "updated_at" not in corpo:
                    novo["updated_at"] = agora()
                if chave(t, novo) != chave(t, l):
                    BANCO.apagar(t, l)
                BANCO.gravar(t, novo)
                feitos.append(novo)
            BANCO.salvar()
            return self.escrita(t, feitos, opcoes, prefer, objeto, 200)
        if metodo == "DELETE":
            alvo = filtrar(t, opcoes)
            for l in alvo:
                BANCO.apagar(t, l)
            BANCO.salvar()
            return self.escrita(t, alvo, opcoes, prefer, objeto, 200)
        return self.enviar(405, {"message": "método"})

    def escrita(self, t, feitas, opcoes, prefer, objeto, status):
        if "return=representation" not in prefer:
            return self.enviar(201 if status == 201 else 204)
        itens = ler_select(opcoes["select"])
        montadas = [m for m in (montar(t, l, itens, opcoes) for l in feitas) if m is not None]
        return self.resposta(montadas, objeto, None, 0, status)

    def resposta(self, linhas, objeto, total, ini, status):
        extra = {}
        if total is not None:
            fim = ini + len(linhas) - 1
            extra["Content-Range"] = (f"{ini}-{fim}" if linhas else "*") + f"/{total}"
        if objeto:
            if len(linhas) != 1:
                return self.enviar(406, {"code": "PGRST116", "details": f"The result contains {len(linhas)} rows",
                                         "hint": None, "message": "JSON object requested, multiple (or no) rows returned"})
            return self.enviar(status, linhas[0], extra=extra)
        return self.enviar(status, linhas, extra=extra)

    def auth(self, metodo, rota):
        if rota.startswith("token") or rota in ("signup", "otp", "verify"):
            self.corpo_bruto()
            return self.enviar(200, sessao())
        if rota == "user":
            if metodo == "PUT":
                corpo = self.corpo_json() or {}
                meta = corpo.get("data") or {}
                if meta.get("full_name"):
                    p = BANCO.tabela("profiles").get(UID)
                    if p:
                        p["full_name"] = meta["full_name"]
                        BANCO.gravar("profiles", p)
                        BANCO.salvar()
            return self.enviar(200, usuario())
        if rota == "logout":
            self.corpo_bruto()
            return self.enviar(204)
        if rota == "settings":
            return self.enviar(200, {"external": {"email": True}, "disable_signup": False})
        if rota.startswith("factors") or rota.startswith("mfa"):
            return self.enviar(200, {"all": [], "totp": [], "phone": []})
        return self.enviar(200, {})

    def storage(self, metodo, rota, q):
        partes = rota.split("/")
        base = os.path.join(DADOS, "arquivos")
        if partes[:2] == ["object", "list"] and metodo == "POST":
            corpo = self.corpo_json() or {}
            pasta = os.path.join(base, partes[2], corpo.get("prefix") or "")
            itens = []
            if os.path.isdir(pasta):
                for n in sorted(os.listdir(pasta)):
                    cam = os.path.join(pasta, n)
                    eh_arq = os.path.isfile(cam)
                    itens.append({"name": n, "id": n if eh_arq else None, "created_at": agora(), "updated_at": agora(),
                                  "metadata": {"size": os.path.getsize(cam), "mimetype": mimetypes.guess_type(n)[0]} if eh_arq else None})
            return self.enviar(200, itens)
        if partes[0] == "object" and metodo == "DELETE":
            corpo = self.corpo_json() or {}
            removidos = []
            for p in corpo.get("prefixes", []):
                cam = os.path.normpath(os.path.join(base, partes[1], p))
                if cam.startswith(base) and os.path.isfile(cam):
                    os.remove(cam)
                    removidos.append({"name": p})
            return self.enviar(200, removidos)
        if partes[:2] == ["object", "sign"] and metodo == "POST":
            self.corpo_bruto()
            return self.enviar(200, {"signedURL": "/object/sign/" + "/".join(partes[2:]) + "?token=local"})
        if partes[:2] == ["object", "upload"] or partes[:3] == ["object", "upload", "sign"]:
            return self.enviar(200, {"url": "/object/" + "/".join(partes[3:]) + "?token=local", "token": "local"})
        if partes[0] == "object" and metodo in ("POST", "PUT"):
            rel = "/".join(partes[1:])
            cam = os.path.normpath(os.path.join(base, rel))
            if not cam.startswith(base):
                return self.enviar(400, {"error": "caminho"})
            bruto = self.corpo_bruto()
            if "multipart/form-data" in (self.headers.get("Content-Type") or ""):
                for campo, (_, dados, _) in self.multipart(bruto).items():
                    if campo != "cacheControl" and dados:
                        bruto = dados
            os.makedirs(os.path.dirname(cam), exist_ok=True)
            with open(cam, "wb") as f:
                f.write(bruto)
            return self.enviar(200, {"Key": rel, "Id": rel, "path": "/".join(partes[2:]), "fullPath": rel})
        if partes[0] == "object" and metodo == "GET":
            resto = partes[1:]
            if resto and resto[0] in ("public", "authenticated", "sign"):
                resto = resto[1:]
            cam = os.path.normpath(os.path.join(base, *resto))
            if cam.startswith(base) and os.path.isfile(cam):
                with open(cam, "rb") as f:
                    return self.enviar(200, f.read(), mimetypes.guess_type(cam)[0] or "application/octet-stream")
            return self.enviar(404, {"error": "not_found", "message": "Object not found", "statusCode": "404"})
        if partes[0] == "bucket":
            return self.enviar(200, [] if metodo == "GET" else {"name": partes[-1]})
        return self.enviar(404, {"error": "rota"})

    def estatico(self, caminho):
        raiz = os.path.abspath(WEB)
        cam = os.path.normpath(os.path.join(raiz, caminho.lstrip("/")))
        if not cam.startswith(raiz) or not os.path.isfile(cam):
            cam = os.path.join(raiz, "index.html")
        if not os.path.isfile(cam):
            return self.enviar(503, b"Painel ainda nao montado: rode abrir.sh", "text/plain")
        with open(cam, "rb") as f:
            dados = f.read()
        tipo = mimetypes.guess_type(cam)[0] or "application/octet-stream"
        extra = {"Cache-Control": "public, max-age=31536000, immutable"} if "/assets/" in cam else {}
        return self.enviar(200, dados, tipo, extra)


class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def main():
    semear()
    ogab.iniciar(BANCO, UID)
    srv = Servidor(("127.0.0.1", PORTA), Pedido)
    print(f"Meu Negócio do O Gab em http://127.0.0.1:{PORTA}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
