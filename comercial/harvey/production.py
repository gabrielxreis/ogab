"""From "fechou" to production: details, client folder for /ogab, revisions.

When a job is won:
  1. The brain reads the conversation (and the proposal briefing) and fills
     the production details: shoot date/time, address, on-site contact,
     delivery due date, revision rounds, and a checklist (shots, deliverables,
     things to bring).
  2. The client folder is created where /ogab keeps clients (its config's
     `pasta_saida`, e.g. ~/Documents/CLAUDE BRAIN/<Cliente>/), with:
       <Cliente>.md        brand memory in /ogab's format (created if missing,
                           a "job fechado" line appended under requests)
       briefing-<date>.md  everything Gab needs to start: scope, references,
                           dates, contacts, what the client said
     So `/ogab` opens the job already knowing the client.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import date
from pathlib import Path

from harvey import market  # noqa: E402

logger = logging.getLogger("harvey.production")

OGAB_CONFIG = Path.home() / ".claude" / "skills" / "ogab" / "config.json"
DEFAULT_CLIENTS_DIR = Path.home() / "Documents" / "Mariana" / "clientes"

# /ogab's brand memory sections (scripts/projeto.py SECOES), kept in sync by hand.
OGAB_SECTIONS = {"pedido": "Pedidos diferentes do usuário",
                 "aprendizado": "Inteligência nova (o que funcionou e por quê)",
                 "proxima": "Fazer da próxima vez", "feito": "Histórico de vídeos"}


def clients_dir(config=None) -> Path:
    """Where client folders live: /ogab's pasta_saida when installed."""
    custom = getattr(getattr(config, "production", None), "clients_dir", "") if config else ""
    if custom:
        return Path(custom).expanduser()
    try:
        data = json.loads(OGAB_CONFIG.read_text(encoding="utf-8"))
        if data.get("pasta_saida"):
            return Path(data["pasta_saida"]).expanduser()
    except (OSError, ValueError):
        pass
    return DEFAULT_CLIENTS_DIR


def folder_name(name: str) -> str:
    """'Igreja Batista São João!' → 'Igreja Batista Sao Joao' (like the existing folders)."""
    text = unicodedata.normalize("NFKD", name or "Cliente").encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip()
    return re.sub(r"\s+", " ", text)[:60] or "Cliente"


def ensure_brand_memory(folder: Path, note: str) -> Path:
    """Create <Cliente>.md in /ogab's format if missing, append the note."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{folder.name}.md"
    if not path.exists():
        path.write_text(
            f"# {folder.name}: memória da marca\n\nLida no começo de todo vídeo desta marca. "
            "Regra que virou fixa sobe para o estilo.md do cliente.\n\n"
            + "".join(f"## {v}\n\n" for v in OGAB_SECTIONS.values()), encoding="utf-8")
    lines = path.read_text(encoding="utf-8").split("\n")
    header = "## " + OGAB_SECTIONS["pedido"]
    if header not in lines:
        lines += [header, ""]
    i = lines.index(header) + 1
    while i < len(lines) and not lines[i].startswith("## "):
        i += 1
    while i > 0 and lines[i - 1] == "":
        i -= 1
    lines.insert(i, f"- {date.today():%d/%m/%Y}: {note}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


async def extract_production(brain, thread_text: str, briefing: dict, language: str) -> dict:
    prompt = f"""A video job was just closed. From the conversation and the proposal
briefing, fill the production details. Use ONLY what is written; leave
unknown fields empty. Write text in {market.name_for_code(language)}.

PROPOSAL BRIEFING:
{json.dumps(briefing, ensure_ascii=False)[:4000]}

CONVERSATION:
{thread_text[:8000]}

Return JSON:
{{"shoot_date": "YYYY-MM-DD", "shoot_time": "HH:MM", "address": "", "onsite_contact": "name + phone",
  "delivery_due": "YYYY-MM-DD", "revisions_included": 2,
  "deliverables": ["what will be delivered, formats and durations"],
  "references": ["reference videos or links the client mentioned"],
  "client_requests": ["specific things the client asked for or wants to avoid"],
  "checklist": ["shots to capture and things to bring/confirm, 6-12 short items"]}}"""
    result = await brain.think_json(prompt, agent="production", task="extract")
    return result if isinstance(result, dict) else {}


def write_briefing(folder: Path, job: dict, prod: dict, briefing: dict, thread_text: str) -> Path:
    today = date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", (job.get("service") or "job").lower()).strip("-")[:30] or "job"
    path = folder / f"briefing-{today}-{slug}.md"

    def bullets(items):
        return "\n".join(f"- {i}" for i in items or []) or "- (não informado)"

    path.write_text(f"""# Briefing: {job.get('company_name')} ({job.get('service') or 'job'})

Fechado pela Mariana em {date.today():%d/%m/%Y}. Contato: {job.get('contact_name')}.

## Projeto
{briefing.get('project') or job.get('service') or ''}

- **Valor:** {job.get('value') or '(ver proposta)'}
- **Gravação:** {prod.get('shoot_date') or '?'} {prod.get('shoot_time') or ''}
- **Local:** {prod.get('address') or '?'}
- **Contato no local:** {prod.get('onsite_contact') or '?'}
- **Entrega:** {prod.get('delivery_due') or '?'}
- **Rodadas de revisão:** {prod.get('revisions_included') or 2}
- **Onde vai ser usado:** {briefing.get('usage') or '?'}
- **Proposta:** {job.get('proposal_path') or '(sem proposta)'}

## Entregáveis
{bullets(prod.get('deliverables') or [f"{i.get('service')}: {i.get('details', '')}" for i in briefing.get('items') or [] if isinstance(i, dict)])}

## Referências
{bullets(prod.get('references') or ([briefing['reference']] if briefing.get('reference') else []))}

## O que o cliente pediu
{bullets(prod.get('client_requests'))}

## Checklist de gravação
{chr(10).join(f"- [ ] {c}" for c in prod.get('checklist') or []) or '- [ ] (montar)'}

## Conversa com o cliente
```
{thread_text[-6000:]}
```
""", encoding="utf-8")
    return path


async def on_job_won(state, brain, config, job_id: str) -> dict:
    """Fill production details and create the client folder. Idempotent enough:
    re-running appends a new memory line and a new dated briefing."""
    from harvey import market
    job = await state.get_job(job_id)
    if not job:
        raise ValueError("job not found")
    thread_text, language = "", "pt-BR"
    if job.get("conversation_id"):
        convo = await state.get_conversation(job["conversation_id"])
        if convo:
            thread_text = "\n".join(f"{'EU' if m.sender == 'harvey' else 'CLIENTE'}: {m.content}"
                                    for m in convo.thread[-30:])
    prospect = await state.get_prospect(job["prospect_id"]) if job.get("prospect_id") else None
    if prospect:
        mk = await market.for_prospect(state, prospect, getattr(config.persona, "language", "pt-BR"))
        language = market.language(mk)
    try:
        briefing = json.loads(job.get("briefing_json") or "{}")
    except ValueError:
        briefing = {}
    prod = await extract_production(brain, thread_text, briefing, language) if (thread_text or briefing) else {}

    fields = {k: str(prod[k]) for k in ("shoot_date", "shoot_time", "address", "onsite_contact",
                                         "delivery_due") if prod.get(k)}
    if prod.get("revisions_included"):
        try:
            fields["revisions_included"] = int(prod["revisions_included"])
        except (TypeError, ValueError):
            pass
    if prod.get("checklist"):
        fields["checklist"] = "\n".join(str(c) for c in prod["checklist"])

    folder = clients_dir(config) / folder_name(job.get("company_name") or job.get("contact_name"))
    memory = ensure_brand_memory(
        folder, f"job fechado pela Mariana: {job.get('service') or 'job'}"
        + (f", gravação {fields['shoot_date']}" if fields.get("shoot_date") else "")
        + (f", entrega {fields['delivery_due']}" if fields.get("delivery_due") else "")
        + ". Briefing nesta pasta.")
    merged = {**job, **fields}
    brief = write_briefing(folder, merged, prod, briefing, thread_text)
    fields["project_dir"] = str(folder)
    await state.update_job(job_id, **fields)
    await state.log_action(action_type="project_created", agent="production",
                           details={"client": job.get("company_name"), "folder": str(folder)})
    return {"folder": str(folder), "memory": str(memory), "briefing": str(brief), **fields}
