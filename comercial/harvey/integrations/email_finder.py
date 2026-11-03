"""Email discovery — pattern-first, verify-once, honest about confidence.

Raw SMTP probing is largely dead against Google Workspace and Microsoft
365 (which host most B2B mail): they tarpit probers or accept every
recipient and bounce later. So instead of brute-forcing every name
permutation, this pipeline:

1. Classifies the domain by its MX host (google / microsoft / gateway / other).
2. Derives the domain's email PATTERN once — from cache, then Hunter's
   free domain-search, then known addresses scraped off the site, else a
   sensible default — collapsing N guesses to one candidate.
3. Verifies that single candidate through the best available channel for
   the domain type: a real-verdict API (Reoon, ZeroBounce for the big
   providers), Hunter, or SMTP for small self-hosted servers.
4. Detects catch-all domains and buckets them as ``risky`` instead of
   pretending they're verified.

Every result carries an honest status: verified / risky / guess / invalid.
Only ``verified`` (and optionally ``risky``) should ever be emailed.
"""

import asyncio
import logging
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import dns.resolver
import aiosmtplib
import httpx

logger = logging.getLogger("harvey.email_finder")

# Cache MX host + type per domain to avoid repeated lookups.
_mx_cache: dict[str, Optional[str]] = {}

API_TIMEOUT = httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)

# Named email-format patterns → builder. {f}=first, {l}=last, {fi}=first initial,
# {li}=last initial. Ordered by real-world prevalence for the default fallback.
PATTERN_BUILDERS = {
    "{f}.{l}": lambda f, l: f"{f}.{l}",
    "{f}{l}": lambda f, l: f"{f}{l}",
    "{fi}{l}": lambda f, l: f"{f[0]}{l}",
    "{f}": lambda f, l: f"{f}",
    "{fi}.{l}": lambda f, l: f"{f[0]}.{l}",
    "{f}_{l}": lambda f, l: f"{f}_{l}",
    "{l}": lambda f, l: f"{l}",
    "{l}.{f}": lambda f, l: f"{l}.{f}",
    "{f}-{l}": lambda f, l: f"{f}-{l}",
    "{l}{fi}": lambda f, l: f"{l}{f[0]}",
}
DEFAULT_PATTERN = "{f}.{l}"


@dataclass
class EmailResult:
    """Outcome of an email lookup. status is the source of truth."""
    email: str
    status: str          # verified / risky / guess / invalid
    pattern: str = ""
    mx_type: str = ""

    @property
    def verified(self) -> bool:
        return self.status == "verified"

    @property
    def sendable(self) -> bool:
        """Safe to send cold: confirmed mailbox only (risky is opt-in elsewhere)."""
        return self.status == "verified"


def _clean_domain(domain: str) -> str:
    domain = (domain or "").strip().lower()
    domain = re.sub(r"^https?://", "", domain)
    domain = domain.split("/")[0].split("?")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _clean_name_part(value: str) -> str:
    return re.sub(r"[^a-z]", "", (value or "").lower())


def build_email(pattern: str, first: str, last: str, domain: str) -> str:
    """Render a named pattern into an address, or '' if it can't be built."""
    first = _clean_name_part(first)
    last = _clean_name_part(last)
    domain = _clean_domain(domain)
    if not first or not last or not domain:
        return ""
    builder = PATTERN_BUILDERS.get(pattern)
    if not builder:
        return ""
    try:
        local = builder(first, last)
    except IndexError:
        return ""
    return f"{local}@{domain}" if local else ""


def generate_patterns(first_name: str, last_name: str, domain: str) -> list[str]:
    """All candidate addresses for a person, most-likely first (deduped)."""
    out = []
    for pattern in PATTERN_BUILDERS:
        email = build_email(pattern, first_name, last_name, domain)
        if email:
            out.append(email)
    return list(dict.fromkeys(out))


# ── MX classification ──

def classify_mx(mx_host: str) -> str:
    """Bucket a domain by its mail host — decides the verification strategy."""
    if not mx_host:
        return "none"
    h = mx_host.lower()
    if "google" in h or "googlemail" in h or "aspmx.l" in h:
        return "google"
    if "outlook" in h or "protection.outlook" in h or "microsoft" in h:
        return "microsoft"
    if any(g in h for g in ("pphosted", "mimecast", "barracuda", "proofpoint",
                            "messagelabs", "cisco", "fortinet", "trendmicro")):
        return "gateway"
    return "other"


async def get_mx_host(domain: str) -> Optional[str]:
    """Primary MX host for a domain (cached; None on failure)."""
    domain = _clean_domain(domain)
    if not domain:
        return None
    if domain in _mx_cache:
        return _mx_cache[domain]
    try:
        loop = asyncio.get_event_loop()
        answers = await loop.run_in_executor(
            None, lambda: dns.resolver.resolve(domain, "MX")
        )
        records = sorted(answers, key=lambda x: x.preference)
        mx_host = str(records[0].exchange).rstrip(".") if records else None
        _mx_cache[domain] = mx_host or None
        return _mx_cache[domain]
    except Exception as e:
        logger.debug(f"MX lookup failed for {domain}: {e}")
        _mx_cache[domain] = None
        return None


# ── Pattern derivation ──

def infer_pattern_from_email(email: str, first: str, last: str) -> Optional[str]:
    """Given one known address, work out which named pattern produced it."""
    email = (email or "").strip().lower()
    if "@" not in email:
        return None
    local = email.split("@", 1)[0]
    first = _clean_name_part(first)
    last = _clean_name_part(last)
    if not first or not last:
        return None
    for pattern, builder in PATTERN_BUILDERS.items():
        try:
            if builder(first, last) == local:
                return pattern
        except IndexError:
            continue
    return None


async def _hunter_domain_pattern(domain: str, api_key: str) -> Optional[tuple[str, float]]:
    """Hunter's free domain-search returns the org's dominant email pattern.

    Hunter formats it with {first}/{last}/{f} tokens; translate to ours.
    Returns (named_pattern, confidence 0-1) or None.
    """
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": api_key, "limit": 1},
            )
    except httpx.HTTPError as e:
        logger.debug(f"Hunter domain-search failed for {domain}: {e}")
        return None
    if resp.status_code != 200:
        return None
    try:
        data = (resp.json() or {}).get("data") or {}
    except ValueError:
        return None

    hunter_pattern = data.get("pattern") or ""
    translated = _translate_hunter_pattern(hunter_pattern)
    if translated:
        # Hunter's presence of a pattern is a strong signal; scale by how
        # many known emails back it (capped).
        n = len(data.get("emails") or [])
        confidence = min(0.7 + 0.05 * n, 0.95)
        return translated, confidence
    return None


def _translate_hunter_pattern(hunter_pattern: str) -> Optional[str]:
    """Map Hunter's {first}.{last}-style tokens to our named patterns."""
    if not hunter_pattern:
        return None
    p = hunter_pattern.lower().strip()
    mapping = {
        "{first}.{last}": "{f}.{l}",
        "{first}{last}": "{f}{l}",
        "{f}{last}": "{fi}{l}",
        "{first}": "{f}",
        "{f}.{last}": "{fi}.{l}",
        "{first}_{last}": "{f}_{l}",
        "{last}": "{l}",
        "{last}.{first}": "{l}.{f}",
        "{first}-{last}": "{f}-{l}",
        "{last}{f}": "{l}{fi}",
    }
    return mapping.get(p)


def _hunter_api_key() -> str:
    return os.getenv("HUNTER_API_KEY", "").strip()


# Hunter's free tier is 25 domain-searches/month for the whole account, and
# every call spends one no matter how many people it returns. Paid plans set
# HUNTER_MONTHLY_SEARCHES to their own allowance. Every domain-search call in
# Mariana draws from this one counter, so the pattern lookup and Scout's
# named-contact strategy can't each assume they have the full quota.
HUNTER_FREE_MONTHLY_SEARCHES = 25


def _hunter_monthly_cap() -> int:
    raw = os.getenv("HUNTER_MONTHLY_SEARCHES", "").strip()
    if not raw:
        return HUNTER_FREE_MONTHLY_SEARCHES
    try:
        return max(int(raw), 0)
    except ValueError:
        return HUNTER_FREE_MONTHLY_SEARCHES


def _hunter_usage_key() -> str:
    return f"hunter_domain_search_count:{datetime.now(timezone.utc):%Y-%m}"


async def hunter_searches_remaining(state) -> int:
    """Domain-searches left this calendar month (UTC). Without a state
    store there is nothing to count against, so the full cap is reported."""
    cap = _hunter_monthly_cap()
    if state is None:
        return cap
    try:
        used = int(await state.get_setting(_hunter_usage_key(), "0") or "0")
    except (ValueError, TypeError):
        used = 0
    except Exception as e:
        logger.debug(f"Hunter usage read failed: {e}")
        return 0
    return max(cap - used, 0)


async def record_hunter_search(state) -> None:
    """Count one domain-search against this month's budget. Called before
    the request, so a call that fails mid-flight is still counted."""
    if state is None:
        return
    try:
        await state.increment_setting(_hunter_usage_key())
    except Exception as e:
        logger.debug(f"Hunter usage write failed: {e}")


async def hunter_domain_people(
    domain: str, api_key: str, limit: int = 10
) -> Optional[list[dict]]:
    """Hunter's domain-search doesn't just give a pattern — it lists real
    named people it already has on file for the domain (name, title, email,
    and its own verification verdict). Returns the raw ``emails`` list, or
    None on any failure (network, non-200, bad JSON, or no data).

    Costs one domain-search credit per call regardless of ``limit``, so
    callers must check hunter_searches_remaining() and record_hunter_search()
    first rather than rely on this failing gracefully to protect the quota.
    """
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": api_key, "limit": limit},
            )
    except httpx.HTTPError as e:
        logger.debug(f"Hunter domain-search failed for {domain}: {e}")
        return None
    if resp.status_code != 200:
        return None
    try:
        data = (resp.json() or {}).get("data") or {}
    except ValueError:
        return None
    emails = data.get("emails")
    return emails if isinstance(emails, list) else None


async def derive_pattern(
    domain: str,
    known_emails: Optional[list[tuple[str, str, str]]] = None,
    state=None,
) -> tuple[str, str, float]:
    """Determine a domain's email pattern. Returns (pattern, source, confidence).

    Order: DB cache → a known address for this domain (scraped mailto,
    GitHub, etc.) → Hunter domain-search → default. This is the step that
    collapses six guesses to one and is where free tiers stretch furthest.
    """
    domain = _clean_domain(domain)

    if state is not None:
        try:
            cached = await state.get_email_pattern(domain)
            if cached and cached.get("pattern"):
                return cached["pattern"], cached.get("source", "cache"), cached.get("confidence", 0.6)
        except Exception as e:
            logger.debug(f"Pattern cache read failed for {domain}: {e}")

    # A confirmed address for this domain reveals the pattern for free.
    for email, first, last in known_emails or []:
        if email.split("@")[-1].lower() == domain:
            inferred = infer_pattern_from_email(email, first, last)
            if inferred:
                return inferred, "known_email", 0.9

    key = _hunter_api_key()
    if key and await hunter_searches_remaining(state) > 0:
        await record_hunter_search(state)
        result = await _hunter_domain_pattern(domain, key)
        if result:
            return result[0], "hunter_domain_search", result[1]

    return DEFAULT_PATTERN, "default", 0.3


# ── Verification channels ──

async def verify_reoon(email: str, api_key: str) -> Optional[dict]:
    """Reoon email-verifier — generous free tier, good catch-all flagging.

    Returns {'status': ..., 'catch_all': bool} or None if unavailable.
    Reoon 'status' values: valid / invalid / disabled / catch_all / unknown.
    """
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(
                "https://emailverifier.reoon.com/api/v1/verify",
                params={"email": email, "key": api_key, "mode": "power"},
            )
    except httpx.HTTPError as e:
        logger.debug(f"Reoon request failed for {email}: {e}")
        return None
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    status = str(data.get("status") or "").lower()
    is_catch_all = bool(data.get("is_catch_all") or status == "catch_all")
    return {"status": status, "catch_all": is_catch_all}


async def verify_zerobounce(email: str, api_key: str) -> Optional[dict]:
    """ZeroBounce — its 2026 engine is the reliable one for M365/Workspace catch-alls."""
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(
                "https://api.zerobounce.net/v2/validate",
                params={"email": email, "api_key": api_key},
            )
    except httpx.HTTPError as e:
        logger.debug(f"ZeroBounce request failed for {email}: {e}")
        return None
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    status = str(data.get("status") or "").lower()
    sub = str(data.get("sub_status") or "").lower()
    return {"status": status, "catch_all": sub == "catch-all" or status == "catch-all"}


async def verify_hunter(email: str, api_key: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": api_key},
            )
    except httpx.HTTPError as e:
        logger.debug(f"Hunter verify failed for {email}: {e}")
        return None
    if resp.status_code != 200:
        return None
    try:
        data = (resp.json() or {}).get("data") or {}
    except ValueError:
        return None
    status = str(data.get("status") or data.get("result") or "").lower()
    return {"status": status, "catch_all": bool(data.get("accept_all"))}


async def verify_email_smtp(email: str) -> Optional[bool]:
    """SMTP RCPT check — only trustworthy for small, self-hosted mail servers.

    Returns True (accepted), False (rejected), or None (couldn't tell).
    Port 25 is blocked on most cloud hosts, so this frequently returns None.
    """
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1]
    mx_host = await get_mx_host(domain)
    if not mx_host:
        return None
    smtp = aiosmtplib.SMTP(hostname=mx_host, port=25, timeout=10)
    try:
        await smtp.connect()
        await smtp.ehlo()
        await smtp.mail("verify@example.com")
        code, _ = await smtp.rcpt(email)
        if code == 250:
            return True
        if code in (550, 551, 553):
            return False
        return None
    except Exception as e:
        logger.debug(f"SMTP verification failed for {email}: {e}")
        return None
    finally:
        try:
            await smtp.quit()
        except Exception:
            pass


async def detect_catch_all(domain: str) -> Optional[bool]:
    """Probe a definitely-fake address; if accepted, the domain is catch-all.

    Only works where SMTP probing works at all (small hosts). Returns None
    when we can't tell.
    """
    fake = f"zz-no-such-user-{random.randint(10000, 99999)}@{_clean_domain(domain)}"
    result = await verify_email_smtp(fake)
    if result is True:
        return True   # accepted a fake address → catch-all
    if result is False:
        return False  # rejected a fake address → not catch-all
    return None


def _status_from_verdict(verdict: dict) -> Optional[str]:
    """Map a provider verdict dict to our status, or None if inconclusive."""
    if verdict.get("catch_all"):
        return "risky"
    status = verdict.get("status", "")
    if status in ("valid", "deliverable"):
        return "verified"
    if status in ("invalid", "undeliverable", "disabled"):
        return "invalid"
    if status in ("catch_all", "catch-all", "accept_all"):
        return "risky"
    return None  # unknown / risky-unknown — inconclusive


async def _verify_candidate(email: str, mx_type: str, env) -> tuple[Optional[str], bool]:
    """Run the best available verifier for this domain type.

    Returns (status_or_None, catch_all_seen). Order is chosen so scarce
    paid-ish credits are spent only where they actually resolve the domain.
    """
    reoon_key = getattr(env, "reoon_api_key", "") if env else ""
    zerobounce_key = getattr(env, "zerobounce_api_key", "") if env else ""
    hunter_key = _hunter_api_key()

    catch_all_seen = False

    # Big providers: ZeroBounce first (its engine cracks their catch-alls),
    # then Reoon, then Hunter. SMTP is useless/misleading here.
    if mx_type in ("google", "microsoft", "gateway"):
        channels = []
        if zerobounce_key:
            channels.append(lambda: verify_zerobounce(email, zerobounce_key))
        if reoon_key:
            channels.append(lambda: verify_reoon(email, reoon_key))
        if hunter_key:
            channels.append(lambda: verify_hunter(email, hunter_key))
        for channel in channels:
            verdict = await channel()
            if verdict is None:
                continue
            if verdict.get("catch_all"):
                catch_all_seen = True
            status = _status_from_verdict(verdict)
            if status is not None:
                return status, catch_all_seen
        return None, catch_all_seen

    # Small / self-hosted: Reoon → SMTP (still works here) → Hunter.
    if reoon_key:
        verdict = await verify_reoon(email, reoon_key)
        if verdict:
            if verdict.get("catch_all"):
                catch_all_seen = True
            status = _status_from_verdict(verdict)
            if status is not None:
                return status, catch_all_seen

    smtp = await verify_email_smtp(email)
    if smtp is True:
        # Confirm it's not just a catch-all before trusting "verified".
        if await detect_catch_all(email.split("@")[1]) is True:
            return "risky", True
        return "verified", catch_all_seen
    if smtp is False:
        return "invalid", catch_all_seen

    if hunter_key:
        verdict = await verify_hunter(email, hunter_key)
        if verdict:
            if verdict.get("catch_all"):
                catch_all_seen = True
            status = _status_from_verdict(verdict)
            if status is not None:
                return status, catch_all_seen

    return None, catch_all_seen


# ── Top-level entry point ──

async def find_email(
    first_name: str,
    last_name: str,
    domain: str,
    verify: bool = True,
    env=None,
    state=None,
    known_emails: Optional[list[tuple[str, str, str]]] = None,
) -> EmailResult:
    """Find and honestly grade one email for a person at a company.

    Returns an EmailResult whose ``status`` is verified / risky / guess /
    invalid. When ``verify`` is False (or no verifier is configured), the
    best pattern guess is returned as ``guess`` — never as verified.
    """
    domain = _clean_domain(domain)
    if not (first_name and last_name and domain):
        return EmailResult(email="", status="invalid")

    mx_host = await get_mx_host(domain)
    if not mx_host:
        # No MX → cannot receive mail at all.
        guess = build_email(DEFAULT_PATTERN, first_name, last_name, domain)
        return EmailResult(email=guess, status="invalid", mx_type="none")

    mx_type = classify_mx(mx_host)

    pattern, source, confidence = await derive_pattern(
        domain, known_emails=known_emails, state=state
    )
    candidate = build_email(pattern, first_name, last_name, domain)
    if not candidate:
        candidate = build_email(DEFAULT_PATTERN, first_name, last_name, domain)
        pattern = DEFAULT_PATTERN

    if state is not None:
        try:
            await state.save_email_pattern(
                domain, pattern=pattern, source=source,
                confidence=confidence, mx_type=mx_type,
            )
        except Exception as e:
            logger.debug(f"Pattern cache write failed for {domain}: {e}")

    if not verify:
        return EmailResult(email=candidate, status="guess", pattern=pattern, mx_type=mx_type)

    status, catch_all = await _verify_candidate(candidate, mx_type, env)

    if catch_all and state is not None:
        try:
            await state.save_email_pattern(domain, mx_type=mx_type, is_catch_all=1)
        except Exception:
            pass

    if status is None:
        # Verification couldn't decide — an honest guess, never "verified".
        status = "guess"

    logger.info(f"Email de {first_name} {last_name}@{domain}: {candidate} [{status}]")
    return EmailResult(email=candidate, status=status, pattern=pattern, mx_type=mx_type)
