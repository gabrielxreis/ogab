"""Post-job: the cheapest next job is the client you already have.

Two moments, both drafted for approval, never sent on their own:
  * N days after delivery: thank them, ask for a short testimonial and for
    one person who might need video too.
  * Before the client's next event (next_event_date): offer to cover it,
    referencing the work already done together.

Brazilian clients get it on WhatsApp when there is a number (they're
clients now, so the Cloud API may send it); everyone else by email.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from harvey import market
from harvey.integrations.whatsapp import normalize_phone

logger = logging.getLogger("harvey.postjob")


def _parse(d: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime((d or "")[:10], fmt).date()
        except ValueError:
            continue
    return None


class PostJobAgent:
    def __init__(self, brain, state, config, env=None):
        self.brain = brain
        self.state = state
        self.config = config
        self.env = env

    @property
    def cfg(self):
        return self.config.postjob

    def due(self, job: dict, today: date) -> str:
        """'testimonial', 'reengage' or '' for one job."""
        delivered = _parse(job.get("delivered_at", ""))
        if (job.get("status") == "delivered" and delivered
                and not job.get("testimonial_requested_at")
                and today >= delivered + timedelta(days=self.cfg.testimonial_after_days)):
            return "testimonial"
        nxt = _parse(job.get("next_event_date", ""))
        if (job.get("status") in ("won", "delivered") and nxt and today < nxt
                and today >= nxt - timedelta(days=self.cfg.reengage_days_before_event)):
            last = _parse(job.get("reengaged_at", ""))
            if not last or last < nxt - timedelta(days=self.cfg.reengage_days_before_event):
                return "reengage"
        return ""

    async def _write(self, moment: str, job: dict, language: str, channel: str) -> str:
        goal = ("thank them for the project, ask for a short testimonial (2-3 lines they "
                "can reply with) and ask if they know one person or company that could "
                "use video too" if moment == "testimonial" else
                f"their next event is on {job.get('next_event_date')}: offer to cover it, "
                "reference the previous project in one line, ask if they want to talk")
        linkedin = (getattr(self.config.persona, "linkedin", "") or "").strip()
        words, links = 70, "no links"
        if moment == "testimonial" and linkedin:
            goal += (f". Also ask, as a favor, for a recommendation on LinkedIn ({linkedin}): "
                     "include a suggested recommendation of 2 or 3 sentences in quotes, "
                     "written in the client's voice about this project, that they can adjust "
                     "and paste")
            words, links = 130, f"the only link allowed is {linkedin}"
        prompt = f"""Write a short {channel} message from an audiovisual professional to a
past client, in {market.name_for_code(language)},
first person, warm and direct, under {words} words, one question at the end. No em
dashes, no exclamation marks, no signature, {links}.

Client: {job.get('contact_name')} at {job.get('company_name')}
Previous project: {job.get('service')} ({job.get('segment')})
Goal: {goal}

Return ONLY the message text."""
        text = await self.brain.think(prompt, agent="postjob", task=moment)
        return (text or "").strip().strip('"').replace("—", ",").replace("–", ",")

    # ── proposal follow-up and production reminders ──

    def followup_due(self, job: dict, today: date, last_client_msg: date | None) -> bool:
        """Proposal sent, no answer since, and the next follow-up day reached."""
        if job.get("status") != "proposal" or not job.get("proposal_sent_at"):
            return False
        days = self.config.production.proposal_followup_days
        n = int(job.get("followups") or 0)
        if n >= len(days):
            return False
        since = _parse(job.get("last_followup_at") or "") or _parse(job["proposal_sent_at"])
        sent = _parse(job["proposal_sent_at"])
        if last_client_msg and sent and last_client_msg >= sent:
            return False  # they answered after the proposal: a human conversation now
        return bool(since and today >= since + timedelta(days=days[n]))

    async def _last_client_message(self, job: dict) -> date | None:
        if not job.get("conversation_id"):
            return None
        convo = await self.state.get_conversation(job["conversation_id"])
        if not convo:
            return None
        stamps = [m.timestamp for m in convo.thread if m.sender != "harvey" and m.timestamp]
        return max(stamps).date() if stamps else None

    async def _draft_to_client(self, job: dict, prospect, body: str, kind: str, subject: str):
        """On the conversation's channel when it isn't email, else email."""
        channel = "email"
        if job.get("conversation_id"):
            convo = await self.state.get_conversation(job["conversation_id"])
            channel = (convo.channel if convo else "email") or "email"
        if channel != "email":
            last = await self.state.channel_target_for_prospect(prospect.id, channel)
            target = (last or {}).get("target", "")
            if target:
                await self.state.add_channel_item(
                    channel=channel, target=target, body=body, kind=kind,
                    prospect_id=prospect.id, company_id=prospect.company_id,
                    contact_name=job.get("contact_name", ""),
                    company_name=job.get("company_name", ""),
                    opted_in=(channel == "whatsapp"),
                    mode=(self.config.channels.whatsapp.mode if channel == "whatsapp" else "manual"),
                    conversation_id=job.get("conversation_id", ""),
                )
                return channel
        if prospect.email:
            await self.state.add_outbox_item(
                prospect_id=prospect.id, to_email=prospect.email, subject=subject, body=body,
                kind=kind, status="pending_review", conversation_id=job.get("conversation_id", ""),
                send_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            )
            return "email"
        return ""

    async def _short(self, goal: str, job: dict, language: str) -> str:
        prompt = f"""Write a short message from an audiovisual professional to a client, in
{market.name_for_code(language)}, first person,
warm, under 50 words, no em dashes, no exclamation marks, no signature, no links.
Client: {job.get('contact_name')} at {job.get('company_name')}. Project: {job.get('service')}.
Goal: {goal}
Return ONLY the message."""
        text = await self.brain.think(prompt, agent="postjob", task="short")
        return (text or "").strip().strip('"').replace("\u2014", ",").replace("\u2013", ",")

    async def production_tick(self, today: date | None = None) -> int:
        """Proposal follow-ups, shoot-eve reminders, delivery alerts."""
        from harvey.notify import notify
        today = today or date.today()
        done = 0
        for job in await self.state.get_jobs():
            prospect = await self.state.get_prospect(job["prospect_id"]) if job.get("prospect_id") else None
            if not prospect or prospect.status == "opted_out":
                continue
            mk = await market.for_prospect(self.state, prospect,
                                           getattr(self.config.persona, "language", "pt-BR"))
            language = market.language(mk)

            if self.followup_due(job, today, await self._last_client_message(job)):
                n = int(job.get("followups") or 0)
                goal = ("a light check-in about the proposal you sent a few days ago; ask if "
                        "they had a chance to look and if any question came up" if n == 0 else
                        "a last, gracious check-in about the proposal; offer to adjust the scope "
                        "or date if that helps; no pressure")
                body = await self._short(goal, job, language)
                if body and await self._draft_to_client(
                        job, prospect, body, "proposal_followup",
                        market.pick(language, pt="sobre a proposta", es="sobre la propuesta", fr="à propos de la proposition", en="about the proposal")):
                    await self.state.update_job(job["id"], followups=n + 1,
                                                last_followup_at=today.isoformat())
                    done += 1

            shoot = _parse(job.get("shoot_date", ""))
            if (self.config.production.shoot_reminder and job.get("status") == "won"
                    and shoot == today + timedelta(days=1) and not job.get("reminder_sent_at")):
                details = " | ".join(x for x in (
                    f"{job.get('shoot_time') or ''}".strip(), job.get("address", ""),
                    job.get("onsite_contact", "")) if x)
                checklist = (job.get("checklist") or "").replace("\n", " · ")
                await notify(self.config, self.env, f"Amanhã: {job.get('company_name')}",
                             f"{details}\n{checklist}"[:300])
                body = await self._short(
                    f"confirm tomorrow's shoot ({job.get('shoot_time') or ''} at "
                    f"{job.get('address') or 'the location'}) and ask them to confirm the on-site "
                    "contact", job, language)
                if body:
                    await self._draft_to_client(job, prospect, body, "reminder",
                                                market.pick(language, pt="amanhã", es="mañana", fr="demain", en="tomorrow"))
                await self.state.update_job(job["id"], reminder_sent_at=today.isoformat())
                done += 1

            due = _parse(job.get("delivery_due", ""))
            if job.get("status") == "won" and due == today + timedelta(days=1):
                await notify(self.config, self.env, f"Entrega amanhã: {job.get('company_name')}",
                             f"{job.get('service')} · pasta: {job.get('project_dir') or '?'}")
        return done

    async def run(self) -> int:
        try:
            await self.production_tick()
        except Exception as e:
            logger.warning(f"PostJob: falhou a rodada de produção: {e}")
        if not self.cfg.enabled:
            return 0
        today = date.today()
        drafted = 0
        for job in await self.state.get_jobs():
            moment = self.due(job, today)
            if not moment or not job.get("prospect_id"):
                continue
            prospect = await self.state.get_prospect(job["prospect_id"])
            if not prospect or prospect.status == "opted_out":
                continue
            mk = await market.for_prospect(self.state, prospect,
                                           getattr(self.config.persona, "language", "pt-BR"))
            language = market.language(mk)
            phone = ""
            if mk == market.BR:
                last = await self.state.channel_target_for_prospect(prospect.id, "whatsapp")
                phone = (last or {}).get("target") or normalize_phone(
                    prospect.phone, self.config.channels.whatsapp.default_country_code)
            channel = "whatsapp" if phone else "email"
            if channel == "email" and not prospect.email:
                continue
            body = await self._write(moment, job, language, channel)
            if not body:
                continue
            if channel == "whatsapp":
                await self.state.add_channel_item(
                    channel="whatsapp", target=phone, body=body, kind="postjob",
                    prospect_id=prospect.id, company_id=prospect.company_id,
                    contact_name=job.get("contact_name", ""),
                    company_name=job.get("company_name", ""), language=language,
                    opted_in=True, mode=self.config.channels.whatsapp.mode,
                )
            else:
                subject = (market.pick(language, pt="obrigado pelo projeto", es="gracias por el proyecto",
                                       fr="merci pour le projet", en="thank you for the project")
                           if moment == "testimonial" else
                           market.pick(language, pt="próximo evento", es="su próximo evento",
                                       fr="votre prochain événement", en="your next event"))
                await self.state.add_outbox_item(
                    prospect_id=prospect.id, to_email=prospect.email, subject=subject,
                    body=body, kind="postjob", status="pending_review",
                    send_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                )
            stamp = today.isoformat()
            await self.state.update_job(
                job["id"], **({"testimonial_requested_at": stamp} if moment == "testimonial"
                              else {"reengaged_at": stamp}))
            drafted += 1
            logger.info(f"PostJob: rascunho de {moment} para {job.get('company_name')} ({channel}).")
        return drafted
