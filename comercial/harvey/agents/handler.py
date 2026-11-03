"""Handler — monitors replies and manages conversations.

Works against Instantly (legacy) or a native mail provider (Gmail/SMTP).
The native path also owns bounce handling: a bounce marks the address
invalid, cancels the prospect's queued sends, and — past a bounce-rate
threshold — flips the global kill switch so a bad list can't torch the
sending domain while nobody's watching.
"""

import logging
from datetime import datetime, timezone

from harvey.brain import Brain, BrainUnavailable
from harvey.config import MarianaConfig, EnvConfig
from harvey.integrations.instantly import InstantlyClient
from harvey.integrations.mail_provider import NATIVE_PROVIDERS, get_mail_provider
from harvey.models.conversation import Conversation, Message
from harvey.state import StateManager

logger = logging.getLogger("harvey.handler")

KILL_SWITCH_KEY = "sending_paused"
BOUNCE_COUNT_KEY = "bounce_count"
# Kill switch only engages after this many sends (a tiny sample lies).
MIN_SENDS_FOR_KILL_SWITCH = 10

INTENT_LABELS = {
    "interested",
    "objection",
    "not_interested",
    "ooo",
    "wrong_person",
    "question",
    "unsubscribe",
    "escalate",
}

# Intents that get an automated reply. Everything else is closed,
# deferred, or escalated to a human.
AUTO_REPLY_INTENTS = {"interested", "objection", "question", "wrong_person"}

# Hard opt-out phrases. If any of these appear, we ALWAYS honor the
# opt-out regardless of what the LLM classifier says.
OPT_OUT_PATTERNS = (
    "unsubscribe",
    "opt out",
    "opt-out",
    "remove me",
    "take me off",
    "stop emailing",
    "stop contacting",
    "stop sending",
    "do not contact",
    "do not email",
    "don't contact",
    "don't email",
    "never contact",
    "delete my info",
    "delete my data",
)

# Phrases that mean a human must take over. Never auto-reply to these.
ESCALATION_PATTERNS = (
    "lawyer",
    "attorney",
    "legal action",
    "lawsuit",
    "cease and desist",
    "harassment",
    "harassing",
    "report you",
    "reporting you",
    "spam complaint",
    "ftc",
    "gdpr",
    "can-spam",
    "blacklist",
)


class Handler:
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
        self.env = env
        self.instantly = InstantlyClient(env.instantly_api_key)
        self.provider = get_mail_provider(config, env)
        self.skills = ""

    @property
    def is_native(self) -> bool:
        return (
            self.config.channels.email.provider in NATIVE_PROVIDERS
            and self.provider is not None
        )

    async def run(self):
        """Check for new replies and handle them.

        Returns True only if every reply could be fetched and handled. The
        heartbeat sends nothing in a cycle where this isn't True, because a
        reply that wasn't read can't have cancelled its queued follow-ups.
        """
        logger.info("Handler: procurando respostas...")

        # Load foundational skills for this agent
        self.skills = self.brain.load_skills_for_agent("handler")

        if not self.config.channels.email.enabled:
            return True

        if self.is_native:
            return await self._run_native()

        # 1. Fetch active campaigns
        active_campaigns = await self.state.get_campaigns_by_status("active")
        if not active_campaigns:
            logger.info("Handler: nenhuma campanha ativa para acompanhar.")
            return True

        total_handled = 0
        complete = True

        for campaign in active_campaigns:
            if not campaign.instantly_campaign_id:
                continue

            # 2. Get replies from Instantly
            try:
                replies = await self.instantly.get_replies(campaign.instantly_campaign_id)
            except Exception as e:
                logger.error(f"Handler: não deu para buscar as respostas de {campaign.name}: {e}")
                complete = False
                continue
            if not replies:
                continue

            for reply in replies:
                if not isinstance(reply, dict):
                    continue
                try:
                    handled = await self._handle_reply(reply, campaign)
                    if handled:
                        total_handled += 1
                except BrainUnavailable as e:
                    logger.error(f"Handler: parando; as respostas ficam para depois ({e}).")
                    return False
                except Exception as e:
                    logger.error(f"Handler: erro ao tratar a resposta: {e}")
                    complete = False

        if total_handled:
            logger.info(f"Handler: {total_handled} resposta(s) tratada(s).")
        else:
            logger.info("Handler: nenhuma resposta nova.")
        return complete

    async def _handle_reply(self, reply: dict, campaign) -> bool:
        """Process a single reply. Returns True if a new reply was handled."""
        lead_email = (reply.get("lead_email") or reply.get("from_email") or "").strip().lower()
        reply_text = (reply.get("body") or reply.get("text") or "").strip()
        reply_uuid = str(reply.get("uuid") or reply.get("id") or "")

        if not lead_email or not reply_text:
            return False

        # Dedup: skip if we already processed this reply
        if reply_uuid and await self.state.is_reply_processed(reply_uuid):
            logger.debug(f"Handler: Reply {reply_uuid} already processed. Skipping.")
            return False

        logger.info(f"Handler: resposta de {lead_email}")

        consumed = True
        try:
            await self._process_reply(lead_email, reply_text, reply_uuid, campaign.id)
        except BrainUnavailable:
            # Nothing was decided or recorded about this reply yet, so leave
            # it for the next cycle instead of losing it to a provider outage.
            consumed = False
            raise
        finally:
            # Otherwise ALWAYS mark processed — even on early exits (opt-out,
            # OOO, unknown prospect) — so the same reply is never re-handled
            # or double-replied on the next cycle.
            if reply_uuid and consumed:
                await self.state.mark_reply_processed(reply_uuid)
        return True

    async def _process_reply(
        self,
        lead_email: str,
        reply_text: str,
        reply_uuid: str,
        campaign_id: str = "",
        reply_meta: dict | None = None,
        prospect=None,
        channel: str = "email",
    ):
        """Classify, record, and respond to a single reply.

        ``channel`` is where the reply came from. Email replies are found by
        address; WhatsApp / LinkedIn / Instagram replies arrive with their
        prospect already known (pasted in the dashboard, or a Cloud API
        webhook) and are answered on the same channel.
        """
        # Find the prospect by email (indexed lookup)
        if prospect is None:
            prospect = await self.state.get_prospect_by_email(lead_email)
        lead_email = lead_email or prospect.email if prospect else lead_email
        if not prospect:
            logger.warning(f"Handler: nenhum lead encontrado para {lead_email}")
            return

        # Update prospect status + stop-on-reply: a human answered, so every
        # queued sequence email for them is now wrong to send.
        await self.state.update_prospect_status(prospect.id, "replied")
        try:
            cancelled = await self.state.cancel_pending_outbox_for_prospect(prospect.id)
            if cancelled:
                logger.info(
                    f"Handler: cancelei {cancelled} email(s) na fila para "
                    f"{lead_email} (respondeu)."
                )
            # Same for WhatsApp/LinkedIn/Instagram drafts: they answered.
            await self.state.cancel_pending_channels_for_prospect(prospect.id)
        except Exception as e:
            logger.debug(f"Handler: outbox cancel failed: {e}")

        # 1. Classify intent. Hard keyword checks run FIRST and override
        # the LLM — opt-outs and legal threats must never be missed.
        text_lower = reply_text.lower()
        if any(p in text_lower for p in OPT_OUT_PATTERNS):
            intent = "unsubscribe"
        elif any(p in text_lower for p in ESCALATION_PATTERNS):
            intent = "escalate"
        else:
            intent = await self._classify_intent(reply_text, prospect)
        logger.info(f"Handler: intenção de {lead_email}: {intent}")
        try:
            from harvey.notify import notify_reply
            who = prospect.full_name() or prospect.company or lead_email
            await notify_reply(self.config, self.env, intent, who, channel, reply_text)
        except Exception as e:
            logger.debug(f"Handler: notify failed: {e}")

        # 2. The conversation as it will be, in memory only. Nothing about
        # this reply is stored until every model call it needs has succeeded:
        # if the provider goes down part-way (BrainUnavailable), the reply is
        # left unprocessed and the retry starts from the same stored state,
        # so the thread never gets the message twice or its stage advanced
        # twice. (Stop-on-reply above is idempotent and stays first.)
        existing_convos = await self.state.get_conversations_by_status("open")
        stored = next(
            (c for c in existing_convos if c.prospect_id == prospect.id), None
        )
        if stored is not None:
            convo = stored.model_copy(deep=True)
        else:
            convo = Conversation(
                id="",
                prospect_id=prospect.id,
                campaign_id=campaign_id,
                channel=channel,
                intent=intent,
                status="open",
            )
        convo.thread.append(Message(sender="prospect", content=reply_text))
        convo.channel = channel  # the draft is shaped for where they wrote
        convo.intent = intent
        old_stage = convo.stage
        convo.stage = self._determine_stage(intent, convo.stage, reply_text)

        # 2b. Draft the reply now, while nothing is stored yet.
        response = ""
        if intent in AUTO_REPLY_INTENTS:
            response = await self._generate_response(intent, reply_text, prospect, convo)

        # 2c. Store the conversation in one write.
        if stored is None:
            convo.id = await self.state.add_conversation(convo)
        else:
            await self.state.update_conversation(
                convo.id,
                thread_json=convo.thread_json(),
                intent=intent,
                stage=convo.stage,
            )
        if convo.stage != old_stage:
            logger.info(f"Handler: estágio de {lead_email}: {old_stage} -> {convo.stage}")

        # 3. Route based on intent
        if intent == "unsubscribe":
            # Honor opt-outs ALWAYS. No reply, no future contact.
            await self.state.update_conversation(convo.id, status="closed", stage="closed_lost")
            await self.state.update_prospect_status(prospect.id, "opted_out")
            await self.state.log_action(
                action_type="opt_out",
                agent="handler",
                details={"prospect_email": lead_email},
            )
            logger.info(f"Handler: {lead_email} pediu para sair. Bloqueado para sempre. Nenhuma resposta enviada.")
            return

        if intent == "escalate":
            # Angry / legal / compliance replies go to a human. Never auto-reply.
            await self.state.update_conversation(convo.id, status="needs_human")
            await self.state.log_action(
                action_type="escalation",
                agent="handler",
                details={
                    "prospect_email": lead_email,
                    "reply_preview": reply_text[:200],
                },
            )
            logger.warning(
                f"Handler: resposta de {lead_email} PRECISA DE VOCÊ. Nenhuma resposta automática."
            )
            return

        if intent == "not_interested":
            await self.state.update_conversation(convo.id, status="closed", stage="closed_lost")
            await self.state.update_prospect_status(prospect.id, "lost")
            logger.info(f"Handler: {lead_email} sem interesse. Encerrando. Um não basta.")
            return

        if intent == "ooo":
            logger.info(f"Handler: {lead_email} está ausente. Volto a falar depois.")
            return

        if intent not in AUTO_REPLY_INTENTS:
            logger.warning(f"Handler: sem regra de resposta para a intenção '{intent}'. Pulando.")
            return

        # For interested, objection, question, wrong_person — the reply drafted above
        if not response:
            # No usable draft from a working provider: hand it to a human
            # rather than leave an answered-looking thread with no reply.
            await self.state.update_conversation(convo.id, status="needs_human")
            await self.state.log_action(
                action_type="escalation",
                agent="handler",
                details={"prospect_email": lead_email, "reason": "no usable reply draft",
                         "reply_preview": reply_text[:200]},
            )
            logger.warning(
                f"Handler: não deu para escrever a resposta para {lead_email}. "
                "Marcada para você revisar."
            )
            return

        # Answer on the channel they used. Non-email replies become drafts
        # in the dashboard's Mensagens tab, sent by you.
        if channel != "email":
            await self._queue_channel_reply(response, prospect, convo, channel, intent)
            return

        # Send the response — natively through the outbox approval ladder,
        # or immediately via Instantly (legacy).
        if self.is_native:
            await self._queue_native_reply(
                response, prospect, convo, reply_meta or {}, intent
            )
        elif reply_uuid:
            result = await self.instantly.send_reply(reply_uuid, response)
            if result is not None:
                # Add our response to conversation
                convo.thread.append(Message(sender="harvey", content=response))
                await self.state.update_conversation(
                    convo.id,
                    thread_json=convo.thread_json(),
                )
                logger.info(f"Handler: respondido para {lead_email}")

                await self.state.log_action(
                    action_type="reply",
                    agent="handler",
                    details={
                        "prospect_email": lead_email,
                        "intent": intent,
                        "response_preview": response[:100],
                    },
                )

    # ── Native provider path (Gmail / SMTP) ──

    async def _run_native(self) -> bool:
        """Poll the mailbox, split bounces from human replies, handle both.
        Returns True only if the mailbox was read and every message handled."""
        if not self.provider.is_configured():
            logger.debug(
                f"Handler: provider '{self.provider.name}' not configured yet."
            )
            return True  # nothing to read; the sender can't send through it either

        try:
            inbound = await self.provider.get_replies()
        except Exception as e:
            logger.error(f"Handler: falhou ao buscar respostas: {e}")
            return False

        handled = 0
        complete = True
        for msg in inbound:
            dedup_key = msg.provider_id or msg.message_id
            if not dedup_key or await self.state.is_reply_processed(dedup_key):
                continue
            consumed = True
            try:
                if msg.is_bounce:
                    await self._handle_bounce(msg)
                elif msg.body.strip():
                    await self._process_reply(
                        msg.from_email,
                        msg.body.strip(),
                        reply_uuid="",
                        reply_meta={
                            "thread_ref": msg.thread_ref,
                            "message_id": msg.message_id,
                            "subject": msg.subject,
                        },
                    )
                handled += 1
            except BrainUnavailable as e:
                consumed = False
                complete = False
                logger.error(f"Handler: parando; as respostas ficam para depois ({e}).")
                break
            except Exception as e:
                logger.error(f"Handler: erro ao tratar {msg.from_email}: {e}")
                complete = False
            finally:
                if consumed:
                    await self.state.mark_reply_processed(dedup_key)

        if handled:
            logger.info(f"Handler: {handled} mensagem(ns) recebida(s) tratada(s).")
        else:
            logger.info("Handler: nenhuma resposta nova.")
        return complete

    async def _handle_bounce(self, msg):
        """A bounce is a data bug AND a reputation threat. Fix both."""
        outbox_item = await self.state.find_outbox_by_message_id(msg.in_reply_to)
        prospect = None
        if outbox_item:
            prospect = await self.state.get_prospect(outbox_item["prospect_id"])

        if prospect:
            await self.state.update_prospect_email(
                prospect.id, prospect.email, "invalid"
            )
            cancelled = await self.state.cancel_pending_outbox_for_prospect(
                prospect.id, reason="bounced"
            )
            logger.warning(
                f"Handler: BOUNCE de {prospect.email}: marcado como inválido, "
                f"{cancelled} email(s) da fila cancelado(s)."
            )
        else:
            logger.warning(
                f"Handler: bounce recebido ({msg.subject[:60]}), mas não deu para "
                "ligar a um email enviado."
            )

        bounces = await self.state.increment_setting(BOUNCE_COUNT_KEY)
        total_sent = await self.state.count_outbox_sent()
        await self.state.log_action(
            action_type="bounce",
            agent="handler",
            details={"prospect": prospect.email if prospect else "unknown",
                     "bounces": bounces, "total_sent": total_sent},
        )

        max_rate = getattr(self.config.channels.email, "max_bounce_rate", 0.05)
        if (
            max_rate > 0
            and total_sent >= MIN_SENDS_FOR_KILL_SWITCH
            and bounces / total_sent > max_rate
        ):
            reason = (
                f"bounce rate {bounces}/{total_sent} exceeded "
                f"{max_rate:.0%} — check list quality before resuming"
            )
            await self.state.set_setting(KILL_SWITCH_KEY, reason)
            logger.error(f"Handler: BOTÃO DE PÂNICO ACIONADO: {reason}")

    async def _queue_native_reply(
        self, response: str, prospect, convo, reply_meta: dict, intent: str
    ):
        """Route Mariana's reply through the outbox (approval ladder applies)."""
        require_approval = getattr(
            self.config.channels.email, "require_approval", True
        )
        subject = reply_meta.get("subject", "")
        if subject and not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        item_id = await self.state.add_outbox_item(
            prospect_id=prospect.id,
            conversation_id=convo.id,
            kind="reply",
            to_email=prospect.email,
            subject=subject or "Re: your note",
            body=response,
            send_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            status="pending_review" if require_approval else "approved",
            provider=self.provider.name if self.provider else "",
            thread_ref=reply_meta.get("thread_ref", ""),
            in_reply_to=reply_meta.get("message_id", ""),
        )
        if item_id:
            mode = "esperando a sua aprovação" if require_approval else "na fila para sair"
            logger.info(f"Handler: resposta para {prospect.email} {mode} ({intent}).")
            await self.state.log_action(
                action_type="reply_queued",
                agent="handler",
                details={"prospect_email": prospect.email, "intent": intent,
                         "response_preview": response[:100]},
            )

    async def _queue_channel_reply(self, response: str, prospect, convo, channel: str,
                                   intent: str):
        """Draft the answer on WhatsApp / LinkedIn / Instagram."""
        last = await self.state.channel_target_for_prospect(prospect.id, channel)
        target = (last or {}).get("target", "")
        if not target and channel == "whatsapp":
            from harvey.integrations.whatsapp import normalize_phone
            target = normalize_phone(prospect.phone, self.config.channels.whatsapp.default_country_code)
        if not target and channel == "linkedin":
            target = prospect.linkedin_url
        item_id = await self.state.add_channel_item(
            channel=channel, target=target, body=response, kind="reply",
            conversation_id=convo.id, prospect_id=prospect.id,
            company_id=prospect.company_id, contact_name=prospect.full_name(),
            company_name=prospect.company or (last or {}).get("company_name", ""),
            language=(last or {}).get("language", ""),
            # They wrote first, so WhatsApp replies may go through the API.
            opted_in=(channel == "whatsapp"),
            mode=(self.config.channels.whatsapp.mode if channel == "whatsapp" else "manual"),
        )
        if item_id:
            logger.info(f"Handler: resposta de {channel} para {prospect.full_name()} esperando "
                        f"na aba Mensagens ({intent}).")
            await self.state.log_action(
                action_type="reply_queued", agent="handler",
                details={"channel": channel, "intent": intent,
                         "response_preview": response[:100]},
            )

    async def handle_external_reply(self, prospect, reply_text: str, channel: str) -> str:
        """A reply that arrived outside email (pasted in the dashboard or via
        the WhatsApp webhook). Stops every queued email and draft for the
        person, records the conversation, and drafts the answer on that
        channel. Returns the conversation id."""
        self.skills = self.skills or self.brain.load_skills_for_agent("handler")
        await self._process_reply(
            prospect.email, reply_text, reply_uuid="", prospect=prospect, channel=channel,
        )
        convos = await self.state.get_conversations_by_status("open")
        convos += await self.state.get_conversations_by_status("needs_human")
        convo = next((c for c in convos if c.prospect_id == prospect.id), None)
        return convo.id if convo else ""

    async def _reply_context(self, intent: str, prospect, convo) -> str:
        """Real free slots and the right portfolio pieces, for the draft."""
        lines = []
        language = "pt-BR"
        try:
            from harvey import market
            mk = await market.for_prospect(self.state, prospect,
                                           getattr(self.config.persona, "language", "pt-BR"))
            language = market.language(mk)
        except Exception:
            pass
        offer = self.config.product.offer
        if intent in ("interested", "question"):
            if offer.booking_method == "calendar_link" and offer.booking_url:
                lines.append(f"Booking link to offer for a call: {offer.booking_url}")
            else:
                try:
                    from harvey.integrations.calendar import CalendarClient, format_slots
                    slots = await CalendarClient(self.config, self.env).get_available_slots()
                    if slots:
                        lines.append("Real free times on the calendar (offer these, exactly): "
                                     + format_slots(slots, language))
                except Exception as e:
                    logger.debug(f"Handler: calendar unavailable: {e}")
        try:
            from harvey import portfolio
            company = await self.state.get_company(prospect.company_id) if prospect.company_id else None
            pieces = portfolio.match(prospect.industry, prospect.company, prospect.title,
                                     company.name if company else "",
                                     company.description if company else "")
            if pieces:
                lines.append("Portfolio pieces that match this client (share ONE link only "
                             "if they asked to see work, or if it helps the next step):\n"
                             + portfolio.describe(pieces))
        except Exception as e:
            logger.debug(f"Handler: portfolio match failed: {e}")
        return "\n".join(lines)

    async def _classify_intent(self, reply_text: str, prospect) -> str:
        """Ask the brain to classify the reply's intent."""
        prompt = f"""Classify this email reply into exactly ONE category:
- "interested" — wants to learn more, open to a meeting, positive response
- "objection" — has concerns but hasn't said no (price, timing, competition)
- "not_interested" — a clear no, not now, or "we're all set"
- "unsubscribe" — asks to stop being contacted, remove from list, opt out
- "escalate" — angry, hostile, threatens legal action, or mentions spam/compliance
- "ooo" — out of office / auto-reply
- "wrong_person" — not the right contact, suggests someone else
- "question" — asking for more information before deciding

When in doubt between "not_interested" and "unsubscribe", choose "unsubscribe".
When in doubt between anything and "escalate", choose "escalate".

Reply from {prospect.full_name()} ({prospect.title} at {prospect.company}):
\"\"\"{reply_text}\"\"\"

Respond with ONLY the category label, nothing else."""

        result = await self.brain.think(
            prompt, session_id="harvey-handler",
            agent="handler", task="classify_intent",
        )
        if not result:
            paused = getattr(self.brain, "paused_reason", "")
            if paused:
                # The provider is down (login, setup, usage limit), not this
                # reply: don't escalate it, leave it unprocessed.
                raise BrainUnavailable(paused)
            # Classifier failed. Do NOT auto-reply blind — flag for a human.
            logger.warning("Handler: a classificação não devolveu nada. Passando para você.")
            return "escalate"

        # Robust extraction: take the first recognized label anywhere in
        # the response (models sometimes add explanation despite instructions).
        cleaned = result.strip().strip('"').strip("'").lower()
        if cleaned in INTENT_LABELS:
            return cleaned
        for label in sorted(INTENT_LABELS, key=len, reverse=True):
            if label in cleaned:
                return label

        logger.warning(f"Handler: intenção desconhecida '{cleaned[:80]}'. Tratando como 'question'.")
        return "question"

    def _determine_stage(self, intent: str, current_stage: str, reply_text: str) -> str:
        """Advance the conversation stage based on intent and context."""
        text_lower = reply_text.lower()

        # Terminal states
        if intent in ("not_interested", "unsubscribe"):
            return "closed_lost"

        if intent == "escalate":
            return current_stage  # Human decides what happens next

        # Stage advancement rules
        if intent == "interested":
            # Meeting/call signals from an interested prospect → closing
            if any(w in text_lower for w in ["let's meet", "schedule", "calendar", "book a call", "free on", "available"]):
                return "closing"
            if current_stage == "initial_outreach":
                return "engaged"
            if current_stage == "engaged":
                # Check if they're asking about specifics → presenting
                if any(w in text_lower for w in ["price", "cost", "how much", "pricing", "demo", "trial"]):
                    return "presenting"
                return "qualifying"
            if current_stage in ("qualifying", "presenting"):
                return "negotiating"
            if current_stage == "negotiating":
                return "closing"

        if intent == "objection":
            # Objections typically happen during presenting or negotiating
            if current_stage in ("initial_outreach", "engaged"):
                return "qualifying"
            # Stay in current stage during objection handling

        if intent == "question":
            if current_stage == "initial_outreach":
                return "engaged"
            if current_stage == "engaged":
                return "qualifying"

        return current_stage

    async def _generate_response(
        self, intent: str, reply_text: str, prospect, convo: Conversation
    ) -> str:
        """Generate an appropriate response based on intent."""
        # Build conversation history for context
        history = "\n".join(
            f"{'Me' if m.sender == 'harvey' else prospect.full_name()}: {m.content}"
            for m in convo.thread[-6:]  # Last 6 messages for context
        )

        objection_context = ""
        if intent == "objection":
            # Check if we have a pre-configured response
            for trigger, response in self.config.product.objection_responses.items():
                if trigger.lower() in reply_text.lower():
                    objection_context = f"\nSuggested approach for this objection: {response}"
                    break

        prompt = self.brain.load_prompt("handler", stage=convo.stage)
        if not prompt:
            prompt = f"""You are {self.config.persona.name}, {self.config.persona.role} at {self.config.persona.company}.
Your tone is: {self.config.persona.tone}
Product: {self.config.product.name} — {self.config.product.description}"""

        # Inject objection handling + sales methodology skills
        if self.skills:
            prompt += "\n\n" + self.skills

        prompt += f"""

Conversation so far:
{history}

The prospect's intent is: {intent}
{objection_context}
{await self._reply_context(intent, prospect, convo)}

Reply in the same language the prospect wrote in.
Write a reply that:"""

        if intent == "interested":
            prompt += """
- Acknowledges their interest warmly
- Suggests a specific next step (brief call or meeting)
- Keeps it short (under 80 words)
- Includes a clear CTA with flexibility on timing"""
        elif intent == "objection":
            prompt += """
- Addresses the concern directly and empathetically
- Provides evidence or a reframe
- Doesn't argue — redirect toward value
- Keeps it under 100 words"""
        elif intent == "question":
            prompt += """
- Answers their question clearly and concisely
- Ties the answer back to value for them
- Ends with a soft CTA
- Under 100 words"""
        elif intent == "wrong_person":
            prompt += """
- Thanks them politely
- Asks who the right person would be
- Makes it easy for them to refer (one-line ask)
- Under 50 words"""

        if convo.channel and convo.channel != "email":
            prompt += (f"\n\nThis is a {convo.channel} message: shorter than an email, "
                       "conversational, no subject, no signature, no markdown.")
        else:
            prompt += "\n\nWrite ONLY the email body. No subject line, no greeting label, no signature block, no markdown."

        response = await self.brain.think(
            prompt, session_id="harvey-handler",
            agent="handler", task="generate_response",
        )
        if not response:
            paused = getattr(self.brain, "paused_reason", "")
            if paused:
                # The provider went down mid-reply; nothing is stored yet,
                # so leave the reply for a clean retry.
                raise BrainUnavailable(paused)
            return ""
        response = response.strip()
        # Guard against the model returning meta-text instead of an email
        if response.lower().startswith(("i can't", "i cannot", "as an ai", "sorry,")):
            logger.warning("Handler: o modelo devolveu um comentário em vez da mensagem. Descartado.")
            return ""
        return response
