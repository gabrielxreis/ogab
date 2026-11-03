"""Configuration loader for Mariana. Reads harvey.yaml + .env."""

import logging
import os
import re
from datetime import time as _time
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from harvey.paths import PROJECT_ROOT

logger = logging.getLogger("harvey.config")


class ConfigError(Exception):
    """Raised when Mariana's configuration is missing or invalid."""


class ConfigFileNotFoundError(ConfigError, FileNotFoundError):
    """Config file is missing. Subclasses FileNotFoundError for
    backward compatibility with existing callers/tests."""


class SignatureConfig(BaseModel):
    """What goes under every email Mariana sends, and into signature.html.

    Every field is optional; empty ones are simply left out. Built by
    harvey/signature.py and appended at send time, after the pre-send gate,
    so its links never count against the cold-email link budget.
    """
    enabled: bool = True
    name: str = ""            # defaults to persona.name
    title: str = ""           # defaults to persona.role
    company: str = ""         # defaults to persona.company
    phone: str = ""
    whatsapp: str = ""        # digits with country code, e.g. 5521999998888
    website: str = ""
    instagram: str = ""
    portfolio: str = ""       # reel / Vimeo / YouTube showreel
    extra_lines: list[str] = []
    accent_color: str = "#111111"
    photo_url: str = ""       # optional square headshot or logo for the HTML version


class PersonaConfig(BaseModel):
    name: str
    company: str
    role: str
    email: str
    linkedin: str
    tone: str
    # Language for drafts when the prospect's own can't be inferred:
    # pt-BR for Brazil, en for the US.
    language: str = "pt-BR"
    signature: SignatureConfig = SignatureConfig()


class OfferConfig(BaseModel):
    primary: str = ""
    entry: str = ""
    goal: str = "book_call"  # book_call, start_trial, get_reply
    booking_method: str = "calendar_link"  # calendar_link, suggest_times, ask_preference
    booking_url: str = ""
    meeting_duration: str = "15 minutes"
    meeting_owner: str = ""


class ProductConfig(BaseModel):
    name: str
    description: str
    pricing: str
    key_benefits: list[str]
    objection_responses: dict[str, str]
    offer: OfferConfig = OfferConfig()


class ICPConfig(BaseModel):
    industries: list[str]
    company_size: str
    titles: list[str]
    geography: list[str]
    # Role keywords that indicate a company is in-market right now (a company
    # hiring a "Head of Growth" is buying growth tooling). Empty → falls back
    # to `titles`. Used for careers-page scanning and job-board discovery.
    hiring_signals: list[str] = []
    # Discovery needs a radius, not a place name. Maps each entry in
    # `geography` to "lat,lng,radius_km" — e.g.
    #   "Denver, CO": "39.7392,-104.9903,50"
    # Without one, listings providers can only match on the business name.
    geo_coordinates: dict[str, str] = {}


class EmailChannelConfig(BaseModel):
    enabled: bool = True
    # "instantly" (legacy), "gmail" (Gmail/Workspace via API — recommended),
    # "microsoft" (Microsoft 365 / Outlook via Graph), or "smtp" (any
    # SMTP+IMAP mailbox: AgentMail, Fastmail, ...)
    provider: str = "instantly"
    max_daily_sends: int = 50
    # When True, also send to catch-all ("risky") domains, not just verified
    # mailboxes. Off by default — catch-alls accept everything, so a bad
    # guess still bounces.
    send_to_risky: bool = False
    # Copilot mode (native providers): every outgoing email waits in the
    # outbox for your approval (dashboard → Outbox, or `mariana outbox`).
    # Set false for full autopilot once you trust the output.
    require_approval: bool = True
    # Kill switch: pause all sending when bounces exceed this fraction of
    # sent mail (measured over the trailing sends). 0 disables the switch.
    max_bounce_rate: float = 0.05

    @field_validator("max_daily_sends")
    @classmethod
    def _sends_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("max_daily_sends must be >= 0")
        return v


class LinkedInChannelConfig(BaseModel):
    enabled: bool = True
    max_daily_connections: int = 20
    max_daily_messages: int = 10
    # LinkedIn restricts accounts above ~100 invites a week: stay under it.
    max_weekly_connections: int = 80
    warmup: bool = True                 # comment on a post before inviting
    warmup_days: int = 2                # days between the comment and the invite
    withdraw_after_days: int = 21       # pending invites older than this: withdraw
    # Mariana drafts LinkedIn invites and messages; the user sends them from
    # their own account. There is no LinkedIn login or browser robot.


class InstagramChannelConfig(BaseModel):
    """DM drafts for businesses whose Instagram is linked from their site.
    Always sent by hand from the dashboard."""
    enabled: bool = True


WHATSAPP_MODES = ("link", "cloud_api")


class WhatsAppChannelConfig(BaseModel):
    """WhatsApp drafts for prospects with a phone number.

    mode "link" (default): Mariana writes the message and the dashboard opens
    your own WhatsApp with it typed in; you press send. No account risk.
    mode "cloud_api": approved messages go out through Meta's WhatsApp
    Business Cloud API, and ONLY to contacts marked opted_in (they replied or
    asked). Meta's policy forbids unsolicited business messages, so cold
    numbers always stay in link mode regardless of this setting.
    """
    enabled: bool = True
    mode: str = "link"
    max_daily_sends: int = 20
    require_approval: bool = True
    default_country_code: str = "55"
    # Country calling codes WhatsApp is used for. Everyone else (US and the
    # rest of the world) is reached by email and LinkedIn instead, where
    # cold business outreach is the norm. Empty list = every country.
    countries: list[str] = ["55"]
    # Cloud API only: an approved template used to open a conversation
    # with an opted-in contact outside the 24h window.
    template_name: str = ""
    template_language: str = "pt_BR"

    @field_validator("mode")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        v = (v or "link").strip().lower()
        if v not in WHATSAPP_MODES:
            raise ValueError(f"whatsapp.mode must be one of {WHATSAPP_MODES}")
        return v


class ChannelsConfig(BaseModel):
    email: EmailChannelConfig = EmailChannelConfig()
    linkedin: LinkedInChannelConfig = LinkedInChannelConfig()
    whatsapp: WhatsAppChannelConfig = WhatsAppChannelConfig()
    instagram: InstagramChannelConfig = InstagramChannelConfig()


PRECLEARED_ADDRESS_SOURCES = ("published", "bought", "scraped", "given", "unknown")


class PreclearedConfig(BaseModel):
    """Optional per-recipient cold-email check through Precleared.

    Off by default. When on, each new recipient is checked once, before the
    first cold email, against UK PECR, US CAN-SPAM, Canada's CASL, Germany's
    UWG and France's rules. Any verdict other than ok_to_email holds the
    email back with the reason. See harvey/integrations/precleared.py.
    """

    enabled: bool = False
    # Where your business is based: GB or US. Required when enabled.
    sender_country: str = ""
    # Where prospect addresses come from, in Precleared's terms. Mariana
    # builds most addresses from a learned pattern, so the honest default
    # is "unknown"; use "published" only if yours are copied from the
    # businesses' own websites.
    address_source: str = "unknown"

    @field_validator("sender_country", mode="before")
    @classmethod
    def _upper_country(cls, v) -> str:
        return str(v or "").strip().upper()

    @field_validator("address_source", mode="before")
    @classmethod
    def _valid_source(cls, v) -> str:
        v = str(v or "unknown").strip().lower()
        if v not in PRECLEARED_ADDRESS_SOURCES:
            raise ValueError(
                f"'{v}' is not a valid address_source. "
                f"Use one of: {', '.join(PRECLEARED_ADDRESS_SOURCES)}."
            )
        return v

    @model_validator(mode="after")
    def _country_when_enabled(self):
        if self.enabled and self.sender_country not in ("GB", "US"):
            raise ValueError(
                "compliance.precleared.sender_country must be GB or US "
                "when the check is enabled."
            )
        return self


class ComplianceConfig(BaseModel):
    precleared: PreclearedConfig = PreclearedConfig()


class QuietHoursConfig(BaseModel):
    start: str = "22:00"
    end: str = "07:00"
    timezone: str = "America/New_York"

    @field_validator("start", "end")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        try:
            _time.fromisoformat(v)
        except ValueError:
            raise ValueError(
                f"'{v}' is not a valid time. Use 24h HH:MM format, e.g. '22:00'."
            )
        return v

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, v: str) -> str:
        import pytz

        if v not in pytz.all_timezones_set:
            raise ValueError(
                f"'{v}' is not a valid timezone. Use an IANA name like 'America/New_York'."
            )
        return v


class UsageConfig(BaseModel):
    max_daily_claude_percent: float = 80.0
    heartbeat_interval_minutes: int = 15
    quiet_hours: QuietHoursConfig = QuietHoursConfig()

    @field_validator("max_daily_claude_percent")
    @classmethod
    def _valid_percent(cls, v: float) -> float:
        if not 0 < v <= 100:
            raise ValueError("max_daily_claude_percent must be between 0 and 100")
        return v

    @field_validator("heartbeat_interval_minutes")
    @classmethod
    def _valid_interval(cls, v: int) -> int:
        if v < 1:
            raise ValueError("heartbeat_interval_minutes must be at least 1")
        return v


BRAIN_PROVIDERS = ("claude", "codex")
CODEX_REASONING_EFFORTS = ("minimal", "low", "medium", "high", "xhigh")

# Model names are passed to a CLI, so they must look like a model name and
# never like a flag ("-x") or anything a shell would treat specially.
_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/\[\]-]{0,127}$")


class BrainConfig(BaseModel):
    """Which subscription Mariana thinks with.

    ``claude`` (default) runs Claude Code headless on your Claude plan.
    ``codex`` runs Codex on your ChatGPT plan. There is never an automatic
    fallback between them, and an explicit ``model`` only affects Mariana —
    your own Claude Code / Codex settings are never read or changed.
    """

    provider: str = "claude"
    model: str = ""  # empty = the provider's own default
    reasoning_effort: str = ""  # codex only; empty = model default

    @field_validator("provider", mode="before")
    @classmethod
    def _valid_provider(cls, v) -> str:
        v = str(v or "claude").strip().lower()
        if v not in BRAIN_PROVIDERS:
            raise ValueError(
                f"'{v}' is not a supported brain provider. "
                f"Use one of: {', '.join(BRAIN_PROVIDERS)}."
            )
        return v

    @field_validator("model", mode="before")
    @classmethod
    def _valid_model(cls, v) -> str:
        v = str(v or "").strip()
        if v and not _MODEL_NAME_RE.match(v):
            raise ValueError(f"'{v}' is not a valid model name.")
        return v

    @field_validator("reasoning_effort", mode="before")
    @classmethod
    def _valid_effort(cls, v) -> str:
        v = str(v or "").strip().lower()
        if v and v not in CODEX_REASONING_EFFORTS:
            raise ValueError(
                f"'{v}' is not a valid reasoning effort. "
                f"Use one of: {', '.join(CODEX_REASONING_EFFORTS)}."
            )
        return v


class CalendarConfig(BaseModel):
    """Real free slots from Google Calendar, offered in replies.

    Uses the same Google sign-in as Gmail (`mariana gmail auth`), with the
    Calendar API enabled in the same Google Cloud project.
    """
    enabled: bool = True
    calendar_id: str = "primary"
    working_hours: str = "09:00-18:00"
    working_days: list[int] = [0, 1, 2, 3, 4]   # Monday=0
    meeting_minutes: int = 30
    min_notice_hours: int = 20
    days_ahead: int = 7
    slots_to_offer: int = 3
    create_events: bool = True                  # book confirmed calls on the calendar


class NotifyConfig(BaseModel):
    """Phone/desktop alert when a lead answers with interest.

    macOS notification always (when on a Mac). For the phone: install the
    free ntfy app, subscribe to a hard-to-guess topic and put it in
    NTFY_TOPIC, or use a Telegram bot (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID).
    """
    enabled: bool = True
    intents: list[str] = ["interested", "question", "objection"]
    macos: bool = True


class PostJobConfig(BaseModel):
    """After delivery: testimonial + referral, then re-engage before the
    client's next event."""
    enabled: bool = True
    testimonial_after_days: int = 3
    reengage_days_before_event: int = 45


class ProductionConfig(BaseModel):
    """Client folders for /ogab, proposal follow-up, shoot reminders."""
    clients_dir: str = ""            # empty = /ogab's pasta_saida, else ~/Documents/Mariana/clientes
    proposal_followup_days: list[int] = [3, 5]   # 1st follow-up after 3 days, 2nd 5 days later
    shoot_reminder: bool = True      # alert the day before + client confirmation draft
    default_revisions: int = 2


class MarianaConfig(BaseModel):
    persona: PersonaConfig
    product: ProductConfig
    icp: ICPConfig
    channels: ChannelsConfig = ChannelsConfig()
    usage: UsageConfig = UsageConfig()
    brain: BrainConfig = BrainConfig()
    compliance: ComplianceConfig = ComplianceConfig()
    calendar: CalendarConfig = CalendarConfig()
    notify: NotifyConfig = NotifyConfig()
    postjob: PostJobConfig = PostJobConfig()
    production: ProductionConfig = ProductionConfig()


class EnvConfig(BaseModel):
    instantly_api_key: str = ""
    # Discovery providers
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    dataforseo_sandbox: str = ""   # any truthy value routes to the free sandbox
    hunter_api_key: str = ""
    serper_api_key: str = ""
    reoon_api_key: str = ""
    zerobounce_api_key: str = ""
    # Native mail providers (channels.email.provider: gmail | smtp)
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    imap_host: str = ""
    imap_port: int = 993
    imap_username: str = ""
    imap_password: str = ""
    # Microsoft 365 (channels.email.provider: microsoft)
    m365_client_id: str = ""
    m365_tenant_id: str = ""
    # Optional: only used when compliance.precleared.enabled is true.
    precleared_api_key: str = ""
    # WhatsApp Business Cloud API (channels.whatsapp.mode: cloud_api)
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""      # webhook verification (Cloud API inbound)
    ntfy_topic: str = ""
    ntfy_server: str = "https://ntfy.sh"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


def _format_validation_error(e: ValidationError) -> str:
    """Turn a pydantic ValidationError into a readable, actionable message."""
    lines = []
    for err in e.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)


def load_config(config_path: str | None = None) -> MarianaConfig:
    """Load Mariana configuration from YAML file.

    Raises ConfigError with a clear, actionable message on any problem.
    """
    if config_path is None:
        config_path = _find_config_file()

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigFileNotFoundError(
            f"Config file not found: {config_path}. "
            "Create one from harvey.yaml.example or run 'mariana setup'."
        )
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}:\n  {e}")
    except OSError as e:
        raise ConfigError(f"Could not read {config_path}: {e}")

    if data is None:
        raise ConfigError(f"{config_path} is empty. Run 'mariana setup' to configure Mariana.")
    if not isinstance(data, dict):
        raise ConfigError(
            f"{config_path} must contain a YAML mapping (key: value pairs), "
            f"got {type(data).__name__}."
        )

    try:
        return MarianaConfig(**data)
    except ValidationError as e:
        # Log a friendly, actionable summary, then re-raise the original
        # ValidationError so callers (and tests) keep the pydantic type.
        logger.error(
            f"Invalid configuration in {config_path}:\n{_format_validation_error(e)}\n"
            "Corrija os campos acima ou rode 'mariana onboard' de novo."
        )
        raise


def load_brain_config(config_path: str | None = None) -> BrainConfig:
    """Read just the ``brain:`` section, without validating the rest.

    Training runs before a product is configured (the template harvey.yaml
    still has placeholder values), but it must still think with the
    provider the user chose. A missing file or section means the Claude
    default; an invalid section raises rather than silently switching
    providers.
    """
    if config_path is None:
        try:
            config_path = _find_config_file()
        except ConfigFileNotFoundError:
            return BrainConfig()
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return BrainConfig()
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Could not read the brain settings in {config_path}: {e}")
    section = data.get("brain") if isinstance(data, dict) else None
    if section is None:
        return BrainConfig()
    if not isinstance(section, dict):
        raise ConfigError(f"'brain' in {config_path} must be a mapping.")
    try:
        return BrainConfig(**section)
    except ValidationError as e:
        raise ConfigError(
            f"Invalid brain settings in {config_path}:\n{_format_validation_error(e)}"
        )


def load_env() -> EnvConfig:
    """Load environment variables from .env file."""
    load_dotenv()
    env = EnvConfig(
        instantly_api_key=os.getenv("INSTANTLY_API_KEY", "").strip(),
        dataforseo_login=os.getenv("DATAFORSEO_LOGIN", "").strip(),
        dataforseo_password=os.getenv("DATAFORSEO_PASSWORD", "").strip(),
        dataforseo_sandbox=os.getenv("DATAFORSEO_SANDBOX", "").strip(),
        hunter_api_key=os.getenv("HUNTER_API_KEY", "").strip(),
        serper_api_key=os.getenv("SERPER_API_KEY", "").strip(),
        reoon_api_key=os.getenv("REOON_API_KEY", "").strip(),
        zerobounce_api_key=os.getenv("ZEROBOUNCE_API_KEY", "").strip(),
        gmail_client_id=os.getenv("GMAIL_CLIENT_ID", "").strip(),
        gmail_client_secret=os.getenv("GMAIL_CLIENT_SECRET", "").strip(),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587").strip() or 587),
        smtp_username=os.getenv("SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
        imap_host=os.getenv("IMAP_HOST", "").strip(),
        imap_port=int(os.getenv("IMAP_PORT", "993").strip() or 993),
        imap_username=os.getenv("IMAP_USERNAME", "").strip(),
        imap_password=os.getenv("IMAP_PASSWORD", "").strip(),
        m365_client_id=os.getenv("M365_CLIENT_ID", "").strip(),
        m365_tenant_id=os.getenv("M365_TENANT_ID", "").strip(),
        precleared_api_key=os.getenv("PRECLEARED_API_KEY", "").strip(),
        whatsapp_token=os.getenv("WHATSAPP_TOKEN", "").strip(),
        whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
        whatsapp_verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip(),
        ntfy_topic=os.getenv("NTFY_TOPIC", "").strip(),
        ntfy_server=os.getenv("NTFY_SERVER", "https://ntfy.sh").strip() or "https://ntfy.sh",
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
    )
    return env


def _find_config_file() -> str:
    """Search for Mariana's config.

    ``harvey.local.yaml`` wins when present. It is gitignored, so a fork can
    carry a real product configuration (trained on an actual company) while
    the tracked ``harvey.yaml`` stays an untrained template — nobody
    publishes their positioning, pricing, and prospect targeting by accident.
    """
    candidates = [
        Path.cwd() / "harvey.local.yaml",
        PROJECT_ROOT / "harvey.local.yaml",
        Path.cwd() / "harvey.yaml",
        Path.cwd().parent / "harvey.yaml",
        PROJECT_ROOT / "harvey.yaml",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    raise ConfigFileNotFoundError(
        "harvey.yaml not found in "
        + ", ".join(str(p.parent) for p in candidates)
        + ". Create one from harvey.yaml.example or run 'mariana setup'."
    )
