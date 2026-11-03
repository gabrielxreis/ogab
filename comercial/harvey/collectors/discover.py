"""DISCOVER — who exists, and how visible they are.

The only stage that costs money, so it is the one with a provider menu, a
mandatory cost estimate, and a budget check inside the loop.

Two shapes of discovery, and the difference matters:

* **Listings** ask "which businesses of this type are in this place?" and come
  back with a phone, a category, a rating and — crucially — whether there is a
  website at all. For local SMB verticals this is the primary path.
* **SERP** asks "who ranks for this search?" and comes back with a rank
  position. You are buying the *signal*, not the list: positions 11-30 are
  businesses visible enough to be trying and not winning, which is the most
  useful prospecting signal there is.

Cost discipline lives here, not in the database. A table can only record spend
after the fact; only the collector can decline to spend it. Every run
estimates first, checks a budget between batches, reads the kill switch, and
flushes observations per batch — a long run that dies must not lose what it
already learned.
"""

import asyncio
import base64
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from harvey.models import Company

logger = logging.getLogger("harvey.collectors.discover")

TIMEOUT = httpx.Timeout(connect=10.0, read=45.0, write=10.0, pool=10.0)


# ── Junk filtering ────────────────────────────────────────────────────
# Discovery fills a database with directories, hospital systems, media and
# lead-gen middlemen unless you filter hard. Match PATTERNS, not a literal
# list: a literal list is exactly how `whatclinic.com` and `ufhealth.org` get
# through on the first run.

# Anchored on a dot boundary, not the string start: SERP results arrive as
# `en.wikipedia.org` and `m.facebook.com` at least as often as bare domains,
# and `^(www\.)?` catches neither.
JUNK_DOMAIN_PATTERNS = tuple(re.compile(p, re.I) for p in (
    # directories & marketplaces
    r"(^|\.)(yelp|yellowpages|superpages|manta|bbb|angi|angieslist|homeadvisor)\.",
    r"(^|\.)(thumbtack|houzz|porch|buildzoom|networx|modernize|nextdoor)\.",
    r"(^|\.)(facebook|instagram|twitter|x|linkedin|youtube|tiktok|pinterest)\.",
    r"(^|\.)(indeed|glassdoor|ziprecruiter|craigslist|zillow|realtor)\.",
    r"(^|\.)(mapquest|foursquare|tripadvisor|trustpilot|birdeye|expertise)\.",
    r"(directory|listings?|find-?a-|top\d+|best-?of)\.",
    # media & reference
    r"(^|\.)(wikipedia|reddit|quora|medium|substack|forbes|inc|entrepreneur)\.",
    r"(news|magazine|journal|gazette|tribune|herald)\.(com|org|net)$",
    # institutional
    r"\.(edu|gov|mil)$",
    r"(hospital|healthsystem|medicalcenter)\.",
    r"health\.org$",
    # infrastructure that is never a prospect
    r"(^|\.)(google|bing|yahoo|duckduckgo|amazon|apple|microsoft)\.",
    r"(wordpress|wix|squarespace|shopify|godaddy|weebly|webflow)\.com$",
))

# Names that mean the row is a category page or an aggregator, not a business.
JUNK_NAME_PATTERNS = tuple(re.compile(p, re.I) for p in (
    r"^\s*(top|best|\d+)\s+\d*\s*(best\s+)?\w+.*\b(in|near|of)\b",
    r"\b(directory|listings?|reviews? of|compare|find a)\b",
))


def normalize_domain(url_or_domain: str) -> str:
    """A bare, lowercase, www-less hostname — the entity-resolution key.

    Entity resolution decides whether any of this is real. Get it wrong and
    every trend built on top is garbage.
    """
    if not url_or_domain:
        return ""
    raw = url_or_domain.strip().lower()
    if "://" not in raw:
        raw = "http://" + raw
    host = (urlparse(raw).hostname or "").strip(".")
    return host[4:] if host.startswith("www.") else host


def is_junk(domain: str, name: str = "") -> bool:
    """True when this row would pollute the database rather than fill it."""
    if domain:
        if any(p.search(domain) for p in JUNK_DOMAIN_PATTERNS):
            return True
        # A bare TLD or an IP address is never a business we can profile.
        if "." not in domain or re.fullmatch(r"[\d.]+", domain):
            return True
    if name and any(p.search(name) for p in JUNK_NAME_PATTERNS):
        return True
    return False


# ── Geocoding ─────────────────────────────────────────────────────────
# Listings providers search a radius, not a place name, so "Denver, CO" has to
# become coordinates. Nominatim allows exactly this (single place lookups at
# <=1 req/s) and forbids bulk enumeration, so every result is cached forever in
# the settings table: a given city is looked up once, ever.

NOMINATIM = "https://nominatim.openstreetmap.org/search"
GEOCODE_UA = "Mariana/0.1 (open-source sales agent; github.com/gabrielxreis/ogab)"


async def geocode_city(state, city: str, radius_km: int = 40,
                       client: httpx.AsyncClient | None = None) -> str:
    """"Denver, CO" -> "39.7392,-104.9903,40". Cached permanently."""
    if not city:
        return ""
    cache_key = f"geo:{city.strip().lower()}"
    cached = await state.get_setting(cache_key)
    if cached:
        # A previous miss is cached as "-" so we don't re-ask every run.
        return "" if cached == "-" else f"{cached},{radius_km}"

    owned = client is None
    client = client or httpx.AsyncClient(timeout=TIMEOUT)
    try:
        r = await client.get(
            NOMINATIM,
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": GEOCODE_UA},
        )
        r.raise_for_status()
        hits = r.json()
    except Exception as e:
        logger.warning("não deu para achar as coordenadas de %r: %s", city, e)
        return ""
    finally:
        if owned:
            await client.aclose()

    if not hits:
        await state.set_setting(cache_key, "-")
        logger.warning("coordenadas: nada encontrado para %r", city)
        return ""

    point = f"{float(hits[0]['lat']):.4f},{float(hits[0]['lon']):.4f}"
    await state.set_setting(cache_key, point)
    return f"{point},{radius_km}"


async def resolve_coordinates(state, queries: list["DiscoveryQuery"],
                              radius_km: int = 40,
                              client: httpx.AsyncClient | None = None
                              ) -> list["DiscoveryQuery"]:
    """Fill in coordinates for any query that lacks them.

    Configured ``icp.geo_coordinates`` always wins; this only covers what the
    user did not spell out. Distinct cities are geocoded once each, however
    many queries share them.
    """
    needed = {q.location for q in queries if q.location and not q.coordinate}
    points: dict[str, str] = {}
    for i, city in enumerate(sorted(needed)):
        if i:
            await asyncio.sleep(1.1)     # Nominatim: max 1 request/second
        points[city] = await geocode_city(state, city, radius_km, client)

    for query in queries:
        if not query.coordinate:
            query.coordinate = points.get(query.location, "")
    return queries


# ── The record every provider returns ─────────────────────────────────


@dataclass
class Business:
    """One discovered business, normalised across providers."""

    name: str = ""
    domain: str = ""
    website: str = ""
    phone: str = ""
    address: str = ""
    location: str = ""
    category: str = ""
    rating: float | None = None
    review_count: int | None = None
    is_claimed: bool | None = None
    has_website: bool | None = None
    rank: int | None = None          # organic rank, when the provider gives one
    external_id: str = ""            # "<provider>:<stable id>"
    source_url: str = ""
    provider: str = ""

    def identity(self) -> str:
        return self.domain or self.external_id


@dataclass
class DiscoveryQuery:
    """What to look for, and where."""

    term: str                        # "roofing contractor"
    location: str = ""               # "Denver, CO"
    category: str = ""               # provider-native category slug, optional
    coordinate: str = ""             # "lat,lng,radius_km" for listings providers
    depth: int = 30                  # SERP depth; ignored by listings providers
    limit: int = 100                 # max records to take from one query

    def keyword(self) -> str:
        return f"{self.term} {self.location}".strip()


# ── Provider adapters ─────────────────────────────────────────────────


class DiscoveryProvider:
    """One way of answering "who exists".

    Subclasses implement ``fetch``. Everything else — the menu metadata the
    dashboard renders, cost estimation, configuration checks — lives here so a
    new provider is a small class rather than a wiring exercise.
    """

    key: str = ""
    label: str = ""
    kind: str = "listings"           # listings | serp
    blurb: str = ""
    cost_note: str = ""
    free_tier: str = ""
    signup_url: str = ""
    env_keys: tuple[str, ...] = ()
    caveat: str = ""

    def configured(self, env: dict) -> bool:
        return all(env.get(k) for k in self.env_keys)

    def estimate(self, queries: list[DiscoveryQuery]) -> float:
        """Projected spend, in dollars, before anything is called."""
        return 0.0

    async def fetch(self, client: httpx.AsyncClient, env: dict,
                    query: DiscoveryQuery) -> list[Business]:
        raise NotImplementedError

    # Shared helper: providers report their own per-query spend so the run log
    # records what actually happened, not what was projected.
    last_cost: float = 0.0


class DataForSEOListings(DiscoveryProvider):
    """Google Business Profile data as a queryable database, not a scrape.

    The cheapest way to enumerate local businesses anywhere, and the only one
    with a filter for "has no website" — which for anyone selling websites is
    the highest-intent query available.
    """

    key = "dataforseo_listings"
    label = "DataForSEO Business Listings"
    kind = "listings"
    blurb = ("Lista todas as empresas de um tipo num raio, com telefone, site, "
             "nota e se o perfil é reivindicado. A melhor escolha para negócios "
             "locais: espaços de evento, clínicas, academias, restaurantes.")
    cost_note = "US$ 0,372 por 1.000 empresas (US$ 0,012/busca + US$ 0,00036 cada)"
    free_tier = "US$ 1 de crédito no cadastro; depósito mínimo de US$ 50 para usar de verdade"
    signup_url = "https://app.dataforseo.com/api-access"
    env_keys = ("dataforseo_login", "dataforseo_password")
    caveat = "Não traz email: a Mariana resolve isso numa etapa seguinte."

    TASK_COST = 0.012
    ITEM_COST = 0.00036

    def estimate(self, queries):
        return sum(self.TASK_COST + self.ITEM_COST * q.limit for q in queries)

    def _auth(self, env: dict) -> str:
        raw = f"{env['dataforseo_login']}:{env['dataforseo_password']}"
        return base64.b64encode(raw.encode()).decode()

    def base_url(self, env: dict) -> str:
        # The sandbox mirrors the response schema exactly and is never
        # charged — the right target for a first run and for the test suite.
        return ("https://sandbox.dataforseo.com/v3"
                if env.get("dataforseo_sandbox") else
                "https://api.dataforseo.com/v3")

    async def fetch(self, client, env, query):
        payload = {
            "limit": min(query.limit, 1000),
            "order_by": ["rating.votes_count,desc"],
        }
        if query.category:
            payload["categories"] = [query.category]
        else:
            payload["title"] = query.term
        if query.coordinate:
            payload["location_coordinate"] = query.coordinate
        elif query.location:
            # Without coordinates the API can only match on the title, so say
            # so rather than silently returning nationwide results.
            payload["description"] = query.location

        r = await client.post(
            f"{self.base_url(env)}/business_data/business_listings/search/live",
            headers={"Authorization": f"Basic {self._auth(env)}",
                     "Content-Type": "application/json"},
            json=[payload],
        )
        r.raise_for_status()
        data = r.json()
        self.last_cost = float(data.get("cost") or 0.0)
        return [self._to_business(item) for item in _dfs_items(data)]

    def _to_business(self, item: dict) -> Business:
        url = item.get("url") or ""
        rating = (item.get("rating") or {})
        addr = item.get("address_info") or {}
        city = ", ".join(x for x in (addr.get("city"), addr.get("region")) if x)
        return Business(
            name=item.get("title") or "",
            domain=normalize_domain(item.get("domain") or url),
            website=url,
            phone=item.get("phone") or "",
            address=item.get("address") or "",
            location=city,
            category=item.get("category") or "",
            rating=rating.get("value"),
            review_count=rating.get("votes_count"),
            is_claimed=item.get("is_claimed"),
            has_website=bool(url),
            external_id=f"dataforseo:{item['place_id']}" if item.get("place_id") else "",
            source_url=item.get("check_url") or "",
            provider=self.key,
        )


class DataForSEOSerp(DiscoveryProvider):
    """Organic rank as the buying signal.

    Buy the rank, not the list. A business sitting at 11-30 for its own core
    search is visible enough to have tried and is losing — the single most
    useful thing you can know before writing to them.
    """

    key = "dataforseo_serp"
    label = "DataForSEO SERP (organic rank)"
    kind = "serp"
    blurb = ("Busca '<serviço> <cidade>' e registra a posição de cada empresa. "
             "Acha empresas novas E pontua as que você já tinha.")
    cost_note = "US$ 0,0006 por 10 resultados (profundidade 30 = US$ 0,0018 por busca)"
    free_tier = "US$ 1 de crédito; sandbox grátis; depósito mínimo de US$ 50"
    signup_url = "https://app.dataforseo.com/api-access"
    env_keys = ("dataforseo_login", "dataforseo_password")
    caveat = ("O Google tirou os 100 resultados por página em setembro de 2025, "
              "então profundidade 100 custa 10x a 10. O ideal é 20 a 30; abaixo "
              "da posição 30 quase só aparecem diretórios.")

    PAGE_COST = 0.0006

    def estimate(self, queries):
        # Billing is base price x number of pages, 10 results to a page.
        return sum(self.PAGE_COST * max(1, -(-q.depth // 10)) for q in queries)

    _auth = DataForSEOListings._auth
    base_url = DataForSEOListings.base_url

    async def fetch(self, client, env, query):
        r = await client.post(
            f"{self.base_url(env)}/serp/google/organic/live/advanced",
            headers={"Authorization": f"Basic {self._auth(env)}",
                     "Content-Type": "application/json"},
            json=[{"keyword": query.keyword(), "language_code": "en",
                   "depth": query.depth, "device": "desktop"}],
        )
        r.raise_for_status()
        data = r.json()
        self.last_cost = float(data.get("cost") or 0.0)

        out = []
        for item in _dfs_items(data):
            if item.get("type") != "organic":
                continue
            domain = normalize_domain(item.get("domain") or item.get("url") or "")
            if not domain:
                continue
            out.append(Business(
                name=item.get("title") or domain,
                domain=domain,
                website=item.get("url") or "",
                location=query.location,
                # rank_group is position within organic results.
                # `position` in this payload means left/right column, NOT rank.
                rank=item.get("rank_group"),
                has_website=True,
                source_url=item.get("url") or "",
                provider=self.key,
            ))
        return out


class Serper(DiscoveryProvider):
    """Google search with the friendliest free tier and the best depth pricing.

    The one provider that did not go to 10x for depth 100 when Google removed
    100-results-per-page, and 2,500 free queries with no card.
    """

    key = "serper"
    label = "Serper"
    kind = "serp"
    blurb = ("Busca rápida no Google com posição. O mais fácil de testar: "
             "2.500 buscas grátis, sem cartão, uma chave só.")
    cost_note = "~US$ 0,30 a 1,00 por 1.000 buscas, conforme o plano"
    free_tier = "2.500 buscas grátis, sem cartão"
    signup_url = "https://serper.dev"
    env_keys = ("serper_api_key",)
    caveat = "Os planos pagos começam num pacote pré-pago de US$ 50; os créditos vencem em 6 meses."

    def estimate(self, queries):
        # One credit per 10 results on the standard plan.
        return sum(0.001 * max(1, -(-q.depth // 10)) for q in queries)

    async def fetch(self, client, env, query):
        r = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": env["serper_api_key"],
                     "Content-Type": "application/json"},
            json={"q": query.keyword(), "num": min(query.depth, 100)},
        )
        r.raise_for_status()
        data = r.json()
        out = []
        for item in data.get("organic") or []:
            domain = normalize_domain(item.get("link") or "")
            if not domain:
                continue
            out.append(Business(
                name=item.get("title") or domain,
                domain=domain,
                website=item.get("link") or "",
                location=query.location,
                rank=item.get("position"),
                has_website=True,
                source_url=item.get("link") or "",
                provider=self.key,
            ))
        return out


class OpenStreetMap(DiscoveryProvider):
    """Genuinely free, no account, no key. Honest about what that costs you.

    Good enough to try the whole pipeline end to end without signing up for
    anything, and a useful cross-reference layer afterwards. Not good enough
    to be your only source: OSM maps physical premises, so service-area
    businesses (roofers, HVAC, plumbers) are heavily under-represented.
    """

    key = "osm"
    label = "OpenStreetMap (Overpass)"
    kind = "listings"
    blurb = ("Dados públicos de mapa. Sem cadastro, sem chave, sem cartão. Teste "
             "o funil inteiro antes de pagar qualquer coisa.")
    cost_note = "grátis"
    free_tier = "ilimitado, respeitando o uso da comunidade"
    signup_url = "https://www.openstreetmap.org"
    env_keys = ()
    caveat = ("A cobertura é fraca para quem não tem endereço físico: o mapa "
              "registra lugares. Ótimo para testar de graça ou cruzar dados; "
              "não é uma lista completa.")

    # Several public Overpass instances run the same API. The main one
    # throttles readily, so try the mirrors before giving up — a free source
    # that fails half the time is not usable as a default.
    ENDPOINTS = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    )
    # Overpass etiquette for a shipped tool: modest volume, no parallelism.
    MIN_INTERVAL = 2.0
    BACKOFF = 5.0

    # A friendly term maps to the OSM tags that actually carry those businesses.
    TAG_MAP = {
        "roof": ['craft=roofer', 'shop=roofing'],
        "plumb": ['craft=plumber'],
        "hvac": ['craft=hvac'],
        "electric": ['craft=electrician'],
        "dentist": ['amenity=dentist'],
        "lawyer": ['office=lawyer'],
        "attorney": ['office=lawyer'],
        "contractor": ['craft=builder', 'office=construction_company'],
        "landscap": ['craft=gardener', 'shop=garden_centre'],
        # Audiovisual buyers (Mariana). Portuguese and English terms.
        "igreja": ['amenity=place_of_worship'],
        "church": ['amenity=place_of_worship'],
        "evento": ['amenity=events_venue', 'amenity=conference_centre'],
        "event": ['amenity=events_venue', 'amenity=conference_centre'],
        "casamento": ['amenity=events_venue', 'shop=wedding'],
        "wedding": ['amenity=events_venue', 'shop=wedding'],
        "academia": ['leisure=fitness_centre', 'leisure=sports_centre'],
        "gym": ['leisure=fitness_centre', 'leisure=sports_centre'],
        "imobili": ['office=estate_agent'],
        "real estate": ['office=estate_agent'],
        "restaurant": ['amenity=restaurant'],
        "restaurante": ['amenity=restaurant'],
        "hotel": ['tourism=hotel'],
        "clínica": ['amenity=clinic', 'healthcare=clinic'],
        "clinica": ['amenity=clinic', 'healthcare=clinic'],
        "clinic": ['amenity=clinic', 'healthcare=clinic'],
        "escola": ['amenity=school', 'amenity=college'],
        "school": ['amenity=school', 'amenity=college'],
        "agência": ['office=advertising_agency'],
        "agencia": ['office=advertising_agency'],
        "agency": ['office=advertising_agency'],
        "marketing": ['office=advertising_agency'],
        "carro": ['shop=car'],
        "car dealer": ['shop=car'],
        "boate": ['amenity=nightclub'],
        "nightclub": ['amenity=nightclub'],
        "teatro": ['amenity=theatre'],
        "theatre": ['amenity=theatre'],
        "esporte": ['leisure=sports_centre', 'club=sport'],
        "sports": ['leisure=sports_centre', 'club=sport'],
        "marca": ['office=company', 'shop=boutique'],
        "brand": ['office=company', 'shop=boutique'],
    }

    def _tags(self, term: str) -> list[str]:
        """The OSM tags that actually carry this kind of business, or none.

        There is deliberately no catch-all fallback. An earlier version fell
        back to `office=company`, which answers "roofers in Denver" with every
        registered office in Denver — coffee roasters, churches, photography
        studios. A search this source cannot answer has to say so; filling the
        database with plausible-looking junk is far worse than returning
        nothing.
        """
        low = term.lower()
        for needle, tags in self.TAG_MAP.items():
            if needle in low:
                return tags
        return []

    async def fetch(self, client, env, query):
        if not query.coordinate:
            logger.warning("osm: sem coordenada (coordinate) para %r: o mapa precisa de "
                           "lat,lng,raio para buscar", query.keyword())
            return []
        tags = self._tags(query.term)
        if not tags:
            raise RuntimeError(
                f"OpenStreetMap has no category for {query.term!r}. It can only "
                f"search mapped trades ({', '.join(sorted(self.TAG_MAP))}). Use a "
                f"listings or SERP provider for this one.")
        lat, lng, radius_km = (query.coordinate.split(",") + ["", "", ""])[:3]
        radius_m = int(float(radius_km or 25) * 1000)
        clauses = "".join(
            f'node[{tag.split("=")[0]}={tag.split("=")[1]}](around:{radius_m},{lat},{lng});'
            f'way[{tag.split("=")[0]}={tag.split("=")[1]}](around:{radius_m},{lat},{lng});'
            for tag in tags
        )
        body = f"[out:json][timeout:40];({clauses});out center {query.limit};"

        # Overpass is a free volunteer service and 429s/504s readily under
        # load. Walk the mirrors, then RAISE: returning [] would make a
        # throttled run look exactly like a market with no businesses in it.
        headers = {"User-Agent": "Mariana/0.1 (open-source sales agent; "
                                 "github.com/gabrielxreis/ogab)"}
        r = None
        for i, endpoint in enumerate(self.ENDPOINTS):
            if i:
                await asyncio.sleep(self.BACKOFF)
            try:
                r = await client.post(endpoint, content=body.encode(),
                                      headers=headers)
            except httpx.HTTPError as e:
                logger.warning("osm: %s unreachable (%s)", endpoint, e)
                continue
            if r.status_code not in (429, 504):
                break
            logger.warning("osm: %s está limitando (%s); tentando o próximo servidor",
                           endpoint, r.status_code)
        else:
            raise RuntimeError(
                "Every public Overpass mirror is throttling right now. This is "
                "free volunteer infrastructure — wait a few minutes and re-run, "
                "or use a paid provider for bulk work.")
        if r is None:
            raise RuntimeError("Could not reach any Overpass mirror.")
        r.raise_for_status()

        out = []
        for el in r.json().get("elements") or []:
            tags = el.get("tags") or {}
            name = tags.get("name") or ""
            if not name:
                continue
            site = tags.get("website") or tags.get("contact:website") or ""
            city = ", ".join(x for x in (tags.get("addr:city"),
                                         tags.get("addr:state")) if x)
            out.append(Business(
                name=name,
                domain=normalize_domain(site),
                website=site,
                phone=tags.get("phone") or tags.get("contact:phone") or "",
                address=" ".join(x for x in (tags.get("addr:housenumber"),
                                             tags.get("addr:street")) if x),
                location=city or query.location,
                category=tags.get("craft") or tags.get("shop") or tags.get("office") or "",
                has_website=bool(site),
                external_id=f"osm:{el.get('type')}/{el.get('id')}",
                source_url=f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}",
                provider=self.key,
            ))
        return out


PROVIDERS: dict[str, DiscoveryProvider] = {
    p.key: p for p in (
        OpenStreetMap(),
        DataForSEOListings(),
        DataForSEOSerp(),
        Serper(),
    )
}

DEFAULT_PROVIDER = "osm"


def _dfs_items(payload: dict) -> list[dict]:
    """Pull result items out of a DataForSEO envelope, surfacing errors.

    A bare status code costs three wrong guesses; the message in the body
    usually makes the problem obvious immediately.
    """
    if payload.get("status_code") not in (20000, None):
        raise RuntimeError(
            f"DataForSEO {payload.get('status_code')}: "
            f"{payload.get('status_message')}")
    tasks = payload.get("tasks") or []
    if not tasks:
        return []
    task = tasks[0]
    if task.get("status_code") not in (20000, None):
        raise RuntimeError(
            f"DataForSEO task {task.get('status_code')}: "
            f"{task.get('status_message')}")
    results = task.get("result") or []
    if not results or not results[0]:
        return []
    return results[0].get("items") or []


# ── The run ───────────────────────────────────────────────────────────


@dataclass
class DiscoveryReport:
    """What a run did — the honest version, including what it skipped."""

    provider: str = ""
    queries: int = 0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    found: int = 0
    junk: int = 0
    new_companies: int = 0
    known_companies: int = 0
    observations: int = 0
    run_id: str = ""
    errors: list[str] = field(default_factory=list)
    stopped: str = ""

    def as_dict(self) -> dict:
        return {
            "provider": self.provider, "queries": self.queries,
            "estimated_cost": round(self.estimated_cost, 4),
            "actual_cost": round(self.actual_cost, 4),
            "found": self.found, "junk": self.junk,
            "new_companies": self.new_companies,
            "known_companies": self.known_companies,
            "observations": self.observations,
            "run_id": self.run_id, "errors": self.errors,
            "stopped": self.stopped,
        }


def build_queries(config, cities: list[str] | None = None,
                  depth: int = 30, limit: int = 100) -> list[DiscoveryQuery]:
    """Turn the configured ICP into a concrete query list.

    One query per (industry x city). Coordinates come from
    ``icp.geo_coordinates`` when present, because listings providers need a
    radius, not a place name.
    """
    icp = config.icp
    terms = list(icp.industries) or [config.product.name]
    places = cities if cities is not None else list(icp.geography) or [""]
    coords = getattr(icp, "geo_coordinates", {}) or {}

    return [
        DiscoveryQuery(term=term, location=place, depth=depth, limit=limit,
                       coordinate=coords.get(place, ""))
        for term in terms
        for place in places
    ]


def estimate_cost(provider_key: str, queries: list[DiscoveryQuery]) -> float:
    """Projected spend. Always call this before a run — and print it."""
    provider = PROVIDERS.get(provider_key)
    return provider.estimate(queries) if provider else 0.0


async def run_discovery(
    state,
    config,
    provider_key: str = DEFAULT_PROVIDER,
    queries: list[DiscoveryQuery] | None = None,
    max_spend: float = 1.0,
    dry_run: bool = False,
) -> DiscoveryReport:
    """Discover businesses and record what was learned about them.

    ``dry_run`` estimates and returns without calling anything. Run it first,
    every time: the first small trial is what exposes the data-quality
    problems that would otherwise poison every market you scale to.
    """
    from harvey.config import load_env
    from harvey.signals import seed_signal_catalog

    provider = PROVIDERS.get(provider_key)
    if provider is None:
        raise ValueError(f"unknown discovery provider: {provider_key!r}")

    queries = queries or build_queries(config)
    if provider.kind == "listings":
        queries = await resolve_coordinates(state, queries)
    report = DiscoveryReport(provider=provider_key, queries=len(queries))
    report.estimated_cost = provider.estimate(queries)

    if dry_run:
        return report

    env = load_env().model_dump()
    if not provider.configured(env):
        missing = ", ".join(k.upper() for k in provider.env_keys
                            if not env.get(k))
        report.errors.append(f"{provider.label} needs {missing} in .env")
        report.stopped = "not configured"
        return report

    if report.estimated_cost > max_spend:
        report.errors.append(
            f"estimated ${report.estimated_cost:.2f} exceeds the ${max_spend:.2f} "
            f"cap — raise the cap or run fewer queries")
        report.stopped = "over budget"
        return report

    await seed_signal_catalog(state)
    confirmed = await state.confirmed_signal_codes()
    if not confirmed:
        report.errors.append(
            "no signals confirmed — confirm signals first (dashboard → Signals, "
            "or `mariana signals --confirm free`) or discovery has nothing to record")
        report.stopped = "no confirmed signals"
        return report

    report.run_id = await state.start_run(
        "discover", provider=provider_key,
        params={"queries": len(queries), "estimate": report.estimated_cost},
    )

    seen: set[str] = set()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            for i, query in enumerate(queries):
                # The kill switch is read between batches, not once at the
                # top: a long run has to be stoppable while it is running.
                if await state.get_setting("discovery_paused"):
                    report.stopped = "paused"
                    break
                if report.actual_cost > max_spend:
                    report.stopped = "budget reached"
                    break
                if i and provider.key == "osm":
                    await asyncio.sleep(OpenStreetMap.MIN_INTERVAL)

                try:
                    provider.last_cost = 0.0
                    found = await provider.fetch(client, env, query)
                    report.actual_cost += provider.last_cost
                except Exception as e:
                    # A failure is an observation about the run, not a reason
                    # to lose the queries that already succeeded.
                    logger.warning("discover: %s falhou em %r: %s",
                                   provider_key, query.keyword(), e)
                    report.errors.append(f"{query.keyword()}: {e}")
                    continue

                report.found += len(found)
                batch = []
                for biz in found:
                    if is_junk(biz.domain, biz.name):
                        report.junk += 1
                        continue
                    ident = biz.identity()
                    if not ident or ident in seen:
                        continue
                    seen.add(ident)

                    company_id, is_new = await _upsert(state, biz, query)
                    if is_new:
                        report.new_companies += 1
                    else:
                        report.known_companies += 1
                    batch.extend(_observations(biz, company_id, confirmed,
                                               report.run_id))

                # Flush every batch. The observations are the asset; buffering
                # them until some threshold means a run that dies loses them.
                if batch:
                    report.observations += await state.add_observations(
                        batch, run_id=report.run_id)

        await state.finish_run(report.run_id, status="completed",
                               records=report.new_companies + report.known_companies,
                               cost_usd=report.actual_cost)
    except Exception as e:
        logger.exception("discover run failed")
        report.errors.append(str(e))
        await state.finish_run(report.run_id, status="failed",
                               records=report.new_companies,
                               cost_usd=report.actual_cost, error=str(e))
    return report


async def _upsert(state, biz: Business, query: DiscoveryQuery) -> tuple[str, bool]:
    """Record the business, returning (id, was_new)."""
    # Look before inserting, so "already knew this one" is a fact we report
    # rather than something inferred from an insert's return value.
    existing = None
    if biz.domain:
        existing = await state.get_company_by_domain(biz.domain)
    if existing is None and biz.external_id:
        existing = await state.get_company_by_external_id(biz.external_id)
    if existing:
        return existing.id, False

    company = Company(
        name=biz.name,
        domain=biz.domain,
        website=biz.website,
        phone=biz.phone,
        industry=biz.category or query.term,
        location=biz.location or query.location,
        source=f"discover:{biz.provider}",
        source_url=biz.source_url,
        external_id=biz.external_id,
    )
    return await state.add_company(company), True


def _observations(biz: Business, company_id: str, confirmed: set[str],
                  run_id: str) -> list[dict]:
    """Every fact this business gave us, as rows — and only the confirmed ones."""
    rows: list[dict] = []

    def add(code, *, num=None, text="", conf=1.0):
        if code in confirmed:
            rows.append({
                "company_id": company_id, "signal_code": code,
                "collector": "discover", "value_num": num, "value_text": text,
                "confidence": conf, "evidence_url": biz.source_url,
                "run_id": run_id,
            })

    add("FOUND_IN_SERP", text=biz.provider)
    if biz.rank is not None:
        add("SERP_RANK", num=float(biz.rank))
    if biz.has_website is False:
        add("NO_WEBSITE", num=1.0)
    if biz.is_claimed is False:
        add("UNCLAIMED_LISTING", num=1.0)
    if biz.rating is not None:
        add("REVIEW_RATING", num=float(biz.rating))
    if biz.review_count is not None:
        add("REVIEW_COUNT", num=float(biz.review_count))
    return rows


def provider_menu(env: dict | None = None) -> list[dict]:
    """The menu the dashboard renders: what each provider does, and its cost."""
    env = env or {}
    return [
        {
            "key": p.key, "label": p.label, "kind": p.kind, "blurb": p.blurb,
            "cost_note": p.cost_note, "free_tier": p.free_tier,
            "signup_url": p.signup_url, "caveat": p.caveat,
            "env_keys": [k.upper() for k in p.env_keys],
            "configured": p.configured(env),
            "needs_key": bool(p.env_keys),
        }
        for p in PROVIDERS.values()
    ]
