"""Onboarding: Mariana learns everything about who she works for.

Runs on first use (``mariana onboard``) and any time after to update.
Everything she later writes, every prospect she picks and every price she
quotes comes from what is gathered here, so it asks for as much as it can:

  1. Material: any .md / .txt / .pdf the person hands over about themselves
     or their company, their website (crawled), and previous answers.
  2. The brain reads it all and lists what is still missing.
  3. A short interview asks ONLY the missing questions.
  4. The brain merges material + answers into one profile.
  5. Mariana writes, deterministically from that profile:
       harvey.local.yaml            config (gitignored)
       skills/product_knowledge.md  the dossier every agent reads (gitignored)
       data/onboarding.json         raw profile + answers, for re-runs
       data/signature.*             the email signature

Non-interactive use (/ogab comercial, CI): pass --answers answers.json
and --yes; unanswered questions are left for the dashboard to show.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import yaml

from harvey.brain import Brain
from harvey.config import load_brain_config
from harvey.paths import PROJECT_ROOT
from harvey.state import StateManager

logger = logging.getLogger("harvey.onboard")

LOCAL_CONFIG = PROJECT_ROOT / "harvey.local.yaml"
KNOWLEDGE_FILE = PROJECT_ROOT / "skills" / "product_knowledge.md"
ONBOARDING_FILE = PROJECT_ROOT / "data" / "onboarding.json"
MAX_MATERIAL_CHARS = 60000

# The profile Mariana needs. Every key is optional; the interview fills gaps.
PROFILE_SCHEMA = {
    "person": {
        "name": "full name of the professional (or the company's main contact)",
        "role": "what they call themselves, e.g. 'Filmmaker e editor de vídeo'",
        "company": "brand / company name (can equal the person's name)",
        "email": "email address outreach is sent from",
        "whatsapp": "WhatsApp number with country code, digits only",
        "website": "", "instagram": "", "portfolio": "reel / Vimeo / YouTube link",
        "linkedin": "", "city": "", "country": "",
        "languages": ["languages they work in"],
        "bio": "3-5 sentence professional bio in their own voice",
    },
    "offer": {
        "services": [{"name": "", "description": "", "starting_price": "",
                      "turnaround": ""}],
        "packages": ["named packages with what is included, if any"],
        "pricing_note": "how pricing works (from X, per day, per project...)",
        "key_benefits": ["why clients hire them, concrete"],
        "differentiators": ["what makes them different from other filmmakers"],
        "past_clients": ["real clients they may cite publicly"],
        "notable_work": ["projects worth mentioning, with links if any"],
        "portfolio_items": [{"title": "", "url": "", "description": "",
                             "segment": "igreja | evento | casamento | esporte | marca | "
                                        "imobiliaria | institucional | musica | geral"}],
        "travel": "do they travel / work remotely / where",
        "equipment": "short, only if it matters to clients",
    },
    "targets": {
        "industries": ["kinds of clients to look for"],
        "titles": ["decision maker titles to write to"],
        "markets": [{"place": "city, state/country", "lat": 0.0, "lng": 0.0,
                     "radius_km": 50, "language": "pt-BR or en"}],
        "company_size": "", "avoid": ["clients they do NOT want"],
        "dream_clients": ["specific companies they'd love to work with"],
    },
    "voice": {
        "tone": "how they write, e.g. 'direto, leve, criativo'",
        "default_language": "pt-BR or en",
        "never_say": ["words or phrases they hate"],
    },
    "goals": {
        "jobs_per_month": "", "booking_method": "calendar_link | suggest_times | ask_preference",
        "booking_url": "", "meeting_duration": "15 minutes",
        "main_offer": "the offer outreach leads with",
        "entry_offer": "a low-commitment first step, if any",
    },
    "signature": {"accent_color": "#111111", "photo_url": "", "extra_lines": []},
    "timezone": "IANA timezone, e.g. America/Sao_Paulo",
}

# Asked when the material doesn't answer them; the brain may add more.
CORE_QUESTIONS = [
    ("person.name", "Qual o seu nome completo (como aparece pros clientes)?"),
    ("person.company", "Nome da marca ou empresa (pode ser o seu nome):"),
    ("person.role", "Como você se apresenta? (ex.: filmmaker e editor de vídeo)"),
    ("person.email", "De qual email a Mariana vai enviar?"),
    ("person.whatsapp", "Seu WhatsApp com DDI e DDD (ex.: 5521999998888):"),
    ("person.portfolio", "Link do seu portfólio / showreel:"),
    ("offer.services", "Quais serviços você vende e a partir de quanto cada um?"),
    ("offer.past_clients", "Clientes que você pode citar publicamente:"),
    ("offer.portfolio_items", "Seus melhores trabalhos, um por linha: título, link e "
                              "tipo de cliente (igreja, evento, casamento, esporte, marca...):"),
    ("targets.industries", "Que tipo de cliente você quer fechar? (igrejas, eventos, marcas...)"),
    ("targets.markets", "Em quais cidades/países a Mariana deve procurar clientes?"),
    ("targets.avoid", "Algum tipo de cliente que você NÃO quer?"),
    ("voice.tone", "Como é o seu jeito de escrever? (ex.: direto e leve)"),
    ("goals.main_offer", "Qual oferta a Mariana deve usar pra puxar conversa?"),
]


def _get(d: dict, dotted: str):
    for part in dotted.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(part)
    return d


def _filled(value) -> bool:
    if value in (None, "", [], {}, 0, 0.0):
        return False
    if isinstance(value, list):
        return any(_filled(v) for v in value)
    if isinstance(value, dict):
        return any(_filled(v) for v in value.values())
    return True


def read_material_file(path: Path) -> str:
    """Text from a .md/.txt (or .pdf when pypdf is installed)."""
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return (f"[{path.name}: PDF não lido. Instale pypdf ou mande o "
                    "conteúdo em .md/.txt]")
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")


async def crawl_site(url: str, max_pages: int = 15) -> str:
    from harvey.trainer import FallbackCrawler, _normalize_start_url
    url = _normalize_start_url(url)
    try:
        pages = await FallbackCrawler().crawl(url, max_pages=max_pages)
    except Exception as e:
        logger.warning(f"onboard: não deu para ler {url}: {e}")
        return ""
    return "\n\n".join(f"--- {u} ---\n{t[:6000]}" for u, t in pages.items())


class Onboarding:
    def __init__(self, brain: Brain | None = None):
        if brain is None:
            brain = Brain(StateManager(), load_brain_config())
        self.brain = brain

    async def extract(self, material: str, previous: dict) -> dict:
        """First pass: what the material says, and what's still missing."""
        prompt = f"""You are Mariana's onboarding analyst. Mariana is an AI booking
assistant that finds clients and books jobs for an audiovisual professional
(filmmaker, video editor, producer, photographer or production company).

Read everything below and fill this profile schema. Use ONLY what the
material says; leave anything unknown empty. Never invent prices, clients
or links. For each target market, give approximate lat/lng of the city.

SCHEMA (keys and what they mean):
{json.dumps(PROFILE_SCHEMA, ensure_ascii=False, indent=1)}

PREVIOUS PROFILE (may be empty; keep what is still true):
{json.dumps(previous, ensure_ascii=False)[:8000]}

MATERIAL:
{material[:MAX_MATERIAL_CHARS]}

Then list up to 8 extra questions (in Brazilian Portuguese, short, one idea
each) that would most improve outreach and are NOT answered above. Prefer
questions about prices, best past work, ideal clients, and what makes them
different.

Return JSON: {{"profile": {{...schema...}}, "questions": [{{"key": "dotted.key or free", "question": "..."}}]}}"""
        result = await self.brain.think_json(prompt, agent="onboard", task="extract")
        if not isinstance(result, dict):
            return {"profile": previous or {}, "questions": []}
        result.setdefault("profile", {})
        result.setdefault("questions", [])
        return result

    async def build(self, material: str, profile: dict, answers: dict) -> dict:
        """Second pass: merge material + interview answers into the final profile."""
        prompt = f"""Merge the draft profile with the person's interview answers
into the final profile. Answers override the draft. Keep the exact schema.
Normalize: WhatsApp to digits with country code; prices as written by the
person; every portfolio link becomes a portfolio_items entry with a segment
(guess it from the title/client when not given); markets with approximate lat/lng and radius_km (default 50) and the
language spoken there (pt-BR for Brazil, en elsewhere). Write the bio in the
person's own voice and default language. Fill "timezone" from their city.
Never invent clients, prices or links that are not in the inputs.

SCHEMA:
{json.dumps(PROFILE_SCHEMA, ensure_ascii=False)}

DRAFT PROFILE:
{json.dumps(profile, ensure_ascii=False)}

INTERVIEW ANSWERS:
{json.dumps(answers, ensure_ascii=False)}

EXTRA MATERIAL (for reference):
{material[:20000]}

Return ONLY the final profile JSON."""
        result = await self.brain.think_json(prompt, agent="onboard", task="build")
        return result if isinstance(result, dict) else profile

    @staticmethod
    def pending_questions(extracted: dict) -> list[tuple[str, str]]:
        profile = extracted.get("profile", {})
        questions = [(k, q) for k, q in CORE_QUESTIONS if not _filled(_get(profile, k))]
        seen = {k for k, _ in questions}
        for item in extracted.get("questions", []):
            key = str(item.get("key") or item.get("question", ""))[:60]
            q = str(item.get("question", "")).strip()
            if q and key not in seen:
                questions.append((key, q))
                seen.add(key)
        return questions


# ── Writing the outputs (deterministic: no model involved) ──

def _list(values) -> list[str]:
    return [str(v) for v in (values or []) if str(v).strip()]


def build_config(profile: dict, existing: dict | None = None) -> dict:
    """harvey.local.yaml from the profile, keeping operational settings
    (channels, usage, brain, compliance) from the existing config."""
    existing = existing or {}
    person = profile.get("person", {})
    offer = profile.get("offer", {})
    targets = profile.get("targets", {})
    voice = profile.get("voice", {})
    goals = profile.get("goals", {})
    sig = profile.get("signature", {})

    services = offer.get("services") or []
    service_lines = [
        f"{s.get('name')}: {s.get('description', '')}".strip(": ")
        + (f" (a partir de {s['starting_price']})" if s.get("starting_price") else "")
        for s in services if isinstance(s, dict) and s.get("name")
    ]
    description = person.get("bio") or "; ".join(service_lines)
    pricing = offer.get("pricing_note") or "; ".join(
        f"{s.get('name')}: {s.get('starting_price')}"
        for s in services if isinstance(s, dict) and s.get("starting_price")
    ) or "Sob orçamento"

    markets = [m for m in targets.get("markets") or [] if isinstance(m, dict) and m.get("place")]
    geography = [m["place"] for m in markets]
    geo = {
        m["place"]: f"{m.get('lat', 0)},{m.get('lng', 0)},{m.get('radius_km', 50)}"
        for m in markets if m.get("lat") and m.get("lng")
    }
    default_lang = voice.get("default_language") or (
        "pt-BR" if str(person.get("country", "")).lower() in ("brasil", "brazil", "br", "")
        else "en")

    config = {
        "persona": {
            "name": person.get("name") or "",
            "company": person.get("company") or person.get("name") or "",
            "role": person.get("role") or "Filmmaker",
            "email": person.get("email") or "",
            "linkedin": person.get("linkedin") or "",
            "tone": voice.get("tone") or "direto, caloroso, criativo",
            "language": default_lang,
            "signature": {
                "enabled": True,
                "whatsapp": person.get("whatsapp") or "",
                "website": person.get("website") or "",
                "instagram": person.get("instagram") or "",
                "portfolio": person.get("portfolio") or "",
                "accent_color": sig.get("accent_color") or "#111111",
                "photo_url": sig.get("photo_url") or "",
                "extra_lines": _list(sig.get("extra_lines")),
            },
        },
        "product": {
            "name": person.get("company") or person.get("name") or "",
            "description": description,
            "pricing": pricing,
            "key_benefits": _list(offer.get("key_benefits")) or service_lines[:3],
            "objection_responses": {},
            "offer": {
                "primary": goals.get("main_offer") or "",
                "entry": goals.get("entry_offer") or "",
                "goal": "book_call",
                "booking_method": goals.get("booking_method") or "suggest_times",
                "booking_url": goals.get("booking_url") or "",
                "meeting_duration": goals.get("meeting_duration") or "15 minutes",
                "meeting_owner": person.get("name") or "",
            },
        },
        "icp": {
            "industries": _list(targets.get("industries")) or ["Eventos", "Igrejas", "Marcas"],
            "company_size": targets.get("company_size") or "1-200",
            "titles": _list(targets.get("titles")) or [
                "Owner", "Founder", "Marketing", "Communications Director"],
            "geography": geography or ["Rio de Janeiro, RJ"],
            "geo_coordinates": geo,
        },
    }
    for key in ("channels", "usage", "brain", "compliance"):
        if key in existing:
            config[key] = existing[key]
    config.setdefault("usage", {}).setdefault("quiet_hours", {})
    tz = profile.get("timezone")
    if tz:
        config["usage"]["quiet_hours"]["timezone"] = tz
    config["usage"]["quiet_hours"].setdefault("start", "21:00")
    config["usage"]["quiet_hours"].setdefault("end", "08:00")
    return config


def render_knowledge(profile: dict) -> str:
    """skills/product_knowledge.md: the dossier every agent reads."""
    p, o = profile.get("person", {}), profile.get("offer", {})
    t, v, g = profile.get("targets", {}), profile.get("voice", {}), profile.get("goals", {})
    out = [f"# Quem a Mariana representa: {p.get('name') or p.get('company') or '?'}", ""]
    if p.get("bio"):
        out += [p["bio"], ""]
    facts = [("Marca", p.get("company")), ("Apresentação", p.get("role")),
             ("Cidade", ", ".join(x for x in (p.get("city"), p.get("country")) if x)),
             ("Idiomas", ", ".join(_list(p.get("languages")))),
             ("Portfólio", p.get("portfolio")), ("Site", p.get("website")),
             ("Instagram", p.get("instagram")), ("LinkedIn", p.get("linkedin"))]
    out += [f"- **{k}:** {val}" for k, val in facts if val] + [""]

    services = [s for s in o.get("services") or [] if isinstance(s, dict) and s.get("name")]
    if services:
        out += ["## Serviços e preços", "",
                "| Serviço | O que é | A partir de | Prazo |", "|---|---|---|---|"]
        out += [f"| {s.get('name','')} | {s.get('description','')} | "
                f"{s.get('starting_price','') or 'sob orçamento'} | {s.get('turnaround','')} |"
                for s in services]
        out.append("")
    pieces = [i for i in o.get("portfolio_items") or [] if isinstance(i, dict) and i.get("url")]
    if pieces:
        out += ["## Portfólio por segmento", "",
                "Mande o trabalho do mesmo segmento do cliente.", "",
                "| Segmento | Trabalho | Link |", "|---|---|---|"]
        out += [f"| {i.get('segment') or 'geral'} | {i.get('title') or ''} | {i['url']} |"
                for i in sorted(pieces, key=lambda i: i.get("segment") or "")]
        out.append("")
    for title, key in (("Pacotes", "packages"), ("Por que contratam", "key_benefits"),
                       ("Diferenciais", "differentiators"),
                       ("Clientes que podem ser citados", "past_clients"),
                       ("Trabalhos de destaque", "notable_work")):
        items = _list(o.get(key))
        if items:
            out += [f"## {title}", ""] + [f"- {i}" for i in items] + [""]
    if o.get("pricing_note"):
        out += ["## Como funciona o preço", "", o["pricing_note"], ""]
    if o.get("travel"):
        out += ["## Deslocamento e remoto", "", o["travel"], ""]

    out += ["## Quem procurar", ""]
    out += [f"- **Segmentos:** {', '.join(_list(t.get('industries')))}",
            f"- **Cargos:** {', '.join(_list(t.get('titles')))}"]
    markets = [m.get("place") for m in t.get("markets") or [] if isinstance(m, dict)]
    if markets:
        out.append(f"- **Mercados:** {', '.join(x for x in markets if x)}")
    if _list(t.get("dream_clients")):
        out.append(f"- **Clientes dos sonhos:** {', '.join(_list(t.get('dream_clients')))}")
    if _list(t.get("avoid")):
        out.append(f"- **Não procurar:** {', '.join(_list(t.get('avoid')))}")
    out.append("")
    out += ["## Voz", "", f"- **Tom:** {v.get('tone', '')}"]
    if _list(v.get("never_say")):
        out.append(f"- **Nunca dizer:** {', '.join(_list(v.get('never_say')))}")
    out.append("")
    if g.get("main_offer") or g.get("entry_offer"):
        out += ["## Oferta", "", f"- **Principal:** {g.get('main_offer', '')}",
                f"- **Primeiro passo:** {g.get('entry_offer', '')}", ""]
    out += ["## Regras", "",
            "- Só cite clientes, trabalhos e preços que estão neste arquivo.",
            "- Preço fora da tabela, data ou contrato: ofereça mandar uma proposta.", ""]
    return "\n".join(out)


def write_outputs(profile: dict, answers: dict) -> dict[str, Path]:
    existing = {}
    if LOCAL_CONFIG.exists():
        existing = yaml.safe_load(LOCAL_CONFIG.read_text(encoding="utf-8")) or {}
    elif (PROJECT_ROOT / "harvey.yaml").exists():
        existing = yaml.safe_load((PROJECT_ROOT / "harvey.yaml").read_text(encoding="utf-8")) or {}
    config = build_config(profile, existing)
    LOCAL_CONFIG.write_text(
        "# Gerado por `mariana onboard`. Pode editar à mão; rode de novo para atualizar.\n"
        + yaml.dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_FILE.write_text(render_knowledge(profile), encoding="utf-8")
    ONBOARDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    ONBOARDING_FILE.write_text(
        json.dumps({"profile": profile, "answers": answers}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    paths = {"config": LOCAL_CONFIG, "knowledge": KNOWLEDGE_FILE,
             "onboarding": ONBOARDING_FILE}
    try:
        from harvey.config import load_config
        from harvey.signature import write_files
        paths.update(write_files(load_config(str(LOCAL_CONFIG))))
    except Exception as e:
        logger.warning(f"onboard: a assinatura ainda não foi gerada: {e}")
    return paths


def load_previous() -> tuple[dict, dict]:
    if ONBOARDING_FILE.exists():
        try:
            data = json.loads(ONBOARDING_FILE.read_text(encoding="utf-8"))
            return data.get("profile", {}), data.get("answers", {})
        except ValueError:
            pass
    return {}, {}


async def run_onboarding(
    files: list[str] | None = None,
    site: str = "",
    answers_file: str = "",
    assume_yes: bool = False,
) -> dict[str, Path] | None:
    previous, previous_answers = load_previous()
    print("\n  Oi! Eu sou a Mariana. Antes de procurar clientes, preciso te conhecer.")
    print("  Quanto mais eu souber, melhores ficam as mensagens.\n")

    interactive = sys.stdin.isatty() and not assume_yes
    files = list(files or [])
    if interactive and not files:
        raw = input("  Tem algum arquivo (.md, .txt, .pdf) falando de você ou da empresa?\n"
                    "  Cole o caminho (ou Enter pra pular): ").strip().strip("'\"")
        if raw:
            files.append(raw)
    if interactive and not site:
        site = input("  Seu site ou portfólio (Enter pra pular): ").strip()

    material = []
    for f in files:
        path = Path(f).expanduser()
        if path.is_file():
            material.append(f"=== ARQUIVO {path.name} ===\n{read_material_file(path)}")
            print(f"  ✓ Li {path.name}")
        else:
            print(f"  ! Não achei {path}")
    if site:
        print(f"  Lendo {site}...")
        text = await crawl_site(site)
        if text:
            material.append(f"=== SITE {site} ===\n{text}")
    material_text = "\n\n".join(material)

    ob = Onboarding()
    print("  Analisando o que você me mandou...")
    extracted = await ob.extract(material_text, previous)

    answers = dict(previous_answers)
    if answers_file:
        answers.update(json.loads(Path(answers_file).expanduser().read_text(encoding="utf-8")))
    pending = [(k, q) for k, q in ob.pending_questions(extracted) if k not in answers]
    if pending and interactive:
        print(f"\n  Faltam {len(pending)} perguntas rápidas (Enter pula):\n")
        for i, (key, question) in enumerate(pending, 1):
            reply = input(f"  [{i}/{len(pending)}] {question}\n  > ").strip()
            if reply:
                answers[key] = reply
    elif pending:
        print(f"  {len(pending)} pergunta(s) sem resposta; dá pra completar depois:")
        for _, q in pending:
            print(f"    - {q}")

    print("\n  Montando seu perfil...")
    profile = await ob.build(material_text, extracted.get("profile", {}), answers)
    paths = write_outputs(profile, answers)
    print("\n  Pronto. Arquivos gerados:")
    for name, path in paths.items():
        print(f"    - {name}: {path}")
    print("\n  Próximos passos:")
    print("    mariana signature        (ver e instalar a assinatura)")
    print("    mariana email-check      (checar o email de envio)")
    print("    mariana whatsapp-check   (checar o WhatsApp)")
    print("    mariana dashboard        (painel em http://localhost:5555)\n")
    return paths
