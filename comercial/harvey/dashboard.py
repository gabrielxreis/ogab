"""Mariana Dashboard — local web UI to set up, control, and monitor Mariana."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse, JSONResponse, PlainTextResponse, Response,
)

logger = logging.getLogger("harvey.dashboard")

from harvey.paths import PROJECT_ROOT  # noqa: E402
DB_PATH = PROJECT_ROOT / "data" / "harvey.db"
ENV_FILE = PROJECT_ROOT / ".env"
CONFIG_FILE = PROJECT_ROOT / "harvey.yaml"
PID_FILE = PROJECT_ROOT / "data" / "harvey.pid"
LOG_FILE = PROJECT_ROOT / "data" / "harvey.log"


def _resolve_config_file() -> Path:
    """harvey.local.yaml wins when present — same resolution as config.py's
    loader, so the dashboard doesn't judge setup complete against the
    tracked harvey.yaml template while the real trained config sits in the
    gitignored local override."""
    from harvey.config import _find_config_file, ConfigFileNotFoundError
    try:
        return Path(_find_config_file())
    except ConfigFileNotFoundError:
        return CONFIG_FILE

app = FastAPI(title="Mariana Dashboard")

# Mariana process tracking
_harvey_process: subprocess.Popen | None = None
_harvey_started_at: datetime | None = None
_env_lock = asyncio.Lock()


# ── Helpers ──


async def query_db(sql: str, params: tuple = ()) -> list[dict]:
    """Run a query and return results as list of dicts.

    Never raises: a missing DB file, missing table, or malformed schema
    returns [] so no dashboard route can 500 on an empty install.
    """
    if not DB_PATH.exists():
        return []
    try:
        async with aiosqlite.connect(str(DB_PATH)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    except Exception as e:
        logger.warning("consulta ao banco falhou (%s): %s", sql.split(None, 4)[:4], e)
        return []


def _mask_key(key: str) -> str:
    """Mask an API key for display: show first 4 and last 4 chars."""
    if not key or len(key) < 10:
        return "****" if key else ""
    return key[:4] + "****" + key[-4:]


def _read_env_file() -> dict[str, str]:
    """Read .env file and return as dict."""
    env_vars = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    return env_vars


def _write_env_file(updates: dict[str, str]):
    """Update .env file with new values, preserving existing entries."""
    existing = _read_env_file()
    existing.update(updates)
    lines = [f"{k}={v}" for k, v in existing.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    load_dotenv(str(ENV_FILE), override=True)


def _check_harvey_pid() -> int | None:
    """Check if there's a running Mariana process from a PID file."""
    global _harvey_process, _harvey_started_at
    if _harvey_process and _harvey_process.poll() is None:
        return _harvey_process.pid
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)  # Check if process exists
            return pid
        except (ValueError, ProcessLookupError, PermissionError):
            PID_FILE.unlink(missing_ok=True)
    return None


# ── Setup Status ──


@app.get("/api/setup-status")
async def get_setup_status():
    """Check what's configured and what still needs setup."""
    checks = []

    # 1. Venv
    checks.append({
        "id": "venv", "label": "Ambiente Python",
        "done": (PROJECT_ROOT / ".venv").is_dir(),
        "required": True,
        "help": "Rode o instalador: bash install.sh",
    })

    # 2. Env file
    env_vars = _read_env_file()
    env_exists = ENV_FILE.exists() and bool(env_vars)
    checks.append({
        "id": "env_file", "label": "Arquivo de chaves (.env)",
        "done": env_exists,
        "required": True,
        "help": "Coloque as suas chaves na aba Configurações.",
    })

    # 3. Email provider configured (matches channels.email.provider)
    provider = _current_provider()

    def _has(*keys):
        return all((env_vars.get(k, "") or os.getenv(k, "")).strip() for k in keys)

    if provider == "gmail":
        provider_done = _has("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET") and \
            (PROJECT_ROOT / "data" / "gmail_token.json").is_file()
        provider_help = ("Coloque o ID e o segredo do Gmail em Configurações e rode "
                         "'mariana gmail auth' no terminal.")
    elif provider == "microsoft":
        provider_done = _has("M365_CLIENT_ID") and \
            (PROJECT_ROOT / "data" / "m365_token.json").is_file()
        provider_help = ("Coloque M365_CLIENT_ID e M365_TENANT_ID no .env e rode "
                         "'mariana microsoft auth' no terminal.")
    elif provider == "smtp":
        provider_done = _has("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD")
        provider_help = "Coloque o servidor, o usuário e a senha do SMTP em Configurações."
    else:
        instantly_key = env_vars.get("INSTANTLY_API_KEY", "") or os.getenv("INSTANTLY_API_KEY", "")
        provider_done = bool(instantly_key) and instantly_key != "your_instantly_api_key_here"
        provider_help = "Coloque a chave do Instantly em Configurações."
    checks.append({
        "id": "email_provider", "label": f"Email de envio conectado ({provider})",
        "done": provider_done,
        "required": True,
        "help": provider_help,
    })

    # 4. Email verification (needed for addresses to be sendable, not 'guess')
    verifier_set = _has("REOON_API_KEY") or _has("ZEROBOUNCE_API_KEY") or _has("HUNTER_API_KEY")
    checks.append({
        "id": "verifier", "label": "Chave de verificação de email",
        "done": verifier_set,
        "required": True,
        "help": "Coloque uma chave do Reoon (600 grátis/mês), ZeroBounce ou Hunter em Configurações. "
                "Sem ela, os emails encontrados ficam como 'guess' e nunca recebem mensagem.",
    })

    # 5. Config valid
    config_valid = False
    config_path = _resolve_config_file()
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            company = cfg.get("persona", {}).get("company", "")
            product = cfg.get("product", {}).get("name", "")
            config_valid = company not in ("Your Company", "") and product not in ("Your Product", "")
        except Exception:
            pass
    checks.append({
        "id": "config", "label": f"Mariana configurada ({config_path.name})",
        "done": config_valid,
        "required": True,
        "help": "Rode o onboarding: mariana onboard (ou /ogab comercial onboard no Claude Code).",
    })

    # 6. Product trained
    product_trained = (PROJECT_ROOT / "skills" / "product_knowledge.md").exists()
    checks.append({
        "id": "product_trained", "label": "Dossiê do onboarding",
        "done": product_trained,
        "required": True,
        "help": "Rode: mariana onboard (pode mandar um .md sobre você).",
    })

    # 8. Cloudflare (optional)
    cf_id = env_vars.get("CLOUDFLARE_ACCOUNT_ID", "") or os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    cf_token = env_vars.get("CLOUDFLARE_API_TOKEN", "") or os.getenv("CLOUDFLARE_API_TOKEN", "")
    checks.append({
        "id": "cloudflare", "label": "Leitura profunda de sites (Cloudflare)",
        "done": bool(cf_id) and bool(cf_token),
        "required": False,
        "help": "Opcional. Para ler sites que dependem de JavaScript no treinamento.",
    })

    required_checks = [c for c in checks if c["required"]]
    completed_required = sum(1 for c in required_checks if c["done"])

    return {
        "checks": checks,
        "completed": completed_required,
        "total_required": len(required_checks),
        "percent": int(completed_required / len(required_checks) * 100) if required_checks else 0,
    }


# ── Settings ──


def _current_provider() -> str:
    """Read channels.email.provider from the active config (best-effort)."""
    try:
        with open(_resolve_config_file(), encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return ((cfg.get("channels") or {}).get("email") or {}).get("provider", "instantly")
    except Exception:
        return "instantly"


@app.get("/api/settings")
async def get_settings():
    """Get current settings — presence flags only for secrets, never raw values."""
    env_vars = _read_env_file()
    all_keys = [
        "INSTANTLY_API_KEY",
        "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
        "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD",
        "IMAP_HOST", "IMAP_PORT", "IMAP_USERNAME", "IMAP_PASSWORD",
        "REOON_API_KEY", "ZEROBOUNCE_API_KEY", "HUNTER_API_KEY",
    ]
    for key in all_keys:
        if key not in env_vars:
            env_vars[key] = os.getenv(key, "")

    def is_set(k):
        return bool((env_vars.get(k) or "").strip())

    # Gmail is authorized once mariana gmail auth has stored a token file.
    gmail_token = (PROJECT_ROOT / "data" / "gmail_token.json").is_file()

    return {
        "provider": _current_provider(),
        # Non-secret values echo back so fields repopulate; secrets are
        # presence-only so keys never leave the box.
        "instantly_api_key_set": is_set("INSTANTLY_API_KEY"),
        "cloudflare_account_id": env_vars.get("CLOUDFLARE_ACCOUNT_ID", ""),
        "cloudflare_api_token_set": is_set("CLOUDFLARE_API_TOKEN"),
        "gmail_client_id": env_vars.get("GMAIL_CLIENT_ID", ""),
        "gmail_client_secret_set": is_set("GMAIL_CLIENT_SECRET"),
        "gmail_authorized": gmail_token,
        "smtp_host": env_vars.get("SMTP_HOST", ""),
        "smtp_port": env_vars.get("SMTP_PORT", ""),
        "smtp_username": env_vars.get("SMTP_USERNAME", ""),
        "smtp_password_set": is_set("SMTP_PASSWORD"),
        "imap_host": env_vars.get("IMAP_HOST", ""),
        "imap_port": env_vars.get("IMAP_PORT", ""),
        "reoon_api_key_set": is_set("REOON_API_KEY"),
        "zerobounce_api_key_set": is_set("ZEROBOUNCE_API_KEY"),
        "hunter_api_key_set": is_set("HUNTER_API_KEY"),
    }


@app.post("/api/settings/env")
async def save_env_settings(request: Request):
    """Save environment variables to .env file."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"success": False, "message": "Invalid request body."}, status_code=400)
    if not isinstance(data, dict):
        return JSONResponse({"success": False, "message": "Invalid request body."}, status_code=400)
    async with _env_lock:
        updates = {}
        for key in ["INSTANTLY_API_KEY",
                     "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
                     "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET",
                     "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD",
                     "IMAP_HOST", "IMAP_PORT", "IMAP_USERNAME", "IMAP_PASSWORD",
                     "REOON_API_KEY", "ZEROBOUNCE_API_KEY", "HUNTER_API_KEY"]:
            if key in data and data[key] is not None:
                # Strip newlines so a crafted value can't inject extra .env entries
                updates[key] = str(data[key]).replace("\n", " ").replace("\r", " ").strip()
        if updates:
            try:
                _write_env_file(updates)
            except Exception as e:
                logger.warning("Não deu para salvar o .env: %s", e)
                return {"success": False, "message": "Could not write .env file."}
    return {"success": True}


@app.post("/api/settings/test-instantly")
async def test_instantly(request: Request):
    """Test an Instantly API key."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    api_key = str(data.get("api_key", "") or "")
    if not api_key:
        return {"success": False, "message": "No API key provided."}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.instantly.ai/api/v2/accounts",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return {"success": True, "message": "Connected to Instantly."}
            else:
                return {"success": False, "message": f"API returned {resp.status_code}. Check your key."}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


# ── Companies ──


@app.get("/api/companies")
async def get_companies():
    """All companies with contact counts."""
    rows = await query_db("""
        SELECT c.*,
            (SELECT COUNT(*) FROM prospects p WHERE p.company_id = c.id) as contact_count
        FROM companies c ORDER BY c.created_at DESC LIMIT 200
    """)
    return rows


@app.get("/api/companies/{company_id}/contacts")
async def get_company_contacts(company_id: str):
    """Get all contacts for a specific company."""
    rows = await query_db(
        "SELECT * FROM prospects WHERE company_id = ? ORDER BY score DESC",
        (company_id,),
    )
    return rows


# ── Feedback ──


@app.post("/api/feedback")
async def add_feedback(request: Request):
    """Add a comment/feedback on any entity."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    entity_type = str(data.get("entity_type", "") or "")[:50]
    entity_id = str(data.get("entity_id", "") or "")[:100]
    comment = str(data.get("comment", "") or "").strip()[:4000]
    if not comment:
        return {"success": False, "message": "Comment is required."}
    feedback_id = uuid.uuid4().hex[:12]
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(str(DB_PATH)) as db:
            # Ensure the table exists so feedback works even on a fresh install
            await db.execute(
                """CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT,
                    entity_id TEXT,
                    comment TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )"""
            )
            await db.execute(
                "INSERT INTO feedback (id, entity_type, entity_id, comment) VALUES (?, ?, ?, ?)",
                (feedback_id, entity_type, entity_id, comment),
            )
            await db.commit()
    except Exception as e:
        logger.warning("Não deu para salvar o comentário: %s", e)
        return {"success": False, "message": "Could not save feedback."}
    return {"success": True, "id": feedback_id}


@app.get("/api/feedback/{entity_type}/{entity_id}")
async def get_feedback(entity_type: str, entity_id: str):
    """Get feedback for an entity."""
    rows = await query_db(
        "SELECT * FROM feedback WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC",
        (entity_type, entity_id),
    )
    return rows


# ── Mariana Controls ──


@app.get("/api/harvey/status")
async def get_harvey_status():
    """Check if Mariana is currently running."""
    pid = _check_harvey_pid()
    started = _harvey_started_at.isoformat() if _harvey_started_at else None
    return {"running": pid is not None, "pid": pid, "started_at": started}


@app.post("/api/harvey/start")
async def start_harvey():
    """Start Mariana's heartbeat loop as a subprocess."""
    global _harvey_process, _harvey_started_at

    if _check_harvey_pid():
        return {"success": False, "message": "Mariana is already running."}

    # Ensure data dir exists
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)

    try:
        log_handle = open(LOG_FILE, "a", encoding="utf-8")
        try:
            _harvey_process = subprocess.Popen(
                [sys.executable, "-m", "harvey"],
                cwd=str(PROJECT_ROOT),
                stdout=log_handle,
                stderr=log_handle,
                start_new_session=True,
            )
        finally:
            # Child holds its own copies of the fds; don't leak ours.
            log_handle.close()
    except Exception as e:
        logger.warning("Não deu para ligar a Mariana: %s", e)
        return {"success": False, "message": f"Failed to start Mariana: {e}"}
    _harvey_started_at = datetime.now()

    # Write PID file
    try:
        PID_FILE.write_text(str(_harvey_process.pid), encoding="utf-8")
    except OSError as e:
        logger.warning("Não deu para salvar o arquivo PID: %s", e)

    return {"success": True, "pid": _harvey_process.pid}


@app.post("/api/harvey/stop")
async def stop_harvey():
    """Stop the Mariana subprocess."""
    global _harvey_process, _harvey_started_at

    pid = _check_harvey_pid()
    if not pid:
        return {"success": False, "message": "Mariana is not running."}

    try:
        os.kill(pid, signal.SIGTERM)
        # Wait briefly for graceful shutdown
        for _ in range(10):
            try:
                os.kill(pid, 0)
                await asyncio.sleep(0.5)
            except ProcessLookupError:
                break
        else:
            # Force kill if still running
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
    except (ProcessLookupError, PermissionError):
        pass

    _harvey_process = None
    _harvey_started_at = None
    PID_FILE.unlink(missing_ok=True)

    return {"success": True}


@app.get("/api/harvey/logs")
async def get_harvey_logs():
    """Get recent log lines."""
    if not LOG_FILE.exists():
        return {"lines": []}
    try:
        # Tail only the last 64KB so a huge log file never blocks the UI
        with open(LOG_FILE, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 65536))
            text = f.read().decode("utf-8", errors="replace")
        lines = text.strip().splitlines()[-100:]
        return {"lines": lines}
    except Exception:
        return {"lines": []}


# ── Pipeline Data (existing endpoints) ──


@app.get("/api/stats")
async def get_stats():
    """Pipeline overview stats."""
    try:
        prospects = await query_db(
            "SELECT status, COUNT(*) as count FROM prospects GROUP BY status"
        )
        prospect_total = sum(r["count"] for r in prospects)
        prospect_map = {r["status"]: r["count"] for r in prospects}

        campaigns = await query_db(
            "SELECT status, COUNT(*) as count FROM campaigns GROUP BY status"
        )
        campaign_map = {r["status"]: r["count"] for r in campaigns}

        conversations = await query_db(
            "SELECT status, COUNT(*) as count FROM conversations GROUP BY status"
        )
        convo_map = {r["status"]: r["count"] for r in conversations}

        actions = await query_db("SELECT COUNT(*) as count FROM actions")
        action_count = actions[0]["count"] if actions else 0

        usage = await query_db(
            "SELECT claude_calls, codex_calls FROM usage_log WHERE date = date('now')"
        )
        usage_today = (usage[0]["claude_calls"] or 0) if usage else 0
        codex_today = (usage[0]["codex_calls"] or 0) if usage else 0

        return {
            "prospects": {"total": prospect_total, "by_status": prospect_map},
            "campaigns": {"total": sum(campaign_map.values()), "by_status": campaign_map},
            "conversations": {"total": sum(convo_map.values()), "by_status": convo_map},
            "actions_total": action_count,
            "claude_calls_today": usage_today,
            "codex_calls_today": codex_today,
            "brain_provider": _active_provider(),
            "brain_status": await _brain_status(),
        }
    except Exception as e:
        return {"error": str(e)}


_USAGE_SUM = (
    "COUNT(DISTINCT CASE WHEN session_id != '' THEN session_id ELSE id END) AS calls, "
    "COALESCE(SUM(input_tokens), 0) AS input_tokens, "
    "COALESCE(SUM(output_tokens), 0) AS output_tokens, "
    "COALESCE(SUM(cache_read_tokens), 0) AS cache_read_tokens, "
    "COALESCE(SUM(cache_creation_tokens), 0) AS cache_creation_tokens, "
    "ROUND(COALESCE(SUM(cost_usd), 0), 4) AS cost_usd"
)

_quota_clients: dict = {}


def _active_brain():
    """The brain config harvey.yaml selects (None if unreadable)."""
    try:
        from harvey.config import load_brain_config
        return load_brain_config()
    except Exception:
        return None


async def _brain_status() -> dict:
    """Last recorded brain health transition ({} if none): lets the
    dashboard say "Codex paused: <why>" instead of looking healthy."""
    from harvey.brain import BRAIN_STATUS_KEY, active_brain_status
    rows = await query_db("SELECT value FROM settings WHERE key = ?", (BRAIN_STATUS_KEY,))
    # Only the configured provider's health (a stale Codex pause isn't
    # Claude's).
    return active_brain_status(rows[0]["value"], _active_provider()) if rows else {}


def _active_provider() -> str:
    brain = _active_brain()
    return brain.provider if brain else ""


def _quota_client_for(provider: str, model: str = ""):
    """One cached quota reader per provider (and Codex model). Each reads
    only its own subscription, so a Claude gauge is never shown as Codex or
    vice versa, and Codex shows the bucket metering the configured model."""
    key = (provider, model if provider == "codex" else "")
    if key not in _quota_clients:
        if provider == "codex":
            from harvey.codex import CodexClient, CodexQuotaClient
            _quota_clients[key] = CodexQuotaClient(CodexClient(model=model))
        elif provider == "claude":
            from harvey.integrations.quota import QuotaClient
            _quota_clients[key] = QuotaClient()
        else:
            return None
    return _quota_clients[key]


@app.get("/api/usage")
async def get_usage():
    """Token/cost accounting + live subscription quota for the Usage tab."""

    totals = {}
    for label, where in (
        ("today", "date(created_at) = date('now')"),
        ("week", "created_at >= datetime('now', '-7 days')"),
        ("month", "created_at >= datetime('now', '-30 days')"),
    ):
        rows = await query_db(f"SELECT {_USAGE_SUM} FROM usage_events WHERE {where}")
        totals[label] = rows[0] if rows else {}

    def grouped(expr, alias):
        return (
            f"SELECT {expr} AS {alias}, {_USAGE_SUM} FROM usage_events "
            f"WHERE created_at >= datetime('now', '-30 days') "
            f"GROUP BY {alias} ORDER BY output_tokens DESC LIMIT 25"
        )

    by_agent = await query_db(grouped("CASE WHEN agent = '' THEN 'other' ELSE agent END", "agent"))
    by_task = await query_db(grouped("CASE WHEN task = '' THEN 'other' ELSE task END", "task"))
    by_model = await query_db(grouped("CASE WHEN model = '' THEN 'unknown' ELSE model END", "model"))
    by_provider = await query_db(grouped("provider", "provider"))
    by_day = await query_db(
        f"SELECT date(created_at) AS day, {_USAGE_SUM} FROM usage_events "
        f"WHERE created_at >= datetime('now', '-30 days') "
        f"GROUP BY day ORDER BY day ASC"
    )

    brain = _active_brain()
    provider = brain.provider if brain else ""
    quota = None
    try:
        client = _quota_client_for(provider, brain.model if brain else "")
        if client is not None:
            quota = await client.get_utilization()
    except Exception as e:
        logger.debug("Quota lookup failed: %s", e)

    return {
        "provider": provider,
        "quota": quota,
        # Whose quota this is, even when it couldn't be read, so the UI shows
        # "unavailable" for the active provider instead of hiding the gauge.
        "quota_provider": provider,
        "quota_status": ("available" if quota else "unavailable") if provider else "",
        "by_provider": by_provider,
        "totals": totals,
        "by_day": by_day,
        "by_agent": by_agent,
        "by_task": by_task,
        "by_model": by_model,
    }


@app.get("/api/prospects")
async def get_prospects():
    rows = await query_db("SELECT * FROM prospects ORDER BY created_at DESC LIMIT 200")
    return rows


def _state():
    from harvey.state import StateManager
    return StateManager(db_path=str(DB_PATH))


@app.get("/api/outbox")
async def get_outbox_api():
    """Outbox queue + kill-switch state for the Outbox tab."""
    try:
        state = _state()
        await state.init_db()
        return {
            "paused": await state.get_setting("sending_paused"),
            "pending": await state.get_outbox(status="pending_review", limit=100),
            "approved": await state.get_outbox(status="approved", limit=50),
            "sent": (await query_db(
                "SELECT * FROM outbox WHERE status = 'sent' "
                "ORDER BY sent_at DESC LIMIT 25")),
            "failed": (await query_db(
                "SELECT * FROM outbox WHERE status IN ('failed','rejected','cancelled') "
                "ORDER BY updated_at DESC LIMIT 25")),
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/outbox/approve-all")
async def outbox_approve_all():
    try:
        state = _state()
        await state.init_db()
        n = await state.approve_outbox()
        return {"success": True, "approved": n}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/outbox/{item_id}/approve")
async def outbox_approve(item_id: str):
    try:
        state = _state()
        await state.init_db()
        n = await state.approve_outbox(item_id)
        return {"success": bool(n)}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/outbox/{item_id}/reject")
async def outbox_reject(item_id: str):
    try:
        state = _state()
        await state.init_db()
        await state.update_outbox_item(item_id, status="rejected")
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.get("/api/channels")
async def get_channels_api():
    """WhatsApp / LinkedIn / Instagram drafts for the Mensagens tab."""
    try:
        from harvey.agents.channels import open_url
        state = _state()
        await state.init_db()

        def with_url(items):
            for it in items:
                it["open_url"] = open_url(it)
            return items

        return {
            "pending": with_url(await state.get_channel_items(status="pending_review", limit=100)),
            "approved": with_url(await state.get_channel_items(status="approved", limit=100)),
            "sent": await query_db(
                "SELECT * FROM channel_outbox WHERE status = 'sent' "
                "ORDER BY sent_at DESC LIMIT 30"),
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/channels/{item_id}/{action}")
async def channel_action(item_id: str, action: str):
    if action not in ("approve", "reject", "sent", "optin"):
        return JSONResponse({"success": False, "message": "unknown action"}, status_code=400)
    try:
        state = _state()
        await state.init_db()
        item = await state.get_channel_item(item_id)
        if not item:
            return JSONResponse({"success": False, "message": "not found"}, status_code=404)
        if action == "approve":
            await state.update_channel_item(item_id, status="approved")
        elif action == "reject":
            await state.update_channel_item(item_id, status="rejected")
        elif action == "optin":
            await state.update_channel_item(item_id, opted_in=True)
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            await state.update_channel_item(item_id, status="sent", sent_at=now)
            prospect = await state.get_prospect(item["prospect_id"]) if item["prospect_id"] else None
            if prospect and prospect.status in ("new", "queued"):
                await state.update_prospect_status(prospect.id, "contacted")
            await state.log_action(
                action_type=f"{item['channel']}_sent", agent="you",
                details={"to": item["target"], "company": item["company_name"]},
            )
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


async def _mariana_handler():
    """A Handler wired like the heartbeat's, for replies that arrive here."""
    from harvey.agents.handler import Handler
    from harvey.brain import Brain
    from harvey.config import load_config, load_env
    config = load_config()
    state = _state()
    await state.init_db()
    return Handler(Brain(state, config.brain), state, config, load_env()), state, config


@app.post("/api/channels/{item_id}/replied")
async def channel_replied(item_id: str, request: Request):
    """They answered on WhatsApp / LinkedIn / Instagram. Paste the reply:
    queued emails stop, the conversation opens, and an answer is drafted."""
    try:
        payload = await request.json()
        text = (payload.get("text") or "").strip()
        if not text:
            return JSONResponse({"success": False, "message": "cole a resposta"}, status_code=400)
        handler, state, _ = await _mariana_handler()
        item = await state.get_channel_item(item_id)
        if not item or not item["prospect_id"]:
            return JSONResponse({"success": False, "message": "not found"}, status_code=404)
        prospect = await state.get_prospect(item["prospect_id"])
        if not prospect:
            return JSONResponse({"success": False, "message": "prospect missing"}, status_code=404)
        if item["status"] != "sent":
            now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            await state.update_channel_item(item_id, status="sent", sent_at=now)
        if item["channel"] == "whatsapp":
            await state.update_channel_item(item_id, opted_in=True)
        convo_id = await handler.handle_external_reply(prospect, text, item["channel"])
        return {"success": True, "conversation_id": convo_id}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.get("/webhooks/whatsapp")
async def whatsapp_verify(request: Request):
    """Meta's webhook handshake (Cloud API). Needs WHATSAPP_VERIFY_TOKEN and a
    public URL to this dashboard (e.g. a Cloudflare tunnel)."""
    from harvey.config import load_env
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == load_env().whatsapp_verify_token \
            and load_env().whatsapp_verify_token:
        return HTMLResponse(q.get("hub.challenge", ""))
    return JSONResponse({"error": "forbidden"}, status_code=403)


@app.post("/webhooks/whatsapp")
async def whatsapp_inbound(request: Request):
    """Inbound WhatsApp messages from the Cloud API: matched to the prospect
    by phone and handled exactly like a pasted reply."""
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}
    try:
        handler, state, config = await _mariana_handler()
        from harvey.integrations.whatsapp import normalize_phone
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                for msg in (change.get("value") or {}).get("messages", []):
                    if msg.get("type") != "text":
                        continue
                    phone = normalize_phone("+" + msg.get("from", ""),
                                            config.channels.whatsapp.default_country_code)
                    rows = await query_db(
                        "SELECT prospect_id FROM channel_outbox WHERE channel = 'whatsapp' "
                        "AND target = ? AND prospect_id != '' ORDER BY created_at DESC LIMIT 1",
                        (phone,))
                    if not rows:
                        logger.info(f"webhook do WhatsApp: mensagem de número desconhecido {phone}")
                        continue
                    prospect = await state.get_prospect(rows[0]["prospect_id"])
                    if prospect:
                        await handler.handle_external_reply(
                            prospect, (msg.get("text") or {}).get("body", ""), "whatsapp")
    except Exception as e:
        logger.error(f"webhook do WhatsApp falhou: {e}")
    return {"ok": True}


@app.post("/api/sending/{action}")
async def sending_toggle(action: str):
    if action not in ("pause", "resume"):
        return JSONResponse({"success": False, "message": "unknown action"}, status_code=400)
    try:
        state = _state()
        await state.init_db()
        if action == "pause":
            await state.set_setting("sending_paused", "paused from dashboard")
        else:
            await state.set_setting("sending_paused", "")
            await state.set_setting("bounce_count", "0")
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.get("/api/export/prospects.csv")
async def export_prospects(all: bool = False, min_score: int = 0, email_status: str = ""):
    """Sequencer-ready CSV download of the prospect list."""
    from harvey.state import StateManager
    from harvey.export import export_prospects_csv

    state = StateManager(db_path=str(DB_PATH))
    try:
        await state.init_db()
        statuses = [s.strip() for s in email_status.split(",") if s.strip()] or None
        _, text = await export_prospects_csv(
            state, email_statuses=statuses, min_score=min_score, include_all=all,
        )
    except Exception as e:
        logger.warning("A exportação de leads falhou: %s", e)
        text = ""
    return PlainTextResponse(
        text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prospects.csv"'},
    )


@app.get("/api/campaigns")
async def get_campaigns():
    rows = await query_db("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 100")
    for row in rows:
        try:
            row["sequence"] = json.loads(row.get("sequence_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            row["sequence"] = []
        try:
            row["prospect_ids"] = json.loads(row.get("prospect_ids_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            row["prospect_ids"] = []
    return rows


@app.get("/api/conversations")
async def get_conversations():
    rows = await query_db("""
        SELECT c.*, p.first_name, p.last_name, p.email as prospect_email, p.company
        FROM conversations c
        LEFT JOIN prospects p ON c.prospect_id = p.id
        ORDER BY c.updated_at DESC LIMIT 100
    """)
    for row in rows:
        try:
            row["thread"] = json.loads(row.get("thread_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            row["thread"] = []
    return rows


@app.get("/api/metrics")
async def get_metrics():
    try:
        from harvey.config import load_config
        from harvey.metrics import compute
        state = _state()
        await state.init_db()
        lang = getattr(load_config().persona, "language", "pt-BR")
        return await compute(state, lang)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/jobs")
async def get_jobs_api():
    try:
        state = _state()
        await state.init_db()
        jobs = await state.get_jobs()
        for j in jobs:
            j["proposal_file"] = Path(j["proposal_path"]).name if j.get("proposal_path") else ""
        return jobs
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/conversations/{conversation_id}/proposal")
async def make_proposal(conversation_id: str):
    """Read the conversation, build the proposal (PDF when Chrome is around)."""
    try:
        from harvey.brain import Brain
        from harvey.config import load_config
        from harvey.proposal import build_proposal
        config = load_config()
        state = _state()
        await state.init_db()
        result = await build_proposal(state, Brain(state, config.brain), config, conversation_id)
        return {"success": True, "job_id": result["job_id"],
                "file": Path(result["path"]).name,
                "suggested_prices": result.get("suggested_prices", []),
                "price_hints": result.get("price_hints", [])}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/conversations/{conversation_id}/job")
async def convo_to_job(conversation_id: str, request: Request):
    """'Fechou': mark the deal won, creating the job if no proposal exists."""
    try:
        payload = {}
        try:
            payload = await request.json()
        except Exception:
            pass
        state = _state()
        await state.init_db()
        convo = await state.get_conversation(conversation_id)
        if not convo:
            return JSONResponse({"success": False, "message": "not found"}, status_code=404)
        prospect = await state.get_prospect(convo.prospect_id)
        job = await state.job_for_conversation(conversation_id)
        fields = {k: str(v) for k, v in payload.items()
                  if k in ("value", "service", "event_date", "next_event_date", "notes")}
        if job:
            await state.update_job(job["id"], status="won", **fields)
            job_id = job["id"]
        else:
            job_id = await state.add_job(
                prospect_id=convo.prospect_id, conversation_id=conversation_id,
                status="won", company_name=prospect.company if prospect else "",
                contact_name=prospect.full_name() if prospect else "", **fields)
        if prospect:
            await state.update_prospect_status(prospect.id, "closed")
        await state.update_conversation(conversation_id, status="closed", stage="closed_won")
        await state.log_action(action_type="job_won", agent="you",
                               details={"company": prospect.company if prospect else ""})
        project = await _start_production(state, job_id)
        return {"success": True, "job_id": job_id, "project": project}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


async def _start_production(state, job_id: str) -> dict:
    """Production details + client folder for /ogab. Never fails the click."""
    try:
        from harvey.brain import Brain
        from harvey.config import load_config
        from harvey.production import on_job_won
        config = load_config()
        return await on_job_won(state, Brain(state, config.brain), config, job_id)
    except Exception as e:
        logger.warning(f"falhou ao preparar a produção: {e}")
        return {"error": str(e)}


JOB_EDITABLE = ("value", "service", "event_date", "next_event_date", "notes", "shoot_date",
                "shoot_time", "address", "onsite_contact", "delivery_due", "delivery_link",
                "revisions_included", "checklist")


@app.post("/api/jobs/{job_id}/{action}")
async def job_action(job_id: str, action: str, request: Request):
    if action not in ("won", "delivered", "lost", "update", "proposal_sent", "revision"):
        return JSONResponse({"success": False, "message": "unknown action"}, status_code=400)
    try:
        payload = {}
        try:
            payload = await request.json()
        except Exception:
            pass
        state = _state()
        await state.init_db()
        job = await state.get_job(job_id)
        if not job:
            return JSONResponse({"success": False, "message": "not found"}, status_code=404)
        fields = {k: (int(v) if k == "revisions_included" and str(v).isdigit() else str(v))
                  for k, v in payload.items() if k in JOB_EDITABLE}
        today = datetime.now().date().isoformat()
        result: dict = {"success": True}
        if action == "proposal_sent":
            fields.update(proposal_sent_at=today, followups=0, last_followup_at="")
        elif action == "revision":
            used = int(job.get("revisions_used") or 0) + 1
            included = int(job.get("revisions_included") or 2)
            fields["revisions_used"] = used
            result.update(revisions_used=used, revisions_included=included,
                          over=used > included)
            if used > included:
                await _draft_extra_revision(state, job, used, included)
        elif action == "delivered":
            fields["delivered_at"] = payload.get("delivered_at") or today
            fields["status"] = "delivered"
        elif action in ("won", "lost"):
            fields["status"] = action
        await state.update_job(job_id, **fields)
        if action == "won" and job.get("status") != "won":
            result["project"] = await _start_production(state, job_id)
        return result
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


async def _draft_extra_revision(state, job: dict, used: int, included: int):
    """Past the agreed rounds: alert, and draft a kind note about extra rounds."""
    try:
        from harvey.agents.postjob import PostJobAgent
        from harvey.brain import Brain
        from harvey.config import load_config, load_env
        from harvey.notify import notify
        config, env = load_config(), load_env()
        await notify(config, env, f"Revisão extra: {job.get('company_name')}",
                     f"Rodada {used} de {included} combinadas.")
        prospect = await state.get_prospect(job["prospect_id"]) if job.get("prospect_id") else None
        if not prospect:
            return
        from harvey import market
        mk = await market.for_prospect(state, prospect, getattr(config.persona, "language", "pt-BR"))
        agent = PostJobAgent(Brain(state, config.brain), state, config, env)
        body = await agent._short(
            f"the agreed {included} revision rounds are done and they asked for round {used}; "
            "say you're happy to do it, mention extra rounds are charged separately and that "
            "you'll send the value, or suggest bundling the remaining changes into one round",
            job, market.language(mk))
        if body:
            await agent._draft_to_client(job, prospect, body, "revision",
                                         market.pick(mk, pt="sobre a revisão", es="sobre la revisión",
                                                     fr="à propos de la révision", en="about the revision"))
    except Exception as e:
        logger.warning(f"falhou o rascunho de revisão extra: {e}")


@app.get("/api/proposals/{name}")
async def get_proposal_file(name: str):
    from fastapi.responses import FileResponse
    folder = (PROJECT_ROOT / "data" / "propostas").resolve()
    path = (folder / name).resolve()
    if path.parent != folder or not path.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(str(path))


@app.get("/api/activity")
async def get_activity():
    rows = await query_db("SELECT * FROM actions ORDER BY created_at DESC LIMIT 100")
    for row in rows:
        try:
            row["details"] = json.loads(row.get("details_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            row["details"] = {}
    return rows


# ── Dashboard UI ──


# ── Discovery: the provider menu, an estimate, and a run ──
#
# This is the only stage that spends money, so the UI never starts one without
# showing what it will cost first.

_discovery_task: asyncio.Task | None = None
_discovery_report: dict | None = None


def _discovery_queries(body: dict, config):
    from harvey.collectors.discover import build_queries

    cities = [c.strip() for c in (body.get("cities") or []) if c.strip()] or None
    return build_queries(
        config, cities=cities,
        depth=int(body.get("depth") or 30),
        limit=int(body.get("limit") or 100),
    )


@app.get("/api/discover/providers")
async def get_discovery_providers():
    """What each source does, what it costs, and whether it's ready to use."""
    try:
        from harvey.collectors.discover import DEFAULT_PROVIDER, provider_menu
        from harvey.config import load_env

        state = _state()
        await state.init_db()
        return {
            "providers": provider_menu(load_env().model_dump()),
            "default": DEFAULT_PROVIDER,
            "selected": await state.get_setting("discovery_provider") or DEFAULT_PROVIDER,
            "paused": await state.get_setting("discovery_paused"),
            "running": bool(_discovery_task and not _discovery_task.done()),
            "last_report": _discovery_report,
        }
    except Exception as e:
        logger.exception("discovery providers failed")
        return {"providers": [], "error": str(e)}


@app.post("/api/discover/estimate")
async def estimate_discovery(request: Request):
    """Projected spend and the exact query list, before anything is called."""
    try:
        from harvey.collectors.discover import PROVIDERS, estimate_cost
        from harvey.config import load_config

        body = await request.json()
        provider = body.get("provider") or ""
        if provider not in PROVIDERS:
            return JSONResponse({"error": f"unknown provider {provider!r}"},
                                status_code=400)

        queries = _discovery_queries(body, load_config())
        return {
            "provider": provider,
            "queries": [q.keyword() for q in queries],
            "query_count": len(queries),
            "estimated_cost": round(estimate_cost(provider, queries), 4),
            "free": PROVIDERS[provider].estimate(queries) == 0,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/discover/run")
async def start_discovery(request: Request):
    """Kick off a run in the background and hand back immediately.

    Discovery takes minutes, not milliseconds — holding the request open
    would just time out. Progress shows up in the run log.
    """
    global _discovery_task, _discovery_report

    if _discovery_task and not _discovery_task.done():
        return JSONResponse({"success": False, "message": "a run is already going"},
                            status_code=409)
    try:
        from harvey.collectors.discover import PROVIDERS
        from harvey.config import load_config
        from harvey.pipeline import run_prospecting

        body = await request.json()
        provider = body.get("provider") or ""
        if provider not in PROVIDERS:
            return JSONResponse({"success": False,
                                 "message": f"unknown provider {provider!r}"},
                                status_code=400)

        config = load_config()
        queries = _discovery_queries(body, config)
        max_spend = float(body.get("max_spend") or 1.0)

        state = _state()
        await state.init_db()
        await state.set_setting("discovery_provider", provider)
        await state.set_setting("discovery_paused", "")

        async def _go():
            global _discovery_report
            try:
                # Discovery chains straight into profiling: reading the sites
                # is free, and it is what makes the results worth anything.
                result = await run_prospecting(state, config, provider, queries,
                                               max_spend=max_spend)
                _discovery_report = {
                    **(result.discover or {}),
                    "profiled_companies": result.profiled_companies,
                    "profile_observations": result.profile_observations,
                    "errors": result.errors,
                }
            except Exception as exc:
                logger.exception("discovery run failed")
                _discovery_report = {"errors": [str(exc)], "stopped": "failed"}

        _discovery_report = None
        _discovery_task = asyncio.create_task(_go())
        return {"success": True, "queries": len(queries)}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/profile/run")
async def start_profile():
    """Read the websites of everything discovered but not yet looked at.

    Free and model-free, so there is nothing to estimate and no cap to set.
    """
    global _discovery_task, _discovery_report

    if _discovery_task and not _discovery_task.done():
        return JSONResponse({"success": False, "message": "a run is already going"},
                            status_code=409)
    try:
        from harvey.pipeline import run_profile_stage

        state = _state()
        await state.init_db()
        pending = await state.count_companies_needing_profile()
        if not pending:
            return {"success": True, "pending": 0}

        async def _go():
            global _discovery_report
            try:
                companies, observations, _ = await run_profile_stage(state, limit=200)
                _discovery_report = {
                    "profiled_companies": companies,
                    "profile_observations": observations,
                }
            except Exception as exc:
                logger.exception("profile run failed")
                _discovery_report = {"errors": [str(exc)], "stopped": "failed"}

        _discovery_report = None
        _discovery_task = asyncio.create_task(_go())
        return {"success": True, "pending": pending}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/discover/stop")
async def stop_discovery():
    """Kill switch. Read between batches, so an in-flight run stops cleanly."""
    try:
        state = _state()
        await state.init_db()
        await state.set_setting("discovery_paused", "stopped from dashboard")
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.get("/api/today")
async def get_today():
    """What needs a human, right now.

    The dashboard opens here rather than on a setup checklist: the question a
    returning user actually has is "is anything waiting on me?", and the
    answer is usually a short list or nothing at all.
    """
    items: list[dict] = []
    stats: dict = {}
    try:
        from harvey.signals import seed_signal_catalog

        state = _state()
        await state.init_db()
        await seed_signal_catalog(state)

        codes = await state.get_signal_codes()
        proposed = [c for c in codes if c.get("status") == "proposed"]
        confirmed = [c for c in codes if c.get("status") == "confirmed"]
        pending = await state.get_outbox(status="pending_review", limit=200)
        approved = await state.get_outbox(status="approved", limit=200)
        paused = await state.get_setting("sending_paused")
        counts = await state.count_prospects_by_status()

        convos = await query_db(
            "SELECT COUNT(*) AS n FROM conversations WHERE status = 'open'"
        )
        open_convos = convos[0]["n"] if convos else 0
        companies = await query_db("SELECT COUNT(*) AS n FROM companies")
        n_companies = companies[0]["n"] if companies else 0

        unprofiled_count = await state.count_companies_needing_profile()
        stats = {
            "companies": n_companies,
            "prospects": sum(counts.values()),
            "signals_confirmed": len(confirmed),
            "outbox_pending": len(pending),
            "outbox_approved": len(approved),
            "open_conversations": open_convos,
            "unprofiled": unprofiled_count,
        }

        # Ordered by how much it blocks Mariana from doing anything at all.
        if paused:
            items.append({
                "key": "paused", "tone": "bad",
                "title": "Envios pausados",
                "detail": str(paused) + ". Nada sai até você retomar.",
                "action": "Revisar e retomar", "tab": "outbox",
            })

        setup = await get_setup_status()
        if isinstance(setup, dict) and setup.get("percent", 100) < 100:
            missing = [c["label"] for c in setup.get("checks", [])
                       if c.get("required") and not c.get("done")]
            items.append({
                "key": "setup", "tone": "warn",
                "title": "Termine de configurar a Mariana",
                "detail": ", ".join(missing[:3]) or "Faltam etapas obrigatórias.",
                "action": "Abrir configurações", "tab": "settings",
            })

        if proposed:
            items.append({
                "key": "signals", "tone": "warn",
                "title": (f"{len(proposed)} sinal esperando a sua confirmação"
                          if len(proposed) == 1
                          else f"{len(proposed)} sinais esperando a sua confirmação"),
                "detail": ("A Mariana não coleta nada que você não aprovou. "
                           "Confirme quais sinais definem um bom cliente para você."),
                "action": "Revisar sinais", "tab": "signals",
            })
        elif not confirmed:
            items.append({
                "key": "signals-none", "tone": "warn",
                "title": "Nenhum sinal confirmado",
                "detail": "Todos os sinais foram recusados, então a prospecção não tem o que coletar.",
                "action": "Revisar sinais", "tab": "signals",
            })

        if not n_companies and confirmed:
            items.append({
                "key": "discover", "tone": "good",
                "title": "Nenhuma empresa ainda",
                "detail": ("Os sinais estão confirmados, mas nada foi coletado. "
                           "A busca é grátis para testar, sem conta."),
                "action": "Buscar empresas", "tab": "discover",
            })

        unprofiled = unprofiled_count
        if unprofiled:
            items.append({
                "key": "profile", "tone": "good",
                "title": f"{unprofiled} empresas ainda não lidas",
                "detail": ("Ler os sites é grátis e é o que deixa a mensagem "
                           "específica: se têm vídeo, Instagram, YouTube, se "
                           "estão anunciando."),
                "action": "Ler os sites", "tab": "discover",
            })

        if pending:
            items.append({
                "key": "outbox", "tone": "warn",
                "title": (f"{len(pending)} email esperando aprovação" if len(pending) == 1
                          else f"{len(pending)} emails esperando aprovação"),
                "detail": "Nada sai sem a sua aprovação. Leia um de cada vez.",
                "action": "Abrir a Outbox", "tab": "outbox",
            })

        if open_convos:
            items.append({
                "key": "replies", "tone": "good",
                "title": (f"{open_convos} conversa aberta" if open_convos == 1
                          else f"{open_convos} conversas abertas"),
                "detail": "Responderam. Veja como a Mariana está conduzindo.",
                "action": "Ler conversas", "tab": "conversations",
            })

        return {"items": items, "stats": stats}
    except Exception as e:
        logger.exception("today load failed")
        return {"items": [], "stats": stats, "error": str(e)}


# ── Signals: Mariana proposes, the user confirms ──
#
# Nothing is collected until a human has said yes to it. This is the gate the
# whole prospecting pipeline hangs off: collectors ask `state.confirmed_signal_codes()`
# and skip anything that isn't in the set.

CATEGORY_META = {
    "discovery": {
        "label": "Descoberta: quem existe",
        "blurb": "Como a Mariana encontra as empresas e o quanto elas aparecem. "
                 "É a única etapa que pode custar dinheiro.",
    },
    "profile": {
        "label": "Perfil: o que elas são",
        "blurb": "Lido das páginas que a empresa já publica. Grátis, sem IA, "
                 "poucas requisições por empresa. São os sinais que deixam a "
                 "mensagem específica (inclusive presença em vídeo).",
    },
    "people": {
        "label": "Pessoas: quem decide",
        "blurb": "Pessoas com nome e se são elas que podem dizer sim.",
    },
    "verification": {
        "label": "Contato: dá pra chegar neles",
        "blurb": "Se o endereço vai receber de verdade, e o que fazer quando "
                 "não vai.",
    },
}
CATEGORY_ORDER = ["discovery", "profile", "people", "verification"]


@app.get("/api/signals")
async def get_signals():
    """The signal vocabulary, grouped for review, with live cohort sizes."""
    try:
        from harvey.signals import seed_signal_catalog

        state = _state()
        await state.init_db()
        # Seeding is idempotent and never overrides a decision the user made,
        # so it is safe to run on every load — new signals shipped in an
        # upgrade show up as `proposed` without any migration step.
        await seed_signal_catalog(state)

        codes = await state.get_signal_codes()
        counts = {c["signal_code"]: c for c in await state.signal_counts()}

        groups, summary = [], {"proposed": 0, "confirmed": 0, "rejected": 0}
        for cat in CATEGORY_ORDER:
            rows = []
            for sig in codes:
                if sig.get("category") != cat:
                    continue
                seen = counts.get(sig["code"], {})
                rows.append({
                    **sig,
                    "companies": seen.get("companies", 0),
                    "observations": seen.get("observations", 0),
                })
            if rows:
                meta = CATEGORY_META.get(cat, {})
                groups.append({
                    "key": cat,
                    "label": meta.get("label", cat.title()),
                    "blurb": meta.get("blurb", ""),
                    "signals": rows,
                })
        for sig in codes:
            summary[sig.get("status", "proposed")] = (
                summary.get(sig.get("status", "proposed"), 0) + 1
            )

        return {"summary": summary, "groups": groups, "total": len(codes)}
    except Exception as e:
        logger.exception("signals load failed")
        return {"error": str(e), "groups": [], "summary": {}}


@app.post("/api/signals/status")
async def set_signals_status(request: Request):
    """Confirm or reject one signal, or a whole category at once."""
    try:
        body = await request.json()
        status = (body.get("status") or "").strip()
        codes = body.get("codes") or ([body["code"]] if body.get("code") else [])
        if status not in ("proposed", "confirmed", "rejected"):
            return JSONResponse(
                {"success": False, "message": f"invalid status: {status!r}"},
                status_code=400,
            )
        if not codes:
            return JSONResponse(
                {"success": False, "message": "no signal codes given"}, status_code=400
            )

        from harvey.signals import seed_signal_catalog

        state = _state()
        await state.init_db()
        # Seed first: a confirm that arrives before anything has loaded the
        # catalog would otherwise report success while changing nothing.
        await seed_signal_catalog(state)

        changed, unknown = 0, []
        for code in codes:
            if await state.set_signal_status(code, status):
                changed += 1
            else:
                unknown.append(code)
        return {
            "success": True, "changed": changed,
            "status": status, "unknown": unknown,
        }
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/cohort")
async def preview_cohort(request: Request):
    """How many companies carry ALL these signals and none of those.

    The payoff for confirming signals: a cohort is a query, not a list. Set
    intersection happens in SQL — intersecting in JS over a capped fetch
    silently returns the wrong answer.
    """
    try:
        body = await request.json()
        require = [c for c in (body.get("require") or []) if c]
        exclude = [c for c in (body.get("exclude") or []) if c]
        if not require:
            return {"size": 0, "companies": []}

        state = _state()
        await state.init_db()
        ids = await state.cohort(require, exclude, limit=1000)
        if not ids:
            return {"size": 0, "companies": []}

        placeholders = ",".join("?" for _ in ids[:200])
        rows = await query_db(
            f"SELECT id, name, domain, industry, location FROM companies "
            f"WHERE id IN ({placeholders})",
            tuple(ids[:200]),
        )
        return {"size": len(ids), "companies": rows}
    except Exception as e:
        return JSONResponse({"size": 0, "companies": [], "error": str(e)}, status_code=500)


@app.get("/api/runs")
async def get_runs_api():
    """The collector run log — what ran, when, what it produced and cost."""
    try:
        state = _state()
        await state.init_db()
        await state.sweep_stale_runs()
        return await state.get_runs(limit=25)
    except Exception as e:
        return {"error": str(e)}


WEB_DIR = (Path(__file__).resolve().parent / "web")


TEXT_TYPES = {".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml"}
BINARY_TYPES = {".woff2": "font/woff2", ".woff": "font/woff", ".png": "image/png"}


@app.get("/static/{path:path}")
async def static_file(path: str):
    """Serve the dashboard's own assets from disk.

    Read per-request rather than cached at import: editing app.css and hitting
    reload is the whole point of having them as real files. Fonts are vendored
    rather than fetched from a CDN — this is a local tool and it should work
    with the network off.
    """
    target = (WEB_DIR / path).resolve()
    root = WEB_DIR.resolve()
    if not target.is_file() or not target.is_relative_to(root):
        return PlainTextResponse("not found", status_code=404)

    if target.suffix in BINARY_TYPES:
        return Response(
            target.read_bytes(),
            media_type=BINARY_TYPES[target.suffix],
            headers={"Cache-Control": "public, max-age=604800"},
        )
    return PlainTextResponse(
        target.read_text(encoding="utf-8"),
        media_type=TEXT_TYPES.get(target.suffix, "text/plain"),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


def start_dashboard(host: str = "127.0.0.1", port: int = 5555):
    """Start the dashboard server."""
    import uvicorn

    print(f"\n  Mariana Dashboard running at http://{host}:{port}")
    print("  Press Ctrl+C to stop.\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
