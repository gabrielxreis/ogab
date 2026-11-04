"""Parte do O Gab no Meu Negócio: conta e assinatura pela key de licença (~/.claude/ogab_licenca.json)
e o resumo que o /ogab lê para responder no chat (GET /api/ogab/resumo)."""
import datetime as dt, json, os, threading, time, urllib.request

ARQ = os.path.join(os.path.expanduser("~"), ".claude", "ogab_licenca.json")
URL = os.environ.get("OGAB_LICENCA_URL", "https://licencas.gabrielxreis.com").rstrip("/")
_cache = {"em": 0, "dados": None}
_trava = threading.Lock()


def _licenca():
    try:
        return json.load(open(ARQ, encoding="utf-8"))
    except Exception:
        return {}


def conta():
    d = _licenca()
    a = _cache["dados"] or {}
    return {"email": d.get("email") or a.get("email") or "", "nome": a.get("nome") or ""}


def assinatura(forcar=False):
    """{plano, pago, ate (ISO ou None), email, nome, offline}. Consulta o servidor no máximo a cada 10 min."""
    with _trava:
        if not forcar and _cache["dados"] and time.time() - _cache["em"] < 600:
            return _cache["dados"]
        d = _licenca()
        saida = {"plano": None, "pago": None, "ate": None, "email": d.get("email", ""), "nome": "", "offline": False,
                 "key": (d.get("key") or "")[:8] + "…" if d.get("key") else None}
        if d.get("key") and d.get("maquina"):
            try:
                req = urllib.request.Request(URL + "/v1/validar", data=json.dumps({"key": d["key"], "maquina": d["maquina"]}).encode(),
                                             headers={"Content-Type": "application/json", "User-Agent": "ogab-negocio/1"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    x = json.loads(r.read() or b"{}")
                saida.update(status=x.get("status"), plano=x.get("plano"), pago=x.get("pago"), nome=x.get("nome") or "",
                             criador=x.get("criador", False), email=x.get("email") or saida["email"])
                if x.get("pago_ate"):
                    saida["ate"] = dt.datetime.fromtimestamp(int(x["pago_ate"]), dt.timezone.utc).isoformat()
            except Exception:
                saida["offline"] = True
        _cache.update(em=time.time(), dados=saida)
        return saida


def _hoje():
    return dt.date.today().isoformat()


def resumo(banco, uid):
    """Visão geral em números: o mesmo que o painel mostra, para o /ogab responder no chat."""
    hoje = _hoje()
    mes = hoje[:7]
    cards = banco.linhas("project_cards")
    colunas = {c["id"]: c for c in banco.linhas("project_columns")}
    projetos = {p["id"]: p for p in banco.linhas("projects")}
    abertos = [c for c in cards if not c.get("is_archived") and not c.get("completed_at")
               and not (colunas.get(c.get("column_id"), {}).get("name", "").lower().startswith(("conclu", "feito", "done", "entreg")))]
    atrasados = [c for c in abertos if c.get("due_date") and str(c["due_date"])[:10] < hoje]
    trans = banco.linhas("financial_transactions")
    do_mes = [t for t in trans if str(t.get("paid_date") or t.get("due_date") or t.get("created_at") or "")[:7] == mes]
    entradas = sum(float(t.get("amount") or 0) for t in do_mes if t.get("type") == "income")
    saidas = sum(float(t.get("amount") or 0) for t in do_mes if t.get("type") == "expense")
    orc = banco.linhas("financial_quotes")
    eventos = [e for e in banco.linhas("calendar_events") if str(e.get("start_date") or "")[:10] == hoje]
    crm = [{"etapa": c.get("funnel_stage") or "lead"} for c in banco.linhas("clients")]
    tarefas_crm = [t for t in banco.linhas("crm_tarefas") if not t.get("feita")]
    return {
        "assinatura": assinatura(),
        "trabalhos": {"abertos": len(abertos), "atrasados": len(atrasados),
                      "lista": [{"titulo": c.get("title"), "projeto": projetos.get(c.get("project_id"), {}).get("name"),
                                 "prazo": c.get("due_date")} for c in sorted(abertos, key=lambda c: str(c.get("due_date") or "9"))[:15]]},
        "orcamentos": {"total": len(orc), "pendentes": len([o for o in orc if o.get("status") in ("draft", "sent", "pending")]),
                       "aprovados": len([o for o in orc if o.get("status") in ("approved", "accepted")]),
                       "valor_pendente": sum(float(o.get("total") or 0) for o in orc if o.get("status") in ("draft", "sent", "pending"))},
        "financeiro_mes": {"mes": mes, "entradas": round(entradas, 2), "saidas": round(saidas, 2), "saldo": round(entradas - saidas, 2)},
        "agenda_hoje": [{"titulo": e.get("title"), "inicio": e.get("start_date")} for e in eventos],
        "crm": {"pessoas": len(crm), "por_etapa": {k: len([p for p in crm if p.get("etapa") == k]) for k in sorted({p.get("etapa") for p in crm if p.get("etapa")})},
                "tarefas_abertas": len(tarefas_crm)},
    }


def rota(metodo, caminho, corpo, banco, uid):
    if caminho == "assinatura":
        return 200, assinatura(forcar=bool(corpo and corpo.get("forcar")))
    if caminho == "resumo":
        return 200, resumo(banco, uid)
    if caminho == "empresa":
        # dados do negócio que o Claude puxou das conversas (negocio.sh empresa <json>); o assistente de
        # primeiro acesso mostra preenchido e a pessoa confere
        arq = os.path.join(os.path.expanduser(os.environ.get("DADOS", "~/.ogab/negocio")), "empresa_sugerida.json")
        if metodo == "POST":
            if not isinstance(corpo, dict):
                return 400, {"error": "mande um JSON com os campos"}
            permitidos = {"tipo", "nome", "documento", "email", "telefone", "instagram", "site", "endereco", "cidade",
                          "pix", "cor", "logo_url", "slogan", "servicos"}
            dados = {k: v for k, v in corpo.items() if k in permitidos and v not in (None, "")}
            with open(arq, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            return 200, {"ok": True, "campos": sorted(dados)}
        try:
            sugerida = json.load(open(arq, encoding="utf-8"))
        except Exception:
            sugerida = {}
        a = assinatura()
        return 200, {"sugerida": sugerida, "conta": {"nome": a.get("nome") or "", "email": a.get("email") or ""}}
    if caminho == "saude":
        # "banco": identidade deste banco; o painel limpa o cache do navegador se ela mudar (banco recriado)
        ids = banco.tabela("ogab_config")
        if "banco" not in ids:
            import uuid
            banco.gravar("ogab_config", {"id": "banco", "valor": str(uuid.uuid4())})
            banco.salvar()
        return 200, {"ok": True, "banco": ids["banco"]["valor"]}
    return 404, {"error": "rota"}


def iniciar(banco, uid):
    threading.Thread(target=assinatura, daemon=True).start()
