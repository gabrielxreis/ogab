"""Event radar: video is bought around dates.

Finds upcoming events in the target markets (Sympla, Even3, Eventbrite,
church conferences, wedding fairs, games), extracts event + date +
organizer, finds the organizer's own website, and records the organizer as a
company with an `upcoming_event` signal. From there the normal pipeline
(profile → contacts → email / WhatsApp / LinkedIn) runs, and the writer's
first email can open with "vi que a conferência de vocês é em novembro".

Uses Serper (Google search API: 2,500 free queries, SERPER_API_KEY). About
one query per (event type, city, month) plus one per organizer.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import httpx

from harvey.collectors.discover import normalize_domain
from harvey.models.company import Company

logger = logging.getLogger("harvey.events")

SERPER_URL = "https://google.serper.dev/search"
COST_PER_QUERY = 0.001
AGGREGATORS = ("sympla.", "even3.", "eventbrite.", "facebook.", "instagram.", "youtube.",
               "linkedin.", "ticketmaster.", "eventim.", "bilheteria", "allevents.",
               "meetup.", "tiktok.", "x.com", "twitter.", "wikipedia.", "google.")

MONTHS_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]

# Industry keyword → event searches, per language.
EVENT_TYPES = {
    "igreja": (["conferência igreja", "congresso gospel", "encontro de jovens igreja"],
               ["church conference", "worship night", "youth conference church"],
               ["conferencia iglesia", "congreso cristiano"]),
    "evento": (["conferência", "congresso", "festival"],
               ["conference", "summit", "festival"],
               ["conferencia", "congreso", "festival"]),
    "casamento": (["feira de noivas", "expo noivas"], ["bridal show", "wedding expo"],
                  ["expo novias", "feria de bodas"]),
    "esporte": (["campeonato", "corrida de rua"], ["tournament", "marathon"],
                ["torneo", "maratón"]),
    "marca": (["lançamento", "feira de negócios"], ["product launch event", "trade show"],
              ["lanzamiento", "feria de negocios"]),
}
MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
SITES = {"pt-BR": "(site:sympla.com.br OR site:even3.com.br OR site:eventbrite.com.br)",
         "en": "(site:eventbrite.com OR site:allevents.in)",
         "es": "(site:eventbrite.com.mx OR site:eventbrite.es OR site:passline.com OR site:allevents.in)"}


def build_queries(industries: list[str], places: list[tuple[str, str]],
                  months: int = 3, today: date | None = None) -> list[str]:
    """Search strings for every (event type, place, month) in the window."""
    today = today or date.today()
    queries = []
    keys = [k for k in EVENT_TYPES if any(k[:5] in i.lower() or
            (k == "igreja" and "church" in i.lower()) or
            (k == "esporte" and "sport" in i.lower()) or
            (k == "marca" and "brand" in i.lower()) or
            (k == "evento" and "event" in i.lower()) or
            (k == "casamento" and "wedding" in i.lower()) for i in industries)] or ["evento"]
    for place, lang in places:
        idx, months_list, site = ((0, MONTHS_PT, SITES["pt-BR"]) if lang.startswith("pt") else
                                  (2, MONTHS_ES, SITES["es"]) if lang.startswith("es") else
                                  (1, MONTHS_EN, SITES["en"]))
        for offset in range(months):
            m = (today.month - 1 + offset) % 12
            year = today.year + (today.month - 1 + offset) // 12
            month = months_list[m]
            for key in keys:
                for term in EVENT_TYPES[key][idx][:2]:
                    queries.append(f'{term} {place} {month} {year} {site}')
    return queries


async def _search(client: httpx.AsyncClient, api_key: str, q: str, num: int = 10) -> list[dict]:
    r = await client.post(SERPER_URL, headers={"X-API-KEY": api_key,
                                               "Content-Type": "application/json"},
                          json={"q": q, "num": num})
    r.raise_for_status()
    return r.json().get("organic") or []


async def extract_events(brain, results: list[dict], today: date, window_days: int) -> list[dict]:
    if not results:
        return []
    lines = "\n".join(f"- {r.get('title')} | {r.get('snippet', '')} | {r.get('link')}"
                      for r in results[:60])
    prompt = f"""These are search results for upcoming events. Today is {today.isoformat()}.
Extract only real, specific events happening between today and {(today + timedelta(days=window_days)).isoformat()}.
For each: the event name, its date (YYYY-MM-DD, or YYYY-MM if only the month
is known), the city, and the ORGANIZER (the church, company, association or
person running it; not the ticketing platform). Skip anything without a clear
organizer, online-only events, and courses/webinars.

{lines}

Return JSON: [{{"event": "", "date": "", "city": "", "organizer": "", "url": ""}}]"""
    data = await brain.think_json(prompt, agent="events", task="extract")
    return [e for e in data if isinstance(e, dict) and e.get("organizer")] if isinstance(data, list) else []


async def find_organizer_site(client, api_key: str, organizer: str, city: str) -> str:
    for item in await _search(client, api_key, f'"{organizer}" {city}', num=8):
        link = item.get("link") or ""
        if link and not any(a in link.lower() for a in AGGREGATORS):
            return link
    return ""


async def run_event_radar(state, brain, config, env, months: int = 3,
                          max_queries: int = 24, estimate_only: bool = False) -> dict:
    from harvey import market
    default_lang = getattr(config.persona, "language", "pt-BR")
    places = [(g, market.language(market.detect(location=g, default_language=default_lang)))
              for g in config.icp.geography]
    queries = build_queries(config.icp.industries, places, months)[:max_queries]
    est = round(len(queries) * COST_PER_QUERY * 2, 3)  # + organizer lookups
    if estimate_only:
        return {"queries": len(queries), "estimated_cost_usd": est, "sample": queries[:3]}
    if not env.serper_api_key:
        raise RuntimeError("SERPER_API_KEY não está no .env (serper.dev, 2.500 buscas grátis).")

    today = date.today()
    results: list[dict] = []
    async with httpx.AsyncClient(timeout=20) as client:
        for q in queries:
            try:
                results += await _search(client, env.serper_api_key, q)
            except httpx.HTTPError as e:
                logger.warning(f"eventos: a busca falhou ({e})")
        events = await extract_events(brain, results, today, months * 31)
        added = 0
        seen: set[str] = set()
        for ev in events:
            key = ev["organizer"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            site = await find_organizer_site(client, env.serper_api_key,
                                             ev["organizer"], ev.get("city", ""))
            company = Company(
                name=ev["organizer"][:120],
                domain=normalize_domain(site) if site else "",
                website=site,
                location=ev.get("city", ""),
                source="events",
                source_url=ev.get("url", ""),
                external_id="" if site else f"event:{key[:80]}",
                industry="Eventos",
                signals=[{"type": "upcoming_event",
                          "detail": f"{ev.get('event')} em {ev.get('date')} ({ev.get('city')})",
                          "url": ev.get("url", "")}],
            )
            company_id = await state.add_company(company)
            await state.update_company_signals(company_id, new_signals=company.signals)
            added += 1
    await state.log_action(action_type="event_radar", agent="events",
                           details={"queries": len(queries), "events": len(events), "organizers": added})
    return {"queries": len(queries), "events": len(events), "organizers": added}
