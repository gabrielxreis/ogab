"""Instagram kit: the user's own Instagram, the same process as the LinkedIn kit.

Nothing here logs into Instagram or posts for the user. The Gab reads the
profile the user already has open (Claude in Chrome, logged in), writes, and
the user pastes, changes the photo and posts from their account:

  perfil      data/instagram/perfil.md   diagnosis of the current profile
                                         (when perfil-atual.txt exists) and
                                         every field ready to paste: name with
                                         the searched keyword, @, category,
                                         bio options, link in bio page,
                                         contact buttons, highlights with the
                                         cover brief, pinned posts, photo
  nota        0 to 100 for the current profile and for the proposal, with the
              history, so the user sees before and after
  posts       data/instagram/posts.md    one post per portfolio piece (Reels or
                                         carousel): hook, cover, beats for the
                                         edit, caption, hashtags. Also the queue
                                         (fila.json)
  calendario  data/instagram/calendario.md  3 posts a week (case, bastidor,
              antes e depois), a free edit only with the client's permission
  fila        the approved posts, one at a time: copy the caption, open
              Instagram, the user posts, the Gab marks it
"""

from __future__ import annotations

import json
import re
import webbrowser
from datetime import date, timedelta
from pathlib import Path

from harvey import portfolio
from harvey.dossie import SOBRE_FILE, copy_to_clipboard
from harvey.linkedin_kit import RULES, _clean
from harvey.onboard import KNOWLEDGE_FILE
from harvey.paths import PROJECT_ROOT

OUT_DIR = PROJECT_ROOT / "data" / "instagram"
CURRENT_FILE = OUT_DIR / "perfil-atual.txt"
SCORES_FILE = OUT_DIR / "notas.json"
QUEUE_FILE = OUT_DIR / "fila.json"
INSTAGRAM_URL = "https://www.instagram.com/"

IG_RULES = """Instagram rules (2026):
- Name field (max 64 chars) is searchable: person or studio name + the service
  and the client type ("Ana Lima | Filmmaker de Igrejas"). The @ stays short.
- Bio max 150 chars, 3 to 4 short lines: what you do and for whom, one proof
  (a number, a client type, a city), what makes you different, a call to
  action pointing to the link or the DM. No emoji walls, at most 2 emojis.
- Link in bio: one page with 3 to 5 buttons in order of what closes jobs
  (WhatsApp or booking, showreel, portfolio by segment, proposal form).
- Highlights: 4 to 7, names up to 15 chars, each one answers a client
  question (Trabalhos, Igrejas, Eventos, Bastidores, Depoimentos, Como funciona,
  Orçamento). Covers follow one visual line.
- Pinned posts (3): the strongest case, the best before and after or showreel,
  and a post that explains how to hire. Reels first.
- Profile photo: face centered, shoulders up, plain background, reads well
  as a small circle (320x320). Same photo family as LinkedIn.
- Posts: hook on screen in the first second, text on the cover up to 8 words,
  caption with the story of the job (problem, what was done, result), at most
  5 specific hashtags, ends with a question or a call to action."""


def _material() -> str:
    parts = []
    for f in (KNOWLEDGE_FILE, SOBRE_FILE):
        if f.exists():
            parts.append(f.read_text(encoding="utf-8")[:30000])
    return "\n\n".join(parts)


async def build_profile(brain, current: str = "") -> Path:
    material = _material()
    if not material:
        raise ValueError("sem material: rode o onboarding ou 'mariana dossie' antes")
    if not current and CURRENT_FILE.exists():
        current = CURRENT_FILE.read_text(encoding="utf-8", errors="replace")
    items = portfolio.load_items()
    prompt = f"""You are an Instagram profile strategist for audiovisual professionals
(filmmakers, video editors, producers). Diagnose the current profile (when
given) and build the complete profile, optimized to be found by and convince
the clients in their dossier. Portuguese (pt) and English (en).

{RULES}

{IG_RULES}

Material about the person:
{material}

Portfolio pieces:
{portfolio.describe(items) or "(none listed)"}

Current Instagram profile (text of the page, may be empty):
{current[:15000] or "(not given)"}

Return JSON:
{{
  "diagnosis": [{{"item": "", "status": "ok|ajustar|falta", "now": "", "fix": ""}}],  // empty when no current profile
  "usernames": [{{"handle": "", "why": ""}}],               // 2-3 options, keep the current one first if it works
  "names": [{{"pt": "", "en": "", "why": ""}}],             // 3 options, max 64 chars, with the keyword clients search
  "category": "",                                           // professional account category to pick
  "bios": [{{"pt": "", "en": "", "why": ""}}],              // 3 options, max 150 chars each
  "link_in_bio": {{"title": "", "buttons": [{{"label": "", "url": "", "why": ""}}]}},
  "contact_buttons": [""],                                  // WhatsApp, email, booking...
  "highlights": [{{"name": "", "content": [""], "cover_brief": ""}}],   // 4-7, strongest first
  "pinned": [{{"piece": "", "url": "", "format": "reels|carrossel|foto", "cover_text": "", "why": ""}}],  // 3
  "photo_tips": "",
  "grid": "",                                               // visual line of covers and colors for the feed
  "missing": [""]                                           // what the person still needs to send
}}"""
    data = await brain.think_json(prompt, agent="instagram", task="profile")
    if not isinstance(data, dict):
        raise RuntimeError("o cérebro não devolveu o perfil; tente de novo")
    data = _clean(data)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "perfil.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    path = OUT_DIR / "perfil.md"
    path.write_text(render_profile(data), encoding="utf-8")
    return path


def render_profile(d: dict) -> str:
    out = ["# Perfil do Instagram (pronto para colar)", "",
           "Cada bloco vai num campo do perfil. Troque o que estiver em [FALTA: ...] antes de colar.",
           "Ordem sugerida: foto, nome, @, categoria, bio, link, botões de contato, destaques, posts fixados.", ""]
    if d.get("diagnosis"):
        marks = {"ok": "ok", "ajustar": "ajustar", "falta": "falta"}
        out += ["## Diagnóstico do perfil de hoje", ""]
        for g in d["diagnosis"]:
            out.append(f"- **{g.get('item', '')}** ({marks.get(g.get('status'), g.get('status', ''))}): "
                       f"{g.get('now', '')} > {g.get('fix', '')}")
        out.append("")
    out += ["## Nome (campo pesquisável): escolha um", ""]
    for n, h in enumerate(d.get("names") or [], 1):
        out += [f"**Opção {n}** ({h.get('why', '')})", "", f"PT: {h.get('pt', '')}", "",
                f"EN: {h.get('en', '')}", ""]
    out += ["## @ (nome de usuário)", ""]
    out += [f"- @{u.get('handle', '').lstrip('@')} ({u.get('why', '')})" for u in d.get("usernames") or []]
    out += ["", "## Categoria (conta profissional)", "", d.get("category", ""), "",
            "## Bio (até 150 caracteres): escolha uma", ""]
    for n, b in enumerate(d.get("bios") or [], 1):
        pt, en = b.get("pt", ""), b.get("en", "")
        out += [f"**Opção {n}** ({b.get('why', '')}, {len(pt)} caracteres)", "", "PT:", "", pt, "",
                "EN:", "", en, ""]
    link = d.get("link_in_bio") or {}
    out += ["## Link na bio", "", f"Página: {link.get('title', '')}", ""]
    out += [f"{n}. **{b.get('label', '')}**: {b.get('url', '')} ({b.get('why', '')})"
            for n, b in enumerate(link.get("buttons") or [], 1)]
    out += ["", "## Botões de contato", "", ", ".join(d.get("contact_buttons") or []), "",
            "## Destaques (capas pela área de design do Gab: /ogab design)", ""]
    for h in d.get("highlights") or []:
        out += [f"### {h.get('name', '')}", "", "Dentro: " + "; ".join(h.get("content") or []), "",
                f"Capa: {h.get('cover_brief', '')}", ""]
    out += ["## Posts fixados (3)", ""]
    for n, p in enumerate(d.get("pinned") or [], 1):
        out.append(f"{n}. **{p.get('piece', '')}** ({p.get('format', '')}): capa \"{p.get('cover_text', '')}\". "
                   f"{p.get('why', '')} {p.get('url', '')}".rstrip())
    out += ["", "## Foto de perfil", "", d.get("photo_tips", ""), "",
            "## Linha visual do feed", "", d.get("grid", ""), ""]
    if d.get("missing"):
        out += ["## Falta você mandar", ""] + [f"- {m}" for m in d["missing"]] + [""]
    return "\n".join(out)


# ── posts of the work and the queue ──

async def build_posts(brain, count: int = 9) -> Path:
    items = portfolio.load_items()
    if not items:
        raise ValueError("nenhum trabalho no portfólio do onboarding (data/onboarding.json)")
    prompt = f"""Plan {min(count, len(items))} Instagram posts, one per portfolio piece below
(best pieces first), for an audiovisual professional. Prefer Reels (a 15 to 30 s
cut of the job); use a carousel when the story is better in frames (before and
after, behind the scenes). Each post tells the story of the job: the client's
problem, what was filmed or edited, the result. Portuguese caption (pt) and
English caption (en).

{RULES}

{IG_RULES}

Material about the person:
{_material()[:15000]}

Portfolio pieces:
{portfolio.describe(items)}

Return JSON: {{"posts": [{{"piece": "", "url": "", "format": "reels|carrossel",
"hook": "", "cover_text": "", "beats": [""], "pt": "", "en": "",
"hashtags": [""], "cta": "", "best_time": ""}}]}}
beats = the cuts of the Reel or the slides of the carousel, in order."""
    data = await brain.think_json(prompt, agent="instagram", task="posts")
    posts = _clean((data or {}).get("posts") if isinstance(data, dict) else None) or []
    if not posts:
        raise RuntimeError("o cérebro não devolveu os posts; tente de novo")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = ["# Posts dos trabalhos no Instagram (rascunhos para aprovar)", "",
           "Nada é publicado sozinho. O Gab edita o Reel ou monta o carrossel, você aprova "
           "e posta da sua conta (`mariana instagram fila`).", ""]
    for n, p in enumerate(posts, 1):
        tags = " ".join("#" + t.lstrip("#") for t in p.get("hashtags") or [])
        out += [f"## {n}. {p.get('piece', '')} ({p.get('format', '')})", "",
                f"Material: {p.get('url', '')}  |  Melhor horário: {p.get('best_time', '')}",
                f"Gancho na tela: {p.get('hook', '')}", f"Capa: {p.get('cover_text', '')}", "",
                "Para o Gab montar:", ""] + [f"{i}. {b}" for i, b in enumerate(p.get("beats") or [], 1)]
        out += ["", "### Legenda PT", "", p.get("pt", ""), "", tags, "",
                "### Caption EN", "", p.get("en", ""), "", tags, ""]
    path = OUT_DIR / "posts.md"
    path.write_text("\n".join(out), encoding="utf-8")
    queue = load_queue()
    known = {q.get("piece") for q in queue}
    for p in posts:
        if p.get("piece") not in known:
            queue.append({**p, "status": "pendente", "posted_at": ""})
    save_queue(queue)
    return path


def load_queue() -> list[dict]:
    try:
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save_queue(queue: list[dict]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


def caption(post: dict, lang: str = "pt") -> str:
    tags = " ".join("#" + t.lstrip("#") for t in post.get("hashtags") or [])
    return f"{post.get(lang) or post.get('pt', '')}\n\n{tags}".strip()


def queue(ask=input, out=print, per_day: int = 1, lang: str = "pt") -> int:
    """Walk the posts queue: copy the caption, open Instagram, the user posts
    from their account and presses Enter; at most `per_day` a day."""
    items = load_queue()
    today = date.today().isoformat()
    left = max(0, per_day - sum(1 for q in items if (q.get("posted_at") or "")[:10] == today))
    pending = [q for q in items if q.get("status") != "publicado"]
    out(f"  Posts na fila: {len(pending)}, {left} cabem hoje.\n")
    done = 0
    for post in pending[:left]:
        out(f"  {post.get('piece', '')} ({post.get('format', '')})  capa: {post.get('cover_text', '')}\n")
        out("    " + caption(post, lang).replace("\n", "\n    ") + "\n")
        copy_to_clipboard(caption(post, lang))
        webbrowser.open(INSTAGRAM_URL)
        answer = (ask("  Legenda copiada e Instagram aberto. Postou? (Enter = sim, p = pular, s = sair) ")
                  or "").strip().lower()
        if answer == "s":
            break
        if answer == "p":
            continue
        post.update(status="publicado", posted_at=today)
        done += 1
    save_queue(items)
    return done


# ── calendar ──

KINDS = ("case", "bastidor", "antes_depois")


def schedule(weeks: int, start: date | None = None) -> list[tuple[date, str]]:
    """Tuesday, Thursday and Saturday, rotating the three kinds."""
    start = start or date.today()
    tuesday = start + timedelta(days=(1 - start.weekday()) % 7 or 7)
    slots = []
    for w in range(weeks):
        for n, offset in enumerate((0, 2, 4)):
            slots.append((tuesday + timedelta(days=7 * w + offset), KINDS[(w + n) % 3]))
    return slots


async def build_calendar(state, brain, weeks: int = 4) -> Path:
    from harvey.linkedin_growth import remake_permissions
    items = portfolio.load_items()
    perms = await remake_permissions(state)
    slots = schedule(weeks)
    plan = "\n".join(f"- {d.isoformat()} ({d.strftime('%a')}): {k}" for d, k in slots)
    prompt = f"""Plan Instagram posts for an audiovisual professional, one per slot below.
Kinds: case (a client project as a Reel: problem, what was done, result),
bastidor (behind the scenes of a shoot or edit, Reel or carousel), antes_depois
(before and after of an edit). For antes_depois use ONLY the free edits the
client allowed to publish; if there are none left, use the professional's own
raw vs final footage, never a client video without permission. Do not repeat a
piece twice in a row. Portuguese caption, 60-150 words, hook on screen in the
first second, at most 5 hashtags. Add one story idea per week to warm the
audience (poll, question box, behind the scenes).

{RULES}

{IG_RULES}

Slots:
{plan}

Material:
{_material()[:12000]}

Portfolio pieces:
{portfolio.describe(items) or "(none)"}

Free edits the client allowed to post:
{json.dumps(perms, ensure_ascii=False) if perms else "(none)"}

Return JSON: {{"posts": [{{"date": "", "kind": "", "format": "reels|carrossel", "piece": "",
"hook": "", "text": "", "media": "what to film or attach"}}], "stories": [{{"week": 1, "idea": ""}}]}}"""
    data = await brain.think_json(prompt, agent="instagram", task="calendar")
    data = _clean(data) if isinstance(data, dict) else {}
    posts = data.get("posts") or []
    if not posts:
        raise RuntimeError("o cérebro não devolveu o calendário; tente de novo")
    labels = {"case": "Case", "bastidor": "Bastidor", "antes_depois": "Antes e depois"}
    out = [f"# Calendário do Instagram ({weeks} semanas)", "",
           "Terça, quinta e sábado. Nada é publicado sozinho: aprove e poste da sua conta.",
           "Antes e depois de cliente só com a permissão dele (`mariana instagram permissao`).", ""]
    for p in posts:
        out += [f"## {p.get('date', '')}: {labels.get(p.get('kind'), p.get('kind', ''))} ({p.get('format', '')})",
                f"_{p.get('piece', '')}_  |  Gancho: {p.get('hook', '')}  |  Mídia: {p.get('media', '')}", "",
                p.get("text", ""), ""]
    if data.get("stories"):
        out += ["## Stories da semana", ""]
        out += [f"- Semana {s.get('week', '')}: {s.get('idea', '')}" for s in data["stories"]]
        out.append("")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "calendario.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


# ── profile score ──

SERVICE_WORDS = ("filmmaker", "video", "vídeo", "videomaker", "editor", "edição", "editing",
                 "produtora", "production", "cinema", "audiovisual", "reels", "motion", "fotografia")
CTA_WORDS = ("link", "whatsapp", "dm", "direct", "orçamento", "agende", "chama", "fale",
             "contato", "book", "contact", "message")
MAX_PARTS = {"foto": 15, "nome": 10, "bio": 25, "link": 10, "destaques": 15, "fixados": 10,
             "categoria": 5, "contato": 5, "frequencia": 5}
FIXES = {"foto": "foto de perfil com o rosto no centro (mariana fotos)",
         "nome": "nome com o serviço e o tipo de cliente (campo pesquisável)",
         "bio": "bio com serviço, público, uma prova com número e chamada para o link",
         "link": "link na bio com WhatsApp, showreel e portfólio",
         "destaques": "5 destaques que respondem o cliente (capas pela área de design)",
         "fixados": "3 posts fixados (case, antes e depois, como contratar)",
         "categoria": "conta profissional com a categoria certa",
         "contato": "botões de contato (WhatsApp ou email)",
         "frequencia": "8 posts por mês (calendário do Instagram)"}


def score(profile: dict, audience: list[str] | None = None) -> dict:
    """Deterministic 0-100, so before and after are comparable."""
    audience = [a.lower() for a in audience or []]
    name = (profile.get("name") or "").lower()
    bio = profile.get("bio") or ""
    bl = bio.lower()
    posts = int(profile.get("posts_last_30") or 0)
    parts = {
        "foto": 15 if profile.get("has_photo") else 0,
        "nome": (6 if any(w in name for w in SERVICE_WORDS) else 0)
                + (4 if any(a.split()[0] in name or a.split()[0] in bl for a in audience if a) else 0),
        "bio": (5 if len(bio) >= 80 else 2 if bio else 0)
               + (5 if any(w in bl for w in SERVICE_WORDS) else 0)
               + (5 if any(a.split()[0] in bl for a in audience if a) else 0)
               + (5 if re.search(r"\d", bio) else 0)
               + (5 if any(w in bl for w in CTA_WORDS) else 0),
        "link": 10 if profile.get("link") else 0,
        "destaques": min(int(profile.get("highlights_count") or 0), 5) * 3,
        "fixados": round(min(int(profile.get("pinned_count") or 0), 3) * 10 / 3),
        "categoria": 5 if profile.get("category") else 0,
        "contato": 5 if profile.get("has_contact") else 0,
        "frequencia": 5 if posts >= 8 else 3 if posts >= 4 else 1 if posts else 0,
    }
    return {"total": sum(parts.values()), "parts": parts}


async def extract_profile(brain, page_text: str) -> dict:
    prompt = f"""This is the text of an Instagram profile page. Extract the fields.
Return JSON: {{"name": "", "username": "", "bio": "", "has_photo": true, "link": "",
"category": "", "has_contact": false, "highlights_count": 0, "pinned_count": 0,
"posts_last_30": 0}}
When the text gives no sign of a photo (default avatar) use false. posts_last_30 =
posts in the last 30 days when dates show, else your best count from the grid text.

{page_text[:30000]}"""
    data = await brain.think_json(prompt, agent="instagram", task="profile_extract")
    return data if isinstance(data, dict) else {}


def profile_from_proposal(d: dict, has_photo: bool) -> dict:
    name = (d.get("names") or [{}])[0]
    bio = (d.get("bios") or [{}])[0]
    link = d.get("link_in_bio") or {}
    return {"name": name.get("pt", ""), "bio": bio.get("pt", ""), "has_photo": has_photo,
            "link": bool(link.get("buttons")), "category": d.get("category", ""),
            "has_contact": bool(d.get("contact_buttons")),
            "highlights_count": len(d.get("highlights") or []),
            "pinned_count": len(d.get("pinned") or []),
            "posts_last_30": min(len(load_queue()), 12)}


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
    lines = [f"  Nota do Instagram ({last['source']}): {last['total']}/100"]
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
