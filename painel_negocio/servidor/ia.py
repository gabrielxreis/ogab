"""IA do Meu Negócio: a pessoa liga a própria chave (Gemini recomendado, grátis no AI Studio; ou Anthropic, ou OpenAI)
em Ajustes, igual ao painel do Instagram do O Gab. A chave fica cifrada em DADOS/ia.enc (chave de cifra em DADOS/.ia_chave,
os dois com permissão 600), nunca no navegador nem no git.

Funções que o painel do Frame Zero chamava no gateway de IA e que respondem aqui com os mesmos formatos:
  ai-generate-budget      {briefing, clientName, projectType} -> {"budget": {...}}
  ai-generate-proposal    {clientName, projectType, briefing, budget, deadline} -> {...proposta...}
  ai-chat                 {messages} -> stream "data: {choices:[{delta:{content}}]}" (botão Refinar)
  parse-bank-statement    extrato em PDF -> {"transactions": [...]} (OFX/CSV seguem no extrato.py, sem IA)
  clean-transaction-names {transactions} -> {"transactions": [...]} com nomes limpos (sem IA devolve igual)
"""
import base64, hashlib, hmac, json, os, re, secrets, urllib.error, urllib.request

DADOS = os.path.expanduser(os.environ.get("DADOS", "~/.ogab/negocio"))
ARQ = os.path.join(DADOS, "ia.enc")
ARQ_CHAVE = os.path.join(DADOS, ".ia_chave")
SEM_CHAVE = "Ligue a IA em Ajustes (chave grátis do Gemini)."
PROVEDORES = ("gemini", "anthropic", "openai")
MODELOS = {
    "gemini": os.environ.get("OGAB_IA_GEMINI", "gemini-flash-latest"),
    "anthropic": os.environ.get("OGAB_IA_ANTHROPIC", "claude-haiku-5-5"),
    "openai": os.environ.get("OGAB_IA_OPENAI", "gpt-5-mini"),
}


class Erro(Exception):
    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


# ---------------------------------------------------------------- chave cifrada

def _segredo():
    if not os.path.exists(ARQ_CHAVE):
        os.makedirs(DADOS, exist_ok=True)
        with open(os.open(ARQ_CHAVE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as f:
            f.write(secrets.token_bytes(32))
    return open(ARQ_CHAVE, "rb").read()


def _fluxo(k, nonce, n):
    saida, i = b"", 0
    while len(saida) < n:
        saida += hashlib.sha256(k + nonce + i.to_bytes(8, "big")).digest()
        i += 1
    return saida[:n]


def _cifrar(dados):
    k = _segredo()
    nonce = secrets.token_bytes(16)
    c = bytes(a ^ b for a, b in zip(dados, _fluxo(k, nonce, len(dados))))
    return nonce + c + hmac.new(k, nonce + c, hashlib.sha256).digest()


def _decifrar(blob):
    k = _segredo()
    nonce, c, tag = blob[:16], blob[16:-32], blob[-32:]
    if not hmac.compare_digest(tag, hmac.new(k, nonce + c, hashlib.sha256).digest()):
        raise Erro("chave da IA corrompida: ligue de novo em Ajustes")
    return bytes(a ^ b for a, b in zip(c, _fluxo(k, nonce, len(c))))


def _config():
    try:
        return json.loads(_decifrar(open(ARQ, "rb").read()))
    except FileNotFoundError:
        return None


def estado():
    c = _config()
    return {"ligada": bool(c), "provedor": c.get("provedor") if c else None,
            "final": c["chave"][-4:] if c else None, "modelo": MODELOS[c["provedor"]] if c else None}


def salvar(provedor, chave):
    provedor, chave = (provedor or "").strip().lower(), (chave or "").strip()
    if provedor not in PROVEDORES:
        raise Erro("Escolha Gemini, Anthropic ou OpenAI")
    if len(chave) < 20:
        raise Erro("Essa chave parece incompleta")
    cfg = {"provedor": provedor, "chave": chave}
    _chamar(cfg, "Responda só OK.", "Teste", max_tokens=20)  # só grava se a chave funcionar
    with open(os.open(ARQ, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as f:
        f.write(_cifrar(json.dumps(cfg).encode()))
    return estado()


def desligar():
    if os.path.exists(ARQ):
        os.remove(ARQ)
    return estado()


# ---------------------------------------------------------------- chamada aos provedores

def _post(url, cabecalhos, corpo):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json", **cabecalhos})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            det = json.loads(e.read() or b"{}")
            msg = (det.get("error") or {}).get("message") if isinstance(det.get("error"), dict) else det.get("error")
        except Exception:
            msg = None
        msg = msg or f"o provedor respondeu {e.code}"
        if e.code in (401, 403) or "API key" in str(msg):
            raise Erro(f"Chave da IA recusada: {msg}", 401)
        if e.code == 429:
            raise Erro("Limite da IA atingido agora. Tente de novo em alguns minutos.", 429)
        raise Erro(f"A IA não respondeu: {msg}", 502)
    except urllib.error.URLError:
        raise Erro("Sem internet para falar com a IA.", 502)


def _chamar(cfg, sistema, usuario, pdf=None, json_saida=False, max_tokens=4000):
    p, k = cfg["provedor"], cfg["chave"]
    if p == "gemini":
        partes = [{"text": usuario}]
        if pdf:
            partes.insert(0, {"inlineData": {"mimeType": "application/pdf", "data": base64.b64encode(pdf).decode()}})
        gc = {"maxOutputTokens": max_tokens * 2}
        if json_saida:
            gc["responseMimeType"] = "application/json"
        r = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELOS[p]}:generateContent", {"x-goog-api-key": k},
                  {"systemInstruction": {"parts": [{"text": sistema}]}, "contents": [{"role": "user", "parts": partes}], "generationConfig": gc})
        return "".join(x.get("text", "") for x in (r.get("candidates") or [{}])[0].get("content", {}).get("parts", [])).strip()
    if p == "anthropic":
        conteudo = [{"type": "text", "text": usuario}]
        if pdf:
            conteudo.insert(0, {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": base64.b64encode(pdf).decode()}})
        r = _post("https://api.anthropic.com/v1/messages", {"x-api-key": k, "anthropic-version": "2023-06-01"},
                  {"model": MODELOS[p], "max_tokens": max_tokens, "system": sistema, "messages": [{"role": "user", "content": conteudo}]})
        return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text").strip()
    conteudo = [{"type": "text", "text": usuario}]
    if pdf:
        conteudo.insert(0, {"type": "file", "file": {"filename": "extrato.pdf", "file_data": "data:application/pdf;base64," + base64.b64encode(pdf).decode()}})
    corpo = {"model": MODELOS[p], "max_completion_tokens": max_tokens * 4, "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": conteudo}]}
    if json_saida:
        corpo["response_format"] = {"type": "json_object"}
    r = _post("https://api.openai.com/v1/chat/completions", {"authorization": f"Bearer {k}"}, corpo)
    return ((r.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip()


def _ia():
    c = _config()
    if not c:
        raise Erro(SEM_CHAVE, 400)
    return c


def _json(texto):
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", texto)
    if m:
        texto = m.group(1)
    m = re.search(r"[\[{][\s\S]*[\]}]", texto)
    if not m:
        raise Erro("A IA respondeu fora do formato. Tente de novo.", 502)
    return json.loads(m.group(0))


# ---------------------------------------------------------------- funções do painel

ORCAMENTO = """Você é um assistente especializado em orçamentos para profissionais criativos (fotógrafos, videomakers, designers, editores).
Baseado no briefing do projeto, gere um orçamento detalhado em formato JSON com a seguinte estrutura:
{"title": "Título do orçamento", "summary": "Resumo executivo do projeto (1-2 frases)",
 "items": [{"description": "Descrição do item/serviço", "quantity": 1, "unit_price": 500.00, "total": 500.00}],
 "subtotal": 0, "discount": 0, "total": 0, "timeline": "Prazo estimado (ex: 5 dias úteis)",
 "payment_terms": "Condições de pagamento sugeridas", "notes": "Observações importantes",
 "scope": ["Item 1 do escopo", "Item 2"], "exclusions": ["O que NÃO está incluído"]}
Considere os preços do mercado brasileiro. Seja realista e detalhado. Os valores devem ser em Reais (BRL).
Sempre inclua todos os custos envolvidos: equipamento, edição, deslocamento, direitos de uso, etc.
Responda APENAS com o JSON."""


def orcamento(corpo):
    corpo = corpo or {}
    if not corpo.get("briefing"):
        raise Erro("Briefing is required")
    usuario = (f"Cliente: {corpo['clientName']}\n" if corpo.get("clientName") else "") + \
              (f"Tipo: {corpo['projectType']}\n" if corpo.get("projectType") else "") + f"Briefing: {corpo['briefing']}"
    b = _json(_chamar(_ia(), ORCAMENTO, usuario, json_saida=True))
    itens = b.get("items") or []
    for it in itens:
        it["total"] = round(float(it.get("quantity") or 1) * float(it.get("unit_price") or 0), 2)
    b["subtotal"] = round(sum(it["total"] for it in itens), 2)
    b["total"] = round(b["subtotal"] - float(b.get("discount") or 0), 2)
    return {"budget": b}


def proposta(corpo, perfil):
    corpo, perfil = corpo or {}, perfil or {}
    nome = f"{perfil.get('first_name') or ''} {perfil.get('last_name') or ''}".strip() or perfil.get("full_name") or ""
    prompt = f"""Você é um especialista em propostas comerciais para profissionais criativos (fotografia, vídeo, design).
Gere uma proposta comercial COMPLETA e profissional em português brasileiro.

Dados do profissional:
- Nome: {nome}
- Empresa: {perfil.get('company_name') or 'Freelancer'}
- Especialidade: {perfil.get('company_slogan') or perfil.get('portfolio_headline') or 'Produção Criativa'}

Dados do projeto:
- Cliente: {corpo.get('clientName') or ''}
- Tipo: {corpo.get('projectType') or ''}
- Briefing: {corpo.get('briefing') or ''}
- Orçamento estimado: R$ {corpo.get('budget') or 'A definir'}
- Prazo: {corpo.get('deadline') or 'A combinar'}

Gere a proposta em JSON:
{{"title": "Título da proposta", "introduction": "Parágrafo de introdução personalizado",
 "scope": ["item 1 do escopo", "item 2"], "deliverables": ["entregável 1", "entregável 2"],
 "timeline": [{{"phase": "Pré-produção", "duration": "X dias", "description": "..."}},
              {{"phase": "Produção", "duration": "X dias", "description": "..."}},
              {{"phase": "Pós-produção", "duration": "X dias", "description": "..."}}],
 "pricing": [{{"item": "descrição", "value": 0}}], "total": 0, "payment_terms": "Condições de pagamento",
 "validity": "15 dias", "terms": ["termo 1", "termo 2"], "conclusion": "Parágrafo de conclusão"}}"""
    return _json(_chamar(_ia(), "Você é um gerador de propostas comerciais. Responda APENAS em JSON válido.", prompt, json_saida=True))


def chat(corpo):
    """Botão Refinar: as mensagens no formato do gateway; devolve o texto todo (o servidor manda como stream)."""
    msgs = (corpo or {}).get("messages") or []
    sistema = "\n\n".join(m.get("content", "") for m in msgs if m.get("role") == "system") or "Você é um assistente útil."
    usuario = "\n\n".join(m.get("content", "") for m in msgs if m.get("role") != "system")
    if not usuario.strip():
        raise Erro("Mensagem vazia")
    return _chamar(_ia(), sistema, usuario, max_tokens=2000)


def extrato_pdf(dados, periodo="all"):
    import datetime as dt
    hoje = dt.date.today()
    inicio = hoje - dt.timedelta(days=int(periodo)) if str(periodo).isdigit() else hoje.replace(year=hoje.year - 5)
    sistema = ("Extraia transações do PDF de extrato bancário. Data: YYYY-MM-DD, description: até 30 caracteres, "
               "amount: positivo, type: income (entrada/crédito) ou expense (saída/débito). Ignore saldos e totais. "
               'Retorne JSON: {"transactions": [{"date":"","description":"","amount":0,"type":"","category":"Outro"}]}')
    t = _json(_chamar(_ia(), sistema, f"Só transações entre {inicio.isoformat()} e {hoje.isoformat()}.", pdf=dados, json_saida=True, max_tokens=8000))
    lista = t.get("transactions") if isinstance(t, dict) else t
    validas = []
    for x in lista or []:
        try:
            v = abs(float(x.get("amount") or 0))
            d = str(x.get("date") or "")[:10]
            if v > 0 and re.match(r"\d{4}-\d{2}-\d{2}$", d) and x.get("type") in ("income", "expense"):
                validas.append({"date": d, "description": str(x.get("description") or "Transação")[:100], "amount": v,
                                "type": x["type"], "category": x.get("category") or "Outro"})
        except (TypeError, ValueError):
            continue
    return validas


def limpar_nomes(transacoes):
    """Deixa os nomes do extrato legíveis ('PIX RECEBIDO 12345 FULANO' -> 'Pix de Fulano'). Sem IA, devolve igual."""
    if not transacoes or not _config():
        return transacoes
    nomes = [t.get("description", "") for t in transacoes]
    sistema = ("Limpe descrições de extrato bancário brasileiro para nomes curtos e legíveis (até 40 caracteres), "
               "sem códigos, números de documento ou datas. Mantenha a mesma ordem e a mesma quantidade. "
               'Responda só JSON: {"nomes": ["...", "..."]}')
    try:
        r = _json(_chamar(_ia(), sistema, json.dumps(nomes, ensure_ascii=False), json_saida=True, max_tokens=3000))
        novos = r.get("nomes") if isinstance(r, dict) else r
        if isinstance(novos, list) and len(novos) == len(transacoes):
            return [{**t, "description": (str(n).strip() or t.get("description"))[:100]} for t, n in zip(transacoes, novos)]
    except Erro:
        pass
    return transacoes
