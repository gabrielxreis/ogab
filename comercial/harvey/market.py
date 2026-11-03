"""Where a prospect is: the country decides the language, the market the channels.

Language: every message is written in the language of the country where the
company is (Brazil → Brazilian Portuguese, Mexico/Spain/Argentina → Spanish,
France → French, USA/UK → English...).

Channels: Brazil = email + WhatsApp; anywhere else = email + LinkedIn
(+ Instagram when the business has one).

The country comes from the strongest evidence available, in order: the
phone's country code, the domain's country ending (.br, .com.mx, .es, .fr...),
then the location text. No evidence falls back to the persona's language.

`detect` / `for_prospect` return a `Market`: a string equal to BR or INTL (so
existing `== market.BR` checks keep working) that also carries `.country`.
"""

from __future__ import annotations

import re
import unicodedata

BR = "BR"
INTL = "INTL"


class Market(str):
    """'BR' or 'INTL', plus the ISO country code when it is known."""

    country: str = ""

    def __new__(cls, value: str, country: str = ""):
        obj = super().__new__(cls, value)
        obj.country = country
        return obj


# ── country → language ──

LANGUAGE_BY_COUNTRY = {
    "BR": "pt-BR", "PT": "pt-PT", "AO": "pt-PT", "MZ": "pt-PT",
    "ES": "es", "MX": "es", "AR": "es", "CL": "es", "CO": "es", "PE": "es",
    "UY": "es", "PY": "es", "BO": "es", "EC": "es", "VE": "es", "CR": "es",
    "PA": "es", "GT": "es", "SV": "es", "HN": "es", "NI": "es", "CU": "es",
    "DO": "es", "PR": "es",
    "FR": "fr", "BE": "fr", "LU": "fr", "MC": "fr",
    "DE": "de", "AT": "de", "CH": "de",
    "IT": "it", "NL": "nl", "PL": "pl", "SE": "sv", "NO": "no", "DK": "da",
    "JP": "ja", "KR": "ko",
    "US": "en", "GB": "en", "IE": "en", "CA": "en", "AU": "en", "NZ": "en",
    "ZA": "en", "IN": "en", "SG": "en", "AE": "en", "IL": "en",
}

LANGUAGE_NAMES = {
    "pt-BR": "Brazilian Portuguese (português do Brasil)",
    "pt-PT": "European Portuguese (português de Portugal)",
    "es": "Spanish (español)",
    "fr": "French (français)",
    "de": "German (Deutsch)",
    "it": "Italian (italiano)",
    "nl": "Dutch (Nederlands)",
    "pl": "Polish (polski)",
    "sv": "Swedish (svenska)",
    "no": "Norwegian (norsk)",
    "da": "Danish (dansk)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "en": "English",
}

COUNTRY_NAMES = {
    "BR": "Brasil", "PT": "Portugal", "ES": "Espanha", "MX": "México",
    "AR": "Argentina", "CL": "Chile", "CO": "Colômbia", "PE": "Peru",
    "UY": "Uruguai", "PY": "Paraguai", "BO": "Bolívia", "EC": "Equador",
    "VE": "Venezuela", "CR": "Costa Rica", "PA": "Panamá", "GT": "Guatemala",
    "DO": "República Dominicana", "PR": "Porto Rico", "FR": "França",
    "BE": "Bélgica", "DE": "Alemanha", "AT": "Áustria", "CH": "Suíça",
    "IT": "Itália", "NL": "Holanda", "US": "EUA", "GB": "Reino Unido",
    "IE": "Irlanda", "CA": "Canadá", "AU": "Austrália", "NZ": "Nova Zelândia",
    "ZA": "África do Sul", "JP": "Japão", "AE": "Emirados Árabes",
}

# ── evidence ──

# Calling codes, longest first so 598 wins over 59 and 1 is checked last.
_CALLING_CODES = {
    "598": "UY", "595": "PY", "591": "BO", "593": "EC", "506": "CR", "507": "PA",
    "502": "GT", "503": "SV", "504": "HN", "505": "NI", "351": "PT", "353": "IE",
    "352": "LU", "377": "MC", "971": "AE", "972": "IL", "244": "AO", "258": "MZ",
    "55": "BR", "52": "MX", "54": "AR", "56": "CL", "57": "CO", "51": "PE",
    "58": "VE", "53": "CU", "34": "ES", "33": "FR", "49": "DE", "43": "AT",
    "41": "CH", "39": "IT", "44": "GB", "31": "NL", "32": "BE", "48": "PL",
    "46": "SE", "47": "NO", "45": "DK", "61": "AU", "64": "NZ", "27": "ZA",
    "81": "JP", "82": "KR", "91": "IN", "65": "SG",
    "1": "US",
}

_TLDS = {
    "br": "BR", "pt": "PT", "es": "ES", "mx": "MX", "ar": "AR", "cl": "CL",
    "pe": "PE", "uy": "UY", "py": "PY", "bo": "BO", "ec": "EC", "ve": "VE",
    "cr": "CR", "pa": "PA", "gt": "GT", "do": "DO", "fr": "FR", "be": "BE",
    "de": "DE", "at": "AT", "ch": "CH", "it": "IT", "nl": "NL", "uk": "GB",
    "ie": "IE", "ca": "CA", "au": "AU", "nz": "NZ", "za": "ZA", "pl": "PL",
    "se": "SE", "no": "NO", "dk": "DK", "jp": "JP", "kr": "KR", "lu": "LU",
}

_US_STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS "
              "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV "
              "WI WY DC").split()
_BR_STATES = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()

_LOCATION_WORDS = [
    ("BR", r"brasil|brazil|rio de janeiro|sao paulo|belo horizonte|brasilia|curitiba|"
           r"porto alegre|salvador|recife|fortaleza|goiania|niteroi|campinas|"
           r"florianopolis|vitoria|manaus|belem"),
    ("PT", r"portugal|lisboa|lisbon|porto, portugal|braga|coimbra"),
    ("ES", r"espanha|spain|espana|madrid|barcelona|valencia|sevilla|malaga|bilbao"),
    ("MX", r"mexico|cdmx|ciudad de mexico|guadalajara|monterrey|cancun|puebla|tijuana"),
    ("AR", r"argentina|buenos aires|cordoba, ar|rosario|mendoza"),
    ("CL", r"chile|santiago de chile|valparaiso"),
    ("CO", r"colombia|bogota|medellin|cali, co|cartagena"),
    ("PE", r"peru|lima, pe|cusco"),
    ("UY", r"uruguay|uruguai|montevideo|montevideu|punta del este"),
    ("PY", r"paraguay|paraguai|asuncion"),
    ("FR", r"france|franca|paris|lyon|marseille|nice, fr|bordeaux|toulouse"),
    ("DE", r"germany|alemanha|deutschland|berlin|munich|munchen|hamburg|frankfurt|cologne|koln"),
    ("IT", r"italy|italia|roma|rome|milano|milan|firenze|florence|napoli|venezia"),
    ("NL", r"netherlands|holanda|amsterdam|rotterdam"),
    ("GB", r"united kingdom|reino unido|england|inglaterra|london|londres|manchester|"
           r"liverpool|scotland|edinburgh"),
    ("IE", r"ireland|irlanda|dublin"),
    ("CA", r"canada|toronto|vancouver|montreal|calgary|ottawa"),
    ("AU", r"australia|sydney|melbourne|brisbane|perth"),
    ("AE", r"dubai|abu dhabi|emirados|united arab emirates"),
    ("US", r"united states|estados unidos|\busa\b|new york|los angeles|miami|orlando|"
           r"chicago|houston|dallas|austin|atlanta|boston|las vegas|san francisco|"
           r"seattle|nashville|baltimore|denver|phoenix|philadelphia|san diego"),
]


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def country_from_phone(phone: str) -> str:
    raw = (phone or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    international = raw.startswith("+") or digits.startswith("00")
    digits = digits.lstrip("0") if digits.startswith("00") else digits
    if not international:
        # Without +/00 only an unmistakable Brazilian number counts.
        return "BR" if digits.startswith("55") and len(digits) >= 12 else ""
    for code in sorted(_CALLING_CODES, key=len, reverse=True):
        if digits.startswith(code):
            return _CALLING_CODES[code]
    return ""


def country_from_domain(domain: str) -> str:
    host = (domain or "").lower().strip().rstrip("/").split(":")[0]
    host = re.sub(r"^https?://", "", host).split("/")[0]
    parts = host.split(".")
    if len(parts) < 2:
        return ""
    tld = parts[-1]
    if tld == "co" and len(parts) >= 3 and parts[-2] in ("com", "org", "net", "edu", "gov"):
        return "CO"
    if tld == "uk":
        return "GB"
    return _TLDS.get(tld, "")


def country_from_location(location: str) -> str:
    if not location:
        return ""
    text = _ascii(location)
    for cc, pattern in _LOCATION_WORDS:
        if re.search(rf"\b(?:{pattern})\b", text):
            return cc
    # "Austin, TX" / "Niterói, RJ": a trailing state code decides
    m = re.search(r",\s*([A-Za-z]{2})\s*$", location.strip())
    if m:
        code = m.group(1).upper()
        if code in _BR_STATES and code not in _US_STATES:
            return "BR"
        if code in _US_STATES and code not in _BR_STATES:
            return "US"
        # Shared codes (AL, MA, MT, PA, SC...): Brazilian user's default wins later.
        return ""
    return ""


def detect_country(phone: str = "", domain: str = "", location: str = "",
                   default_language: str = "pt-BR") -> str:
    """Best-guess ISO country, or "" when there is no evidence at all."""
    cc = country_from_phone(phone) or country_from_domain(domain) or country_from_location(location)
    if cc:
        return cc
    digits = re.sub(r"\D", "", phone or "")
    # A local number with no country code belongs to the user's own market.
    if len(digits) in (10, 11):
        return "BR" if default_language.lower().startswith("pt") else ""
    if location and re.search(r",\s*[A-Za-z]{2}\s*$", location.strip()):
        return "BR" if default_language.lower().startswith("pt") else "US"
    return ""


def detect(phone: str = "", domain: str = "", location: str = "",
           default_language: str = "pt-BR") -> Market:
    cc = detect_country(phone, domain, location, default_language)
    if cc:
        return Market(BR if cc == "BR" else INTL, cc)
    pt = default_language.lower().startswith("pt")
    return Market(BR if pt else INTL, "BR" if pt else "")


def language(market: str) -> str:
    """Language code for a Market (or for a bare 'BR'/'INTL')."""
    cc = getattr(market, "country", "")
    if cc:
        return LANGUAGE_BY_COUNTRY.get(cc, "en")
    return "pt-BR" if market == BR else "en"


def language_name(market: str) -> str:
    """How to name the language in a prompt, with the country for flavor."""
    code = language(market)
    name = LANGUAGE_NAMES.get(code, "English")
    cc = getattr(market, "country", "")
    if code == "en":
        name = "British English" if cc in ("GB", "IE") else "American English"
    if code == "es" and cc:
        name = f"Spanish as spoken in {COUNTRY_NAMES.get(cc, cc)} (español)"
    return name


def is_portuguese(market: str) -> bool:
    return language(market).startswith("pt")


async def for_prospect(state, prospect, default_language: str = "pt-BR") -> Market:
    """Market (with country) for a prospect, looking at its company too."""
    phone, domain, location = prospect.phone, "", ""
    if prospect.company_id:
        try:
            company = await state.get_company(prospect.company_id)
        except Exception:
            company = None
        if company:
            phone = phone or company.phone
            domain = company.domain
            location = company.location
    if not domain and prospect.email and "@" in prospect.email:
        domain = prospect.email.split("@", 1)[1]
    return detect(phone, domain, location, default_language)



def name_for_code(code: str, country: str = "") -> str:
    """Language name for a language code (as stored on drafts and jobs)."""
    if code == "en":
        return "British English" if country in ("GB", "IE") else "American English"
    if code == "es" and country:
        return f"Spanish as spoken in {COUNTRY_NAMES.get(country, country)} (español)"
    return LANGUAGE_NAMES.get(code, "English")


def _code(market_or_code: str) -> str:
    if isinstance(market_or_code, Market) or market_or_code in (BR, INTL):
        return language(market_or_code)
    return market_or_code or "en"


def pick(market_or_code: str, **texts: str) -> str:
    """The text for the prospect's language: pick(mk, pt="oi", es="hola", en="hi").
    Falls back to English, then to the first one given."""
    base = _code(market_or_code).split("-")[0]
    return texts.get(base) or texts.get("en") or next(iter(texts.values()), "")
