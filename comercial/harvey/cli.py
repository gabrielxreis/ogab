"""Mariana CLI — simple commands to install, setup, run, and manage Mariana."""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path


MIN_PYTHON = (3, 11)


def _check_python_version():
    """Refuse to install on a Python that cannot run Mariana.

    `python3 -m venv .venv` on macOS builds the venv from /usr/bin/python3,
    which is 3.9 — old enough that Mariana's `X | Y` type syntax fails at
    import. The install itself appears to succeed and the failure surfaces
    later as an unrelated-looking ImportError, so check up front and name the
    fix.
    """
    if sys.version_info >= MIN_PYTHON:
        return

    have = f"{sys.version_info.major}.{sys.version_info.minor}"
    want = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    print(f"\n  A Mariana precisa do Python {want} ou mais novo. Este é o Python {have}.")
    print(f"  ({sys.executable})\n")
    print("  No macOS, o `python3` costuma ser o 3.9 do sistema, então o ambiente")
    print("  criado com ele também é 3.9. Crie o ambiente com um Python mais novo:\n")
    print("    brew install python@3.13")
    print("    rm -rf .venv")
    print("    $(brew --prefix)/bin/python3.13 -m venv .venv")
    print("    source .venv/bin/activate && pip install -e .\n")
    sys.exit(1)


def cmd_install(args):
    """Install all dependencies including Playwright browsers."""
    _check_python_version()
    print("\n  Instalando as dependências da Mariana...\n")

    # Install Python packages
    print("  [1/2] Instalando os pacotes Python...")
    requirements = Path(args._project_root) / "requirements.txt"
    if requirements.exists():
        pip_args = ["-r", "requirements.txt"]
    else:
        # Fall back to an editable install from pyproject.toml
        pip_args = ["-e", "."]
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *pip_args],
        cwd=args._project_root,
    )
    if result.returncode != 0:
        print("\n  Não deu para instalar os pacotes Python.")
        print("  Dica: confira se está dentro de um ambiente virtual "
              "(python3 -m venv .venv && source .venv/bin/activate).")
        sys.exit(1)
    print("  ✓ Pacotes Python instalados.\n")

    # Install Playwright browsers
    print("  [2/2] Instalando o navegador do Playwright...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            timeout=600,
        )
        playwright_ok = result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        playwright_ok = False
    if not playwright_ok:
        print("\n  Não deu para instalar o navegador do Playwright (opcional: usado no PDF das propostas sem Chrome).")
    else:
        print("  ✓ Navegador do Playwright instalado.\n")

    _ensure_importable(args._project_root)
    print("  Mariana instalada. Agora rode 'mariana onboard'.\n")


def _ensure_importable(project_root: str):
    """Make sure `import harvey` works outside the repo directory.

    Python 3.13 silently skips .pth files carrying the macOS 'hidden'
    file flag, and some Macs propagate that flag to everything inside
    dot-directories like .venv — which breaks editable installs. When
    that happens, fall back to symlinking the package into site-packages
    (imports don't check the hidden flag; only .pth parsing does).
    """
    check = subprocess.run(
        [sys.executable, "-c", "import harvey"],
        cwd="/", capture_output=True,
    )
    if check.returncode == 0:
        return

    try:
        import site
        site_packages = Path(site.getsitepackages()[0])
        link = site_packages / "harvey"
        target = Path(project_root) / "harvey"
        if not link.exists() and target.is_dir():
            link.symlink_to(target)
            recheck = subprocess.run(
                [sys.executable, "-c", "import harvey"],
                cwd="/", capture_output=True,
            )
            if recheck.returncode == 0:
                print("  ✓ Corrigido: o pacote não estava visível (o .pth era "
                      "ignorado; liguei o pacote direto).\n")
                return
    except OSError as e:
        print(f"  Não deu para aplicar a correção: {e}")

    print("\n  Atenção: o pacote não carrega fora da pasta do projeto.")
    print("  Rode os comandos na pasta do projeto, ou reinstale com:")
    print("    pip install -e . --config-settings editable_mode=compat\n")


def cmd_setup(args):
    """Run the interactive setup wizard."""
    from harvey.setup import run_setup

    asyncio.run(run_setup())


def cmd_run(args):
    """Start Mariana's heartbeat loop."""
    from harvey.main import main

    main()


def cmd_train(args):
    """Train Mariana on a website."""
    from harvey.trainer import Trainer

    url = args.url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
        print(f"  Sem http/https: usando {url}")

    if args.max_pages < 1:
        print("  max_pages precisa ser pelo menos 1.")
        sys.exit(2)

    from pydantic import ValidationError
    from harvey.config import BrainConfig, ConfigError, load_brain_config

    try:
        brain_config = load_brain_config()
        overrides = {
            k: v for k, v in (
                ("provider", args.provider),
                ("model", args.model),
                ("reasoning_effort", args.reasoning_effort),
            ) if v is not None
        }
        if overrides:
            if "provider" in overrides and overrides["provider"] != brain_config.provider:
                # A different provider never inherits the other one's model.
                brain_config = BrainConfig(**overrides)
            else:
                brain_config = BrainConfig(**{**brain_config.model_dump(), **overrides})
    except (ConfigError, ValidationError) as e:
        print(f"  {e}")
        sys.exit(2)

    trainer = Trainer(brain_config=brain_config)
    asyncio.run(trainer.train(url, max_pages=args.max_pages))


def cmd_dashboard(args):
    """Launch the local web dashboard."""
    from harvey.dashboard import start_dashboard

    if not 1 <= args.port <= 65535:
        print(f"  Porta inválida: {args.port}. Use de 1 a 65535.")
        sys.exit(2)

    start_dashboard(host=args.host, port=args.port)


def cmd_status(args):
    """Show current pipeline status."""
    from harvey.state import StateManager

    async def _status():
        state = StateManager()
        await state.init_db()
        summary = await state.get_state_summary()

        print("\n  Resumo do funil da Mariana")
        print("  " + "=" * 40)
        print(f"  Leads:                {summary['prospects']}")
        print(f"  Campanhas rascunho:   {summary['draft_campaigns']}")
        print(f"  Campanhas ativas:     {summary['active_campaigns']}")
        print(f"  Conversas abertas:    {summary['open_conversations']}")
        by_provider = summary.get("usage_today_by_provider", {})
        print(f"  Chamadas Claude hoje: {by_provider.get('claude', summary['usage_today'])}")
        print(f"  Chamadas Codex hoje:  {by_provider.get('codex', 0)}")
        from harvey.brain import BRAIN_STATUS_KEY, Brain, active_brain_status
        from harvey.config import ConfigError, load_brain_config
        try:
            brain_config = load_brain_config()
        except ConfigError as e:
            brain_config, config_error = None, e
        # Only the configured provider's health: an old Codex pause says
        # nothing once harvey.yaml has switched to Claude.
        brain_status = active_brain_status(
            await state.get_setting(BRAIN_STATUS_KEY),
            brain_config.provider if brain_config else "")
        healthy = True
        if getattr(args, "check", False):
            if brain_config is None:
                print(f"  Cérebro:              erro no config: {config_error}")
                healthy = False
            else:
                brain = Brain(state, brain_config)
                problem = await brain.preflight()
                label = brain.provider_label + (f" ({brain.model})" if brain.model else "")
                if problem:
                    healthy = False
                    print(f"  Cérebro:              {label} NÃO ESTÁ PRONTO")
                    print(f"                        {problem}")
                elif brain.provider == "codex":
                    print(f"  Cérebro:              {label} pronto (CLI, isolamento, login, "
                          "modelo e conta conferidos; nenhum prompt enviado)")
                else:
                    print(f"  Cérebro:              {label} (não conferido: o Claude é conferido "
                          "na primeira chamada)")
        elif brain_status.get("status") == "paused":
            label = {"claude": "Claude", "codex": "Codex"}.get(brain_status.get("provider"), "Brain")
            print(f"  Cérebro:              {label} PAUSADO desde {brain_status.get('since', '?')}")
            print(f"                        {brain_status.get('reason', '')}")
        print()
        return healthy

    if not asyncio.run(_status()):
        # `mariana status --check` failing is something scripts can act on.
        raise SystemExit(1)


def cmd_usage(args):
    """Show brain usage: active provider's quota, totals, breakdowns."""
    from harvey.state import StateManager
    from harvey.config import ConfigError, load_brain_config

    async def _usage():
        state = StateManager()
        await state.init_db()

        try:
            brain_config = load_brain_config()
        except ConfigError as e:
            print(f"  {e}")
            brain_config = None

        # Live quota for the ACTIVE provider only (best-effort). Each
        # subscription's gauge is read from its own source and labelled as
        # such; one is never shown as the other.
        windows = None
        provider = brain_config.provider if brain_config else None
        try:
            if provider == "codex":
                from harvey.codex import CodexClient, CodexQuotaClient
                windows = await CodexQuotaClient(
                    CodexClient(model=brain_config.model)).get_utilization()
            elif provider == "claude":
                from harvey.integrations.quota import QuotaClient
                windows = await QuotaClient().get_utilization()
        except Exception:
            pass

        label = {"claude": "Claude", "codex": "Codex"}.get(provider, "Cérebro")
        print(f"\n  Uso do {label}")
        print("  " + "=" * 52)
        if windows:
            labels = {"five_hour": "Janela de 5h", "seven_day": "Semanal",
                      "limit_reached": "Limite de uso"}
            for key, w in windows.items():
                resets = f"  (renova {w['resets_at']})" if w.get("resets_at") else ""
                print(f"  {labels.get(key, key):<16} {w['utilization']:5.1f}% usado{resets}")
        elif provider == "codex":
            print("  Cota indisponível (confira o 'codex login', a versão do Codex CLI "
                  "e a rede).")
        elif provider == "claude":
            print("  Cota indisponível (rode 'claude login' ou confira a rede).")

        totals = await state.usage_totals()
        print()
        print(f"  {'Período':<10} {'Chamadas':>8} {'Entrada':>11} {'Saída':>10} {'Cache':>12}")
        for label, key in (("Today", "today"), ("7 days", "week"), ("30 days", "month")):
            t = totals.get(key) or {}
            print(
                f"  {label:<10} {t.get('calls', 0):>7} "
                f"{t.get('input_tokens', 0):>12,} {t.get('output_tokens', 0):>10,} "
                f"{t.get('cache_read_tokens', 0):>12,}"
            )

        by_provider = await state.usage_by_provider(days=args.days)
        if len(by_provider) > 1 or (by_provider and by_provider[0]["provider"] != "claude"):
            print(f"\n  Por provedor (últimos {args.days} dias):")
            for row in by_provider:
                print(
                    f"    {row['provider']:<14} {row['calls']:>5} calls  "
                    f"{row['output_tokens']:>10,} out tokens"
                )

        by_agent = await state.usage_by_agent(days=args.days)
        if by_agent:
            print(f"\n  Por agente (últimos {args.days} dias):")
            for row in by_agent:
                print(
                    f"    {row['agent']:<14} {row['calls']:>5} calls  "
                    f"{row['output_tokens']:>10,} out tokens"
                )

        by_task = await state.usage_by_task(days=args.days)
        if by_task:
            print(f"\n  Por tarefa (últimos {args.days} dias):")
            for row in by_task[:10]:
                print(
                    f"    {row['task']:<22} {row['calls']:>5} calls  "
                    f"{row['output_tokens']:>10,} out tokens"
                )
        print(
            "\n  Assinatura não cobra por token: isto é contagem de uso,"
            "\n  não custo.\n"
        )

    asyncio.run(_usage())


def cmd_export(args):
    """Export the prospect list as a sequencer-ready CSV."""
    from harvey.state import StateManager
    from harvey.export import export_prospects_csv

    async def _export():
        state = StateManager()
        await state.init_db()

        email_statuses = None
        if args.email_status:
            email_statuses = [s.strip() for s in args.email_status.split(",") if s.strip()]
        statuses = None
        if args.status:
            statuses = [s.strip() for s in args.status.split(",") if s.strip()]

        count, _ = await export_prospects_csv(
            state,
            out_path=args.out,
            email_statuses=email_statuses,
            min_score=args.min_score,
            statuses=statuses,
            include_all=args.all,
        )
        scope = "todos os leads" if args.all else (
            f"status de email {email_statuses or ['verified', 'risky']}"
            + (f", nota >= {args.min_score}" if args.min_score else "")
        )
        print(f"\n  {count} lead(s) exportado(s) para {args.out}  ({scope})")
        if count == 0 and not args.all:
            print("  Dica: nenhum email entregável ainda? Coloque uma REOON_API_KEY no .env")
            print("  para a Mariana verificar os endereços, ou use --all para a lista crua.\n")
        else:
            print("  O CSV entra direto no Instantly, Smartlead ou qualquer ferramenta de sequência.\n")

    asyncio.run(_export())


def cmd_gmail(args):
    """Gmail provider utilities (auth / test)."""
    from harvey.config import load_env

    env = load_env()
    if args.gmail_action == "auth":
        from harvey.integrations.gmail import run_auth_flow
        ok = run_auth_flow(env.gmail_client_id, env.gmail_client_secret)
        sys.exit(0 if ok else 1)

    if args.gmail_action == "test":
        from harvey.config import load_config
        from harvey.integrations.gmail import GmailProvider

        async def _test():
            provider = GmailProvider(load_config(), env)
            ok, detail = await provider.test_connection()
            print(f"\n  {'✓' if ok else '✗'} {detail}\n")
            sys.exit(0 if ok else 1)
        asyncio.run(_test())


def cmd_microsoft(args):
    """Microsoft 365 provider utilities (auth / test)."""
    from harvey.config import load_env

    env = load_env()
    if args.microsoft_action == "auth":
        from harvey.integrations.microsoft import run_auth_flow
        ok = run_auth_flow(env.m365_client_id, env.m365_tenant_id)
        sys.exit(0 if ok else 1)

    if args.microsoft_action == "test":
        from harvey.config import load_config
        from harvey.integrations.microsoft import MicrosoftProvider

        async def _test():
            provider = MicrosoftProvider(load_config(), env)
            ok, detail = await provider.test_connection()
            print(f"\n  {'✓' if ok else '✗'} {detail}\n")
            sys.exit(0 if ok else 1)
        asyncio.run(_test())


def cmd_outbox(args):
    """Review and approve queued outgoing emails."""
    from harvey.state import StateManager

    async def _outbox():
        state = StateManager()
        await state.init_db()

        if args.approve_all:
            n = await state.approve_outbox()
            print(f"\n  {n} email(s) aprovado(s). Saem no horário agendado.\n")
            return
        if args.approve:
            n = await state.approve_outbox(args.approve)
            print(f"\n  {'Aprovado.' if n else 'Nenhum item pendente com esse id.'}\n")
            return
        if args.reject:
            await state.update_outbox_item(args.reject, status="rejected")
            print("\n  Recusado.\n")
            return

        paused = await state.get_setting("sending_paused")
        if paused:
            print(f"\n  ⚠ ENVIOS PAUSADOS: {paused}")
            print("  Retome com: mariana sending resume")

        pending = await state.get_outbox(status="pending_review", limit=50)
        approved = await state.get_outbox(status="approved", limit=10)
        print(f"\n  Outbox: {len(pending)} esperando aprovação, "
              f"{len(approved)}+ aprovados/agendados")
        print("  " + "=" * 60)
        for item in pending:
            print(f"\n  [{item['id']}] etapa {item['step']} ({item['kind']}) "
                  f"→ {item['to_email']}  (sai em {item['send_at'][:16]})")
            print(f"  Assunto: {item['subject']}")
            body_preview = (item["body"][:200] + "...") if len(item["body"]) > 200 else item["body"]
            for line in body_preview.splitlines():
                print(f"    {line}")
        if pending:
            print("\n  Aprovar: mariana outbox --approve <id>   |   todos: mariana outbox --approve-all")
            print("  Recusar: mariana outbox --reject <id>\n")
        else:
            print("  Nada esperando revisão.\n")

    asyncio.run(_outbox())


def cmd_profile(args):
    """Read what companies' own websites say about them. Free, no Claude calls."""
    from harvey.state import StateManager
    from harvey.pipeline import run_profile_stage

    async def _profile():
        state = StateManager()
        await state.init_db()

        pending = await state.count_companies_needing_profile(args.stale_days)
        if not pending:
            print("\n  Nada para ler. Toda empresa com site foi lida "
                  "recentemente.\n")
            return

        print(f"\n  {pending} empresas para ler. Lendo até "
              f"{args.limit}...\n")
        companies, observations, _ = await run_profile_stage(
            state, limit=args.limit, stale_days=args.stale_days)
        print(f"  {companies} sites lidos → {observations} observações (grátis)")
        print("\n  Veja o resultado: mariana dashboard → Sinais\n")

    asyncio.run(_profile())


def cmd_discover(args):
    """Find businesses. The only stage that spends money, so it estimates first."""
    from harvey.state import StateManager
    from harvey.config import load_config
    from harvey.collectors.discover import (
        PROVIDERS, build_queries, provider_menu, run_discovery,
    )

    async def _discover():
        if args.providers:
            print("\n  Fontes de busca")
            print("  " + "=" * 68)
            for m in provider_menu():
                mark = "ready" if m["configured"] else "needs setup"
                print(f"\n  {m['label']}  [{m['key']}]  ({mark})")
                print(f"    {m['blurb']}")
                print(f"    Custo: {m['cost_note']}")
                print(f"    Grátis: {m['free_tier']}")
                if m["env_keys"]:
                    print(f"    Precisa: {', '.join(m['env_keys'])} no .env  ({m['signup_url']})")
                if m["caveat"]:
                    print(f"    Obs.: {m['caveat']}")
            print("\n  Rode uma com: mariana discover --provider <fonte> --estimate\n")
            return

        if args.provider not in PROVIDERS:
            print(f"\n  Fonte desconhecida: {args.provider!r}. "
                  f"Veja: mariana discover --providers\n")
            return

        config = load_config()
        state = StateManager()
        await state.init_db()

        # Semicolons, not commas: "Denver, CO" is one city, not two.
        cities = [c.strip() for c in args.city.split(";") if c.strip()] or None
        queries = build_queries(config, cities=cities,
                                depth=args.depth, limit=args.limit)

        report = await run_discovery(state, config, args.provider, queries,
                                     max_spend=args.max_spend, dry_run=True)
        print(f"\n  {len(queries)} buscas via {PROVIDERS[args.provider].label}")
        for q in queries[:8]:
            print(f"    - {q.keyword()}" + ("" if q.coordinate else
                  "   (sem coordenadas: coloque icp.geo_coordinates para buscar por raio)"))
        if len(queries) > 8:
            print(f"    ... e mais {len(queries) - 8}")
        print(f"\n  Custo estimado: US$ {report.estimated_cost:.4f}"
              f"   (teto: US$ {args.max_spend:.2f})")

        if args.estimate:
            print("\n  Só estimativa. Rode sem --estimate para coletar.\n")
            return

        print("\n  Rodando...\n")
        from harvey.pipeline import run_prospecting

        result = await run_prospecting(
            state, config, args.provider, queries,
            max_spend=args.max_spend, profile=not args.no_profile,
        )
        r = result.discover or {}
        print(f"  BUSCA: {r.get('found', 0)} resultados em "
              f"{r.get('queries', 0)} buscas")
        print(f"    {r.get('new_companies', 0)} empresas novas, "
              f"{r.get('known_companies', 0)} já conhecidas")
        print(f"    {r.get('junk', 0)} descartadas (diretórios/agregadores)")
        print(f"    {r.get('observations', 0)} observações registradas")
        print(f"    custo real: US$ {r.get('actual_cost', 0):.4f}")
        if r.get("stopped"):
            print(f"    parou antes: {r['stopped']}")

        if args.no_profile:
            print("\n  LEITURA: pulada (--no-profile)")
        else:
            print(f"\n  LEITURA: {result.profiled_companies} sites lidos, "
                  f"{result.profile_observations} observações  (grátis)")

        for err in result.errors[:5]:
            print(f"    ! {err}")
        print("\n  Próximo: mariana dashboard → Sinais → construtor de público\n")

    asyncio.run(_discover())


def cmd_signals(args):
    """Review the signal vocabulary — Mariana proposes, you confirm.

    Nothing is collected until a signal is confirmed, so a fresh install
    prospects against nothing until someone makes these decisions.
    """
    from harvey.state import StateManager
    from harvey.signals import seed_signal_catalog

    async def _signals():
        state = StateManager()
        await state.init_db()
        await seed_signal_catalog(state)

        codes = [a.strip().upper() for a in (args.confirm or args.reject or "").split(",")
                 if a.strip()]
        if codes:
            status = "confirmed" if args.confirm else "rejected"
            if codes == ["ALL"]:
                codes = [c["code"] for c in await state.get_signal_codes()]
            elif codes == ["FREE"]:
                # Only signals whose cost note STARTS with free/included. A
                # substring match would sweep in "1 credit (free tiers
                # available)", which is not free.
                codes = [c["code"] for c in await state.get_signal_codes()
                         if (c["cost_note"] or "").lower().startswith(("free", "included", "grátis", "incluído"))]
            changed = sum(
                [1 for c in codes if await state.set_signal_status(c, status)]
            )
            print(f"\n  {changed} sinal(is) {'confirmado(s)' if status == 'confirmed' else 'desligado(s)'}.\n")
            return

        rows = await state.get_signal_codes()
        counts = {c["signal_code"]: c for c in await state.signal_counts()}
        by_status = {"confirmed": 0, "proposed": 0, "rejected": 0}
        for r in rows:
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1

        print(f"\n  Sinais: {by_status['confirmed']} confirmados, "
              f"{by_status['proposed']} esperando você, {by_status['rejected']} desligados")
        print("  " + "=" * 66)
        mark = {"confirmed": "[sim]", "proposed": "[ ? ]", "rejected": "[não]"}
        current = None
        for r in rows:
            if r["category"] != current:
                current = r["category"]
                print(f"\n  {current.upper()}")
            seen = counts.get(r["code"], {}).get("companies", 0)
            seen_txt = f"  ({seen} empresas)" if seen else ""
            print(f"    {mark.get(r['status'], '     ')} {r['code']:<22} "
                  f"{r['label']}{seen_txt}")
            print(f"          {r['cost_note']}")

        if by_status["proposed"]:
            print("\n  Confirme com: mariana signals --confirm CÓDIGO[,CÓDIGO...]")
            print("  Tudo o que é grátis: mariana signals --confirm free")
            print("  Detalhes e descrições: mariana dashboard → Sinais\n")
        else:
            print("")

    asyncio.run(_signals())


def cmd_sending(args):
    """Pause/resume the sending kill switch."""
    from harvey.state import StateManager

    async def _run():
        state = StateManager()
        await state.init_db()
        if args.sending_action == "pause":
            await state.set_setting("sending_paused", "paused manually")
            print("\n  Envios pausados. Nada sai da Outbox.\n")
        elif args.sending_action == "resume":
            await state.set_setting("sending_paused", "")
            await state.set_setting("bounce_count", "0")
            print("\n  Envios retomados (contador de bounce zerado).\n")
        else:
            paused = await state.get_setting("sending_paused")
            print(f"\n  Envios: {'PAUSADOS: ' + paused if paused else 'ativos'}\n")

    asyncio.run(_run())


def main():
    from harvey.paths import PROJECT_ROOT
    # Windows terminals default to cp1252: accents and ✓ would crash print().
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    project_root = str(PROJECT_ROOT)

    parser = argparse.ArgumentParser(
        prog="mariana",
        description="Mariana: secretária de IA que fecha trabalhos de audiovisual e edição.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # mariana install
    sub = subparsers.add_parser("install", help="Instalar dependências")
    sub.set_defaults(func=cmd_install)

    # mariana setup
    sub = subparsers.add_parser("setup", help="Assistente de configuração (o onboard é o recomendado)")
    sub.set_defaults(func=cmd_setup)

    # mariana run
    sub = subparsers.add_parser("run", help="Ligar o ciclo da Mariana")
    sub.set_defaults(func=cmd_run)

    # mariana train <url>
    sub = subparsers.add_parser("train", help="Aprender um produto a partir de um site")
    sub.add_argument("url", help="Endereço do site para ler e aprender")
    sub.add_argument(
        "max_pages",
        nargs="?",
        type=int,
        default=100,
        help="Máximo de páginas a ler (padrão: 100)",
    )
    sub.add_argument(
        "--provider", choices=["claude", "codex"], default=None,
        help="Assinatura usada para pensar (padrão: a do config, senão claude)",
    )
    sub.add_argument("--model", default=None, help="Modelo deste provedor (padrão: o do provedor)")
    sub.add_argument(
        "--reasoning-effort", default=None,
        help="Esforço de raciocínio do Codex (minimal/low/medium/high/xhigh)",
    )
    sub.set_defaults(func=cmd_train)

    # mariana dashboard
    sub = subparsers.add_parser("dashboard", help="Abrir o painel")
    sub.add_argument("--host", default="127.0.0.1", help="Endereço (padrão: 127.0.0.1)")
    sub.add_argument("--port", type=int, default=5555, help="Porta (padrão: 5555)")
    sub.set_defaults(func=cmd_dashboard)

    # mariana status
    sub = subparsers.add_parser("status", help="Mostrar o resumo do funil")
    sub.add_argument(
        "--check", action="store_true",
        help="Também testar o cérebro configurado agora (Codex: versão, isolamento "
             "e login; sem chamar o modelo)",
    )
    sub.set_defaults(func=cmd_status)

    # mariana export
    sub = subparsers.add_parser(
        "export", help="Exportar leads em CSV"
    )
    sub.add_argument("--out", default="prospects.csv", help="Arquivo de saída (padrão: prospects.csv)")
    sub.add_argument(
        "--email-status", default="",
        help="Status de email a incluir, separados por vírgula (padrão: verified,risky)",
    )
    sub.add_argument("--min-score", type=int, default=0, help="Nota mínima de perfil")
    sub.add_argument("--status", default="", help="Status do funil, separados por vírgula (ex.: new,queued)")
    sub.add_argument("--all", action="store_true", help="Exportar tudo, sem filtro")
    sub.set_defaults(func=cmd_export)

    # mariana gmail auth|test
    sub = subparsers.add_parser("gmail", help="Conectar o Gmail (e o Google Agenda)")
    sub.add_argument("gmail_action", choices=["auth", "test"],
                     help="auth: conectar uma vez; test: conferir a conexão")
    sub.set_defaults(func=cmd_gmail)

    # mariana microsoft auth|test
    sub = subparsers.add_parser("microsoft", help="Conectar o Microsoft 365")
    sub.add_argument("microsoft_action", choices=["auth", "test"],
                     help="auth: entrar uma vez; test: conferir a conexão")
    sub.set_defaults(func=cmd_microsoft)

    # mariana outbox
    sub = subparsers.add_parser("outbox", help="Revisar e aprovar emails na fila")
    sub.add_argument("--approve", metavar="ID", default="", help="Aprovar um item")
    sub.add_argument("--approve-all", action="store_true", help="Aprovar todos os pendentes")
    sub.add_argument("--reject", metavar="ID", default="", help="Recusar um item")
    sub.set_defaults(func=cmd_outbox)

    # mariana sending pause|resume|status
    sub = subparsers.add_parser("discover", help="Encontrar empresas do seu perfil de cliente")
    sub.add_argument("--provider", default="osm",
                     help="Fonte de busca (padrão: osm, grátis e sem conta)")
    sub.add_argument("--providers", action="store_true",
                     help="Listar as fontes com custo e configuração e sair")
    sub.add_argument("--estimate", action="store_true",
                     help="Mostrar o gasto estimado e sair sem chamar nada")
    sub.add_argument("--city", default="",
                     help='Semicolon-separated cities, e.g. "Denver, CO;Dallas, TX" '
                          '(default: icp.geography)')
    sub.add_argument("--depth", type=int, default=30,
                     help="Profundidade da busca (padrão: 30; 100 custa 10x desde set/2025)")
    sub.add_argument("--limit", type=int, default=100,
                     help="Máximo de resultados por busca (padrão: 100)")
    sub.add_argument("--max-spend", type=float, default=1.0,
                     help="Teto de gasto em dólares (padrão: 1.00)")
    sub.add_argument("--no-profile", action="store_true",
                     help="Não ler os sites encontrados (ler é grátis)")
    sub.set_defaults(func=cmd_discover)

    sub = subparsers.add_parser(
        "profile", help="Ler os sites das empresas encontradas (grátis, sem IA)")
    sub.add_argument("--limit", type=int, default=200,
                     help="Máximo de sites a ler (padrão: 200)")
    sub.add_argument("--stale-days", type=int, default=90,
                     help="Reler um site depois de tantos dias (padrão: 90)")
    sub.set_defaults(func=cmd_profile)

    sub = subparsers.add_parser(
        "signals", help="Revisar e confirmar os sinais que a Mariana procura")
    sub.add_argument("--confirm", metavar="CODES", default="",
                     help="Códigos a confirmar, separados por vírgula (aceita 'all' ou 'free')")
    sub.add_argument("--reject", metavar="CODES", default="",
                     help="Códigos a desligar, separados por vírgula")
    sub.set_defaults(func=cmd_signals)

    sub = subparsers.add_parser("sending", help="Botão de pânico: pausar/retomar envios")
    sub.add_argument("sending_action", nargs="?", default="status",
                     choices=["pause", "resume", "status"])
    sub.set_defaults(func=cmd_sending)

    # mariana usage
    sub = subparsers.add_parser("usage", help="Mostrar uso e cota da assinatura (Claude ou Codex)")
    sub.add_argument("--days", type=int, default=30, help="Janela em dias (padrão: 30)")
    sub.set_defaults(func=cmd_usage)

    # Mariana: onboarding, signature, email and WhatsApp checks
    from harvey.mariana_cli import register as register_mariana
    register_mariana(subparsers)

    args = parser.parse_args()
    args._project_root = project_root

    if args.command is None:
        parser.print_help()
        print("\n  Começo rápido:")
        print("    mariana onboard    : a Mariana aprende sobre você (primeiro uso)")
        print("    mariana signature  : gera e instala a assinatura de email")
        print("    mariana email-check: confere o email de envio")
        print("    mariana run        : começa a procurar e escrever")
        print("    mariana dashboard  : painel em http://localhost:5555")
        print()
        sys.exit(0)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n  Interrompido. Até mais.")
        sys.exit(130)
    except Exception as e:
        # ConfigError and friends carry actionable messages — show them
        # cleanly instead of a raw traceback.
        from harvey.config import ConfigError

        if isinstance(e, ConfigError):
            print(f"\n  Problema na configuração:\n  {e}\n")
        else:
            print(f"\n  Erro ao rodar 'mariana {args.command}': {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
