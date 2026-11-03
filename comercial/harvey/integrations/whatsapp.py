"""WhatsApp: click-to-chat links and the official Cloud API.

Two ways out, on purpose:

* ``wa_link`` — https://wa.me/<number>?text=<message>. Opens WhatsApp (app or
  web) on the user's own phone with the message typed in; the user presses
  send. This is how every cold message goes: no automation touches the
  account, so there is nothing for WhatsApp to ban.

* ``CloudAPIClient`` — Meta's WhatsApp Business Cloud API, for contacts who
  replied or asked to be contacted (``opted_in``). Meta's Business Messaging
  Policy requires that opt-in; unsolicited API messages get the number
  restricted. Free-form text only works inside the 24h window after the
  contact last wrote; outside it an approved template is required.

Unofficial automation of WhatsApp Web is deliberately not offered.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import quote

import httpx

logger = logging.getLogger("harvey.whatsapp")

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
TIMEOUT = 20.0


def normalize_phone(raw: str, default_country_code: str = "55") -> str:
    """Digits-only E.164 without '+', or "" when it can't be a mobile number.

    Brazilian numbers come in every shape ("(21) 99999-8888", "021 ...",
    "+55 21 ..."); US ones as "(512) 555-0100" or "+1 512 ...".
    """
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if (raw or "").strip().startswith("+") or digits.startswith("00"):
        digits = digits.lstrip("0")
    elif default_country_code == "55":
        digits = digits.lstrip("0")
        if not digits.startswith("55") or len(digits) <= 11:
            digits = "55" + digits
    elif default_country_code == "1":
        if len(digits) == 10:
            digits = "1" + digits
    elif not digits.startswith(default_country_code):
        digits = default_country_code + digits.lstrip("0")
    if not 10 <= len(digits) <= 15:
        return ""
    return digits


def is_probably_mobile(phone: str) -> bool:
    """Brazil: mobiles are 55 + DDD + 9 digits starting with 9. Landlines
    can't receive WhatsApp unless they're a WhatsApp Business landline,
    so they are flagged, not dropped. Other countries: assume yes."""
    if phone.startswith("55"):
        local = phone[4:]
        return len(local) == 9 and local.startswith("9")
    return True


def wa_link(phone: str, text: str) -> str:
    return f"https://wa.me/{phone}?text={quote(text, safe='')}"


class CloudAPIClient:
    """Minimal WhatsApp Business Cloud API client (send + check)."""

    def __init__(self, token: str, phone_number_id: str):
        self.token = token
        self.phone_number_id = phone_number_id

    def is_configured(self) -> bool:
        return bool(self.token and self.phone_number_id)

    async def _post(self, payload: dict) -> tuple[bool, str, str]:
        url = f"{GRAPH_BASE}/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as e:
            return False, "", f"network: {e}"
        if resp.status_code >= 400:
            try:
                err = resp.json().get("error", {})
                detail = f"{err.get('code')}: {err.get('message')}"
            except ValueError:
                detail = resp.text[:200]
            return False, "", detail
        messages = (resp.json() or {}).get("messages") or [{}]
        return True, messages[0].get("id", ""), ""

    async def send_text(self, to_phone: str, body: str) -> tuple[bool, str, str]:
        """Free-form text. Only delivered inside the 24h service window."""
        return await self._post({
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": body, "preview_url": True},
        })

    async def send_template(
        self, to_phone: str, name: str, language: str, params: list[str] | None = None
    ) -> tuple[bool, str, str]:
        template: dict = {"name": name, "language": {"code": language}}
        if params:
            template["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            }]
        return await self._post({
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": template,
        })

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured():
            return False, "WHATSAPP_TOKEN / WHATSAPP_PHONE_NUMBER_ID missing from .env"
        url = f"{GRAPH_BASE}/{self.phone_number_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    url, headers=headers,
                    params={"fields": "display_phone_number,verified_name,quality_rating"},
                )
        except httpx.HTTPError as e:
            return False, f"network: {e}"
        if resp.status_code >= 400:
            return False, f"Cloud API {resp.status_code}: {resp.text[:200]}"
        d = resp.json()
        return True, (f"{d.get('verified_name', '?')} "
                      f"({d.get('display_phone_number', '?')}), "
                      f"quality {d.get('quality_rating', '?')}")
