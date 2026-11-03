"""Gmail / Google Workspace mailbox provider — raw REST, no SDK weight.

Setup (one-time):
1. Google Cloud Console → create a project → enable the Gmail API.
2. OAuth consent screen (internal or testing) → create an OAuth client of
   type "Desktop app". Put its id/secret in .env as GMAIL_CLIENT_ID /
   GMAIL_CLIENT_SECRET.
3. Run ``mariana gmail auth`` — opens a browser, stores the refresh token
   in data/gmail_token.json. Done: Mariana can send and read.

Deliverability notes: use a mailbox on a dedicated SECONDARY domain (never
your main one), configure SPF/DKIM/DMARC, ramp volume slowly, and watch
Google Postmaster Tools. Mariana's outbox pacing + kill switches handle the
rest.
"""

import base64
import json
import logging
import time
import webbrowser
from email.message import EmailMessage
from email.utils import parseaddr

import httpx

from harvey.paths import PROJECT_ROOT
from harvey.integrations.mail_provider import (
    InboundMessage,
    MailProvider,
    SendResult,
    looks_like_bounce,
)

logger = logging.getLogger("harvey.gmail")

TOKEN_FILE = PROJECT_ROOT / "data" / "gmail_token.json"
API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
# gmail.settings.basic lets `mariana signature --install-gmail` set your
# Gmail signature; sending and reading need only gmail.modify.
# calendar.freebusy + calendar.events let Mariana offer real free slots and
# put confirmed calls on the calendar (harvey/integrations/calendar.py).
SCOPE = ("https://www.googleapis.com/auth/gmail.modify "
         "https://www.googleapis.com/auth/gmail.settings.basic "
         "https://www.googleapis.com/auth/calendar.freebusy "
         "https://www.googleapis.com/auth/calendar.events")
LOOPBACK_PORT = 8765

TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)


def _load_token() -> dict | None:
    try:
        if TOKEN_FILE.is_file():
            data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("refresh_token"):
                return data
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Não deu para ler o token do Gmail: {e}")
    return None


def _save_token(data: dict):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass


class GmailProvider(MailProvider):
    name = "gmail"

    def __init__(self, config, env):
        self.config = config
        self.client_id = getattr(env, "gmail_client_id", "")
        self.client_secret = getattr(env, "gmail_client_secret", "")
        self._access_token = ""
        self._access_expires = 0.0

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and _load_token())

    async def _token(self) -> str | None:
        """Valid access token, refreshing via the stored refresh token."""
        if self._access_token and time.time() < self._access_expires - 60:
            return self._access_token
        stored = _load_token()
        if not stored:
            logger.error("Gmail: não conectado. Rode 'mariana gmail auth'.")
            return None
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(TOKEN_URL, data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": stored["refresh_token"],
                    "grant_type": "refresh_token",
                })
        except httpx.HTTPError as e:
            logger.error(f"A renovação do token do Gmail falhou: {e}")
            return None
        if resp.status_code != 200:
            logger.error(
                f"Gmail token refresh rejected ({resp.status_code}). "
                "Re-run 'mariana gmail auth'."
            )
            return None
        data = resp.json()
        self._access_token = data.get("access_token", "")
        self._access_expires = time.time() + float(data.get("expires_in", 3600))
        return self._access_token or None

    async def _request(self, method: str, path: str, **kwargs):
        token = await self._token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.request(
                    method, f"{API_BASE}{path}", headers=headers, **kwargs
                )
        except httpx.HTTPError as e:
            logger.error(f"O pedido ao Gmail falhou ({path}): {e}")
            return None
        if resp.status_code >= 400:
            logger.error(f"API do Gmail {resp.status_code} em {path}: {resp.text[:200]}")
            return None
        try:
            return resp.json()
        except ValueError:
            return {}

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_ref: str = "",
        in_reply_to: str = "",
    ) -> SendResult:
        msg = EmailMessage()
        persona = self.config.persona
        msg["To"] = to_email
        msg["From"] = f"{persona.name} <{persona.email}>" if persona.email else persona.name
        msg["Subject"] = subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        from harvey.signature import compose
        text, html_part = compose(self.config, body)
        msg.set_content(text)
        if html_part:
            msg.add_alternative(html_part, subtype="html")

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        payload: dict = {"raw": raw}
        if thread_ref:
            payload["threadId"] = thread_ref

        data = await self._request("POST", "/messages/send", json=payload)
        if data is None:
            return SendResult(ok=False, error="gmail send failed")

        # Fetch the assigned RFC Message-ID for bounce/thread matching later.
        message_id = ""
        gmail_id = data.get("id", "")
        if gmail_id:
            meta = await self._request(
                "GET", f"/messages/{gmail_id}",
                params={"format": "metadata", "metadataHeaders": "Message-ID"},
            )
            for h in ((meta or {}).get("payload") or {}).get("headers", []):
                if h.get("name", "").lower() == "message-id":
                    message_id = h.get("value", "")
        return SendResult(
            ok=True,
            message_id=message_id or gmail_id,
            thread_ref=data.get("threadId", ""),
        )

    async def get_replies(self, limit: int = 50) -> list[InboundMessage]:
        listing = await self._request(
            "GET", "/messages",
            params={"q": "in:inbox -from:me newer_than:7d", "maxResults": limit},
        )
        if not listing:
            return []
        out = []
        for stub in listing.get("messages", [])[:limit]:
            data = await self._request(
                "GET", f"/messages/{stub['id']}", params={"format": "full"}
            )
            if not data:
                continue
            msg = self._parse_message(data)
            if msg:
                out.append(msg)
        return out

    @staticmethod
    def _parse_message(data: dict) -> InboundMessage | None:
        payload = data.get("payload") or {}
        headers = {
            h.get("name", "").lower(): h.get("value", "")
            for h in payload.get("headers", [])
        }
        from_email = parseaddr(headers.get("from", ""))[1].lower()
        if not from_email:
            return None
        subject = headers.get("subject", "")
        body = GmailProvider._extract_text(payload) or data.get("snippet", "")
        return InboundMessage(
            provider_id=data.get("id", ""),
            from_email=from_email,
            subject=subject,
            body=body[:5000],
            message_id=headers.get("message-id", ""),
            in_reply_to=headers.get("in-reply-to", ""),
            thread_ref=data.get("threadId", ""),
            date=headers.get("date", ""),
            is_bounce=looks_like_bounce(from_email, subject),
            headers=headers,
        )

    @staticmethod
    def _extract_text(payload: dict) -> str:
        """Depth-first hunt for the text/plain part of a MIME tree."""
        def decode(part) -> str:
            data = (part.get("body") or {}).get("data", "")
            if not data:
                return ""
            try:
                return base64.urlsafe_b64decode(data + "===").decode(errors="replace")
            except Exception:
                return ""

        if payload.get("mimeType", "").startswith("text/plain"):
            return decode(payload)
        for part in payload.get("parts", []) or []:
            text = GmailProvider._extract_text(part)
            if text:
                return text
        if payload.get("mimeType", "").startswith("text/html"):
            import re
            html = decode(payload)
            return re.sub(r"<[^>]+>", " ", html)
        return ""

    async def test_connection(self) -> tuple[bool, str]:
        if not self.client_id or not self.client_secret:
            return False, "GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET missing from .env"
        if not _load_token():
            return False, "Not authorized yet — run 'mariana gmail auth'"
        data = await self._request("GET", "/profile")
        if data and data.get("emailAddress"):
            return True, f"Connected as {data['emailAddress']}"
        return False, "Token refresh or profile fetch failed"


    async def install_signature(self, signature_html: str) -> tuple[bool, str]:
        """Set the Gmail signature of the address Mariana sends from.

        Needs the gmail.settings.basic scope; a token from before that scope
        was added gets a 403 here, fixed by re-running `mariana gmail auth`.
        """
        profile = await self._request("GET", "/profile")
        address = (profile or {}).get("emailAddress", "")
        if not address:
            return False, "Could not read the Gmail profile. Run 'mariana gmail auth'."
        data = await self._request(
            "PATCH", f"/settings/sendAs/{address}",
            json={"signature": signature_html},
        )
        if data is None:
            return False, ("Gmail refused the signature change. Re-run "
                           "'mariana gmail auth' to grant the settings permission.")
        return True, f"Signature installed on {address}"


def run_auth_flow(client_id: str, client_secret: str) -> bool:
    """One-time OAuth (installed-app loopback). Blocks until the browser
    round-trip completes; stores the refresh token for GmailProvider."""
    import http.server
    import secrets
    import threading
    import urllib.parse

    if not client_id or not client_secret:
        print("  Coloque GMAIL_CLIENT_ID e GMAIL_CLIENT_SECRET no .env antes.")
        print("  (Google Cloud Console → APIs → Credenciais → ID do cliente OAuth, App para computador)")
        return False

    state = secrets.token_urlsafe(16)
    redirect_uri = f"http://localhost:{LOOPBACK_PORT}"
    auth_url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })

    result: dict = {}
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if query.get("state", [""])[0] != state:
                self.send_response(400); self.end_headers()
                return
            result["code"] = query.get("code", [""])[0]
            result["error"] = query.get("error", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                "<h2>Mariana est\u00e1 conectada ao Gmail.</h2>Pode fechar esta aba.".encode())
            done.set()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("localhost", LOOPBACK_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(f"\n  Abrindo o navegador para entrar no Google...\n  {auth_url}\n")
    webbrowser.open(auth_url)
    if not done.wait(timeout=300):
        server.shutdown()
        print("  O navegador não voltou a tempo. Tente de novo.")
        return False
    server.shutdown()

    if result.get("error") or not result.get("code"):
        print(f"  A autorização falhou: {result.get('error') or 'nenhum código recebido'}")
        return False

    resp = httpx.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": result["code"],
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }, timeout=30)
    if resp.status_code != 200:
        print(f"  A troca do token falhou ({resp.status_code}): {resp.text[:200]}")
        return False
    data = resp.json()
    if not data.get("refresh_token"):
        print("  O Google não devolveu o token de renovação. Tire a Mariana da lista"
              " de apps com acesso à sua conta e tente de novo.")
        return False
    _save_token({
        "refresh_token": data["refresh_token"],
        "scope": data.get("scope", SCOPE),
        "obtained_at": int(time.time()),
    })
    print(f"  ✓ Gmail conectado. Token salvo em {TOKEN_FILE}")
    return True
