"""LinkedIn growth: warm-up, the right moment, the "oi" video, posts calendar
and the profile score. Nothing here clicks or logs into LinkedIn.

  aquecer     before the invite, the user comments on a recent post of the lead.
              Mariana opens the lead's activity page, the user pastes the post,
              she writes two comment options; the invite waits `warmup_days`.
  aceitou     the user marks who accepted; the message goes after that.
  retirar     pending invites older than `withdraw_after_days`, to withdraw.
  momento     open video/social media roles, announced events and new
              marketing roles (Serper search), saved as signals; the lead goes
              first and the message opens with the reason.
  video       a 20 s personal "oi" for accepted invites: Gab (/ogab) puts the
              lead's site or Instagram on screen with the user saying their
              name. `video-pronto` turns the follow-up message into one with
              the link.
  calendario  3 posts a week (bastidor, case, antes e depois). A free edit only
              becomes a post with the client's permission.
  nota        0 to 100 for the current profile and for Mariana's proposal,
              with the history, so the user sees before and after.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

import httpx

from harvey import market, portfolio
from harvey.agents.channels import TRIGGER_TAG
from harvey.dossie import copy_to_clipboard
from harvey.linkedin_kit import OUT_DIR, RULES, _clean, _material, _now
from harvey.paths import PROJECT_ROOT

SERPER_URL = "https://google.serper.dev/search"
VIDEO_DIR = PROJECT_ROOT / "data" / "videos-oi"
SCORES_FILE = OUT_DIR / "notas.json"
PERMISSIONS_KEY = "remake_permissions"


def _no_dash(text: str) -> str:
    return (text or "").replace("—", ",").replace("–", ",").strip().strip('"')


def activity_url(profile_url: str) -> str:
    """A person's recent posts, or a company's posts page."""
    url = (profile_url or "").rstrip("/")
    if "/company/" in url:
        return url + "/posts/"
    if "/in/" in url:
        return url + "/recent-activity/all/"
    return url


# ── 1. warm-up ──

async def comment_options(brain, post: str, item: dict) -> list[str]:
    lang = market.name_for_code(item.get("language") or "pt-BR")
    prompt = f"""An audiovisual professional wants to leave a genuine comment on this
LinkedIn post by {item.get('contact_name')} ({item.get('company_name')}), before
sending a connection invite. Write 2 different comments in {lang}, 15 to 40
words each: react to something specific in the post, add one real thought or
question from a filmmaker's point of view. Never sell, never mention services,
no links, no emojis, no hashtags, no em dashes, no flattery like "great post".

Post:
{post[:4000]}

Return JSON: {{"comments": ["", ""]}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="warmup")
    return [_no_dash(c) for c in ((data or {}).get("comments") or []) if c][:2] \
        if isinstance(data, dict) else []


async def warmup(state, brain, config, ask=input, out=print, limit: int = 10) -> int:
    items = [it for it in await state.get_channel_items("linkedin", limit=2000)
             if it["status"] in ("pending_review", "approved") and it.get("note")
             and not it.get("warmed_at")]
    items.sort(key=lambda it: not it.get("trigger"))
    if not items:
        out("  Nenhum convite esperando aquecimento.")
        return 0
    import webbrowser
    done = 0
    for item in items[:limit]:
        out(f"\n  {item.get('contact_name')} | {item.get('company_name')}")
        url = activity_url(item["target"])
        if url.startswith("http"):
            webbrowser.open(url)
        post = (ask("  Abri os posts. Cole o texto do post que quer comentar "
                    "(Enter vazio = não tem post recente, s = sair): ") or "").strip()
        if post.lower() == "s":
            break
        if not post:
            await state.update_channel_item(item["id"], warmed_at=f"skip:{_now().isoformat()}")
            out("  Sem post recente: o convite já pode sair.")
            continue
        options = await comment_options(brain, post, item)
        if not options:
            out("  Não consegui escrever o comentário agora; fica para a próxima.")
            continue
        for n, c in enumerate(options, 1):
            out(f"    {n}. {c}")
        pick = (ask("  Qual copio? (1/2, p = pular) ") or "1").strip()
        if pick == "p":
            continue
        copy_to_clipboard(options[1] if pick == "2" and len(options) > 1 else options[0])
        if (ask("  Copiado. Comentou? (Enter = sim) ") or "").strip().lower() in ("", "s", "sim", "y"):
            await state.update_channel_item(item["id"], warmed_at=_now().isoformat())
            done += 1
    return done


# ── 7. account care ──

async def mark_accepted(state, ask=input, out=print) -> int:
    pending = [it for it in await state.get_channel_items("linkedin", "sent", limit=5000)
               if it.get("note") and not it.get("accepted_at") and not it.get("withdrawn_at")]
    if not pending:
        out("  Nenhum convite pendente.")
        return 0
    out("  Convites pendentes (veja em linkedin.com/mynetwork/invitation-manager/sent/):")
    for n, it in enumerate(pending, 1):
        out(f"    {n}. {it.get('contact_name')} | {it.get('company_name')}")
    picked = ask("  Quem aceitou? Números separados por vírgula: ") or ""
    n = 0
    for part in re.split(r"[,\s]+", picked.strip()):
        if part.isdigit() and 1 <= int(part) <= len(pending):
            await state.update_channel_item(pending[int(part) - 1]["id"], accepted_at=_now().isoformat())
            n += 1
    return n


async def withdraw(state, config, ask=input, out=print) -> int:
    from harvey.linkedin_kit import stale_invites
    stale = await stale_invites(state, config.channels.linkedin)
    if not stale:
        out("  Nenhum convite velho para retirar.")
        return 0
    import webbrowser
    webbrowser.open("https://www.linkedin.com/mynetwork/invitation-manager/sent/")
    out("  Abri os convites enviados. Retire estes (botão Retirar):")
    for it in stale:
        out(f"    - {it.get('contact_name')} | {it.get('company_name')}")
    if (ask("  Retirou todos? (Enter = sim) ") or "").strip().lower() in ("", "s", "sim", "y"):
        for it in stale:
            await state.update_channel_item(it["id"], withdrawn_at=_now().isoformat())
        return len(stale)
    return 0


# ── 3. the right moment ──

def moment_queries(company: str, person: str) -> list[tuple[str, str]]:
    year = date.today().year
    q = [("hiring", f'"{company}" (videomaker OR "editor de vídeo" OR "video editor" OR '
                    f'"social media" OR "content creator") (vaga OR job OR hiring OR contratando)'),
         ("event", f'"{company}" (evento OR conferência OR congresso OR conference OR event '
                   f'OR lançamento OR launch) {year}')]
    if person.strip():
        q.append(("new_role", f'"{person}" "{company}" ("novo cargo" OR "new position" OR '
                              f'"começando um novo" OR "started a new position" OR "joined")'))
    return q


SIGNAL_OF = {"hiring": "HIRING_ROLE", "event": "EVENT_ANNOUNCED", "new_role": "NEW_ROLE"}


async def classify_moments(brain, company: str, person: str, results: list[dict]) -> list[dict]:
    if not results:
        return []
    today = date.today().isoformat()
    lines = "\n".join(f"- [{r.get('kind')}] {r.get('title', '')} | {r.get('snippet', '')} | "
                      f"{r.get('date', '')} | {r.get('link', '')}" for r in results[:24])
    prompt = f"""Today is {today}. From these search results, keep ONLY clear, recent
facts about the company "{company}" (contact: {person or "unknown"}) that make
this a good moment to offer video production:
- hiring: an OPEN role for video, social media or content at THIS company (last 60 days)
- event: an event THIS company organizes in the next 4 months
- new_role: THIS contact started a marketing/communications role in the last 90 days
Ignore other companies with similar names, old news and guesses.

{lines}

Return JSON: {{"moments": [{{"type": "hiring|event|new_role",
"summary": "one short line in Portuguese", "url": ""}}]}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="moment")
    moments = (data or {}).get("moments") if isinstance(data, dict) else None
    return [m for m in moments or [] if m.get("type") in SIGNAL_OF and m.get("summary")]


async def find_moments(state, brain, config, env, max_leads: int = 20, estimate: bool = False,
                       out=print) -> int:
    leads = []
    for status in ("queued", "contacted", "new"):
        leads += await state.get_prospects_by_status(status)
    leads.sort(key=lambda p: -(p.score or 0))
    leads = leads[:max_leads]
    searches = sum(len(moment_queries(p.company or "x", p.full_name())) for p in leads)
    if estimate:
        out(f"  {len(leads)} lead(s), {searches} busca(s) no Serper (2.500 grátis por conta).")
        return 0
    if not env.serper_api_key:
        raise RuntimeError("SERPER_API_KEY não está no .env (serper.dev, 2.500 buscas grátis).")
    from harvey.agents.channels import ChannelsAgent
    from harvey.signals import seed_signal_catalog
    await seed_signal_catalog(state)
    writer = ChannelsAgent(brain, state, config)
    found = 0
    async with httpx.AsyncClient(timeout=20) as client:
        for p in leads:
            company = p.company
            if not company:
                continue
            results = []
            for kind, q in moment_queries(company, p.full_name()):
                try:
                    r = await client.post(SERPER_URL, headers={"X-API-KEY": env.serper_api_key},
                                          json={"q": q, "num": 8, "tbs": "qdr:m3"})
                    r.raise_for_status()
                    results += [dict(x, kind=kind) for x in r.json().get("organic") or []]
                except httpx.HTTPError as e:
                    out(f"  ✗ busca falhou para {company}: {e}")
            moments = await classify_moments(brain, company, p.full_name(), results)
            if not moments:
                continue
            for m in moments:
                await state.add_observation(SIGNAL_OF[m["type"]], company_id=p.company_id,
                                            prospect_id=p.id, collector="momento",
                                            value_text=_no_dash(m["summary"])[:300],
                                            evidence_url=m.get("url", ""))
            line = f"{TRIGGER_TAG} " + "; ".join(_no_dash(m["summary"]) for m in moments)
            base = "\n".join(l for l in (p.personalization_notes or "").splitlines()
                             if not l.startswith(TRIGGER_TAG)).strip()
            p.personalization_notes = f"{base}\n{line}".strip()
            await state.update_prospect_notes(p.id, p.personalization_notes[:1500])
            # Drafts still waiting for review are rewritten with the reason.
            for it in await state.get_channel_items(status="pending_review", limit=2000):
                if it["prospect_id"] != p.id or it["kind"] != "first":
                    continue
                mk = await market.for_prospect(state, p, getattr(config.persona, "language", "pt-BR"))
                draft = await writer.write(it["channel"], p, it.get("company_name") or company, mk)
                fields = {"trigger": line[len(TRIGGER_TAG):].strip()}
                if draft and draft.get("body"):
                    fields.update(body=draft["body"], note=draft.get("note") or it.get("note", ""),
                                  opener=draft.get("opener", ""))
                await state.update_channel_item(it["id"], **fields)
            found += 1
            out(f"  ✓ {company}: {line[len(TRIGGER_TAG):].strip()}")
    return found


# ── 2. the "oi" video ──

async def video_briefs(state, brain, config, prospect_ids: list[str] | None = None) -> tuple[Path, list[dict]]:
    items = [it for it in await state.get_channel_items("linkedin", "sent", limit=5000)
             if it.get("accepted_at") and not it.get("msg_sent_at")]
    if prospect_ids:
        items = [it for it in items if it["prospect_id"] in prospect_ids]
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    path = VIDEO_DIR / f"{date.today().isoformat()}.md"
    out = [f"# Vídeos de oi ({date.today().strftime('%d/%m/%Y')})", "",
           "Para o Gab (/ogab): 20 s, 9:16 ou 1:1. Tela: o site ou o Instagram do lead rolando "
           "devagar. No canto, um círculo com você falando o roteiro olhando para a câmera "
           "(grave no celular, luz de janela). Legenda, sem música alta. Nunca publicar.", ""]
    done = []
    for it in items:
        p = await state.get_prospect(it["prospect_id"])
        if not p:
            continue
        c = await state.get_company(p.company_id) if p.company_id else None
        links = {}
        if p.company_id:
            for row in await state.get_observations(company_id=p.company_id, latest_only=True):
                if row["signal_code"] in ("INSTAGRAM_PROFILE", "HAS_YOUTUBE_CHANNEL") and row.get("value_text"):
                    links[row["signal_code"]] = row["value_text"]
        site = (c.website or c.domain) if c else ""
        lang = market.name_for_code(it.get("language") or "pt-BR")
        script = _no_dash(await brain.think(
            f"""Write a 20-second spoken script (40 to 50 words) in {lang}, first person,
for an audiovisual professional recording a personal video for
{p.first_name or p.full_name()} at {it.get('company_name')}, who just accepted their
LinkedIn invite. Say the first name in the first sentence, mention one concrete
thing from their site or content (only from the notes), say in one line what you
could do with video for them, end with an easy question. Natural, spoken, no em
dashes, no exclamation marks.

Notes: {p.personalization_notes}

Return ONLY the script.""", agent="linkedin", task="video_script"))
        block = [f"## {it.get('company_name')}: {p.full_name()}", "",
                 f"- **Na tela:** {site or 'site não encontrado'}"
                 + "".join(f" | {v}" for v in links.values()),
                 f"- **Roteiro:** {script}",
                 f"- **Quando pronto:** `mariana linkedin video-pronto --prospect {p.id} --link <link>`", ""]
        out += block
        done.append({"prospect": p, "item": it, "folder": _video_folder(config, it.get("company_name") or p.company, block)})
    if not done:
        out.append("Ninguém aceitou o convite ainda. Marque quem aceitou com `mariana linkedin aceitou`.")
    path.write_text("\n".join(out), encoding="utf-8")
    return path, done


def _video_folder(config, name: str, block: list[str]) -> str:
    from harvey.production import clients_dir, ensure_brand_memory, folder_name
    try:
        folder = clients_dir(config) / f"{folder_name(name)} (oi)"
        ensure_brand_memory(folder, "Lead da Mariana: vídeo de oi personalizado de 20 s para o LinkedIn. "
                                    "Só para o próprio lead, nunca publicar.")
        (folder / "briefing-oi.md").write_text("\n".join([f"# Vídeo de oi: {name}", ""] + block),
                                               encoding="utf-8")
        return str(folder)
    except OSError:
        return ""


async def video_ready(state, brain, prospect_id: str, link: str) -> str:
    items = [it for it in await state.get_channel_items("linkedin", limit=5000)
             if it["prospect_id"] == prospect_id and it.get("note")]
    if not items:
        raise ValueError("esse lead não tem convite do LinkedIn na fila")
    it = items[-1]
    lang = market.name_for_code(it.get("language") or "pt-BR")
    body = _no_dash(await brain.think(
        f"""Write a short LinkedIn message in {lang}, first person, from an audiovisual
professional to {it.get('contact_name')} ({it.get('company_name')}) who just accepted
the invite: thank them for connecting and say you recorded a quick personal video
for them. Under 45 words, warm, one easy question at the end, no em dashes, no
exclamation marks, no signature. Include this link exactly once: {link}

Return ONLY the message.""", agent="linkedin", task="video_message"))
    if link not in body:
        body = f"{body}\n\n{link}"
    await state.update_channel_item(it["id"], body=body)
    return it["id"]


# ── 5. posts calendar ──

async def remake_permissions(state) -> list[dict]:
    try:
        return json.loads((await state.get_setting(PERMISSIONS_KEY)) or "[]")
    except ValueError:
        return []


async def grant_permission(state, prospect_id: str, link: str, note: str = "") -> int:
    perms = [p for p in await remake_permissions(state) if p.get("prospect_id") != prospect_id]
    prospect = await state.get_prospect(prospect_id)
    perms.append({"prospect_id": prospect_id, "link": link, "note": note,
                  "company": prospect.company if prospect else "",
                  "date": date.today().isoformat()})
    await state.set_setting(PERMISSIONS_KEY, json.dumps(perms, ensure_ascii=False))
    return len(perms)


KINDS = ("bastidor", "case", "antes_depois")


def schedule(weeks: int, start: date | None = None) -> list[tuple[date, str]]:
    """Monday, Wednesday and Friday, rotating the three kinds."""
    start = start or date.today()
    monday = start + timedelta(days=(7 - start.weekday()) % 7 or 7)
    slots = []
    for w in range(weeks):
        for n, offset in enumerate((0, 2, 4)):
            slots.append((monday + timedelta(days=7 * w + offset), KINDS[(w + n) % 3]))
    return slots


async def build_calendar(state, brain, weeks: int = 4) -> Path:
    items = portfolio.load_items()
    perms = await remake_permissions(state)
    slots = schedule(weeks)
    plan = "\n".join(f"- {d.isoformat()} ({d.strftime('%a')}): {k}" for d, k in slots)
    prompt = f"""Plan LinkedIn posts for an audiovisual professional, one per slot below.
Kinds: bastidor (behind the scenes of a shoot or edit), case (a client project:
problem, what was done, result), antes_depois (before and after of an edit).
For antes_depois use ONLY the free edits the client allowed to publish; if
there are none left, use the professional's own raw vs final footage from a
portfolio piece, never a client video without permission. Do not repeat a
piece twice in a row. Portuguese, 100-200 words each, hook in the first line,
at most 3 hashtags.

{RULES}

Slots:
{plan}

Material:
{_material()[:12000]}

Portfolio pieces:
{portfolio.describe(items) or "(none)"}

Free edits the client allowed to post:
{json.dumps(perms, ensure_ascii=False) if perms else "(none)"}

Return JSON: {{"posts": [{{"date": "", "kind": "", "piece": "", "text": "",
"media": "what to film or attach"}}]}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="calendar")
    posts = _clean((data or {}).get("posts") if isinstance(data, dict) else None) or []
    if not posts:
        raise RuntimeError("o cérebro não devolveu o calendário; tente de novo")
    labels = {"bastidor": "Bastidor", "case": "Case", "antes_depois": "Antes e depois"}
    out = [f"# Calendário do LinkedIn ({weeks} semanas)", "",
           "Segunda, quarta e sexta. Nada é publicado sozinho: aprove e publique da sua conta.",
           "Antes e depois de cliente só com a permissão dele (`mariana linkedin permissao`).", ""]
    for p in posts:
        out += [f"## {p.get('date', '')}: {labels.get(p.get('kind'), p.get('kind', ''))}",
                f"_{p.get('piece', '')}_  |  Mídia: {p.get('media', '')}", "", p.get("text", ""), ""]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "calendario.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


# ── 6. profile score ──

SERVICE_WORDS = ("filmmaker", "video", "vídeo", "videomaker", "editor", "edição", "editing",
                 "produtora", "production", "cinema", "audiovisual", "reels", "motion")
CTA_WORDS = ("contato", "fale", "chama", "whatsapp", "email", "e-mail", "dm", "contact",
             "reach out", "message me", "agende", "book")


def score(profile: dict, audience: list[str] | None = None) -> dict:
    """Deterministic 0-100, so before and after are comparable."""
    audience = [a.lower() for a in audience or []]
    head = (profile.get("headline") or "").lower()
    about = profile.get("about") or ""
    al = about.lower()
    parts = {
        "foto": 15 if profile.get("has_photo") else 0,
        "capa": 5 if profile.get("has_banner") else 0,
        "titulo": (8 if 60 <= len(head) <= 220 else 4 if head else 0)
                  + (4 if any(w in head for w in SERVICE_WORDS) else 0)
                  + (3 if any(a.split()[0] in head for a in audience if a) else 0),
        "sobre": (8 if len(about) >= 1000 else 4 if len(about) >= 400 else 0)
                 + (4 if any(w in al for w in CTA_WORDS) else 0)
                 + (4 if sum(w in al for w in SERVICE_WORDS) >= 3 else 0)
                 + (4 if re.search(r"\d", about) else 0),
        "destaques": round(min(int(profile.get("featured_count") or 0), 3) * 10 / 3),
        "experiencia": min(sum(1 for e in profile.get("experience") or [] if e.get("has_description")), 2) * 5,
        "competencias": min(int(profile.get("skills_count") or 0), 10),
        "url": 5 if profile.get("custom_url") and not re.search(r"-[0-9a-f]{6,}/?$",
                                                                  profile["custom_url"]) else 0,
        "servicos": 5 if profile.get("services") else 0,
        "recomendacoes": 5 if int(profile.get("recommendations_count") or 0) >= 3
                         else 3 if int(profile.get("recommendations_count") or 0) >= 1 else 0,
    }
    return {"total": sum(parts.values()), "parts": parts}


MAX_PARTS = {"foto": 15, "capa": 5, "titulo": 15, "sobre": 20, "destaques": 10, "experiencia": 10,
             "competencias": 10, "url": 5, "servicos": 5, "recomendacoes": 5}
FIXES = {"foto": "foto de perfil (mariana fotos)", "capa": "capa pela área de design (/ogab design)",
         "titulo": "título com o serviço e o tipo de cliente", "sobre": "Sobre com 1000+ caracteres, números e chamada para contato",
         "destaques": "3 trabalhos em Destaques", "experiencia": "descrição nas experiências",
         "competencias": "10+ competências", "url": "URL personalizada", "servicos": "seção Serviços",
         "recomendacoes": "3 recomendações (o pós-job já pede)"}


async def extract_profile(brain, page_text: str) -> dict:
    prompt = f"""This is the text of a LinkedIn profile page. Extract the fields.
Return JSON: {{"headline": "", "about": "", "has_photo": true, "has_banner": true,
"featured_count": 0, "experience": [{{"title": "", "has_description": true}}],
"skills_count": 0, "custom_url": "", "services": [""], "recommendations_count": 0}}
When the text gives no sign of a photo or banner (e.g. a default avatar), use false.

{page_text[:30000]}"""
    data = await brain.think_json(prompt, agent="linkedin", task="profile_extract")
    return data if isinstance(data, dict) else {}


def profile_from_proposal(d: dict, has_photo: bool) -> dict:
    h = (d.get("headlines") or [{}])[0]
    about = d.get("about") or {}
    return {"headline": h.get("pt", ""), "about": about.get("pt", "") if isinstance(about, dict) else about,
            "has_photo": has_photo, "has_banner": bool(d.get("banner_brief")),
            "featured_count": len(d.get("featured") or []),
            "experience": [{"has_description": True} for _ in d.get("experience") or []],
            "skills_count": len(d.get("skills") or []), "custom_url": d.get("custom_url", ""),
            "services": d.get("services") or [], "recommendations_count": 0}


def save_score(source: str, result: dict) -> list[dict]:
    try:
        history = json.loads(SCORES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        history = []
    history.append({"date": date.today().isoformat(), "source": source, **result})
    SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCORES_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return history


def report(history: list[dict]) -> str:
    last = history[-1]
    lines = [f"  Nota do perfil ({last['source']}): {last['total']}/100"]
    if len(history) > 1:
        first = history[0]
        diff = last["total"] - first["total"]
        lines.append(f"  Antes: {first['total']} ({first['date']}) → agora: {last['total']} "
                     f"({'+' if diff >= 0 else ''}{diff})")
    gaps = sorted(((MAX_PARTS[k] - v, k) for k, v in last["parts"].items() if v < MAX_PARTS[k]),
                  reverse=True)
    if gaps:
        lines.append("  Para subir:")
        lines += [f"    - {FIXES[k]} (+{g})" for g, k in gaps[:5]]
    return "\n".join(lines)
