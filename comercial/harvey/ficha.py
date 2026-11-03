"""Conversation sheet for a lead: what they like and which work to show.

Before a call or a reply, `mariana ficha` reads what is public about the lead
(their site, the signals already collected, the notes from prospecting) and
writes data/fichas/<company>.md with:
  - interests and tastes, each with the evidence it came from
  - icebreakers that connect those interests to the user's own story
  - likely pains and what to ask
  - the 3 portfolio pieces that make the difference for THIS lead, and why
  - what to avoid

The icebreaker and the chosen pieces also go into the lead's notes, so the
next message the agents write already uses them. Only public, professional
information: no private life, family or anything they did not publish.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path

from harvey import portfolio
from harvey.dossie import SOBRE_FILE
from harvey.onboard import KNOWLEDGE_FILE, crawl_site
from harvey.paths import PROJECT_ROOT

OUT_DIR = PROJECT_ROOT / "data" / "fichas"
NOTE_TAG = "[ficha]"


def _slug(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "lead").encode("ascii", "ignore").decode()
    return re.sub(r"[^\w-]+", "-", text.lower()).strip("-")[:60] or "lead"


def _about_user() -> str:
    parts = []
    for f in (KNOWLEDGE_FILE, SOBRE_FILE):
        if f.exists():
            parts.append(f.read_text(encoding="utf-8")[:12000])
    return "\n\n".join(parts)


async def build(state, brain, prospect_id: str, crawl: bool = True) -> Path:
    p = await state.get_prospect(prospect_id)
    if not p:
        raise ValueError("lead não encontrado")
    c = await state.get_company(p.company_id) if p.company_id else None
    name = c.name if c else p.company
    signals = []
    if p.company_id:
        for row in await state.get_observations(company_id=p.company_id, latest_only=True):
            value = row.get("value_text") or row.get("value_num") or ""
            signals.append(f"- {row['signal_code']}: {value}")
    site_text = ""
    site = (c.website or c.domain) if c else ""
    if crawl and site:
        site_text = (await crawl_site(site, max_pages=6))[:15000]
    items = portfolio.load_items()
    seg = portfolio.segment_of(p.industry, name, c.description if c else "")

    prompt = f"""You prepare an audiovisual professional for a conversation with a
potential client. Write in Portuguese (Brazil). Never use em dashes.

Use ONLY the evidence below. Every interest must cite where it came from
(site page, signal, note). If there is no evidence for something, say so.
Only public, professional information: never private life, family, health,
politics or anything the lead did not publish.

LEAD: {p.full_name()} ({p.title}) at {name}
Industry: {p.industry}  |  Segment: {seg or "geral"}
Notes from prospecting: {p.personalization_notes}
Company description: {c.description if c else ""}
Signals:
{chr(10).join(signals) or "(none)"}

THEIR SITE:
{site_text or "(not read)"}

ABOUT THE PROFESSIONAL (to connect stories):
{_about_user()}

PORTFOLIO (choose from these only):
{portfolio.describe(items) or "(none)"}

Return JSON:
{{
  "summary": "",                                    // 2 lines: who they are and what they want now
  "interests": [{{"what": "", "evidence": ""}}],
  "icebreakers": [""],                              // 3, each linking their interest to the professional
  "pains": [""],
  "questions": [""],                                // 3 discovery questions
  "works": [{{"title": "", "url": "", "why": ""}}],  // the 3 that make the difference for this lead
  "avoid": [""]
}}"""
    d = await brain.think_json(prompt, agent="ficha", task="lead_sheet")
    if not isinstance(d, dict):
        raise RuntimeError("o cérebro não devolveu a ficha; tente de novo")

    def clean(s):
        return str(s).replace("—", ",").replace("–", ",")

    out = [f"# Ficha de conversa: {name}", "",
           f"_{p.full_name()} ({p.title}) | segmento {seg or 'geral'} | {date.today().strftime('%d/%m/%Y')}_", "",
           clean(d.get("summary", "")), "", "## Gostos e interesses", ""]
    out += [f"- **{clean(i.get('what', ''))}** ({clean(i.get('evidence', ''))})"
            for i in d.get("interests") or []] or ["- Sem evidência pública ainda."]
    out += ["", "## Para quebrar o gelo", ""] + [f"- {clean(x)}" for x in d.get("icebreakers") or []]
    out += ["", "## Dores prováveis", ""] + [f"- {clean(x)}" for x in d.get("pains") or []]
    out += ["", "## Perguntas", ""] + [f"- {clean(x)}" for x in d.get("questions") or []]
    out += ["", "## Trabalhos para mostrar", ""]
    out += [f"- **{clean(w.get('title', ''))}**: {w.get('url', '')} ({clean(w.get('why', ''))})"
            for w in d.get("works") or []]
    out += ["", "## Evitar", ""] + [f"- {clean(x)}" for x in d.get("avoid") or []] + [""]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{_slug(name)}.md"
    path.write_text("\n".join(out), encoding="utf-8")

    # The next message the agents write already uses the sheet.
    ice = clean((d.get("icebreakers") or [""])[0])
    works = ", ".join(f"{w.get('title', '')} {w.get('url', '')}".strip() for w in d.get("works") or [])
    base = (p.personalization_notes or "").split(NOTE_TAG)[0].strip()
    note = f"{base}\n{NOTE_TAG} Gancho: {ice} | Trabalhos: {works}".strip()
    await state.update_prospect_notes(p.id, note[:1500])
    return path
