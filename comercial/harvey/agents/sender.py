"""Sender — deploys campaigns via Instantly, or sends natively via the
configured mail provider (Gmail / SMTP) through the outbox approval ladder.

Native flow:
  1. Draft campaigns are STAGED: merge variables rendered per prospect,
     one outbox row per (prospect, step) with a scheduled send_at.
     Rows start as pending_review (copilot) or approved (autopilot).
  2. Each heartbeat DRAINS due approved rows: kill-switch check, stop-on-
     reply check, deterministic pre-send gate, then provider.send_email
     with jittered pacing and the daily cap.
"""

import asyncio
import logging
import random
import re
from datetime import date, datetime, timedelta, timezone

from harvey.brain import Brain
from harvey.config import MarianaConfig, EnvConfig
from harvey.gate import pre_send_check
from harvey.integrations.instantly import InstantlyClient
from harvey.integrations.mail_provider import NATIVE_PROVIDERS, get_mail_provider
from harvey.integrations.precleared import PreclearedClient
from harvey.state import StateManager

logger = logging.getLogger("harvey.sender")

# Max sends drained per heartbeat cycle — spreads volume through the day
# instead of bursting the daily cap in one minute.
MAX_SENDS_PER_CYCLE = 8
SEND_JITTER_SECONDS = (4, 15)

# Prospect pipeline statuses that mean "stop emailing this person".
STOP_STATUSES = {"replied", "opted_out", "lost", "meeting", "closed"}

KILL_SWITCH_KEY = "sending_paused"
BOUNCE_COUNT_KEY = "bounce_count"

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# Only prospects in these statuses may be added as leads. This guarantees
# we never re-send to someone already contacted, replied, opted out, or lost.
SENDABLE_STATUSES = {"new", "queued"}

# Email confidence levels safe to send to. "verified" only by default;
# "risky" (catch-all domains) is opt-in via config. Never send to a "guess"
# or "invalid" address — that bounces and burns the sending domain.
SENDABLE_EMAIL_STATUSES = {"verified"}
SENDABLE_EMAIL_STATUSES_WITH_RISKY = {"verified", "risky"}


class Sender:
    def __init__(
        self,
        brain: Brain,
        state: StateManager,
        config: MarianaConfig,
        env: EnvConfig,
    ):
        self.brain = brain
        self.state = state
        self.config = config
        self.instantly = InstantlyClient(env.instantly_api_key)
        self.provider = get_mail_provider(config, env)
        # Optional per-recipient compliance check; None unless enabled.
        self.precleared = PreclearedClient.from_config(config, env)
        # Disabled in tests to skip inter-send sleeps.
        self.send_pacing = True

    @property
    def is_native(self) -> bool:
        return (
            self.config.channels.email.provider in NATIVE_PROVIDERS
            and self.provider is not None
        )

    async def run(self):
        """Deploy campaigns — natively through the outbox, or via Instantly."""
        if not self.config.channels.email.enabled:
            logger.info("Sender: canal de email desligado. Pulando.")
            return

        if self.is_native:
            await self._run_native()
            return

        logger.info("Sender: procurando campanhas para enviar...")
        draft_campaigns = await self.state.get_campaigns_by_status("draft")
        if not draft_campaigns:
            logger.info("Sender: nenhuma campanha para enviar.")
            return

        # Enforce daily send limit
        max_sends = self.config.channels.email.max_daily_sends
        sends_today = await self._count_sends_today()
        remaining = max_sends - sends_today
        if remaining <= 0:
            logger.info(f"Sender: limite diário de envio atingido ({sends_today}/{max_sends}). Pulando.")
            return

        for campaign in draft_campaigns:
            try:
                await self._deploy_campaign(campaign)
            except Exception as e:
                logger.error(f"Sender: não deu para enviar a campanha {campaign.name}: {e}")

    def _validate_sequence(self, campaign) -> bool:
        """Never deploy a broken or empty sequence."""
        if not campaign.sequence:
            logger.error(f"Sender: a campanha '{campaign.name}' não tem emails. Marcada como falha.")
            return False
        for step in campaign.sequence:
            if not (step.subject or "").strip() or not (step.body or "").strip():
                logger.error(
                    f"Sender: a campanha '{campaign.name}' tem a etapa {step.step} sem "
                    "assunto ou corpo. Marcada como falha."
                )
                return False
            if step.delay_days < 0:
                logger.error(
                    f"Sender: a campanha '{campaign.name}' tem a etapa {step.step} com atraso negativo."
                )
                return False
        return True

    async def _deploy_campaign(self, campaign):
        """Deploy a single campaign to Instantly. Idempotent: safe to retry."""
        logger.info(f"Sender: enviando a campanha '{campaign.name}'...")

        # 0. Validate before touching the network
        if not self._validate_sequence(campaign):
            await self.state.update_campaign(campaign.id, status="failed")
            return

        # 1. Create campaign in Instantly — or resume one from a previous
        # partially-failed deploy. Never create a duplicate.
        campaign_id = campaign.instantly_campaign_id
        if campaign_id:
            logger.info(
                f"Sender: Campaign '{campaign.name}' already has Instantly ID "
                f"{campaign_id}. Resuming deploy instead of recreating."
            )
        else:
            instantly_campaign = await self.instantly.create_campaign(campaign.name)
            if not instantly_campaign or not isinstance(instantly_campaign, dict):
                logger.error(f"Sender: não deu para criar a campanha no Instantly: {campaign.name}")
                return

            campaign_id = instantly_campaign.get("id")
            if not campaign_id:
                logger.error("Sender: o Instantly não devolveu o ID da campanha.")
                return

            # Persist the ID immediately so a crash mid-deploy resumes this
            # campaign instead of creating a second one (double-send guard).
            await self.state.update_campaign(campaign.id, instantly_campaign_id=campaign_id)
            campaign.instantly_campaign_id = campaign_id

        # 2. Set email sequence
        sequences = [
            {
                "subject": step.subject.strip(),
                "body": step.body.strip(),
                "wait": step.delay_days,
            }
            for step in campaign.sequence
        ]

        result = await self.instantly.set_campaign_emails(campaign_id, sequences)
        if result is None:
            logger.error(f"Sender: não deu para colocar os emails na campanha {campaign_id}")
            return

        # 3. Add leads — validated, deduped, never-contacted, deliverable-only
        allow_risky = getattr(self.config.channels.email, "send_to_risky", False)
        sendable_email = (
            SENDABLE_EMAIL_STATUSES_WITH_RISKY if allow_risky
            else SENDABLE_EMAIL_STATUSES
        )
        prospects = []
        seen_emails: set[str] = set()
        skipped_unverified = 0
        for prospect_id in campaign.prospect_ids:
            prospect = await self.state.get_prospect(prospect_id)
            if not prospect or not prospect.email:
                continue
            email = prospect.email.strip().lower()
            if not EMAIL_RE.match(email):
                logger.warning(f"Sender: pulando email inválido '{prospect.email}'")
                continue
            if email in seen_emails:
                continue
            if prospect.status not in SENDABLE_STATUSES:
                # Already contacted / replied / opted out — never double-send.
                logger.debug(
                    f"Sender: Skipping {email} (status '{prospect.status}' is not sendable)."
                )
                continue
            # Deliverability gate: never send to unverified/guessed addresses —
            # bounces are the fastest way to torch a sending domain.
            if (prospect.email_status or "guess") not in sendable_email:
                skipped_unverified += 1
                logger.debug(
                    f"Sender: Skipping {email} (email_status "
                    f"'{prospect.email_status or 'guess'}' not deliverable)."
                )
                continue
            seen_emails.add(email)
            prospects.append(prospect)

        if skipped_unverified:
            logger.info(
                f"Sender: segurei {skipped_unverified} lead(s) com "
                f"email não verificado da campanha '{campaign.name}'."
            )

        if not prospects:
            # Retry path: leads were already staged and marked 'contacted'
            # on a previous cycle but activation failed. Just activate.
            already_staged = False
            for pid in campaign.prospect_ids:
                p = await self.state.get_prospect(pid)
                if p and p.status == "contacted":
                    already_staged = True
                    break
            if already_staged:
                logger.info(
                    f"Sender: os leads de '{campaign.name}' já estão na fila. Tentando ativar de novo."
                )
                if await self.instantly.activate_campaign(campaign_id) is not None:
                    await self.state.update_campaign(campaign.id, status="active")
                    logger.info(f"Sender: campanha '{campaign.name}' ativada na nova tentativa.")
                return
            logger.warning(f"Sender: nenhum lead válido para a campanha {campaign.name}")
            return

        # Check remaining daily send budget
        max_sends = self.config.channels.email.max_daily_sends
        sends_today = await self._count_sends_today()
        remaining = max_sends - sends_today
        if remaining <= 0:
            logger.info(f"Sender: Daily limit reached. Deferring campaign '{campaign.name}'.")
            return
        if len(prospects) > remaining:
            logger.info(f"Sender: limitando os leads de {len(prospects)} para {remaining} (limite diário).")
            prospects = prospects[:remaining]

        leads = [
            {
                "email": p.email.strip().lower(),
                "first_name": p.first_name,
                "last_name": p.last_name,
                "company_name": p.company,
                "variables": {
                    "title": p.title,
                    "personalization": p.personalization_notes,
                },
            }
            for p in prospects
        ]

        result = await self.instantly.add_leads(campaign_id, leads)
        if result is None:
            logger.error(f"Sender: não deu para adicionar os leads na campanha {campaign_id}")
            return

        # Mark prospects as contacted BEFORE activation: if activation
        # succeeds but this write failed, a retry would re-add the same
        # leads. Better to under-count than double-send.
        for prospect in prospects:
            await self.state.update_prospect_status(prospect.id, "contacted")

        # 4. Activate campaign
        result = await self.instantly.activate_campaign(campaign_id)
        if result is None:
            logger.error(
                f"Sender: não deu para ativar a campanha {campaign_id}. "
                "Os leads estão na fila; tento ativar no próximo ciclo."
            )
            return

        # 5. Update our records
        await self.state.update_campaign(
            campaign.id,
            instantly_campaign_id=campaign_id,
            status="active",
        )

        await self.state.log_action(
            action_type="send_campaign",
            agent="sender",
            details={
                "campaign_name": campaign.name,
                "instantly_campaign_id": campaign_id,
                "leads_added": len(leads),
            },
        )

        logger.info(
            f"Sender: campanha '{campaign.name}' enviada ao Instantly "
            f"com {len(leads)} leads. ID da campanha: {campaign_id}"
        )

    async def _count_sends_today(self) -> int:
        """Count how many prospects were contacted today."""
        import aiosqlite
        today = date.today().isoformat()
        async with aiosqlite.connect(self.state.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM prospects WHERE status = 'contacted' AND updated_at LIKE ?",
                (f"{today}%",),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ── Native provider flow (Gmail / SMTP via the outbox) ──

    async def _run_native(self):
        """Stage new campaigns into the outbox, then drain what's due."""
        paused = await self.state.get_setting(KILL_SWITCH_KEY)
        if paused:
            logger.warning(
                f"Sender: ENVIOS PAUSADOS ({paused}). Retome pelo painel "
                "ou com `mariana sending resume` depois de resolver."
            )
            return

        for campaign in await self.state.get_campaigns_by_status("draft"):
            try:
                await self._stage_campaign_native(campaign)
            except Exception as e:
                logger.error(f"Sender: falhou ao colocar '{campaign.name}' na fila: {e}")

        await self._drain_due()

    def _render(self, text: str, prospect) -> str:
        """Fill merge variables. The pre-send gate rejects any leftovers."""
        replacements = {
            "first_name": prospect.first_name,
            "last_name": prospect.last_name,
            "company": prospect.company,
            "title": prospect.title,
            "personalization": prospect.personalization_notes,
        }
        for key, value in replacements.items():
            text = text.replace("{{" + key + "}}", value or "")
            text = text.replace("{{ " + key + " }}", value or "")
        return text.strip()

    async def _stage_campaign_native(self, campaign):
        """Render + schedule a draft campaign's emails into the outbox."""
        if not self._validate_sequence(campaign):
            await self.state.update_campaign(campaign.id, status="failed")
            return

        require_approval = getattr(
            self.config.channels.email, "require_approval", True
        )
        initial_status = "pending_review" if require_approval else "approved"
        allow_risky = getattr(self.config.channels.email, "send_to_risky", False)
        sendable_email = (
            SENDABLE_EMAIL_STATUSES_WITH_RISKY if allow_risky
            else SENDABLE_EMAIL_STATUSES
        )

        staged = 0
        skipped = 0
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        seen_emails: set[str] = set()

        for prospect_id in campaign.prospect_ids:
            prospect = await self.state.get_prospect(prospect_id)
            if not prospect or not prospect.email:
                continue
            email = prospect.email.strip().lower()
            if not EMAIL_RE.match(email) or email in seen_emails:
                continue
            if prospect.status not in SENDABLE_STATUSES:
                continue
            if (prospect.email_status or "guess") not in sendable_email:
                skipped += 1
                continue
            seen_emails.add(email)

            cumulative_days = 0
            for step in campaign.sequence:
                cumulative_days += max(0, step.delay_days)
                send_at = now + timedelta(days=cumulative_days)
                item_id = await self.state.add_outbox_item(
                    prospect_id=prospect.id,
                    campaign_id=campaign.id,
                    step=step.step,
                    to_email=email,
                    subject=self._render(step.subject, prospect),
                    body=self._render(step.body, prospect),
                    send_at=send_at.isoformat(),
                    status=initial_status,
                    provider=self.provider.name,
                )
                if item_id:
                    staged += 1
            await self.state.update_prospect_status(prospect.id, "queued")

        await self.state.update_campaign(campaign.id, status="active")
        if skipped:
            logger.info(
                f"Sender: segurei {skipped} lead(s) com email não "
                f"verificado da campanha '{campaign.name}'."
            )
        if staged:
            mode = "esperando a sua aprovação" if require_approval else "aprovados"
            logger.info(
                f"Sender: {staged} email(s) na fila para '{campaign.name}' "
                f"({mode}). Revise na aba Outbox do painel."
            )
            await self.state.log_action(
                action_type="stage_campaign",
                agent="sender",
                details={"campaign": campaign.name, "staged": staged, "mode": mode},
            )

    async def _drain_due(self):
        """Send due, approved outbox items through the provider."""
        if not self.provider.is_configured():
            logger.warning(
                f"Sender: o provedor de email '{self.provider.name}' não está configurado "
                "ainda: a Outbox está segurando. Veja /ogab comercial email (passo 4 do guia)."
            )
            return

        max_daily = self.config.channels.email.max_daily_sends
        sent_today = await self.state.count_outbox_sent_today()
        budget = min(MAX_SENDS_PER_CYCLE, max_daily - sent_today)
        if budget <= 0:
            logger.info(f"Sender: limite diário atingido ({sent_today}/{max_daily}).")
            return

        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        due = await self.state.get_outbox(
            status="approved", due_before=now, limit=budget * 3
        )
        if self.precleared is not None:
            # Cold emails held by an unavailable compliance check stay
            # approved at the front of the queue and could fill the page
            # above, so fetch replies (and any other unchecked kind) on their
            # own too. Bounded: one extra query of the same size.
            seen = {item["id"] for item in due}
            unchecked = await self.state.get_outbox(
                status="approved", due_before=now, limit=budget * 3,
                exclude_kind="sequence",
            )
            extra = [item for item in unchecked if item["id"] not in seen]
            if extra:
                due = sorted(
                    due + extra,
                    key=lambda i: (i.get("send_at") or "", i.get("created_at") or ""),
                )
        if not due:
            return

        allow_risky = getattr(self.config.channels.email, "send_to_risky", False)
        sent = 0
        # Set when Precleared can't be asked (allowance used up, network):
        # cold emails wait for a later cycle, replies still go out.
        compliance_paused = False
        for item in due:
            if sent >= budget:
                break
            needs_check = self.precleared is not None and item["kind"] == "sequence"
            if needs_check and compliance_paused:
                continue

            prospect = await self.state.get_prospect(item["prospect_id"])
            if prospect is None:
                await self.state.update_outbox_item(
                    item["id"], status="failed", error="prospect missing"
                )
                continue

            # Stop-on-reply / opt-out: never continue a sequence after contact.
            if item["kind"] == "sequence" and prospect.status in STOP_STATUSES:
                await self.state.update_outbox_item(
                    item["id"], status="cancelled",
                    error=f"prospect status '{prospect.status}'",
                )
                continue

            gate = pre_send_check(
                item["to_email"], item["subject"], item["body"],
                prospect=prospect, allow_risky=allow_risky, kind=item["kind"],
            )
            if not gate:
                await self.state.update_outbox_item(
                    item["id"], status="failed",
                    error="gate: " + "; ".join(gate.reasons)[:300],
                )
                logger.warning(
                    f"Sender: o filtro bloqueou o email para {item['to_email']}: "
                    f"{gate.reasons}"
                )
                continue

            # Optional compliance check (compliance.precleared): one per
            # address, before the first cold email. Replies are never checked.
            receipt_id = ""
            if needs_check:
                clearance = await self.precleared.clear(item["to_email"], self.state)
                if clearance.held:
                    compliance_paused = True
                    logger.warning(
                        f"Sender: checagem de lei indisponível, segurando o email "
                        f"frio para um próximo ciclo: {clearance.reason}"
                    )
                    continue
                if not clearance.allowed:
                    await self.state.update_outbox_item(
                        item["id"], status="failed",
                        error=f"precleared: {clearance.verdict}: {clearance.reason}"[:300],
                    )
                    logger.warning(
                        f"Sender: o Precleared segurou o email para {item['to_email']}: "
                        f"{clearance.verdict} ({clearance.reason})"
                    )
                    continue
                receipt_id = clearance.receipt_id

            result = await self.provider.send_email(
                item["to_email"], item["subject"], item["body"],
                thread_ref=item.get("thread_ref", ""),
                in_reply_to=item.get("in_reply_to", ""),
            )
            if not result.ok:
                await self.state.update_outbox_item(
                    item["id"], status="failed", error=result.error[:300]
                )
                continue

            sent += 1
            now_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            await self.state.update_outbox_item(
                item["id"], status="sent", sent_at=now_iso,
                message_id=result.message_id, thread_ref=result.thread_ref,
            )
            if prospect.status in ("new", "queued"):
                await self.state.update_prospect_status(prospect.id, "contacted")

            # A sent reply belongs in its conversation thread.
            if item["kind"] == "reply" and item.get("conversation_id"):
                try:
                    convo = await self.state.get_conversation(item["conversation_id"])
                    if convo:
                        from harvey.models.conversation import Message
                        convo.thread.append(
                            Message(sender="harvey", content=item["body"])
                        )
                        await self.state.update_conversation(
                            convo.id, thread_json=convo.thread_json()
                        )
                except Exception as e:
                    logger.debug(f"Sender: convo append failed: {e}")
            details = {
                "to": item["to_email"], "step": item["step"],
                "kind": item["kind"], "provider": self.provider.name,
            }
            if receipt_id:
                details["precleared_receipt"] = receipt_id
            await self.state.log_action(
                action_type="email_sent",
                agent="sender",
                details=details,
            )
            logger.info(
                f"Sender: enviada a etapa {item['step']} para {item['to_email']} "
                f"pelo {self.provider.name}."
            )
            # Human-ish pacing BETWEEN sends (not after the last, and never
            # in tests where pacing is disabled).
            if self.send_pacing and sent < budget:
                await asyncio.sleep(random.uniform(*SEND_JITTER_SECONDS))

        if sent:
            logger.info(f"Sender: {sent} email(s) enviado(s) neste ciclo "
                        f"({sent_today + sent}/{max_daily} hoje).")
