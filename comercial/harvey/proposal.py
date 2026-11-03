"""Proposals: from a conversation to a PDF the client can say yes to.

1. The brain reads the conversation and fills the briefing (what, when,
   where, where it will be used, reference, budget) and picks services from
   the catalog the person gave in onboarding. It never invents a price: lines
   without a catalog price say "sob consulta".
2. Mariana renders the proposal deterministically: services and prices from
   data/onboarding.json, the portfolio pieces matching the client's segment,
   next steps, contacts from the signature.
3. PDF through the installed Google Chrome (or Playwright's Chromium); HTML
   when neither is available. Saved under data/propostas/.

A job row (status "proposal") is created or updated, so the deal shows up in
the Jobs tab and post-job follow-up can run later.
"""

from __future__ import annotations

import html
import json
import logging
import re
import unicodedata
from datetime import date
from pathlib import Path

from harvey import market, portfolio
from harvey.paths import PROJECT_ROOT

logger = logging.getLogger("harvey.proposal")

OUT_DIR = PROJECT_ROOT / "data" / "propostas"
ONBOARDING_FILE = PROJECT_ROOT / "data" / "onboarding.json"

LABELS = {
    "pt-BR": {"title": "Proposta", "for": "Para", "brief": "O que entendi do projeto",
              "what": "Projeto", "when": "Data", "where": "Local", "usage": "Onde vai ser usado",
              "ref": "Referência", "scope": "Escopo", "service": "Serviço", "price": "Investimento",
              "on_request": "sob consulta", "work": "Trabalhos parecidos",
              "next": "Próximos passos", "valid": "Proposta válida por 15 dias.",
              "timeline": "Prazo", "total": "Total"},
    "en": {"title": "Proposal", "for": "For", "brief": "What I understood",
           "what": "Project", "when": "Date", "where": "Location", "usage": "Where it will be used",
           "ref": "Reference", "scope": "Scope", "service": "Service", "price": "Investment",
           "on_request": "on request", "work": "Similar work", "next": "Next steps",
           "valid": "This proposal is valid for 15 days.", "timeline": "Timeline", "total": "Total"},
    "es": {"title": "Propuesta", "for": "Para", "brief": "Lo que entendí del proyecto",
           "what": "Proyecto", "when": "Fecha", "where": "Lugar", "usage": "Dónde se usará",
           "ref": "Referencia", "scope": "Alcance", "service": "Servicio", "price": "Inversión",
           "on_request": "a consultar", "work": "Trabajos similares", "next": "Próximos pasos",
           "valid": "Propuesta válida por 15 días.", "timeline": "Plazo", "total": "Total"},
    "fr": {"title": "Proposition", "for": "Pour", "brief": "Ce que j'ai compris du projet",
           "what": "Projet", "when": "Date", "where": "Lieu", "usage": "Utilisation",
           "ref": "Référence", "scope": "Périmètre", "service": "Service", "price": "Investissement",
           "on_request": "sur demande", "work": "Travaux similaires", "next": "Prochaines étapes",
           "valid": "Proposition valable 15 jours.", "timeline": "Délai", "total": "Total"},
}


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "cliente"


def load_profile() -> dict:
    try:
        return json.loads(ONBOARDING_FILE.read_text(encoding="utf-8")).get("profile", {})
    except (OSError, ValueError):
        return {}


async def extract_briefing(brain, thread_text: str, prospect, company_name: str,
                           services: list[dict], language: str) -> dict:
    catalog = "\n".join(
        f"- {s.get('name')}: {s.get('description', '')} | price: {s.get('starting_price') or 'none'}"
        for s in services if isinstance(s, dict) and s.get("name")) or "(no catalog)"
    prompt = f"""Read this conversation between an audiovisual professional and a
potential client and prepare the data for a proposal. Write every text field
in {market.name_for_code(language)}.
Use ONLY what the conversation says; leave unknown fields empty.

Client: {prospect.full_name()} at {company_name}

SERVICE CATALOG (choose from these; copy the price exactly as written; if the
price is "none", leave price empty):
{catalog}

CONVERSATION:
{thread_text}

Return JSON:
{{"project": "one line", "date": "", "location": "", "usage": "", "reference": "",
  "budget": "", "segment": "igreja|evento|casamento|esporte|marca|imobiliaria|institucional|musica|",
  "intro": "2-3 sentences addressed to the client, first person, referencing their project",
  "items": [{{"service": "catalog name", "details": "what is included for THIS project", "price": ""}}],
  "timeline": "delivery timeline only if the catalog or conversation states it",
  "next_steps": ["2-3 short steps, e.g. confirm date, 50% deposit, kickoff call"]}}"""
    result = await brain.think_json(prompt, agent="proposal", task="briefing")
    return result if isinstance(result, dict) else {}


def render_html(briefing: dict, profile: dict, sig: dict, client: str, contact: str,
                language: str) -> str:
    L = LABELS.get(language) or LABELS.get(language.split("-")[0]) or (LABELS["pt-BR"] if language.startswith("pt") else LABELS["en"])
    esc = lambda v: html.escape(str(v or ""))  # noqa: E731
    accent = esc(sig.get("accent_color") or "#111111")
    person = profile.get("person", {})
    pieces = portfolio.match(briefing.get("segment", ""), briefing.get("project", ""), client,
                             items=(profile.get("offer") or {}).get("portfolio_items") or [],
                             limit=3)
    rows = "".join(
        f"<tr><td><b>{esc(i.get('service'))}</b><br><span class='muted'>{esc(i.get('details'))}</span></td>"
        f"<td class='price'>{esc(i.get('price') or L['on_request'])}</td></tr>"
        for i in briefing.get("items") or [] if isinstance(i, dict))
    facts = "".join(
        f"<div><span class='muted'>{L[key]}</span><br>{esc(briefing.get(field))}</div>"
        for key, field in (("what", "project"), ("when", "date"), ("where", "location"),
                           ("usage", "usage"), ("ref", "reference"), ("timeline", "timeline"))
        if briefing.get(field))
    work = "".join(
        f"<li><a href='{esc(p['url'])}'>{esc(p.get('title') or p['url'])}</a>"
        f" <span class='muted'>({esc(p.get('segment') or '')})</span></li>" for p in pieces)
    steps = "".join(f"<li>{esc(s)}</li>" for s in briefing.get("next_steps") or [])
    contacts = " · ".join(esc(x) for x in (
        person.get("email"), person.get("website") or sig.get("website"),
        ("WhatsApp +" + re.sub(r"\D", "", person.get("whatsapp") or "")) if person.get("whatsapp") else "",
        person.get("instagram")) if x)
    return f"""<!doctype html><html lang="{esc(language)}"><head><meta charset="utf-8">
<title>{L['title']}: {esc(client)}</title><style>
@page {{ size: A4; margin: 18mm; }}
body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; color:#1a1a1a; font-size:12.5px; line-height:1.55; }}
h1 {{ font-size:28px; margin:0 0 4px; letter-spacing:-.5px; }}
h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:1.5px; color:{accent}; margin:28px 0 10px; }}
.top {{ border-bottom:3px solid {accent}; padding-bottom:14px; margin-bottom:8px; }}
.muted {{ color:#777; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px 24px; }}
table {{ width:100%; border-collapse:collapse; }}
td {{ padding:10px 0; border-bottom:1px solid #e5e5e5; vertical-align:top; }}
td.price {{ text-align:right; white-space:nowrap; font-weight:600; padding-left:16px; }}
a {{ color:{accent}; }}
.foot {{ margin-top:36px; font-size:11px; color:#777; border-top:1px solid #e5e5e5; padding-top:10px; }}
</style></head><body>
<div class="top"><div class="muted">{L['title']} · {date.today().strftime('%d/%m/%Y')}</div>
<h1>{esc(briefing.get('project') or client)}</h1>
<div>{L['for']}: <b>{esc(contact)}</b>{(' · ' + esc(client)) if client and client != contact else ''}</div></div>
<p>{esc(briefing.get('intro'))}</p>
{f'<h2>{L["brief"]}</h2><div class="grid">{facts}</div>' if facts else ''}
{f'<h2>{L["scope"]}</h2><table>{rows}</table>' if rows else ''}
{f'<h2>{L["work"]}</h2><ul>{work}</ul>' if work else ''}
{f'<h2>{L["next"]}</h2><ol>{steps}</ol>' if steps else ''}
<div class="foot"><b>{esc(person.get('name'))}</b> · {esc(person.get('role'))}<br>{contacts}<br>{L['valid']}</div>
</body></html>"""


async def to_pdf(html_path: Path) -> Path | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    pdf_path = html_path.with_suffix(".pdf")
    async with async_playwright() as p:
        for launch in ({"channel": "chrome"}, {}):
            try:
                browser = await p.chromium.launch(**launch)
            except Exception:
                continue
            page = await browser.new_page()
            await page.goto(html_path.as_uri())
            await page.pdf(path=str(pdf_path), format="A4", print_background=True)
            await browser.close()
            return pdf_path
    logger.info("proposta: sem Chrome/Chromium para o PDF; ficou em HTML "
                "(instale com: playwright install chromium)")
    return None


async def build_proposal(state, brain, config, conversation_id: str) -> dict:
    """Create the proposal for a conversation. Returns paths + the job id."""
    from harvey import market
    convo = await state.get_conversation(conversation_id)
    if not convo:
        raise ValueError("conversation not found")
    prospect = await state.get_prospect(convo.prospect_id)
    if not prospect:
        raise ValueError("prospect not found")
    company = await state.get_company(prospect.company_id) if prospect.company_id else None
    client = prospect.company or (company.name if company else "")
    mk = await market.for_prospect(state, prospect, getattr(config.persona, "language", "pt-BR"))
    language = market.language(mk)
    profile = load_profile()
    services = (profile.get("offer") or {}).get("services") or []
    thread = "\n".join(f"{'ME' if m.sender == 'harvey' else 'CLIENT'}: {m.content}"
                       for m in convo.thread[-20:])
    briefing = await extract_briefing(brain, thread, prospect, client, services, language)
    if not briefing:
        raise RuntimeError("could not read a briefing from the conversation")

    # Price suggestions from closed jobs (only where the catalog has no price).
    from harvey import pricing
    jobs = await state.get_jobs()
    hints = []
    for item in briefing.get("items") or []:
        if not isinstance(item, dict):
            continue
        hist = pricing.history(jobs, briefing.get("segment", ""), item.get("service", ""))
        if hist:
            hints.append(f"{item.get('service')}: {hist['text']}")
            if not item.get("price"):
                item["price"] = pricing._fmt(hist["median"], hist["symbol"])
                item["price_suggested"] = True
    sig = config.persona.signature.model_dump() if hasattr(config.persona, "signature") else {}
    page = render_html(briefing, profile, sig, client, prospect.full_name() or client, language)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html_path = OUT_DIR / f"{date.today().isoformat()}-{_slug(client or prospect.full_name())}.html"
    html_path.write_text(page, encoding="utf-8")
    pdf_path = await to_pdf(html_path)
    final = pdf_path or html_path

    items = [i for i in briefing.get("items") or [] if isinstance(i, dict)]
    fields = dict(
        company_name=client, contact_name=prospect.full_name(),
        segment=briefing.get("segment", ""),
        service=", ".join(i.get("service", "") for i in items),
        value=" + ".join(i.get("price", "") for i in items if i.get("price")),
        event_date=briefing.get("date", ""), proposal_path=str(final),
        conversation_id=conversation_id,
        briefing_json=json.dumps(briefing, ensure_ascii=False),
        notes=("Histórico de preço: " + "; ".join(hints)) if hints else "",
    )
    job = await state.job_for_conversation(conversation_id)
    if job:
        await state.update_job(job["id"], **fields)
        job_id = job["id"]
    else:
        job_id = await state.add_job(prospect_id=prospect.id, status="proposal", **fields)
    await state.log_action(action_type="proposal_created", agent="proposal",
                           details={"client": client, "file": final.name})
    suggested = [i.get("service") for i in items if i.get("price_suggested")]
    return {"job_id": job_id, "path": str(final), "html": str(html_path),
            "pdf": str(pdf_path) if pdf_path else "", "briefing": briefing,
            "price_hints": hints, "suggested_prices": suggested}
