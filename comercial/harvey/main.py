"""Mariana's main heartbeat loop. Always Be Closing."""

import asyncio
import logging
import signal
import sys
from datetime import datetime, time, timedelta

import pytz

from harvey.brain import Brain
from harvey.config import ConfigError, load_config, load_env, MarianaConfig
from harvey.pipeline import run_profile_stage
from harvey.state import StateManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("harvey")

# Backoff for consecutive failed cycles: 60s, 120s, 240s, ... capped at 15 min
ERROR_BACKOFF_BASE = 60
ERROR_BACKOFF_CAP = 900

# Hard ceiling on one cycle's parallel agents. return_exceptions=True on
# gather() only isolates a task that raises — a task that hangs (a socket or
# lock that never resolves) blocks gather() forever, taking the whole
# heartbeat loop down silently with it. This is the only thing standing
# between one stuck agent and Mariana freezing for hours with no agent
# knowing it's dead — found in production after exactly that happened.
CYCLE_TIMEOUT_SECONDS = 600

# Cap on a single quiet-hours sleep chunk. See the quiet-hours block in
# heartbeat() for why this exists — a system sleep/wake cycle during one
# multi-hour asyncio.wait_for left Mariana silently stalled well past when
# quiet hours actually ended.
QUIET_HOURS_POLL_SECONDS = 300

# Phase-1 tasks that read replies; sending waits for all of them to succeed.
REPLY_READERS = ("handle_replies", "read_replies")


def in_quiet_hours(config: MarianaConfig) -> bool:
    """Check if we're currently in quiet hours."""
    qh = config.usage.quiet_hours
    tz = pytz.timezone(qh.timezone)
    now = datetime.now(tz).time()
    start = time.fromisoformat(qh.start)
    end = time.fromisoformat(qh.end)

    if start <= end:
        return start <= now <= end
    else:
        # Quiet hours cross midnight (e.g., 22:00 - 07:00)
        return now >= start or now <= end


def seconds_until_quiet_hours_end(config: MarianaConfig) -> int:
    """Calculate seconds until quiet hours end."""
    qh = config.usage.quiet_hours
    tz = pytz.timezone(qh.timezone)
    now = datetime.now(tz)
    end = time.fromisoformat(qh.end)
    end_today = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)

    if end_today <= now:
        # End time is tomorrow
        end_today = end_today + timedelta(days=1)

    delta = end_today - now
    return max(int(delta.total_seconds()), 60)


async def decide_next_action(
    brain: Brain,
    state: StateManager,
    config: MarianaConfig,
    summary: dict | None = None,
) -> str:
    """Decide what Mariana should do next based on current state.

    Uses deterministic priority rules (handle_replies > send_campaign >
    write_campaign > prospect > idle) instead of burning a Claude call on a
    decision that is fully derivable from pipeline counts. This saves budget
    every cycle and removes a fragile LLM string-parsing step.
    """
    if summary is None:
        summary = await state.get_state_summary()

    prospects = summary.get("prospects") or {}
    new_prospects = prospects.get("new", 0) if isinstance(prospects, dict) else 0
    draft_campaigns = summary.get("draft_campaigns", 0) or 0
    open_conversations = summary.get("open_conversations", 0) or 0

    if open_conversations > 0:
        action, reason = "handle_replies", f"{open_conversations} conversa(s) aberta(s) esperando"
    elif draft_campaigns > 0:
        action, reason = "send_campaign", f"{draft_campaigns} campanha(s) pronta(s) para a fila"
    elif new_prospects > 0:
        action, reason = "write_campaign", f"{new_prospects} lead(s) novo(s) sem mensagem ainda"
    elif new_prospects < 20:
        action, reason = "prospect", f"só {new_prospects} lead(s) novo(s); o funil precisa de leads"
    else:
        action, reason = "idle", "funil saudável; rodando a análise"

    logger.info(f"Decisão: {action} ({reason})")
    return action


async def _run_agents(tasks: list) -> dict:
    """Run (name, coroutine) pairs in parallel; return {name: outcome}.

    Errors are caught per task so one bad agent never takes down the cycle,
    and the whole batch is bounded so one HUNG agent (no exception, just
    never returns) can't either. A task's outcome is what it returned, or
    the exception it raised; a task cut off by the bound has no outcome.
    """
    if not tasks:
        return {}
    if len(tasks) > 1:
        logger.info(f"Rodando {len(tasks)} agentes em paralelo: {[t[0] for t in tasks]}")
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*[t[1] for t in tasks], return_exceptions=True),
            timeout=CYCLE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(
            f"O ciclo passou de {CYCLE_TIMEOUT_SECONDS}s com "
            f"{[t[0] for t in tasks]} ainda rodando: cancelado, "
            "seguindo para o próximo ciclo em vez de travar."
        )
        results = []
    outcomes = {}
    for (name, _), result in zip(tasks, results):
        if isinstance(result, asyncio.CancelledError):
            raise result
        if isinstance(result, Exception):
            logger.error(f"O agente {name} falhou: {result}", exc_info=result)
        outcomes[name] = result
    return outcomes


async def _interruptible_sleep(seconds: float, stop_event: asyncio.Event) -> bool:
    """Sleep up to `seconds`, waking immediately on shutdown.

    Returns True if a shutdown was requested during the sleep.
    """
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
        return True
    except asyncio.TimeoutError:
        return False


async def heartbeat(stop_event: asyncio.Event | None = None):
    """Mariana's main loop. Wakes up, decides, acts, sleeps. Repeat."""
    if stop_event is None:
        stop_event = asyncio.Event()

    logger.info("=" * 60)
    logger.info("Mariana está online. Bora fechar job.")
    logger.info("=" * 60)

    try:
        config = load_config()
    except (ConfigError, Exception) as e:
        if isinstance(e, (KeyboardInterrupt, asyncio.CancelledError)):
            raise
        logger.error(f"Não deu para ligar: erro na configuração:\n{e}")
        return
    env = load_env()
    state = StateManager()
    brain = Brain(state, config.brain)
    logger.info(
        f"Pensando com {brain.provider_label}"
        + (f" ({brain.model})" if brain.model else "")
        + ". Para trocar, mude brain.provider no config."
    )

    await state.init_db()
    logger.info("Banco de dados pronto.")

    # Import agents here to avoid circular imports
    from harvey.agents.scout import Scout
    from harvey.agents.writer import Writer
    from harvey.agents.sender import Sender
    from harvey.agents.handler import Handler
    from harvey.agents.analyst import Analyst
    from harvey.agents.channels import ChannelsAgent
    from harvey.agents.postjob import PostJobAgent

    scout = Scout(brain, state, config, env)
    writer = Writer(brain, state, config, env)
    sender = Sender(brain, state, config, env)
    handler = Handler(brain, state, config, env)
    analyst = Analyst(state)
    channels = ChannelsAgent(brain, state, config, env)
    postjob = PostJobAgent(brain, state, config, env)

    interval = config.usage.heartbeat_interval_minutes * 60
    max_calls = max(int(200 * (config.usage.max_daily_claude_percent / 100)), 1)
    consecutive_errors = 0

    while not stop_event.is_set():
        try:
            # 1. Check quiet hours
            if in_quiet_hours(config):
                sleep_for = seconds_until_quiet_hours_end(config)
                logger.info(f"Horário de silêncio. Dormindo {sleep_for // 60} minutos.")
                # Sleep in short polled chunks rather than one multi-hour
                # wait: found in production that a system sleep/wake cycle
                # during a long asyncio.wait_for left the process silently
                # stalled for the rest of the quiet-hours window (11+ hours
                # in one case) instead of resuming once the Mac woke up.
                # Re-checking wall-clock quiet hours every few minutes
                # bounds the worst case to QUIET_HOURS_POLL_SECONDS instead
                # of however long the missed timer would have run.
                shutting_down = False
                while in_quiet_hours(config):
                    if await _interruptible_sleep(QUIET_HOURS_POLL_SECONDS, stop_event):
                        shutting_down = True
                        break
                if shutting_down:
                    break
                continue

            # 2. Is the brain usable at all? (Codex: CLI version, isolation,
            # login, account and model checked without a prompt.) If not, do nothing
            # this cycle — no replies consumed, nothing written or sent —
            # and say why, rather than running agents that would each fail.
            problem = await brain.preflight()
            if problem:
                logger.error(
                    f"Mariana pausada: {problem} Nada foi enviado nem mudado. "
                    f"Confiro de novo em {config.usage.heartbeat_interval_minutes} minutos."
                )
                if await _interruptible_sleep(interval, stop_event):
                    break
                continue

            # 3. Check usage budget (real subscription quota when readable,
            # else Mariana's own call counter)
            if not await brain.is_within_budget(
                max_calls, max_percent=config.usage.max_daily_claude_percent
            ):
                logger.info(
                    f"Limite de uso do {brain.provider_label} atingido "
                    f"({config.usage.max_daily_claude_percent}% da cota ou "
                    f"{max_calls} chamadas). Dormindo 1h e confiro de novo."
                )
                if await _interruptible_sleep(3600, stop_event):
                    break
                continue

            # 4. Decide what to do
            logger.info("Conferindo o funil...")
            summary = await state.get_state_summary()
            action = await decide_next_action(brain, state, config, summary=summary)

            # 5. Execute — run independent agents in parallel where possible
            # Handler is always safe to run alongside other agents
            tasks = []
            has_open_convos = summary.get("open_conversations", 0) > 0

            if action == "handle_replies":
                tasks.append(("handle_replies", handler.run()))
            elif action == "prospect":
                tasks.append(("prospect", scout.run()))
                # Also handle replies in parallel if needed
                if has_open_convos:
                    tasks.append(("handle_replies", handler.run()))
                # Analyst is cheap (no Claude calls) — keep analytics fresh
                tasks.append(("analyze", analyst.run()))
            elif action == "write_campaign":
                tasks.append(("write_campaign", writer.run()))
                if has_open_convos:
                    tasks.append(("handle_replies", handler.run()))
            elif action == "idle":
                tasks.append(("analyze", analyst.run()))

            # Sending happens in a second phase, after every agent above has
            # finished: the handler's stop-on-reply must cancel follow-ups to
            # people who just replied before anything is sent. Native mail
            # providers drain the outbox every cycle, so their mailbox is
            # read every cycle too (handle_replies above only runs when a
            # conversation is already open).
            send_tasks = []
            if action == "send_campaign":
                send_tasks.append(("send_campaign", sender.run))
            elif sender.is_native:
                send_tasks.append(("send_outbox", sender.run))
            if sender.is_native and not any(n == "handle_replies" for n, _ in tasks):
                tasks.append(("read_replies", handler.run()))

            # WhatsApp / LinkedIn / Instagram drafts for prospects already in
            # a campaign. Bounded per cycle; nothing goes out without approval.
            if action in ("write_campaign", "send_campaign", "idle", "prospect"):
                tasks.append(("channels", channels.run()))
            # Testimonials, referrals, re-engagement before the next event.
            # Only calls the brain when a job is actually due.
            tasks.append(("postjob", postjob.run()))

            # Profiling rides along every cycle. It is three HTTP requests per
            # business with no model call, so it costs nothing against the
            # Claude budget the rest of this loop is rationing — and it is what
            # turns a name and a domain into something worth writing about.
            if summary.get("unprofiled", 0):
                tasks.append(("profile", run_profile_stage(state, limit=25)))

            outcomes = await _run_agents(tasks)

            # Phase 2: send — only after every reply-reading task this cycle
            # finished reading and handling replies (it returns True; a
            # failure, exception or timeout doesn't), and only if the brain
            # didn't stop being usable meanwhile. Otherwise a reply may be
            # unread, so its stop-on-reply hasn't run: queued emails wait.
            if send_tasks:
                unread = [n for n, _ in tasks
                          if n in REPLY_READERS and outcomes.get(n) is not True]
                paused = brain.paused_reason
                if paused or unread:
                    reason = paused or "nem todas as respostas puderam ser lidas e tratadas."
                    logger.error(
                        f"Sem envios neste ciclo: {reason} Os emails da fila esperam "
                        "até as respostas poderem ser lidas de novo."
                    )
                else:
                    await _run_agents([(name, run()) for name, run in send_tasks])

            # 6. Log the action (best-effort; never kills the loop)
            try:
                await state.log_action(action_type=action, agent="main")
            except Exception as e:
                logger.warning(f"Não deu para registrar a ação '{action}': {e}")

            consecutive_errors = 0

            # 7. Sleep until next heartbeat
            logger.info(
                f"Ciclo concluído. Dormindo {config.usage.heartbeat_interval_minutes} minutos."
            )
            if await _interruptible_sleep(interval, stop_event):
                break

        except (KeyboardInterrupt, asyncio.CancelledError):
            break
        except Exception as e:
            consecutive_errors += 1
            backoff = min(
                ERROR_BACKOFF_BASE * (2 ** (consecutive_errors - 1)),
                ERROR_BACKOFF_CAP,
            )
            logger.error(
                f"Erro no ciclo (falha nº {consecutive_errors}): {e}",
                exc_info=True,
            )
            logger.info(f"Recuperando... dormindo {backoff}s antes de tentar de novo.")
            if await _interruptible_sleep(backoff, stop_event):
                break

    logger.info("Mariana encerrando. Até a próxima.")


def _needs_setup() -> bool:
    """Check if Mariana needs first-time setup."""
    from harvey.paths import PROJECT_ROOT
    from harvey.config import _find_config_file, ConfigFileNotFoundError

    env_file = PROJECT_ROOT / ".env"

    # If .env doesn't exist, definitely needs setup
    if not env_file.exists():
        return True

    # harvey.local.yaml wins over the tracked harvey.yaml template, same
    # resolution order the real config loader uses (see config.py).
    try:
        config_file = _find_config_file()
    except ConfigFileNotFoundError:
        return True

    try:
        with open(config_file, encoding="utf-8") as f:
            import yaml
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            return True
        company = (config.get("persona") or {}).get("company", "")
        if company in ("Your Company", ""):
            return True
    except Exception:
        return True

    return False


async def _run_with_signals():
    """Run the heartbeat with SIGINT/SIGTERM wired to a graceful shutdown."""
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_shutdown(sig_name: str):
        if stop_event.is_set():
            logger.info("Segundo pedido para parar: saindo agora.")
            sys.exit(1)
        logger.info(f"Recebi {sig_name}. Terminando o que estou fazendo e desligando...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown, sig.name)
        except (NotImplementedError, RuntimeError):
            # Windows / non-main-thread fallback
            signal.signal(sig, lambda s, f: _request_shutdown(signal.Signals(s).name))

    await heartbeat(stop_event)


def main():
    """Entry point."""
    # Check for first-time setup
    if _needs_setup():
        print("\n  Primeira vez? Antes de tudo, a Mariana precisa te conhecer.\n")
        from harvey.onboard import run_onboarding
        asyncio.run(run_onboarding())
        return

    try:
        asyncio.run(_run_with_signals())
    except KeyboardInterrupt:
        logger.info("Até mais.")


if __name__ == "__main__":
    main()
