"""Mariana's own commands: onboarding, signature, email and WhatsApp checks.

Kept apart from cli.py so the upstream Mariana commands stay untouched.
"""

from __future__ import annotations

import asyncio
import json
import webbrowser
from pathlib import Path

DKIM_SELECTORS = ("google", "selector1", "selector2", "default", "k1", "s1",
                  "dkim", "mail", "zoho", "mxvault")


def cmd_onboard(args):
    from harvey.onboard import run_onboarding
    asyncio.run(run_onboarding(
        files=args.file or [], site=args.site or "",
        answers_file=args.answers or "", assume_yes=args.yes,
    ))


def cmd_signature(args):
    from harvey.config import load_config
    from harvey.signature import render_text, write_files

    config = load_config()
    paths = write_files(config)
    print("\n  Assinatura (texto, vai em todo email):\n")
    for line in render_text(config).splitlines():
        print(f"    {line}")
    print(f"\n  HTML pra colar em qualquer cliente de email: {paths['html']}")
    print(f"  Prévia no navegador: {paths['preview']}")
    if not args.no_open:
        webbrowser.open(paths["preview"].as_uri())

    if args.install_gmail:
        from harvey.config import load_env
        from harvey.integrations.gmail import GmailProvider
        provider = GmailProvider(config, load_env())
        if not provider.is_configured():
            print("\n  Gmail ainda não está conectado: rode 'mariana gmail auth'.")
            return
        ok, detail = asyncio.run(provider.install_signature(paths["html"].read_text(encoding="utf-8")))
        print(f"\n  {'✓' if ok else '✗'} {detail}")
    print()


def _txt(name: str) -> list[str]:
    import dns.resolver
    try:
        answers = dns.resolver.resolve(name, "TXT", lifetime=8)
    except Exception:
        return []
    return [b"".join(r.strings).decode(errors="replace") for r in answers]


def _mx(domain: str) -> list[str]:
    import dns.resolver
    try:
        return sorted(str(r.exchange).rstrip(".").lower()
                      for r in dns.resolver.resolve(domain, "MX", lifetime=8))
    except Exception:
        return []


def check_domain(domain: str) -> list[tuple[bool, str, str]]:
    """(ok, item, advice) for MX / SPF / DKIM / DMARC of a sending domain."""
    results = []
    mx = _mx(domain)
    google = any("google" in m for m in mx)
    microsoft = any("outlook" in m or "microsoft" in m for m in mx)
    results.append((bool(mx), "MX", ", ".join(mx[:3]) if mx else
                    "Sem MX: esse domínio não recebe email. Respostas vão se perder."))

    spf = [t for t in _txt(domain) if t.lower().startswith("v=spf1")]
    if not spf:
        include = ("include:_spf.google.com" if google else
                   "include:spf.protection.outlook.com" if microsoft else "include:<seu provedor>")
        results.append((False, "SPF", f'Crie um TXT em {domain}: "v=spf1 {include} ~all"'))
    elif len(spf) > 1:
        results.append((False, "SPF", "Há mais de um registro SPF; junte num só."))
    else:
        results.append((True, "SPF", spf[0]))

    found = ""
    for sel in DKIM_SELECTORS:
        if any("v=dkim1" in t.lower() or "k=rsa" in t.lower()
               for t in _txt(f"{sel}._domainkey.{domain}")):
            found = sel
            break
    advice = ("Ative o DKIM: Google Admin > Apps > Gmail > Autenticar email"
              if google else "Ative o DKIM no painel do seu provedor de email")
    results.append((bool(found), "DKIM", f"seletor '{found}'" if found else advice))

    dmarc = [t for t in _txt(f"_dmarc.{domain}") if t.lower().startswith("v=dmarc1")]
    results.append((bool(dmarc), "DMARC", dmarc[0] if dmarc else
                    f'Crie um TXT em _dmarc.{domain}: "v=DMARC1; p=none; rua=mailto:dmarc@{domain}"'))
    return results


def cmd_email_check(args):
    from harvey.config import load_config, load_env
    from harvey.integrations.mail_provider import get_mail_provider
    from harvey.signature import compose

    config = load_config()
    env = load_env()
    email = config.persona.email
    print(f"\n  Email de envio: {email or '(vazio: preencha persona.email)'}")
    if not email or "@" not in email:
        return
    domain = email.split("@", 1)[1].lower()
    if domain in ("gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "icloud.com"):
        print(f"  ! {domain} é um email pessoal. Funciona pra começar, mas o ideal é um")
        print("    domínio próprio (ex.: contato@suamarca.com.br) e, pra volume, um")
        print("    domínio secundário só de prospecção.")
    else:
        print(f"\n  DNS de {domain}:")
        for ok, item, detail in check_domain(domain):
            print(f"    {'✓' if ok else '✗'} {item:6} {detail}")

    provider = get_mail_provider(config, env)
    if provider is None:
        print(f"\n  Provedor '{config.channels.email.provider}' não é nativo. Use gmail,")
        print("  microsoft ou smtp em channels.email.provider.")
        return
    ok, detail = asyncio.run(provider.test_connection())
    print(f"\n  {'✓' if ok else '✗'} Conexão ({provider.name}): {detail}")
    if ok and args.send_test:
        body = ("Teste da Mariana: se este email chegou, o envio e a assinatura "
                "estão funcionando.")
        result = asyncio.run(provider.send_email(email, "teste da mariana", body))
        print(f"  {'✓' if result.ok else '✗'} Email de teste para {email}"
              + ("" if result.ok else f": {result.error}"))
        print("\n  Como vai sair:\n")
        for line in compose(config, body)[0].splitlines():
            print(f"    {line}")
    print()


def cmd_whatsapp_check(args):
    from harvey.config import load_config, load_env
    from harvey.integrations.whatsapp import CloudAPIClient, normalize_phone, wa_link

    config = load_config()
    env = load_env()
    wa = config.channels.whatsapp
    mine = normalize_phone(config.persona.signature.whatsapp, wa.default_country_code)
    print(f"\n  WhatsApp {'ligado' if wa.enabled else 'desligado'}, modo: {wa.mode}")
    print(f"  Países: {', '.join('+' + c for c in wa.countries) or 'todos'}")
    print(f"  Seu número (assinatura): {('+' + mine) if mine else '(vazio)'}")
    if wa.mode == "link":
        print("\n  Modo link: a Mariana escreve, o painel abre o seu WhatsApp com o")
        print("  texto pronto e você aperta enviar. Nada a configurar.")
        if mine:
            print(f"  Teste: {wa_link(mine, 'Teste da Mariana')}")
    else:
        client = CloudAPIClient(env.whatsapp_token, env.whatsapp_phone_number_id)
        ok, detail = asyncio.run(client.test_connection())
        print(f"\n  {'✓' if ok else '✗'} Cloud API: {detail}")
        print("  Lembrete: pela API só vão mensagens para quem respondeu ou pediu")
        print("  contato (marcado como opt-in no painel). Frio continua manual.")
    print()


async def _ctx():
    from harvey.brain import Brain
    from harvey.config import load_config, load_env
    from harvey.state import StateManager
    config = load_config()
    state = StateManager()
    await state.init_db()
    return config, load_env(), state, Brain(state, config.brain)


def cmd_events(args):
    from harvey.collectors.events import run_event_radar

    async def go():
        config, env, state, brain = await _ctx()
        return await run_event_radar(state, brain, config, env, months=args.months,
                                     max_queries=args.max_queries, estimate_only=args.estimate)
    result = asyncio.run(go())
    if args.estimate:
        print(f"\n  {result['queries']} buscas, custo estimado US$ {result['estimated_cost_usd']}")
        for q in result["sample"]:
            print(f"    ex.: {q}")
    else:
        print(f"\n  {result['events']} eventos encontrados, {result['organizers']} organizadores "
              "adicionados como empresas (sinal 'evento em ...').")
        print("  Próximo: mariana profile  (lê os sites e acha os contatos)")
    print()


def cmd_samples(args):
    from harvey.samples import write_briefs

    async def go():
        config, _, state, _ = await _ctx()
        return await write_briefs(state, top=args.top, mode=args.modo, config=config)
    path, leads = asyncio.run(go())
    print(f"\n  {len(leads)} lead(s) para amostra. Briefing para o Gab: {path}")
    for lead in leads:
        if lead.get("folder"):
            print(f"    pasta do /ogab: {lead['folder']}")
    print("  No Claude: /ogab <colar o briefing de um lead>\n")


def cmd_sample_ready(args):
    from harvey.samples import sample_ready

    async def go():
        config, _, state, brain = await _ctx()
        return await sample_ready(state, brain, config, args.prospect, args.link, mode=args.modo)
    channel = asyncio.run(go())
    where = "Outbox" if channel == "email" else "Mensagens"
    print(f"\n  Mensagem com a amostra criada ({channel}); aprove na aba {where}.\n")


def cmd_proposal(args):
    from harvey.proposal import build_proposal

    async def go():
        config, _, state, brain = await _ctx()
        convo_id = args.conversation
        if not convo_id and args.email:
            prospect = await state.get_prospect_by_email(args.email)
            for status in ("open", "needs_human", "closed"):
                for c in await state.get_conversations_by_status(status):
                    if prospect and c.prospect_id == prospect.id:
                        convo_id = c.id
        if not convo_id:
            raise SystemExit("  Conversa não encontrada (use --conversation ID ou --email).")
        return await build_proposal(state, brain, config, convo_id)
    result = asyncio.run(go())
    print(f"\n  Proposta: {result['path']}")
    if not result["pdf"]:
        print("  (Sem Chrome/Chromium pro PDF. Abra o HTML e salve como PDF, ou rode "
              "'playwright install chromium'.)")
    if not args.no_open:
        webbrowser.open(Path(result["path"]).as_uri())
    print()


def cmd_calendar_check(args):
    from harvey.integrations.calendar import CalendarClient, format_slots

    async def go():
        config, env, _, _ = await _ctx()
        client = CalendarClient(config, env)
        if not client.is_configured():
            return None, config
        return await client.get_available_slots(), config
    slots, config = asyncio.run(go())
    if slots is None:
        print("\n  Agenda não conectada: ative a Calendar API no mesmo projeto do Google Cloud")
        print("  e rode 'mariana gmail auth' de novo (pede a permissão da agenda).\n")
        return
    print(f"\n  Próximos horários livres: {format_slots(slots, config.persona.language) or 'nenhum'}\n")


def cmd_notify_test(args):
    from harvey.notify import notify

    async def go():
        from harvey.config import load_config, load_env
        await notify(load_config(), load_env(), "Mariana: teste",
                     "Se chegou, os avisos de resposta estão funcionando.")
    asyncio.run(go())
    print("\n  Aviso enviado (Mac + ntfy/Telegram se configurados).\n")


def cmd_dossie(args):
    from harvey import dossie

    if args.claude_memory is not None:
        folders = [Path(args.claude_memory).expanduser()] if args.claude_memory else dossie.claude_memory_dirs()
        async def from_memory(text, source):
            _, _, _, brain = await _ctx()
            return await dossie.answer_from(brain, text, source)
        for folder in folders:
            text = dossie.read_claude_memory(folder)
            if not text:
                continue
            source = f"memória do Claude Code ({folder.parent.name})"
            print(f"  Lendo {folder} e organizando no formato do dossiê (leva uns minutos)...")
            organized = asyncio.run(from_memory(text, source))
            path = dossie.merge(source, organized or text)
            print(f"  ✓ {source} → {path}"
                  + ("" if organized else " (sem organizar: o cérebro não respondeu)"))
        if not folders:
            print("  Nenhuma memória do Claude Code encontrada nesta máquina.")
    for f in args.add or []:
        text = Path(f).expanduser().read_text(encoding="utf-8", errors="replace")
        path = dossie.merge(args.fonte or Path(f).stem, text)
        print(f"  ✓ {f} → {path} ({dossie.gaps(text)} campo(s) marcados NÃO SEI)")
    if not (args.add or args.claude_memory is not None or args.onboard):
        copied = dossie.copy_to_clipboard(dossie.prompt_text())
        print(f"\n  Prompt do dossiê: {dossie.PROMPT_FILE}")
        print("  " + ("Copiado. " if copied else "") + "Cole no ChatGPT (ou no claude.ai) com a memória "
              "ligada, responda as perguntas e salve a resposta final num .md.")
        print("  Depois: mariana dossie --add resposta.md --fonte ChatGPT --onboard\n")
    if args.onboard:
        from harvey.onboard import run_onboarding
        from harvey.paths import PROJECT_ROOT
        answers_path = PROJECT_ROOT / "data" / "respostas.json"
        answers = str(answers_path) if answers_path.exists() else ""
        asyncio.run(run_onboarding(files=[str(dossie.SOBRE_FILE)], site=args.site or "",
                                   answers_file=answers, assume_yes=True))


def cmd_linkedin(args):
    from harvey import linkedin_growth as g
    from harvey import linkedin_kit

    async def go():
        config, env, state, brain = await _ctx()
        a = args.acao
        if a == "perfil":
            return await linkedin_kit.build_profile(brain)
        if a == "posts":
            return await linkedin_kit.build_posts(brain, count=args.quantos)
        if a == "calendario":
            return await g.build_calendar(state, brain, weeks=args.semanas)
        if a == "fila":
            if args.aprovar_todas:
                print(f"  {await linkedin_kit.approve_pending(state)} rascunho(s) do LinkedIn aprovados.")
            return f"{await linkedin_kit.queue(state, config)} enviada(s) hoje."
        if a == "aquecer":
            return f"{await g.warmup(state, brain, config, limit=args.max)} lead(s) aquecidos."
        if a == "aceitou":
            return f"{await g.mark_accepted(state)} convite(s) aceitos."
        if a == "retirar":
            return f"{await g.withdraw(state, config)} convite(s) retirados."
        if a == "momento":
            n = await g.find_moments(state, brain, config, env, max_leads=args.max,
                                     estimate=args.estimate)
            return "" if args.estimate else f"{n} lead(s) com momento certo, foram para o topo da fila."
        if a == "video":
            path, done = await g.video_briefs(state, brain, config, args.prospect)
            for d in done:
                if d["folder"]:
                    print(f"    pasta do /ogab: {d['folder']}")
            print(f"  {len(done)} vídeo(s) de oi. No Claude: /ogab <colar o briefing>")
            return path
        if a in ("video-pronto", "permissao"):
            if not (args.prospect and args.link):
                raise SystemExit("  Use --prospect ID --link URL.")
            if a == "video-pronto":
                await g.video_ready(state, brain, args.prospect[0], args.link)
                return "Mensagem com o vídeo pronta: sai na fila depois do aceite."
            n = await g.grant_permission(state, args.prospect[0], args.link)
            return f"Permissão registrada ({n} edição(ões) liberadas para post)."
        if a == "nota":
            if args.arquivo:
                text = Path(args.arquivo).expanduser().read_text(encoding="utf-8", errors="replace")
                profile, source = await g.extract_profile(brain, text), "perfil atual"
            else:
                data = linkedin_kit.OUT_DIR / "perfil.json"
                if not data.exists():
                    raise SystemExit("  Rode 'mariana linkedin perfil' antes, ou passe --arquivo.")
                from harvey.paths import PROJECT_ROOT
                photo = any((PROJECT_ROOT / "data" / "fotos" / "escolhidas").glob("*"))
                profile = g.profile_from_proposal(json.loads(data.read_text(encoding="utf-8")), photo)
                source = "proposta da Mariana"
            history = g.save_score(source, g.score(profile, config.icp.industries))
            return g.report(history)
    result = asyncio.run(go())
    if isinstance(result, Path):
        print(f"\n  Pronto: {result}\n")
        if not args.no_open:
            webbrowser.open(result.as_uri())
    elif result:
        print(f"\n{result if result.startswith('  ') else '  ' + result}\n")


def cmd_instagram(args):
    from harvey import instagram_kit as ig
    from harvey import linkedin_growth as g

    async def go():
        a = args.acao
        if a == "fila":
            return f"{ig.queue(per_day=args.max, lang=args.idioma)} post(s) publicados hoje."
        config, env, state, brain = await _ctx()
        if a == "perfil":
            current = ""
            if args.arquivo:
                current = Path(args.arquivo).expanduser().read_text(encoding="utf-8", errors="replace")
            return await ig.build_profile(brain, current)
        if a == "posts":
            return await ig.build_posts(brain, count=args.quantos)
        if a == "calendario":
            return await ig.build_calendar(state, brain, weeks=args.semanas)
        if a == "permissao":
            if not (args.prospect and args.link):
                raise SystemExit("  Use --prospect ID --link URL.")
            n = await g.grant_permission(state, args.prospect[0], args.link)
            return f"Permissão registrada ({n} edição(ões) liberadas para post)."
        if a == "nota":
            if args.arquivo:
                text = Path(args.arquivo).expanduser().read_text(encoding="utf-8", errors="replace")
                ig.CURRENT_FILE.parent.mkdir(parents=True, exist_ok=True)
                if Path(args.arquivo).expanduser().resolve() != ig.CURRENT_FILE.resolve():
                    ig.CURRENT_FILE.write_text(text, encoding="utf-8")
                profile, source = await ig.extract_profile(brain, text), "perfil atual"
            else:
                data = ig.OUT_DIR / "perfil.json"
                if not data.exists():
                    raise SystemExit("  Rode 'mariana instagram perfil' antes, ou passe --arquivo.")
                from harvey.paths import PROJECT_ROOT
                photo = any((PROJECT_ROOT / "data" / "fotos" / "escolhidas").glob("*"))
                profile = ig.profile_from_proposal(json.loads(data.read_text(encoding="utf-8")), photo)
                source = "proposta do Gab"
            history = ig.save_score(source, ig.score(profile, config.icp.industries))
            return ig.report(history)
    result = asyncio.run(go())
    if isinstance(result, Path):
        print(f"\n  Pronto: {result}\n")
        if not args.no_open:
            webbrowser.open(result.as_uri())
    elif result:
        print(f"\n{result if result.startswith('  ') else '  ' + result}\n")


def cmd_ficha(args):
    from harvey import ficha

    async def go():
        _, _, state, brain = await _ctx()
        ids = list(args.prospect or [])
        if not ids:
            leads = []
            for status in ("replied", "contacted", "queued"):
                leads += await state.get_prospects_by_status(status)
            leads.sort(key=lambda p: (p.status != "replied", -(p.score or 0)))
            ids = [p.id for p in leads[:args.top]]
        paths = []
        for pid in ids:
            try:
                paths.append(await ficha.build(state, brain, pid, crawl=not args.sem_site))
            except (ValueError, RuntimeError) as e:
                print(f"  ✗ {pid}: {e}")
        return paths
    for path in asyncio.run(go()):
        print(f"  ✓ {path}")
    print()


def cmd_fotos(args):
    import re

    from harvey import dossie
    from harvey.paths import PROJECT_ROOT
    folder = PROJECT_ROOT / "prompts" / "fotos"
    (PROJECT_ROOT / "data" / "fotos" / "originais").mkdir(parents=True, exist_ok=True)
    styles_file = folder / f"02-estilos-{'mulher' if args.pessoa == 'woman' else 'homem'}.md"
    if not styles_file.exists():
        raise SystemExit(f"  Ainda não há estilos para esse perfil ({styles_file.name}).")
    styles = re.split(r"^## ", styles_file.read_text(encoding="utf-8"), flags=re.M)[1:]
    if args.estilo is None:
        text = (folder / "01-ficha-personagem.md").read_text(encoding="utf-8")
        label = "ficha de personagem"
        print("\n  Estilos para depois da ficha:")
        for s in styles:
            print(f"    {s.splitlines()[0]}")
    else:
        if not 1 <= args.estilo <= len(styles):
            raise SystemExit(f"  Estilo de 1 a {len(styles)}.")
        style = styles[args.estilo - 1]
        body = "\n".join(style.splitlines()[1:])
        identity = (folder / "00-identidade.md").read_text(encoding="utf-8").strip()
        text = f"{identity}\n\n{body.strip()}"
        label = style.splitlines()[0]
    copied = dossie.copy_to_clipboard(text)
    print(f"\n  Prompt ({label}){' copiado' if copied else ''}. Anexe as fotos reais"
          + (" e a ficha aprovada" if args.estilo else "") + ".\n")
    if args.mostrar:
        print(text + "\n")


def register(subparsers):
    sub = subparsers.add_parser("fotos", help="Prompts da ficha de personagem e das fotos de perfil")
    sub.add_argument("--estilo", type=int, help="número do estilo (sem = ficha de personagem)")
    sub.add_argument("--pessoa", choices=["man", "woman"], default="man")
    sub.add_argument("--mostrar", action="store_true", help="imprimir o prompt")
    sub.set_defaults(func=cmd_fotos)

    sub = subparsers.add_parser("dossie", help="Juntar tudo que o ChatGPT/Claude sabem sobre você")
    sub.add_argument("--add", action="append", help="Resposta do ChatGPT/claude.ai salva em .md (pode repetir)")
    sub.add_argument("--fonte", default="", help="Nome da fonte do --add (ex.: ChatGPT)")
    sub.add_argument("--claude-memory", nargs="?", const="", default=None,
                     help="Ler a memória do Claude Code (sem pasta = todas desta máquina)")
    sub.add_argument("--onboard", action="store_true", help="Refazer o dossiê da Mariana com o material")
    sub.add_argument("--site", default="")
    sub.set_defaults(func=cmd_dossie)

    sub = subparsers.add_parser("linkedin", help="Perfil otimizado, posts dos trabalhos e fila de envio")
    sub.add_argument("acao", choices=["perfil", "posts", "fila", "aquecer", "aceitou", "retirar",
                                      "momento", "video", "video-pronto", "permissao",
                                      "calendario", "nota"])
    sub.add_argument("--quantos", type=int, default=5, help="posts: quantos")
    sub.add_argument("--semanas", type=int, default=4, help="calendario: quantas semanas")
    sub.add_argument("--max", type=int, default=20, help="aquecer/momento: quantos leads")
    sub.add_argument("--estimate", action="store_true", help="momento: só mostrar o custo")
    sub.add_argument("--prospect", action="append", help="id do lead")
    sub.add_argument("--link", default="", help="video-pronto/permissao: link do vídeo")
    sub.add_argument("--arquivo", default="", help="nota: texto do perfil atual")
    sub.add_argument("--aprovar-todas", action="store_true",
                     help="fila: aprovar antes todos os rascunhos do LinkedIn")
    sub.add_argument("--no-open", action="store_true")
    sub.set_defaults(func=cmd_linkedin)

    sub = subparsers.add_parser("instagram", help="Perfil do Instagram, nota, posts dos trabalhos e fila")
    sub.add_argument("acao", choices=["perfil", "nota", "posts", "calendario", "fila", "permissao"])
    sub.add_argument("--arquivo", default="", help="perfil/nota: texto do perfil atual")
    sub.add_argument("--quantos", type=int, default=9, help="posts: quantos")
    sub.add_argument("--semanas", type=int, default=4, help="calendario: quantas semanas")
    sub.add_argument("--max", type=int, default=1, help="fila: quantos posts por dia")
    sub.add_argument("--idioma", choices=["pt", "en"], default="pt", help="fila: legenda em pt ou en")
    sub.add_argument("--prospect", action="append", help="permissao: id do lead")
    sub.add_argument("--link", default="", help="permissao: link do vídeo")
    sub.add_argument("--no-open", action="store_true")
    sub.set_defaults(func=cmd_instagram)

    sub = subparsers.add_parser("ficha", help="Ficha de conversa: gostos do lead e trabalhos certos")
    sub.add_argument("--prospect", action="append", help="id do lead (pode repetir)")
    sub.add_argument("--top", type=int, default=5, help="sem --prospect: os N leads mais quentes")
    sub.add_argument("--sem-site", action="store_true", help="não ler o site do lead")
    sub.set_defaults(func=cmd_ficha)

    sub = subparsers.add_parser("eventos", help="Radar de eventos: organizadores com evento chegando")
    sub.add_argument("--months", type=int, default=3, help="Janela em meses (padrão 3)")
    sub.add_argument("--max-queries", type=int, default=24, help="Limite de buscas")
    sub.add_argument("--estimate", action="store_true", help="Só mostrar o custo")
    sub.set_defaults(func=cmd_events)

    sub = subparsers.add_parser("amostras", help="Briefing de amostras para o Gab (/ogab)")
    sub.add_argument("--top", type=int, default=5)
    sub.add_argument("--modo", choices=["corte", "remake"], default="corte",
                     help="remake = refazer um vídeo fraco do lead (antes e depois)")
    sub.set_defaults(func=cmd_samples)

    sub = subparsers.add_parser("amostra-pronta", help="Criar a mensagem com a amostra pronta")
    sub.add_argument("--prospect", required=True)
    sub.add_argument("--link", required=True)
    sub.add_argument("--modo", choices=["corte", "remake"], default="corte")
    sub.set_defaults(func=cmd_sample_ready)

    sub = subparsers.add_parser("proposta", help="Gerar proposta (PDF) a partir de uma conversa")
    sub.add_argument("--conversation", default="")
    sub.add_argument("--email", default="")
    sub.add_argument("--no-open", action="store_true")
    sub.set_defaults(func=cmd_proposal)

    sub = subparsers.add_parser("agenda-check", help="Ver os próximos horários livres do Google Agenda")
    sub.set_defaults(func=cmd_calendar_check)

    sub = subparsers.add_parser("aviso-teste", help="Testar o aviso no Mac/celular")
    sub.set_defaults(func=cmd_notify_test)

    sub = subparsers.add_parser(
        "onboard", help="Primeiro uso: a Mariana aprende tudo sobre você/empresa")
    sub.add_argument("--file", action="append",
                     help="Arquivo .md/.txt/.pdf sobre você (pode repetir)")
    sub.add_argument("--site", default="", help="Site ou portfólio para ler")
    sub.add_argument("--answers", default="", help="JSON com respostas (modo automático)")
    sub.add_argument("--yes", action="store_true", help="Não perguntar nada no terminal")
    sub.set_defaults(func=cmd_onboard)

    sub = subparsers.add_parser("signature", help="Gerar e instalar a assinatura de email")
    sub.add_argument("--install-gmail", action="store_true",
                     help="Definir como assinatura do Gmail conectado")
    sub.add_argument("--no-open", action="store_true", help="Não abrir a prévia")
    sub.set_defaults(func=cmd_signature)

    sub = subparsers.add_parser(
        "email-check", help="Checar DNS (SPF/DKIM/DMARC), conexão e envio de teste")
    sub.add_argument("--send-test", action="store_true",
                     help="Mandar um email de teste para você mesmo")
    sub.set_defaults(func=cmd_email_check)

    sub = subparsers.add_parser("whatsapp-check", help="Checar a configuração do WhatsApp")
    sub.set_defaults(func=cmd_whatsapp_check)
