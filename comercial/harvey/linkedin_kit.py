"""LinkedIn kit: the user's profile, posts of their work and the send queue.

Nothing here logs into LinkedIn or clicks for the user (that breaks LinkedIn's
terms and gets accounts restricted). Mariana writes, the user pastes or sends:

  perfil  data/linkedin/perfil.md   every profile field ready to paste, in
                                    Portuguese and English: headline options,
                                    About, experience, featured, skills,
                                    custom URL, banner brief for the design area (/ogab design)
  posts   data/linkedin/posts.md    one post per portfolio piece, approved by
                                    the user and posted from their account (or
                                    scheduled with a connected official tool)
  fila    the approved LinkedIn drafts of the Mensagens tab, one at a time:
          invites first (only after the warm-up, under the daily and weekly
          caps), then the message of each accepted invite. Copy the text, open
          the profile, the user sends, Mariana marks it. Warm-up, accepted
          invites and the rest live in linkedin_growth.py
"""

from __future__ import annotations

import json
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from harvey import portfolio
from harvey.dossie import SOBRE_FILE, copy_to_clipboard
from harvey.onboard import KNOWLEDGE_FILE
from harvey.paths import PROJECT_ROOT

OUT_DIR = PROJECT_ROOT / "data" / "linkedin"

RULES = """Rules:
- Use ONLY facts from the material. Never invent clients, numbers, dates or awards.
  When something is missing, write [FALTA: what is missing] so the user fills it.
- Never use em dashes or en dashes. Use colons, commas or parentheses.
- No hype words (apaixonado, guru, ninja, rockstar, passionate, visionary).
- Concrete beats adjectives: who you film for, what changed for them."""


def _material() -> str:
    parts = []
    for f in (KNOWLEDGE_FILE, SOBRE_FILE):
        if f.exists():
            parts.append(f.read_text(encoding="utf-8")[:30000])
    return "\n\n".join(parts)


def _clean(value):
    if isinstance(value, str):
        return value.replace("—", ",").replace("–", ",").strip()
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    return value


def _pt_en(d, key) -> tuple[str, str]:
    v = d.get(key) or {}
    if isinstance(v, str):
        return v, ""
    return v.get("pt", ""), v.get("en", "")


async def build_profile(brain) -> Path:
    material = _material()
    if not material:
        raise ValueError("sem material: rode o onboarding ou 'mariana dossie' antes")
    items = portfolio.load_items()
    prompt = f"""You are a LinkedIn profile strategist for audiovisual professionals
(filmmakers, video editors, producers). Build this person's complete profile,
optimized to be found by and convince the clients in their dossier, in
Portuguese (pt) and English (en).

{RULES}

Material about the person:
{material}

Portfolio pieces:
{portfolio.describe(items) or "(none listed)"}

Return JSON:
{{
  "headlines": [{{"pt": "", "en": "", "why": ""}}],        // 3 options, max 220 chars, keywords clients search
  "about": {{"pt": "", "en": ""}},                          // 1500-2200 chars, hook in the first 2 lines, ends with a clear call to action
  "experience": [{{"title": "", "company": "", "period": "", "location": "",
                   "description": {{"pt": "", "en": ""}}}}],  // newest first, bullet results
  "featured": [{{"title": "", "url": "", "why": ""}}],      // 3-5, strongest first
  "skills": [""],                                           // top 15, ordered; first 3 are the pinned ones
  "services": [""],                                         // for the Services section
  "custom_url": "",                                         // suggested linkedin.com/in/<slug>
  "banner_brief": "",                                       // what the cover image says and shows (for a designer)
  "photo_tips": "",
  "open_to": "",                                            // what to set in Open to work / providing services
  "missing": [""]                                           // what the person still needs to send
}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="profile")
    if not isinstance(data, dict):
        raise RuntimeError("o cérebro não devolveu o perfil; tente de novo")
    data = _clean(data)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "perfil.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    path = OUT_DIR / "perfil.md"
    path.write_text(render_profile(data), encoding="utf-8")
    return path


def render_profile(d: dict) -> str:
    out = ["# Perfil do LinkedIn (pronto para colar)", "",
           "Cada bloco vai num campo do perfil. Troque o que estiver em [FALTA: ...] antes de colar.",
           "Ordem sugerida: foto e capa, título, Sobre, Experiência, Destaques, Competências, Serviços, URL.", ""]
    out += ["## Título (headline): escolha um", ""]
    for n, h in enumerate(d.get("headlines") or [], 1):
        out += [f"**Opção {n}** ({h.get('why', '')})", "", f"PT: {h.get('pt', '')}", "",
                f"EN: {h.get('en', '')}", ""]
    pt, en = _pt_en(d, "about")
    out += ["## Sobre", "", "### Português", "", pt, "", "### English", "", en, ""]
    out += ["## Experiência", ""]
    for e in d.get("experience") or []:
        dpt, den = _pt_en(e, "description")
        out += [f"### {e.get('title', '')} | {e.get('company', '')}",
                f"{e.get('period', '')} | {e.get('location', '')}", "", dpt, "", den, ""]
    out += ["## Destaques (Featured)", ""]
    for f in d.get("featured") or []:
        out.append(f"- **{f.get('title', '')}**: {f.get('url', '')} ({f.get('why', '')})")
    out += ["", "## Competências (as 3 primeiras ficam fixadas)", "",
            ", ".join(d.get("skills") or []), "",
            "## Serviços", "", ", ".join(d.get("services") or []), "",
            "## URL personalizada", "", f"linkedin.com/in/{d.get('custom_url', '')}", "",
            "## Capa (para a área de design do Gab: /ogab design)", "", d.get("banner_brief", ""), "",
            "## Foto", "", d.get("photo_tips", ""), "",
            "## Aberto a", "", d.get("open_to", ""), ""]
    if d.get("missing"):
        out += ["## Falta você mandar", ""] + [f"- {m}" for m in d["missing"]] + [""]
    return "\n".join(out)


async def build_posts(brain, count: int = 5) -> Path:
    items = portfolio.load_items()
    if not items:
        raise ValueError("nenhum trabalho no portfólio do onboarding (data/onboarding.json)")
    prompt = f"""Write {min(count, len(items))} LinkedIn posts, one per portfolio piece
below (best pieces first), for an audiovisual professional. Each post tells
the story of the job: the client's problem, what was filmed or edited, the
result. Hook in the first line, short paragraphs, 120-220 words, at most 3
hashtags, ends with a soft question or call to action. Portuguese (pt) and
English (en) versions.

{RULES}

Material about the person:
{_material()[:15000]}

Portfolio pieces:
{portfolio.describe(items)}

Return JSON: {{"posts": [{{"piece": "", "url": "", "pt": "", "en": "",
"media": "what to attach (video, frames, before/after)", "best_time": ""}}]}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="posts")
    posts = _clean((data or {}).get("posts") if isinstance(data, dict) else None) or []
    if not posts:
        raise RuntimeError("o cérebro não devolveu os posts; tente de novo")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = ["# Posts dos trabalhos (rascunhos para aprovar)", "",
           "Nada é publicado sozinho. Aprove, ajuste e publique da sua conta "
           "(ou agende numa ferramenta oficial conectada).", ""]
    for n, p in enumerate(posts, 1):
        out += [f"## {n}. {p.get('piece', '')}", "", f"Link: {p.get('url', '')}",
                f"Mídia: {p.get('media', '')}  |  Melhor horário: {p.get('best_time', '')}", "",
                "### PT", "", p.get("pt", ""), "", "### EN", "", p.get("en", ""), ""]
    path = OUT_DIR / "posts.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


async def approve_pending(state) -> int:
    """Approve every LinkedIn draft waiting for review (the user saw the list)."""
    n = 0
    for item in await state.get_channel_items("linkedin", "pending_review", limit=1000):
        await state.update_channel_item(item["id"], status="approved")
        n += 1
    return n


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _days_since(stamp: str) -> float:
    try:
        return (_now() - datetime.fromisoformat(stamp)).total_seconds() / 86400
    except (TypeError, ValueError):
        return 0.0


def warm_ok(item: dict, cfg) -> bool:
    """The invite waits `warmup_days` after the user commented on a post.
    'skip:' means the lead has no recent post: invite right away."""
    if not cfg.warmup:
        return True
    w = item.get("warmed_at") or ""
    return w.startswith("skip:") or (bool(w) and _days_since(w) >= cfg.warmup_days)


async def counts(state) -> dict:
    """Invites today / this week and messages today, from the queue itself."""
    week = (_now() - timedelta(days=7)).isoformat()
    today = _now().date().isoformat()
    inv_week = inv_today = msg_today = 0
    for it in await state.get_channel_items("linkedin", limit=5000):
        sent = it.get("sent_at") or ""
        if isinstance(sent, datetime):
            sent = sent.isoformat()
        if it["status"] == "sent" and it.get("note"):
            inv_week += sent >= week
            inv_today += sent[:10] == today
        msg = it.get("msg_sent_at") or ""
        if msg[:10] == today or (it["status"] == "sent" and not it.get("note") and sent[:10] == today):
            msg_today += 1
    return {"invites_week": inv_week, "invites_today": inv_today, "messages_today": msg_today}


async def stale_invites(state, cfg) -> list[dict]:
    """Invites pending longer than `withdraw_after_days`: withdraw them
    (too many pending invites is one of the things LinkedIn punishes)."""
    return [it for it in await state.get_channel_items("linkedin", "sent", limit=5000)
            if it.get("note") and not it.get("accepted_at") and not it.get("withdrawn_at")
            and _days_since(str(it.get("sent_at") or "")) >= cfg.withdraw_after_days]


def _walk_one(item, text, copy_text, ask, out) -> str:
    out(f"  {item.get('contact_name') or ''} | {item.get('company_name') or ''}"
        + (f"  (momento: {item['trigger']})" if item.get("trigger") else ""))
    out(f"  {item['target']}\n")
    out("    " + text.replace("\n", "\n    ") + "\n")
    copy_to_clipboard(copy_text)
    if item["target"].startswith("http"):
        webbrowser.open(item["target"])
    return (ask("  Texto copiado e perfil aberto. Enviou? (Enter = sim, p = pular, s = sair) ") or "").strip().lower()


async def queue(state, config, ask=input, out=print) -> int:
    """Walk the LinkedIn queue: invites (after warm-up, under the daily and
    weekly caps), then the messages of accepted invites. Copy, open, the
    user sends, Mariana marks it."""
    cfg = config.channels.linkedin
    c = await counts(state)
    stale = await stale_invites(state, cfg)
    if stale:
        out(f"  {len(stale)} convite(s) pendente(s) há mais de {cfg.withdraw_after_days} dias. "
            "Retire com: mariana linkedin retirar\n")
    inv_left = max(0, min(cfg.max_daily_connections - c["invites_today"],
                          cfg.max_weekly_connections - c["invites_week"]))
    msg_left = max(0, cfg.max_daily_messages - c["messages_today"])
    approved = await state.get_channel_items("linkedin", "approved", limit=1000)
    approved.sort(key=lambda it: not it.get("trigger"))
    invites = [it for it in approved if it.get("note")]
    ready = [it for it in invites if warm_ok(it, cfg)]
    waiting = len(invites) - len(ready)
    direct = [it for it in approved if not it.get("note")]
    after_accept = [it for it in await state.get_channel_items("linkedin", "sent", limit=5000)
                    if it.get("note") and it.get("accepted_at") and not it.get("msg_sent_at")]
    out(f"  Convites: {len(ready)} prontos, {inv_left} cabem hoje "
        f"({c['invites_week']}/{cfg.max_weekly_connections} na semana)."
        + (f" {waiting} esperando o aquecimento (mariana linkedin aquecer)." if waiting else ""))
    out(f"  Mensagens: {len(after_accept) + len(direct)} prontas, {msg_left} cabem hoje.\n")
    done = 0
    for item in ready[:inv_left]:
        answer = _walk_one(item, f"[convite] {item['note']}", item["note"], ask, out)
        if answer == "s":
            return done
        if answer != "p":
            await state.update_channel_item(item["id"], status="sent", sent_at=_now().isoformat())
            done += 1
    for item in (after_accept + direct)[:msg_left]:
        answer = _walk_one(item, item["body"], item["body"], ask, out)
        if answer == "s":
            break
        if answer == "p":
            continue
        now = _now().isoformat()
        if item.get("note"):
            await state.update_channel_item(item["id"], msg_sent_at=now)
        else:
            await state.update_channel_item(item["id"], status="sent", sent_at=now, msg_sent_at=now)
        done += 1
    return done
