"""Alerts when a lead answers: speed of reply closes jobs.

Three outlets, each optional, all best-effort (an alert never breaks the
loop that triggered it):
  * macOS notification center (osascript), when running on a Mac
  * ntfy (free phone app): NTFY_TOPIC, optionally NTFY_SERVER
  * Telegram bot: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
"""

from __future__ import annotations

import asyncio
import logging
import platform
import shutil

import httpx

logger = logging.getLogger("harvey.notify")

INTENT_LABEL = {
    "interested": "Interessado",
    "question": "Pergunta",
    "objection": "Objeção",
    "replied": "Respondeu",
}


def _osascript_quote(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


async def _macos(title: str, message: str):
    if platform.system() != "Darwin" or not shutil.which("osascript"):
        return
    script = (f'display notification "{_osascript_quote(message[:200])}" '
              f'with title "{_osascript_quote(title[:80])}" sound name "Glass"')
    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", script,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()


async def _ntfy(env, title: str, message: str, click: str = ""):
    if not getattr(env, "ntfy_topic", ""):
        return
    headers = {"Title": title.encode("utf-8"), "Priority": "high", "Tags": "movie_camera"}
    if click:
        headers["Click"] = click
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{env.ntfy_server.rstrip('/')}/{env.ntfy_topic}",
                          content=message.encode("utf-8"), headers=headers)


async def _telegram(env, title: str, message: str):
    token = getattr(env, "telegram_bot_token", "")
    chat = getattr(env, "telegram_chat_id", "")
    if not (token and chat):
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": f"{title}\n\n{message}"})


async def notify(config, env, title: str, message: str, click: str = "") -> None:
    cfg = getattr(config, "notify", None)
    if cfg is not None and not cfg.enabled:
        return
    outlets = []
    if cfg is None or cfg.macos:
        outlets.append(_macos(title, message))
    outlets += [_ntfy(env, title, message, click), _telegram(env, title, message)]
    for result in await asyncio.gather(*outlets, return_exceptions=True):
        if isinstance(result, Exception):
            logger.debug(f"notify: outlet failed: {result}")


async def notify_reply(config, env, intent: str, who: str, channel: str, text: str):
    """The standard 'a lead answered' alert, filtered by notify.intents."""
    cfg = getattr(config, "notify", None)
    if cfg is not None and intent not in cfg.intents and intent != "replied":
        return
    label = INTENT_LABEL.get(intent, intent)
    await notify(config, env, f"{label}: {who} ({channel})", text[:300],
                 click="http://localhost:5555/#conversations")
