"""Google Calendar: real free slots for replies, and booking confirmed calls.

Shares the Google sign-in with Gmail (same OAuth client in .env, same token
file, scopes added in gmail.py). Needs the Calendar API enabled in that
Google Cloud project. Everything degrades to "no slots" when not set up, so
callers can use it unconditionally.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta

import httpx

logger = logging.getLogger("harvey.calendar")

API = "https://www.googleapis.com/calendar/v3"
WEEKDAYS_PT = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
WEEKDAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def _tz(name: str):
    import pytz
    try:
        return pytz.timezone(name)
    except Exception:
        return pytz.timezone("America/Sao_Paulo")


def free_slots(busy: list[tuple[datetime, datetime]], *, start: datetime, days: int,
               tzinfo, working_hours: str, working_days: list[int], minutes: int,
               min_notice_hours: int, limit: int) -> list[datetime]:
    """Pure slot finder: earliest `limit` starts, at most one per day, spread out."""
    h0, h1 = working_hours.split("-")
    open_h, open_m = map(int, h0.split(":"))
    close_h, close_m = map(int, h1.split(":"))
    earliest = start + timedelta(hours=min_notice_hours)
    step = timedelta(minutes=30)
    length = timedelta(minutes=minutes)
    picks: list[datetime] = []
    day = start.date()
    for _ in range(days + 7):
        if len(picks) >= limit:
            break
        if day.weekday() in working_days:
            cursor = tzinfo.localize(datetime(day.year, day.month, day.day, open_h, open_m))
            close = tzinfo.localize(datetime(day.year, day.month, day.day, close_h, close_m))
            # Prefer mid-morning and mid-afternoon over the first minute of the day.
            candidates = []
            while cursor + length <= close:
                candidates.append(cursor)
                cursor += step
            preferred = sorted(candidates, key=lambda c: min(abs(c.hour - 10), abs(c.hour - 15)))
            for c in preferred:
                if c < earliest:
                    continue
                if any(c < b_end and c + length > b_start for b_start, b_end in busy):
                    continue
                picks.append(c)
                break
        day += timedelta(days=1)
    return sorted(picks)


def format_slots(slots: list[datetime], language: str = "pt-BR") -> str:
    if not slots:
        return ""
    if language.startswith("es"):
        parts = [f"el {WEEKDAYS_ES[s.weekday()]} {s.day:02d}/{s.month:02d} a las "
                 f"{s.hour}:{s.minute:02d} ({s.tzname()})" for s in slots]
        return ", ".join(parts[:-1]) + (" o " if len(parts) > 1 else "") + parts[-1]
    if language.startswith("fr"):
        parts = [f"{WEEKDAYS_FR[s.weekday()]} {s.day:02d}/{s.month:02d} à "
                 f"{s.hour}h{s.minute:02d} ({s.tzname()})" for s in slots]
        return ", ".join(parts[:-1]) + (" ou " if len(parts) > 1 else "") + parts[-1]
    if language.startswith("pt"):
        parts = [f"{WEEKDAYS_PT[s.weekday()]} ({s.day:02d}/{s.month:02d}) às "
                 f"{s.hour}h{s.minute:02d}".replace("h00", "h") for s in slots]
        return ", ".join(parts[:-1]) + (" ou " if len(parts) > 1 else "") + parts[-1]
    parts = [f"{WEEKDAYS_EN[s.weekday()]} {s.strftime('%b')} {s.day} at "
             f"{s.strftime('%I:%M %p').lstrip('0')} ({s.tzname()})" for s in slots]
    return ", ".join(parts[:-1]) + (" or " if len(parts) > 1 else "") + parts[-1]


class CalendarClient:
    def __init__(self, config=None, env=None):
        self.config = config
        self.env = env
        self._token = ""
        self._expires = 0.0

    @property
    def cfg(self):
        return getattr(self.config, "calendar", None)

    def _timezone(self) -> str:
        try:
            return self.config.usage.quiet_hours.timezone
        except AttributeError:
            return "America/Sao_Paulo"

    def is_configured(self) -> bool:
        from harvey.integrations.gmail import _load_token
        return bool(self.cfg and self.cfg.enabled and self.env
                    and self.env.gmail_client_id and self.env.gmail_client_secret
                    and _load_token())

    async def _access_token(self) -> str:
        from harvey.integrations.gmail import TOKEN_URL, _load_token
        if self._token and time.time() < self._expires - 60:
            return self._token
        stored = _load_token()
        if not stored:
            return ""
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(TOKEN_URL, data={
                "client_id": self.env.gmail_client_id,
                "client_secret": self.env.gmail_client_secret,
                "refresh_token": stored["refresh_token"],
                "grant_type": "refresh_token",
            })
        if resp.status_code != 200:
            logger.warning(f"agenda: a renovação do token falhou ({resp.status_code})")
            return ""
        data = resp.json()
        self._token = data.get("access_token", "")
        self._expires = time.time() + int(data.get("expires_in", 3600))
        return self._token

    async def get_available_slots(self, date_range: str = "") -> list[datetime]:
        """Next free slots, as timezone-aware datetimes. [] when not set up."""
        if not self.is_configured():
            return []
        cfg = self.cfg
        tzinfo = _tz(self._timezone())
        now = datetime.now(tzinfo)
        end = now + timedelta(days=cfg.days_ahead + 7)
        token = await self._access_token()
        if not token:
            return []
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    f"{API}/freeBusy",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"timeMin": now.isoformat(), "timeMax": end.isoformat(),
                          "timeZone": self._timezone(),
                          "items": [{"id": cfg.calendar_id}]},
                )
        except httpx.HTTPError as e:
            logger.warning(f"agenda: a consulta de horários falhou: {e}")
            return []
        if resp.status_code >= 400:
            logger.warning(f"agenda: consulta de horários {resp.status_code}: {resp.text[:200]} "
                           "(a Calendar API está ativada? Rode 'mariana gmail auth' de novo.)")
            return []
        cal = (resp.json().get("calendars") or {}).get(cfg.calendar_id, {})
        busy = [(datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                 datetime.fromisoformat(b["end"].replace("Z", "+00:00")))
                for b in cal.get("busy", [])]
        return free_slots(busy, start=now, days=cfg.days_ahead, tzinfo=tzinfo,
                          working_hours=cfg.working_hours, working_days=cfg.working_days,
                          minutes=cfg.meeting_minutes, min_notice_hours=cfg.min_notice_hours,
                          limit=cfg.slots_to_offer)

    async def book_meeting(self, prospect_email: str, slot: dict) -> bool:
        """Create the event: slot = {"start": iso, "summary": str, "description": str}."""
        if not prospect_email or not isinstance(slot, dict) or not slot.get("start"):
            logger.warning("book_meeting chamado com dados inválidos.")
            return False
        if not self.is_configured() or not self.cfg.create_events:
            return False
        start = datetime.fromisoformat(slot["start"])
        end = start + timedelta(minutes=self.cfg.meeting_minutes)
        token = await self._access_token()
        if not token:
            return False
        body = {
            "summary": slot.get("summary") or "Conversa sobre vídeo",
            "description": slot.get("description", ""),
            "start": {"dateTime": start.isoformat(), "timeZone": self._timezone()},
            "end": {"dateTime": end.isoformat(), "timeZone": self._timezone()},
            "attendees": [{"email": prospect_email}],
            "conferenceData": {"createRequest": {"requestId": f"mariana-{int(time.time())}"}},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{API}/calendars/{self.cfg.calendar_id}/events",
                params={"conferenceDataVersion": 1, "sendUpdates": "all"},
                headers={"Authorization": f"Bearer {token}"}, json=body,
            )
        if resp.status_code >= 400:
            logger.warning(f"agenda: criação do evento {resp.status_code}: {resp.text[:200]}")
            return False
        return True
