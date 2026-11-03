"""PROFILE collector — what a business is, from three HTTP requests.

Cost: $0. No browser, no model. Homepage + robots.txt + sitemap.xml (+ the
team and careers pages when present), then regex over HTML we already hold.

This is the highest value-per-effort stage in the pipeline: it produces the
signals that actually make an email specific — who their incumbent agency is,
whether they're spending on ads today, what's missing from their site.
"""

import asyncio
import logging
from html import unescape as html_unescape
import random
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger("harvey.collectors.profile")

TIMEOUT = httpx.Timeout(connect=8.0, read=12.0, write=8.0, pool=8.0)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# ── Agency detection ──────────────────────────────────────────────────
# Links that appear in footers but are never the site's agency. Matched as
# substrings against the link host.
BENIGN_HOSTS = (
    # social
    "facebook.", "instagram.", "twitter.", "x.com", "linkedin.", "youtube.",
    "tiktok.", "pinterest.", "yelp.", "nextdoor.", "threads.",
    # maps / profiles
    "google.com/maps", "g.page", "maps.app.goo.gl", "goo.gl", "wa.me",
    "bing.com/maps", "apple.com/maps",
    # financing / payments / reviews
    "greensky", "wellsfargo", "synchrony", "affirm", "klarna", "paypal",
    "stripe.com", "bbb.org", "angi.com", "homeadvisor", "houzz.",
    "trustpilot", "birdeye", "podium.com",
    # accessibility / compliance widgets
    "accessibe", "userway", "audioeye", "termly", "iubenda", "onetrust",
    # infra / CDNs / platforms
    "cloudflare", "godaddy", "wordpress.org", "wix.com", "squarespace.com",
    "shopify.com", "webflow.com", "duda.co", "gtranslate", "jquery",
    "gstatic", "googleapis", "cloudfront", "akamai", "w3.org", "schema.org",
    # industry bodies / certs
    "gaf.com", "owenscorning", "certainteed", "nrca.net", "iko.com",
    "energystar.gov", "osha.gov", "nahb.org",
)

# Credit wording → confidence. Only >= 0.75 is recorded: a wrong incumbent in
# an email is worse than saying nothing at all.
STRONG_CREDIT = re.compile(
    r"\b(powered|website|site|web\s*design|designed|developed|built|created|"
    r"marketing)\s+(by|&)\b", re.I)
DESCRIPTIVE_CREDIT = re.compile(
    r"\b(web\s*design|website\s*design|digital\s*marketing|seo|marketing\s*"
    r"agency|web\s*development)\b", re.I)
RECORD_FLOOR = 0.75

# ── Tech / platform fingerprints (name -> regexes over raw HTML) ──
TECH_FINGERPRINTS: dict[str, tuple[str, ...]] = {
    "WordPress": (r"wp-content/", r"wp-includes/"),
    "Shopify": (r"cdn\.shopify\.com", r"myshopify\.com"),
    "Wix": (r"static\.parastorage\.com",),
    "Squarespace": (r"static1\.squarespace\.com",),
    "Webflow": (r"assets\.website-files\.com", r"data-wf-domain"),
    "Duda": (r"irp\.cdn-website\.com", r"d1\.awsstatic"),
    "GoDaddy Website Builder": (r"img1\.wsimg\.com",),
    "HubSpot": (r"js\.hs-scripts\.com", r"js\.hsforms\.net"),
    "Google Analytics": (r"googletagmanager\.com/gtag", r"google-analytics\.com"),
    "Google Tag Manager": (r"googletagmanager\.com/gtm\.js",),
    "Intercom": (r"widget\.intercom\.io",),
    "Drift": (r"js\.driftt\.com",),
    "Podium": (r"connect\.podium\.com",),
    "Birdeye": (r"birdeye\.com",),
    "Calendly": (r"assets\.calendly\.com",),
    "ServiceTitan": (r"servicetitan",),
    "Jobber": (r"getjobber\.com",),
    "Housecall Pro": (r"housecallpro",),
    "CallRail": (r"cdn\.callrail\.com",),
    "Stripe": (r"js\.stripe\.com",),
}

GOOGLE_ADS = (r"googleadservices\.com", r"gtag/js\?id=AW-", r"google_conversion",
              r"googletagmanager\.com/gtag/js\?id=AW-")
META_PIXEL = (r"connect\.facebook\.net/[^\"']*fbevents\.js", r"fbq\s*\(\s*['\"]init")

VIDEO_EMBEDS = (r"youtube(-nocookie)?\.com/embed/", r"player\.vimeo\.com",
                r"<video\b", r"wistia\.(com|net)", r"vidyard", r"fast\.wistia",
                r"youtu\.be/", r"loom\.com/embed", r"jwplayer", r"vimeo\.com/\d+")
YOUTUBE_CHANNEL = re.compile(
    r'href=["\'](https?://(?:www\.)?youtube\.com/(?:@[\w.\-]+|channel/[\w\-]+|c/[\w\-]+|user/[\w\-]+))',
    re.I)
INSTAGRAM_LINK = re.compile(
    r'href=["\'](https?://(?:www\.)?instagram\.com/(?!p/|reel/|explore/|accounts/)[\w.]+)/?["\'?]',
    re.I)
LINKEDIN_COMPANY_LINK = re.compile(
    r'href=["\'](https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:company|school)/[\w\-%.]+)',
    re.I)

BOOKING_HINTS = (r"calendly\.com", r"acuityscheduling", r"schedulicity",
                 r"squareup\.com/appointments", r"setmore", r"book(ing)?[-_]?now",
                 r"schedule[-_]?(an?[-_])?(appointment|estimate|consultation)",
                 r"housecallpro", r"getjobber\.com", r"servicetitan")

AI_CRAWLERS = ("gptbot", "google-extended", "ccbot", "anthropic-ai", "claudebot",
               "perplexitybot", "bytespider")

TEAM_PATHS = ("/team", "/about", "/about-us", "/our-team", "/staff",
              "/leadership", "/meet-the-team", "/company/team")
CAREERS_PATHS = ("/careers", "/jobs", "/join-us", "/employment", "/hiring",
                 "/about/careers", "/careers/")
CONTACT_PATHS = ("/contact", "/contact-us", "/get-a-quote", "/free-estimate",
                 "/request-estimate", "/quote")

# Words that are never part of a person's name. Without this, headings like
# "Request Service", "Baker History" and "Commercial Services" pass a
# Firstname-Lastname regex and become contacts — the single most common
# failure mode when scraping team pages.
NON_NAME_WORDS = frozenset("""
service services repair repairs roofing roof roofs contractor contracting
commercial residential industrial storm damage restoration installation
history about contact quote quotes estimate estimates free request get call
learn more read view our their your team staff careers jobs home page site
company companies inc llc ltd corp group solutions systems partners
gallery projects reviews testimonials financing warranty insurance claims
maintenance inspection replacement gutters siding windows doors metal shingle
shingles tile flat emergency 24 hour hours today now new best top quality
privacy policy terms conditions sitemap blog news events why choose us
areas served locations location city county state north south east west
español espanol menu skip navigation search close open toggle
""".split())

DECISION_MAKER_TITLES = (
    "owner", "founder", "co-founder", "president", "ceo", "principal",
    "partner", "general manager", "operations manager", "practice manager",
    "office manager", "marketing director", "marketing manager",
    "director of marketing", "vice president", "vp ", "managing director",
)


ROLE_HINT = re.compile(
    r"\b(owner|founder|president|ceo|cfo|coo|cto|principal|partner|manager|"
    r"director|supervisor|superintendent|foreman|estimator|specialist|"
    r"consultant|coordinator|representative|rep|sales|marketing|operations|"
    r"office|project|account|service|technician|installer|inspector|"
    r"vice president|vp|executive|lead|head of|chief)\b", re.I)


def title_looks_like_role(text: str) -> bool:
    """True when the text following a name reads like a job title.

    A name with no role nearby is usually a nav link or a page heading, not
    a person — requiring a role is the cheapest high-precision filter.
    """
    return bool(ROLE_HINT.search(text[:160]))


def _strip_code(html: str) -> str:
    """Remove script/style/comments BEFORE any text regex.

    Skipping this is how you end up with contacts named 'return value instan'
    whose title is CEO — minified JS read as prose.
    """
    html = re.sub(r"(?is)<script\b.*?</script>", " ", html)
    html = re.sub(r"(?is)<style\b.*?</style>", " ", html)
    html = re.sub(r"(?s)<!--.*?-->", " ", html)
    return html


def _text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", _strip_code(html)))


class ProfileCollector:
    """Fetches a business's public pages and emits observations.

    Only signals the user CONFIRMED are collected; everything else is skipped
    even if the data is sitting right there in the HTML.
    """

    def __init__(self, state, confirmed: set[str] | None = None, timeout: float = 12.0):
        self.state = state
        self.confirmed = confirmed if confirmed is not None else set()
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    def wants(self, code: str) -> bool:
        return code in self.confirmed

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=TIMEOUT, follow_redirects=True,
            headers={"User-Agent": random.choice(USER_AGENTS),
                     "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
        )
        return self

    async def __aexit__(self, *exc):
        if self._client:
            await self._client.aclose()

    async def _get(self, url: str) -> str:
        try:
            resp = await self._client.get(url)
        except (httpx.HTTPError, ValueError) as e:
            logger.debug(f"fetch failed {url}: {e}")
            return ""
        if resp.status_code != 200:
            return ""
        ctype = resp.headers.get("content-type", "")
        if "html" not in ctype and "xml" not in ctype and "text" not in ctype:
            return ""
        return resp.text

    async def _resolve_site(self, domain: str) -> tuple[str, str]:
        """Return (working base url, homepage html), or ("", "") if none work.

        Tries https/http and bare/www variants — a plain https guess marks
        plenty of live, real small-business sites "unreachable" simply
        because they never got a TLS cert, or only answer on www.
        """
        for base in (
            f"https://{domain}", f"https://www.{domain}",
            f"http://{domain}", f"http://www.{domain}",
        ):
            html = await self._get(base)
            if html:
                return base, html
        return "", ""

    async def _first_present(self, site: str, paths) -> tuple[str, str]:
        """Return (url, html) for the first path that returns content."""
        for path in paths:
            url = f"{site}{path}"
            html = await self._get(url)
            if html and len(html) > 500:
                return url, html
        return "", ""

    # ── individual detectors ──

    def detect_agency(self, html: str, domain: str) -> tuple[str, float, str] | None:
        """Find the agency credited in the footer. (name, confidence, url)."""
        cleaned = _strip_code(html)
        m = re.search(r"(?is)<footer\b.*?</footer>", cleaned)
        region = m.group(0) if m else cleaned[-12000:]

        best = None
        for link in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', region):
            href, anchor = link.group(1), re.sub(r"(?s)<[^>]+>", " ", link.group(2))
            anchor = re.sub(r"\s+", " ", anchor).strip()
            if not href.startswith("http"):
                continue
            host = (urlparse(href).netloc or "").lower().replace("www.", "")
            if not host or host.endswith(domain) or domain.endswith(host):
                continue
            if any(b in href.lower() or b in host for b in BENIGN_HOSTS):
                continue
            if not anchor or len(anchor) > 80:
                continue

            # Context = the ~120 chars before the link, where credits live.
            start = max(0, link.start() - 120)
            context = re.sub(r"(?s)<[^>]+>", " ", region[start:link.start()])
            blob = f"{context} {anchor}"

            if STRONG_CREDIT.search(blob):
                conf = 0.9
            elif DESCRIPTIVE_CREDIT.search(anchor):
                conf = 0.75
            else:
                conf = 0.35  # a bare link — do not record
            if conf >= RECORD_FLOOR and (best is None or conf > best[1]):
                best = (anchor[:80], conf, href)
        return best

    def detect_tech(self, html: str) -> list[str]:
        found = []
        for name, patterns in TECH_FINGERPRINTS.items():
            if any(re.search(p, html, re.I) for p in patterns):
                found.append(name)
        return sorted(found)

    @staticmethod
    def _any(html: str, patterns) -> bool:
        return any(re.search(p, html, re.I) for p in patterns)

    def detect_people(self, html: str) -> list[dict]:
        """Names + titles from a team page. Conservative on purpose."""
        text_html = _strip_code(html)
        people, seen = [], set()
        # Name in a heading, title in the nearby text.
        for m in re.finditer(
            r"(?is)<(h[1-5]|strong|b)[^>]*>\s*([A-Z][a-z'\-]+(?:\s+[A-Z]\.?)?\s+"
            r"[A-Z][a-zA-Z'\-]+)\s*</\1>(?=(.{0,220}))", text_html
        ):
            # NOTE the lookahead above: capturing the trailing context normally
            # would CONSUME it, so finditer would skip every person whose entry
            # fell inside the previous person's 220-char window.
            name = re.sub(r"\s+", " ", m.group(2)).strip()
            # Bound the context at the NEXT heading, in raw HTML, before
            # stripping tags — otherwise one member's role bleeds into the
            # next member's entry.
            raw_after = m.group(3)
            nxt = re.search(r"(?i)<(h[1-5]|strong|b)\b", raw_after)
            if nxt:
                raw_after = raw_after[: nxt.start()]
            after = html_unescape(re.sub(r"(?s)<[^>]+>", " ", raw_after))
            after = re.sub(r"\s+", " ", after).strip()
            if name.lower() in seen or len(name) > 45:
                continue
            # Reject obvious non-names
            if re.search(r"\d|@|\bthe\b|\bour\b|\bwe\b", name, re.I):
                continue
            # Reject headings that merely LOOK like names. Every token must be
            # plausibly a name part; one business word disqualifies the whole
            # match ("Request Service", "Baker History", "Commercial Services").
            tokens = [t.strip(".,'-").lower() for t in name.split()]
            if any(t in NON_NAME_WORDS for t in tokens):
                continue
            # A real contact needs a title that reads like a role; a bare
            # heading with no role text is almost always navigation.
            if not title_looks_like_role(after):
                continue
            title = ""
            low = after.lower()
            for t in DECISION_MAKER_TITLES:
                if t in low:
                    idx = low.index(t)
                    title = after[idx:idx + 60].strip(" ,.|-—·")
                    break
            if not title:
                m2 = re.match(r"[\s,|\-–—·]*([A-Za-z][A-Za-z /&'\-]{2,45})", after)
                if m2:
                    title = m2.group(1).strip()
            seen.add(name.lower())
            parts = name.split()
            people.append({
                "first_name": parts[0], "last_name": " ".join(parts[1:]),
                "title": title[:80],
                "is_decision_maker": any(t in title.lower() for t in DECISION_MAKER_TITLES),
            })
            if len(people) >= 12:
                break
        return people

    # ── the stage itself ──

    async def profile_company(self, company_id: str, domain: str) -> list[dict]:
        """Collect every confirmed profile signal for one business."""
        obs: list[dict] = []
        domain = domain.lower().replace("www.", "").strip("/")

        def add(code, *, num=None, text="", conf=1.0, url=""):
            if not self.wants(code):
                return
            obs.append({
                "signal_code": code, "company_id": company_id, "collector": "profile",
                "value_num": num, "value_text": text, "confidence": conf,
                "evidence_url": url or site,
            })

        site, home = await self._resolve_site(domain)
        if not home:
            # A failure IS an observation — silent failures look like clean results.
            logger.info(f"profile: {domain} unreachable")
            return obs

        # Ads (they are spending TODAY — the strongest budget signal here)
        add("RUNNING_GOOGLE_ADS", num=1 if self._any(home, GOOGLE_ADS) else 0)
        add("RUNNING_META_ADS", num=1 if self._any(home, META_PIXEL) else 0)

        # Platform + tooling
        tech = self.detect_tech(home)
        if tech:
            add("TECH_STACK", text=", ".join(tech))

        # Structured data gap
        has_schema = bool(re.search(r'application/ld\+json', home, re.I)
                          and re.search(r'"@type"', home))
        add("NO_SCHEMA_MARKUP", num=0 if has_schema else 1)

        # Booking gap
        add("NO_ONLINE_BOOKING", num=0 if self._any(home, BOOKING_HINTS) else 1)

        # Video presence: the audiovisual buyer signals
        add("NO_VIDEO_ON_SITE", num=0 if self._any(home, VIDEO_EMBEDS) else 1)
        for code, pattern in (("HAS_YOUTUBE_CHANNEL", YOUTUBE_CHANNEL),
                              ("INSTAGRAM_PROFILE", INSTAGRAM_LINK),
                              ("LINKEDIN_COMPANY", LINKEDIN_COMPANY_LINK)):
            m = pattern.search(home)
            if m:
                add(code, text=m.group(1).rstrip("/"), url=m.group(1))

        # Incumbent agency — the compounding signal
        agency = self.detect_agency(home, domain)
        if agency:
            add("INCUMBENT_AGENCY", text=agency[0], conf=agency[1], url=agency[2])

        # robots.txt → AI crawler policy
        if self.wants("BLOCKS_AI_CRAWLERS"):
            robots = (await self._get(f"{site}/robots.txt")).lower()
            blocked = any(
                re.search(rf"user-agent:\s*{re.escape(bot)}[\s\S]{{0,200}}?disallow:\s*/",
                          robots)
                for bot in AI_CRAWLERS
            )
            add("BLOCKS_AI_CRAWLERS", num=1 if blocked else 0,
                url=f"{site}/robots.txt")

        # sitemap.xml → size + content freshness
        if self.wants("SITE_PAGE_COUNT") or self.wants("BLOG_STALE"):
            sm = await self._get(f"{site}/sitemap.xml")
            if sm:
                locs = re.findall(r"<loc>\s*([^<]+)\s*</loc>", sm)
                if self.wants("SITE_PAGE_COUNT") and locs:
                    add("SITE_PAGE_COUNT", num=len(locs), url=f"{site}/sitemap.xml")
                if self.wants("BLOG_STALE"):
                    dates = re.findall(r"<lastmod>\s*(\d{4}-\d{2}-\d{2})", sm)
                    if dates:
                        newest = max(dates)
                        try:
                            age = (datetime.now(timezone.utc).date()
                                   - datetime.strptime(newest, "%Y-%m-%d").date()).days
                            add("BLOG_STALE", num=age, text=f"newest content {newest}",
                                url=f"{site}/sitemap.xml")
                        except ValueError:
                            pass

        # contact form — reaches the business without needing an email at all
        if self.wants("CONTACT_FORM_URL"):
            if re.search(r"(?is)<form\b", _strip_code(home)):
                add("CONTACT_FORM_URL", text=site, url=site)
            else:
                curl, chtml = await self._first_present(site, CONTACT_PATHS)
                if chtml and re.search(r"(?is)<form\b", _strip_code(chtml)):
                    add("CONTACT_FORM_URL", text=curl, url=curl)

        # careers page → hiring intent
        if self.wants("HIRING_ROLE"):
            curl, chtml = await self._first_present(site, CAREERS_PATHS)
            if chtml:
                roles = []
                for m in re.finditer(
                    r"(?is)<(h[2-5]|a|li)[^>]*>\s*([^<]{6,70})\s*</\1>", _strip_code(chtml)
                ):
                    t = re.sub(r"\s+", " ", m.group(2)).strip()
                    if re.search(r"\b(hiring|apply|position|opening|wanted|"
                                 r"technician|installer|sales|manager|foreman|"
                                 r"estimator|crew|representative)\b", t, re.I):
                        if t.lower() not in [r.lower() for r in roles]:
                            roles.append(t)
                    if len(roles) >= 3:
                        break
                for r in roles:
                    add("HIRING_ROLE", text=r, url=curl)

        # team page → people
        if self.wants("CONTACT_FOUND") or self.wants("DECISION_MAKER_TITLE"):
            turl, thtml = await self._first_present(site, TEAM_PATHS)
            if thtml:
                for person in self.detect_people(thtml):
                    label = f"{person['first_name']} {person['last_name']}"
                    add("CONTACT_FOUND",
                        text=f"{label} — {person['title']}" if person["title"] else label,
                        url=turl)
                    if person["is_decision_maker"]:
                        add("DECISION_MAKER_TITLE",
                            text=f"{label} — {person['title']}", url=turl)

        return obs

    async def _mark_checked(self, company_id: str):
        try:
            await self.state.mark_company_profiled(company_id)
        except Exception as e:
            logger.debug(f"mark_company_profiled failed for {company_id}: {e}")

    async def run(self, companies: list[dict], run_id: str = "") -> int:
        """Profile many businesses, flushing observations after each one.

        Flush-per-item is deliberate: the observations are the asset, and a
        long run that dies must not take them with it.
        """
        total = 0
        for company in companies:
            domain = (company.get("domain") or "").strip()
            if not domain:
                continue
            try:
                obs = await self.profile_company(company["id"], domain)
            except Exception as e:
                logger.warning(f"falhou a leitura de {domain}: {e}")
                await self._mark_checked(company["id"])
                continue
            # Marked regardless of outcome — an unreachable site still counts
            # as checked, or the same handful gets retried every cycle
            # forever instead of rotating through the rest of the backlog.
            await self._mark_checked(company["id"])
            if obs:
                total += await self.state.add_observations(obs, run_id=run_id)
                logger.info(f"profile: {domain} → {len(obs)} observation(s)")
            await asyncio.sleep(random.uniform(0.4, 1.2))
        return total


async def profile_companies(state, companies: list[dict]) -> tuple[int, str]:
    """Convenience entry point: opens a run, profiles, closes the run."""
    from harvey.signals import seed_signal_catalog
    await seed_signal_catalog(state)
    confirmed = await state.confirmed_signal_codes()
    if not confirmed:
        logger.warning(
            "perfil: nenhum sinal confirmado ainda; confirme os sinais antes "
            "(nada é coletado até você escolher o que importa)."
        )
        return 0, ""
    run_id = await state.start_run("profile", provider="http")
    try:
        async with ProfileCollector(state, confirmed) as collector:
            n = await collector.run(companies, run_id=run_id)
        await state.finish_run(run_id, records=n, cost_usd=0.0)
        return n, run_id
    except Exception as e:
        await state.finish_run(run_id, status="failed", error=str(e))
        raise
