"""Channels agent: one non-email message per prospect, on the right channel.

Email is the writer's job and goes to everyone with a deliverable address.
This agent adds the second touch, picked by market (harvey/market.py):

  Brazil   WhatsApp when there is a phone, else Instagram DM.
  Abroad   LinkedIn (connection note + message) when there is a profile,
           else Instagram DM. Never WhatsApp: abroad, cold WhatsApp from an
           unknown number reads as spam.

Every draft waits for approval in the dashboard and, except WhatsApp to
OPTED-IN contacts in cloud_api mode, is sent by you: the dashboard opens
WhatsApp with the text typed in, or opens the profile and copies the text.
No platform account is ever automated, so none can be banned.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from harvey import market
from harvey.brain import Brain
from harvey.config import MarianaConfig
from harvey.integrations.whatsapp import (
    CloudAPIClient, is_probably_mobile, normalize_phone, wa_link,
)
from harvey.state import StateManager

logger = logging.getLogger("harvey.channels")

MAX_DRAFTS_PER_CYCLE = 15
LINKEDIN_NOTE_LIMIT = 300  # LinkedIn's hard cap on a connection note
WORD_LIMITS = {"whatsapp": 70, "linkedin": 90, "instagram": 60}
EM_DASHES = ("—", "–")


OPENERS = ("gatilho", "observacao", "pergunta", "prova_social")
TRIGGER_TAG = "[momento]"


def trigger_of(notes: str) -> str:
    """The 'why now' line `mariana linkedin momento` left in the lead's notes."""
    for line in (notes or "").splitlines():
        if line.startswith(TRIGGER_TAG):
            return line[len(TRIGGER_TAG):].strip()
    return ""


async def best_openers_hint(state, channel: str) -> str:
    """Tell the writer which opening style answers best so far (Numbers tab)."""
    from harvey.metrics import openers
    rows = [r for r in await openers(state) if r["channel"] == channel and r["sent"] >= 10]
    if not rows:
        return ""
    best = max(rows, key=lambda r: r["reply_rate"])
    return (f"Até agora, no {channel}, o estilo que mais teve resposta foi "
            f"{best['opener']} ({best['reply_rate']}% de {best['sent']}). Prefira-o quando couber.")


def clean_message(text: str) -> str:
    """Strip what the model sometimes adds anyway: quotes, labels, dashes."""
    text = (text or "").strip().strip('"').strip()
    text = re.sub(r"^(mensagem|message|whatsapp|dm|note)\s*:\s*", "", text, flags=re.I)
    for dash in EM_DASHES:
        text = text.replace(f" {dash} ", ", ").replace(dash, ", ")
    return text.strip()


def open_url(item: dict) -> str:
    """Where the dashboard's send button goes for this draft."""
    if item["channel"] == "whatsapp":
        return wa_link(item["target"], item["body"])
    return item["target"]


class ChannelsAgent:
    def __init__(self, brain: Brain, state: StateManager, config: MarianaConfig, env=None):
        self.brain = brain
        self.state = state
        self.config = config
        self.env = env
        ch = config.channels
        self.whatsapp = ch.whatsapp
        self.client = CloudAPIClient(
            getattr(env, "whatsapp_token", "") if env else "",
            getattr(env, "whatsapp_phone_number_id", "") if env else "",
        )

    def _enabled(self, channel: str) -> bool:
        cfg = getattr(self.config.channels, channel, None)
        return bool(cfg and cfg.enabled)

    def whatsapp_country_allowed(self, phone: str) -> bool:
        allowed = [c.strip("+ ") for c in (self.whatsapp.countries or [])]
        return not allowed or any(phone.startswith(c) for c in allowed)

    async def _company_links(self, company_id: str) -> dict[str, str]:
        links: dict[str, str] = {}
        if not company_id:
            return links
        try:
            rows = await self.state.get_observations(company_id=company_id,
                                                     latest_only=True)
        except Exception:
            return links
        for r in rows:
            if r["signal_code"] in ("INSTAGRAM_PROFILE", "LINKEDIN_COMPANY"):
                links[r["signal_code"]] = r.get("value_text") or ""
        return links

    async def choose(self, prospect) -> tuple[str, str, str, str] | None:
        """(channel, target, market, company_name) or None when no channel fits."""
        company = None
        if prospect.company_id:
            company = await self.state.get_company(prospect.company_id)
        company_name = prospect.company or (company.name if company else "")
        mk = await market.for_prospect(
            self.state, prospect, getattr(self.config.persona, "language", "pt-BR"))
        links = await self._company_links(prospect.company_id)

        if mk == market.BR and self._enabled("whatsapp"):
            raw = prospect.phone or (company.phone if company else "")
            phone = normalize_phone(raw, self.whatsapp.default_country_code)
            if phone and self.whatsapp_country_allowed(phone):
                return "whatsapp", phone, mk, company_name
        if mk == market.INTL and self._enabled("linkedin"):
            target = prospect.linkedin_url or links.get("LINKEDIN_COMPANY", "")
            if target:
                return "linkedin", target, mk, company_name
        if self._enabled("instagram") and links.get("INSTAGRAM_PROFILE"):
            return "instagram", links["INSTAGRAM_PROFILE"], mk, company_name
        return None

    async def draft_pending(self) -> int:
        drafted_any: set[str] = set()
        for ch in ("whatsapp", "linkedin", "instagram"):
            drafted_any |= await self.state.channel_drafted(ch)
        candidates = []
        for status in ("queued", "contacted"):
            candidates += await self.state.get_prospects_by_status(status)
        candidates = [p for p in candidates if p.id not in drafted_any]
        # Leads with a "why now" (open role, event, new role) go first.
        candidates.sort(key=lambda p: (not trigger_of(p.personalization_notes), -(p.score or 0)))
        if not candidates:
            return 0

        campaign_of = await self._campaign_index()
        drafted = 0
        for prospect in candidates:
            if drafted >= MAX_DRAFTS_PER_CYCLE:
                break
            choice = await self.choose(prospect)
            if not choice:
                continue
            channel, target, mk, company_name = choice
            draft = await self.write(channel, prospect, company_name, mk)
            if not draft or not draft.get("body"):
                continue
            require = (self.whatsapp.require_approval if channel == "whatsapp"
                       else True)
            item_id = await self.state.add_channel_item(
                channel=channel,
                target=target,
                body=draft["body"],
                note=draft.get("note", ""),
                prospect_id=prospect.id,
                company_id=prospect.company_id,
                campaign_id=campaign_of.get(prospect.id, "manual"),
                contact_name=prospect.full_name(),
                company_name=company_name,
                language=market.language(mk),
                status="pending_review" if require else "approved",
                mode=(self.whatsapp.mode if channel == "whatsapp" else "manual"),
                opener=draft.get("opener", ""),
                trigger=trigger_of(prospect.personalization_notes),
            )
            if item_id:
                drafted += 1
                if channel == "whatsapp" and not is_probably_mobile(target):
                    await self.state.update_channel_item(
                        item_id, error="número parece fixo; confira se tem WhatsApp")
        if drafted:
            logger.info(f"Channels: {drafted} mensagem(ns) aguardando aprovação.")
            await self.state.log_action(
                action_type="channel_drafted", agent="channels",
                details={"drafted": drafted},
            )
        return drafted

    async def _campaign_index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        try:
            for campaign in await self.state.get_campaigns():
                for pid in campaign.prospect_ids:
                    index.setdefault(pid, campaign.id)
        except Exception as e:
            logger.debug(f"Channels: campaign index failed: {e}")
        return index

    async def write(self, channel: str, prospect, company_name: str, mk: str) -> dict | None:
        persona = self.config.persona
        product = self.config.product
        prompt = self.brain.load_prompt(
            "channels",
            channel=channel,
            language=market.language_name(mk),
            persona_name=persona.name,
            persona_company=persona.company,
            product_name=product.name,
            product_description=product.description,
            offer_primary=product.offer.primary or product.pricing,
            first_name=prospect.first_name or "",
            company=company_name or "",
            title=prospect.title or "",
            personalization=prospect.personalization_notes or "",
            trigger=trigger_of(prospect.personalization_notes) or "nenhum",
            best_openers=await best_openers_hint(self.state, channel),
            max_words=WORD_LIMITS[channel],
            note_limit=LINKEDIN_NOTE_LIMIT,
        )
        if not prompt:
            return None
        skills = self.brain.load_skills_for_agent("channels")
        result = await self.brain.think_json(
            prompt + (skills or ""), agent="channels", task=f"draft_{channel}")
        if not isinstance(result, dict):
            return None
        body = clean_message(str(result.get("message", "")))
        note = clean_message(str(result.get("note", "")))[:LINKEDIN_NOTE_LIMIT]
        if len(body.split()) > WORD_LIMITS[channel] * 1.5:
            logger.warning(f"Channels: rascunho de {channel} para {company_name} longo demais.")
            return None
        opener = str(result.get("opener", "")).strip().lower()
        return {"body": body, "note": note if channel == "linkedin" else "",
                "opener": opener if opener in OPENERS else ""}

    async def send_approved_whatsapp(self) -> int:
        """Cloud API mode only: send approved WhatsApp drafts of OPTED-IN
        contacts. Cold numbers are never sent through the API."""
        if not self._enabled("whatsapp") or self.whatsapp.mode != "cloud_api":
            return 0
        if not self.client.is_configured():
            logger.warning("WhatsApp: Cloud API sem token. Configure em .env "
                           "(WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID).")
            return 0
        budget = (self.whatsapp.max_daily_sends
                  - await self.state.count_channel_sent_today("whatsapp"))
        sent = 0
        for item in await self.state.get_channel_items("whatsapp", "approved"):
            if sent >= budget:
                break
            if not item["opted_in"]:
                continue
            if self.whatsapp.template_name:
                ok, message_id, error = await self.client.send_template(
                    item["target"], self.whatsapp.template_name,
                    self.whatsapp.template_language,
                    [item.get("contact_name") or item.get("company_name") or ""],
                )
            else:
                ok, message_id, error = await self.client.send_text(
                    item["target"], item["body"])
            now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            if ok:
                sent += 1
                await self.state.update_channel_item(
                    item["id"], status="sent", sent_at=now, message_id=message_id)
            else:
                await self.state.update_channel_item(
                    item["id"], status="failed", error=error[:300])
        if sent:
            logger.info(f"WhatsApp: {sent} mensagem(ns) enviadas pela Cloud API.")
        return sent

    async def run(self):
        await self.draft_pending()
        await self.send_approved_whatsapp()
