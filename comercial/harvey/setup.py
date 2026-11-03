"""Interactive setup wizard — walks you through everything Mariana needs."""

import asyncio
import getpass
import logging
import shutil
from pathlib import Path

import yaml

from pydantic import ValidationError

from harvey.brain import Brain
from harvey.config import BrainConfig
from harvey.state import StateManager

logger = logging.getLogger("harvey.setup")

from harvey.paths import PROJECT_ROOT
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
CONFIG_FILE = PROJECT_ROOT / "harvey.yaml"


def _print_harvey(message: str):
    """Print a message as Mariana."""
    print(f"\n  Mariana: {message}")


def _print_step(step: int, total: int, title: str):
    """Print a step header."""
    print(f"\n{'─'*60}")
    print(f"  Passo {step}/{total}: {title}")
    print(f"{'─'*60}")


def _ask(prompt: str, default: str = "", required: bool = True, secret: bool = False) -> str:
    """Ask the user a question. secret=True hides input (passwords, API keys)."""
    suffix = f" [{default}]" if default else ""
    reader = getpass.getpass if secret else input
    while True:
        try:
            answer = reader(f"\n  → {prompt}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Configuração cancelada.")
            raise SystemExit(1)

        if not answer and default:
            return default
        if not answer and required:
            print("    (obrigatório: digite um valor)")
            continue
        return answer


def _ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question."""
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        answer = input(f"\n  → {prompt}{suffix}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Configuração cancelada.")
        raise SystemExit(1)

    if not answer:
        return default
    return answer in ("y", "yes")


def _check_claude_cli() -> bool:
    """Check if Claude CLI is installed and accessible."""
    return shutil.which("claude") is not None


def _check_codex_cli() -> bool:
    """Check if Codex CLI is installed and accessible."""
    return shutil.which("codex") is not None


async def _test_claude(brain: Brain) -> bool:
    """Test that the configured brain answers (Claude or Codex)."""
    response = await brain.think(
        "Respond with exactly: HARVEY_READY",
        session_id="harvey-setup-test",
    )
    return "HARVEY_READY" in response


def _ask_brain_config() -> BrainConfig:
    """Ask which subscription Mariana thinks with. Claude is the default."""
    _print_harvey("Eu penso usando uma assinatura de IA que você já paga:")
    print("    claude: o seu plano do Claude, pelo Claude Code (padrão)")
    print("    codex:  o seu plano do ChatGPT, pelo Codex CLI")
    while True:
        provider = _ask("Qual? (claude/codex)", default="claude").lower()
        if provider == "codex":
            from harvey.codex import CodexError, require_supported_platform
            try:
                require_supported_platform()
            except CodexError as e:
                print(f"    ({e})")
                continue
        if provider in ("claude", "codex"):
            break
        print("    (digite claude ou codex)")
    if provider == "codex":
        from harvey.codex import SUGGESTED_MODEL
        print(f"    {SUGGESTED_MODEL} é o modelo do Codex que a Mariana verificou como só texto")
        print("    (sem ferramentas de execução). Enter para usar, ou digite outro.")
    while True:
        if provider == "codex":
            model = _ask("Modelo", default=SUGGESTED_MODEL, required=False)
        else:
            model = _ask("Modelo (deixe em branco para o padrão)", required=False)
        try:
            return BrainConfig(provider=provider, model=model)
        except ValidationError:
            print("    (isso não parece nome de modelo: tente de novo ou deixe em branco)")


async def _test_instantly(api_key: str) -> bool:
    """Test the Instantly API key."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.instantly.ai/api/v2/accounts",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            return resp.status_code == 200
    except Exception:
        return False


class SetupWizard:
    def __init__(self):
        self.env_vars: dict[str, str] = {}
        self.config: dict = {}
        self.brain_config = BrainConfig()

    async def run(self):
        """Run the full interactive setup."""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   Assistente de configuração da Mariana                  ║
║   Bora fechar job.                                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝""")

        _print_harvey("Oi, eu sou a Mariana. Vamos me configurar pra eu começar")
        _print_harvey("a fechar trabalhos pra você. Eu te guio em tudo.")
        _print_harvey("Leva uns 5 minutos. (Dica: o mariana onboard é o caminho recomendado.)\n")

        total_steps = 6

        # Step 1: Check prerequisites
        _print_step(1, total_steps, "Conferindo os pré-requisitos")
        await self._check_prerequisites()

        # Step 2: Connect email platform
        _print_step(2, total_steps, "Plataforma de email (Instantly)")
        await self._setup_email_platform()

        # Step 3: LinkedIn (optional)
        _print_step(3, total_steps, "LinkedIn (opcional)")
        self._setup_linkedin()

        # Step 4: Cloudflare crawling (optional)
        _print_step(4, total_steps, "Leitura de sites (opcional)")
        self._setup_cloudflare()

        # Step 5: Train on product
        _print_step(5, total_steps, "Ensinar a Mariana sobre o seu trabalho")
        await self._setup_product()

        # Step 6: Configure behavior
        _print_step(6, total_steps, "Comportamento")
        self._setup_behavior()

        # Write everything
        self._write_env()
        self._write_config()

        # Final summary
        await self._print_summary()

    async def _check_prerequisites(self):
        """Pick the brain provider and verify its CLI is installed and working."""
        self.brain_config = _ask_brain_config()
        if self.brain_config.provider == "codex":
            await self._check_codex()
        else:
            await self._check_claude()

    async def _check_claude(self):
        # Check Claude CLI
        print("\n  Conferindo o Claude Code CLI...", end=" ")
        if _check_claude_cli():
            print("✓ Encontrado")
        else:
            print("✗ Não encontrado")
            _print_harvey("Preciso do Claude Code CLI para pensar. Instale em:")
            print("         https://claude.ai/download")
            print("\n         Depois de instalar, rode 'claude login' para entrar,")
            print("         e rode esta configuração de novo.")
            raise SystemExit(1)

        # Test headless mode
        print("  Testando o Claude em modo automático...", end=" ", flush=True)
        state = StateManager()
        await state.init_db()
        brain = Brain(state, self.brain_config)
        if await _test_claude(brain):
            print("✓ Funcionando")
        else:
            print("✗ Falhou")
            _print_harvey("O Claude CLI está instalado, mas o modo automático não funciona.")
            _print_harvey("Confira se você entrou: rode 'claude login'")
            print("\n         Confira também se a assinatura está ativa.")
            if not _ask_yes_no("Continuar mesmo assim?", default=False):
                raise SystemExit(1)
        self._check_python_packages()

    async def _check_codex(self):
        from harvey.codex import (
            CODEX_INSTALL_HINT, CodexError, check_cli_version, check_native_auth,
        )

        print("\n  Conferindo o Codex CLI...", end=" ")
        if _check_codex_cli():
            print("✓ Encontrado")
        else:
            print("✗ Não encontrado")
            _print_harvey("Preciso do Codex CLI para pensar com o seu plano do ChatGPT:")
            print(f"         {CODEX_INSTALL_HINT}")
            print("\n         Depois rode 'codex login', escolha 'Sign in with ChatGPT',")
            print("         e rode esta configuração de novo.")
            raise SystemExit(1)

        print("  Conferindo a versão do Codex CLI...", end=" ")
        try:
            print(f"✓ {check_cli_version()}")
        except CodexError as e:
            print("✗ Não suportado")
            _print_harvey(str(e))
            raise SystemExit(1)

        print("  Conferindo o login do ChatGPT no Codex...", end=" ")
        try:
            check_native_auth()
            print("✓ Encontrado")
        except CodexError as e:
            print("✗ Não está pronto")
            _print_harvey(str(e))
            raise SystemExit(1)

        # A real (subscription, not API-billed) call through the same
        # isolated runtime Mariana uses for every prompt.
        print("  Testando o Codex (isolado, sem ferramentas)...", end=" ", flush=True)
        state = StateManager()
        await state.init_db()
        brain = Brain(state, self.brain_config)
        if await _test_claude(brain):
            print("✓ Funcionando")
        else:
            print("✗ Falhou")
            _print_harvey("O Codex está instalado, mas a chamada de teste falhou. O registro")
            _print_harvey("acima diz o motivo (login, limite do plano ou isolamento).")
            if not _ask_yes_no("Continuar mesmo assim?", default=False):
                raise SystemExit(1)
        self._check_python_packages()

    def _check_python_packages(self):
        # Check Python packages
        print("  Conferindo as dependências Python...", end=" ")
        missing = []
        for pkg in ["httpx", "aiosqlite", "yaml", "pydantic", "bs4"]:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if not missing:
            print("✓ Tudo instalado")
        else:
            print(f"✗ Faltando: {', '.join(missing)}")
            print("\n  Rode: pip install -r requirements.txt")
            if not _ask_yes_no("Continuar mesmo assim?", default=False):
                raise SystemExit(1)

        _print_harvey("Pré-requisitos ok. Vamos seguir.")

    async def _setup_email_platform(self):
        """Configure Instantly API."""
        _print_harvey("Este passo é para o Instantly (legado). O recomendado é o Gmail:")
        _print_harvey("rode 'mariana gmail auth' depois desta configuração.")

        has_instantly = _ask_yes_no("Você tem conta no Instantly?", default=False)

        if has_instantly:
            api_key = _ask("Chave da API do Instantly (Settings → Integrations; não aparece na tela)", secret=True)
            self.env_vars["INSTANTLY_API_KEY"] = api_key

            # Test the key
            print("\n  Testando a chave...", end=" ", flush=True)
            if await _test_instantly(api_key):
                print("✓ Conectado")
                _print_harvey("Perfeito. Já consigo enviar pelo Instantly.")
            else:
                print("✗ Falhou")
                _print_harvey("Não conectou. A chave pode estar errada, ou você precisa")
                _print_harvey("do plano Growth para a API. Vou salvar mesmo assim;")
                _print_harvey("dá pra corrigir depois no .env.")
        else:
            _print_harvey("Tranquilo. O Gmail é o caminho recomendado:")
            _print_harvey("depois rode 'mariana gmail auth' e 'mariana email-check'.")
            self.env_vars["INSTANTLY_API_KEY"] = ""

    def _setup_linkedin(self):
        """No LinkedIn login: Mariana writes, the user sends from their account."""
        _print_harvey("No LinkedIn eu escrevo os convites e as mensagens, e você envia")
        _print_harvey("da sua conta (mariana linkedin fila). Nunca entro na sua conta.")

    def _setup_cloudflare(self):
        """Configure Cloudflare Browser Rendering for deep crawling."""
        _print_harvey("Ao aprender por um site, posso ler a fundo usando o Cloudflare")
        _print_harvey("Browser Rendering, que lê sites com muito JavaScript.")
        _print_harvey("Custa ~US$ 5/mês por ~12.000 páginas. Totalmente opcional.")

        use_cloudflare = _ask_yes_no("Configurar o Cloudflare?", default=False)

        if use_cloudflare:
            account_id = _ask("Cloudflare Account ID")
            api_token = _ask("API Token do Cloudflare (permissão Browser Rendering - Edit; não aparece na tela)", secret=True)
            self.env_vars["CLOUDFLARE_ACCOUNT_ID"] = account_id
            self.env_vars["CLOUDFLARE_API_TOKEN"] = api_token
            _print_harvey("Boa. Vou usar o Cloudflare para ler os sites.")
        else:
            _print_harvey("Tranquilo. Uso o meu leitor próprio, que funciona na")
            _print_harvey("maioria dos sites (só não roda JavaScript).")
            self.env_vars["CLOUDFLARE_ACCOUNT_ID"] = ""
            self.env_vars["CLOUDFLARE_API_TOKEN"] = ""

    async def _setup_product(self):
        """Train Mariana on the product — either via URL or manual entry."""
        _print_harvey("Agora a parte importante: aprender sobre o seu trabalho.")
        _print_harvey("Posso ler o seu site e descobrir sozinha, ou você me conta")
        _print_harvey("o básico. (O mais completo é o mariana onboard.)\n")

        method = _ask(
            "Aprender pelo site ou digitar à mão? (url/manual)",
            default="url",
        ).lower()

        if method in ("url", "u", "website"):
            url = _ask("Endereço do seu site (ex.: https://seusite.com.br)")

            _print_harvey(f"Um minuto: vou ler {url}")
            _print_harvey("e aprender tudo o que der sobre o seu trabalho.\n")

            from harvey.trainer import Trainer
            trainer = Trainer(brain_config=self.brain_config)
            self.config = await trainer.train(url, str(CONFIG_FILE)) or {}

            if self.config:
                _print_harvey("Pronto, aprendi. Confira o harvey.local.yaml e ajuste")
                _print_harvey("o que estiver estranho.")
                return

            _print_harvey("Não consegui ler esse site. Vamos à mão.")

        # Manual entry
        _print_harvey("Vou te fazer algumas perguntas sobre o seu trabalho.\n")

        company = _ask("Nome da marca/empresa")
        product = _ask("Nome do serviço")
        description = _ask("Descrição em uma linha (o que você faz e para quem)")
        pricing = _ask("Preço", default="Sob orçamento")

        print("\n  Digite de 3 a 5 benefícios (um por linha, linha vazia para terminar):")
        benefits = []
        while True:
            b = _ask(f"  Benefício {len(benefits) + 1}", required=False)
            if not b:
                break
            benefits.append(b)

        _print_harvey("Agora o seu cliente ideal.\n")

        industries = _ask("Segmentos (separados por vírgula)").split(",")
        industries = [i.strip() for i in industries if i.strip()]

        titles = _ask("Cargos de quem decide (separados por vírgula)").split(",")
        titles = [t.strip() for t in titles if t.strip()]

        company_size = _ask("Tamanho da empresa", default="1-200")
        geography = _ask(
            "Cidades/região (com estado ou país, ex.: 'Niterói, RJ'; só o "
            "nome da cidade pode cair no lugar errado)",
            default="Rio de Janeiro, RJ",
        ).split(",")
        geography = [g.strip() for g in geography if g.strip()]

        _print_harvey("Agora a sua oferta: o que acontece quando alguém se interessa?\n")

        primary_offer = _ask(
            "Qual a sua oferta principal? (ex.: 'pacote de 8 Reels por mês', 'aftermovie de evento')",
            required=False,
        )
        entry_offer = _ask(
            "Tem uma oferta de entrada? (ex.: 'um Reel teste', 'call de briefing')",
            default="",
            required=False,
        )

        print("\n  Qual o objetivo quando alguém se interessa?")
        print("    1. Marcar uma call")
        print("    2. Começar um teste")
        print("    3. Só ter resposta / começar a conversa")
        goal_choice = _ask("Objetivo (1/2/3)", default="1")
        goal_map = {"1": "book_call", "2": "start_trial", "3": "get_reply"}
        goal = goal_map.get(goal_choice, "book_call")

        booking_method = "suggest_times"
        booking_url = ""
        meeting_duration = "15 minutes"
        meeting_owner = ""

        if goal == "book_call":
            has_calendar = _ask_yes_no("Você tem link de agendamento (Calendly, Cal.com etc.)?")
            if has_calendar:
                booking_url = _ask("Link de agendamento")
                booking_method = "calendar_link"
            else:
                print("\n  Como a Mariana deve sugerir horários?")
                print("    1. Sugerir horários ('pode ser quinta às 14h?')")
                print("    2. Perguntar a preferência ('como está a sua semana?')")
                method_choice = _ask("Jeito (1/2)", default="1")
                booking_method = "suggest_times" if method_choice == "1" else "ask_preference"

            meeting_duration = _ask("Duração da call", default="15 minutes")
            meeting_owner = _ask("Quem participa da call? (seu nome)", required=False)

        _print_harvey("Quem assina as mensagens?\n")

        persona_name = _ask("Nome que os clientes veem (o seu)")
        persona_email = _ask("Email de envio")
        persona_role = _ask("Como você se apresenta", default="Filmmaker e editor de vídeo")

        self.config = {
            "persona": {
                "name": persona_name,
                "company": company,
                "role": persona_role,
                "email": persona_email,
                "linkedin": "",
                "tone": "professional, consultative, confident",
            },
            "product": {
                "name": product,
                "description": description,
                "pricing": pricing,
                "key_benefits": benefits or ["Benefit 1"],
                "objection_responses": {},
                "offer": {
                    "primary": primary_offer or "",
                    "entry": entry_offer or "",
                    "goal": goal,
                    "booking_method": booking_method,
                    "booking_url": booking_url,
                    "meeting_duration": meeting_duration,
                    "meeting_owner": meeting_owner or "",
                },
            },
            "icp": {
                "industries": industries or ["Technology"],
                "company_size": company_size,
                "titles": titles or ["VP", "Director"],
                "geography": geography,
            },
            "channels": {
                "email": {
                    "enabled": True,
                    "provider": "instantly",
                    "max_daily_sends": 50,
                },
                "linkedin": {
                    "enabled": True,
                    "max_daily_connections": 20,
                    "max_daily_messages": 10,
                },
            },
            "usage": {
                "max_daily_claude_percent": 80,
                "heartbeat_interval_minutes": 15,
                "quiet_hours": {
                    "start": "22:00",
                    "end": "07:00",
                    "timezone": "America/New_York",
                },
            },
        }

        _print_harvey("Pronto, tenho o que preciso sobre o seu trabalho.")

    def _setup_behavior(self):
        """Configure Mariana's operational behavior."""
        _print_harvey("Por último, como eu trabalho.\n")

        # Usage limit
        print("  Eu controlo o meu uso do Claude para não gastar a sua cota inteira.")
        usage_pct = _ask(
            "Máximo de % do uso diário que eu posso gastar",
            default="80",
        )
        try:
            usage_pct = min(100.0, max(1.0, float(usage_pct)))
        except ValueError:
            print("    (não entendi: usando 80)")
            usage_pct = 80.0

        # Heartbeat interval
        print("\n  Eu acordo de tempos em tempos para ver o que fazer.")
        interval = _ask(
            "De quantos em quantos minutos?",
            default="15",
        )
        try:
            interval = max(1, int(interval))
        except ValueError:
            print("    (não entendi: usando 15)")
            interval = 15

        # Quiet hours
        print("\n  No horário de silêncio eu não envio nada.")
        quiet_start = _ask("Início do silêncio (24h)", default="21:00")
        quiet_end = _ask("Fim do silêncio (24h)", default="08:00")
        timezone = _ask("Seu fuso horário", default="America/Sao_Paulo")

        # Daily send limit
        daily_sends = _ask(
            "Máximo de emails por dia",
            default="50",
        )
        try:
            daily_sends = max(1, int(daily_sends))
        except ValueError:
            print("    (não entendi: usando 50)")
            daily_sends = 50
        if daily_sends > 200:
            print("\n  ⚠  Mais de 200 por dia num domínio novo queima a entrega.")
            print("     Aqueça aos poucos (veja o README).")

        # Update config
        if self.config:
            self.config["usage"] = {
                "max_daily_claude_percent": usage_pct,
                "heartbeat_interval_minutes": interval,
                "quiet_hours": {
                    "start": quiet_start,
                    "end": quiet_end,
                    "timezone": timezone,
                },
            }
            if "channels" in self.config and "email" in self.config["channels"]:
                self.config["channels"]["email"]["max_daily_sends"] = daily_sends

        _print_harvey("Perfeito. Tudo configurado.")

    def _write_env(self):
        """Write the .env file, preserving any existing variables we didn't touch."""
        existing: dict[str, str] = {}
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    existing[key.strip()] = value.strip()

        # Wizard answers win, but never blank out a previously-set value
        # (e.g. re-running setup and skipping the LinkedIn step).
        merged = dict(existing)
        for key, value in self.env_vars.items():
            if value or key not in merged:
                merged[key] = value

        lines = [f"{key}={value}" for key, value in merged.items()]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            ENV_FILE.chmod(0o600)  # credentials — owner read/write only
        except OSError:
            pass
        logger.info(f"Wrote {ENV_FILE}")

    def _write_config(self):
        """Write harvey.yaml (only if we have manual config — trainer writes its own)."""
        from harvey.trainer import brain_section

        if self.config:
            self.config["brain"] = brain_section(self.brain_config)
        if self.config and not CONFIG_FILE.exists():
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Wrote {CONFIG_FILE}")
        elif self.config:
            # Config already exists (from trainer), update behavior settings only
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or {}
                existing["usage"] = self.config.get("usage", existing.get("usage", {}))
                existing["brain"] = self.config["brain"]
                if "channels" in self.config:
                    existing.setdefault("channels", {})
                    if "email" in self.config["channels"]:
                        existing["channels"].setdefault("email", {})
                        existing["channels"]["email"]["max_daily_sends"] = (
                            self.config["channels"]["email"].get("max_daily_sends", 50)
                        )
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    yaml.dump(existing, f, default_flow_style=False, sort_keys=False)
            except Exception:
                pass

    async def _print_summary(self):
        """Print final summary and next steps."""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   Configuração concluída!                                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")

        # Show what's configured
        checks = {
            ("Codex CLI (ChatGPT plan)" if self.brain_config.provider == "codex"
             else "Claude Code CLI"): (_check_codex_cli() if self.brain_config.provider == "codex"
                                      else _check_claude_cli()),
            "Instantly API": bool(self.env_vars.get("INSTANTLY_API_KEY")),
            "Cloudflare": bool(self.env_vars.get("CLOUDFLARE_ACCOUNT_ID")),
            "Trabalho configurado": CONFIG_FILE.exists(),
        }

        for name, ok in checks.items():
            status = "✓" if ok else "–"
            print(f"  {status} {name}")

        print(f"""
  Arquivos criados:
    - .env (suas credenciais)
    - harvey.yaml (sua configuração)

  Próximos passos (recomendado):
    mariana onboard       (a Mariana aprende tudo sobre você)
    mariana signature     (assinatura de email)
    mariana gmail auth    (conectar o Gmail e a agenda)
    mariana email-check   (conferir o envio)

  Para ligar a Mariana:
    mariana run

  Antes do primeiro email:
    1. Use, de preferência, um domínio só de prospecção, com SPF,
       DKIM e DMARC configurados.
    2. Aqueça o domínio por 2 a 4 semanas antes de volume de verdade.
    3. Respeite todo pedido de descadastro (a Mariana já faz isso).
    Veja a seção "Lei e entregabilidade" do README.
""")
        _print_harvey("Pronta. Rode 'mariana run' e eu começo.")
        _print_harvey("Bora fechar job.\n")


async def run_setup():
    wizard = SetupWizard()
    await wizard.run()


def main():
    asyncio.run(run_setup())


if __name__ == "__main__":
    main()
