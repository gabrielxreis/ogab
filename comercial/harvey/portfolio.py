"""The right portfolio piece for each client.

Onboarding stores each work sample with a segment (igreja, evento, casamento,
marca, esporte, imobiliária, institucional...). When a lead asks for work, a
proposal is built, or a sample is sent, Mariana picks the pieces whose
segment matches the lead instead of always sending the same reel.
"""

from __future__ import annotations

import json
import re
import unicodedata

from harvey.paths import PROJECT_ROOT

ONBOARDING_FILE = PROJECT_ROOT / "data" / "onboarding.json"

# Segment → words that point to it in an industry, a company name or a reply.
SEGMENTS = {
    "igreja": ["igreja", "church", "ministerio", "ministry", "culto", "worship",
               "pastor", "batista", "assembleia", "comunidade crista", "gospel"],
    "evento": ["evento", "event", "conferencia", "conference", "congresso", "festival",
               "show", "feira", "summit", "venue", "espaco de eventos"],
    "casamento": ["casamento", "wedding", "noiva", "bride", "15 anos", "debutante"],
    "esporte": ["esporte", "sport", "time", "team", "clube", "club", "nfl", "futebol",
                "football", "basquete", "atleta", "athlete", "academia", "gym", "fitness"],
    "marca": ["marca", "brand", "produto", "product", "loja", "store", "ecommerce",
              "lancamento", "launch", "moda", "fashion", "restaurante", "restaurant"],
    "imobiliaria": ["imobili", "real estate", "imovel", "corretor", "realtor", "property"],
    "institucional": ["empresa", "company", "clinica", "clinic", "escola", "school",
                      "hotel", "escritorio", "office", "advocacia", "law"],
    "musica": ["musica", "music", "banda", "band", "clipe", "artista", "artist"],
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return text.lower()


def segment_of(*texts: str) -> str:
    """Best segment for a lead from its industry / name / any text, or ""."""
    blob = _norm(" ".join(t for t in texts if t))
    best, hits = "", 0
    for seg, words in SEGMENTS.items():
        n = sum(1 for w in words if re.search(rf"\b{re.escape(w)}", blob))
        if n > hits:
            best, hits = seg, n
    return best


def load_items(path=ONBOARDING_FILE) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    items = ((data.get("profile") or {}).get("offer") or {}).get("portfolio_items") or []
    return [i for i in items if isinstance(i, dict) and i.get("url")]


def match(*texts: str, items: list[dict] | None = None, limit: int = 2) -> list[dict]:
    """Pieces for this lead: same segment first, then general reels."""
    items = load_items() if items is None else items
    if not items:
        return []
    seg = segment_of(*texts)
    same = [i for i in items if seg and _norm(i.get("segment", "")).startswith(seg[:5])]
    general = [i for i in items if _norm(i.get("segment", "")) in
               ("", "geral", "general", "reel", "showreel")]
    rest = [i for i in items if i not in same and i not in general]
    ordered = same + general + rest
    return ordered[:limit]


def describe(items: list[dict]) -> str:
    """One line per piece, for prompts."""
    return "\n".join(
        f"- {i.get('title') or 'Trabalho'} ({i.get('segment') or 'geral'}): {i['url']}"
        + (f". {i['description']}" if i.get("description") else "")
        for i in items
    )
