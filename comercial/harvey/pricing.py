"""Price suggestions from the jobs you actually closed.

"Aftermovie de igreja fechou entre R$ 2.500 e R$ 4.000 (3 jobs)". Read from
jobs with status won/delivered, grouped by segment and by the service words
they share. The catalog price from onboarding always wins in a proposal;
history is shown next to it, never invented when there is none.
"""

from __future__ import annotations

import re
import unicodedata
from statistics import median

from harvey import portfolio

CURRENCY = {"R$": "BRL", "US$": "USD", "$": "USD", "€": "EUR"}
STOP = {"de", "do", "da", "e", "com", "para", "the", "and", "of", "for", "video", "vídeo"}


def parse_value(text: str) -> tuple[float, str] | None:
    """'R$ 2.500,00' → (2500.0, 'R$'); '$1,200' → (1200.0, '$'). First amount only."""
    if not text:
        return None
    symbol = "R$" if "R$" in text else "US$" if "US$" in text else "$" if "$" in text \
        else "€" if "€" in text else "R$"
    m = re.search(r"\d[\d.,]*", text)
    if not m:
        return None
    raw = m.group(0)
    if symbol == "R$" or re.search(r",\d{2}$", raw):
        raw = raw.replace(".", "").replace(",", ".")      # 2.500,00
    else:
        raw = raw.replace(",", "")                          # 1,200.50
    try:
        value = float(raw)
    except ValueError:
        return None
    if re.search(r"\b(mil|k)\b", text.lower()) and value < 1000:
        value *= 1000
    return value, symbol


def _fmt(value: float, symbol: str) -> str:
    if symbol == "R$":
        return "R$ " + f"{value:,.0f}".replace(",", ".")
    return f"{symbol}{value:,.0f}"


def _words(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return {w for w in re.findall(r"[a-z]{4,}", text) if w not in STOP}


def history(jobs: list[dict], segment: str = "", service: str = "") -> dict | None:
    """Range of closed values for jobs like this one, or None without data."""
    closed = []
    for j in jobs:
        if j.get("status") not in ("won", "delivered"):
            continue
        parsed = parse_value(j.get("value", ""))
        if parsed:
            closed.append((j, *parsed))
    if not closed:
        return None
    want = _words(service)

    def similar(job) -> bool:
        same_seg = segment and (job.get("segment") or "") == segment
        same_service = want and (want & _words(job.get("service", "")))
        return bool(same_seg and (same_service or not want)) or bool(same_service and not segment)

    pool = [c for c in closed if similar(c[0])] or [c for c in closed if want & _words(c[0].get("service", ""))]
    basis = "parecidos"
    if not pool:
        pool = [c for c in closed if segment and c[0].get("segment") == segment]
        basis = "do mesmo segmento"
    if not pool:
        return None
    symbol = max({c[2] for c in pool}, key=lambda s: sum(1 for c in pool if c[2] == s))
    values = sorted(c[1] for c in pool if c[2] == symbol)
    return {
        "count": len(values), "min": values[0], "max": values[-1], "median": median(values),
        "symbol": symbol, "basis": basis,
        "text": (f"{len(values)} job(s) {basis} fecharam entre {_fmt(values[0], symbol)} e "
                 f"{_fmt(values[-1], symbol)} (mediana {_fmt(median(values), symbol)})"
                 if len(values) > 1 else
                 f"1 job {basis} fechou em {_fmt(values[0], symbol)}"),
    }


async def suggest(state, segment: str = "", service: str = "", client_text: str = "") -> dict | None:
    segment = segment or portfolio.segment_of(client_text)
    return history(await state.get_jobs(), segment, service)
