"""Mariana closing features: replies off-email, calendar, portfolio, proposal,
post-job, events, samples, notify and metrics."""

from datetime import date, datetime, timedelta

import pytest
import pytz

from harvey import portfolio
from harvey.config import EnvConfig, MarianaConfig
from harvey.integrations.calendar import format_slots, free_slots
from harvey.models.company import Company
from harvey.models.prospect import Prospect
from harvey.state import StateManager


class FakeBrain:
    """Stands in for the model: labels for classification, text otherwise."""

    def __init__(self, label="interested", text="Oi Bia, que bom. Podemos falar terça?",
                 json_result=None):
        self.label, self.text, self.json_result = label, text, json_result
        self.prompts = []
        self.paused_reason = ""

    def load_prompt(self, name, **kw):
        return ""

    def load_skills_for_agent(self, name):
        return ""

    async def think(self, prompt, **kw):
        self.prompts.append(prompt)
        return self.label if kw.get("task") == "classify_intent" or "Classify" in prompt[:400] \
            else self.text

    async def think_json(self, prompt, **kw):
        self.prompts.append(prompt)
        return self.json_result


def _config(**extra) -> MarianaConfig:
    data = dict(
        persona={"name": "Ana Lima", "company": "Lima Filmes", "role": "Filmmaker",
                 "email": "ana@limafilmes.com.br", "linkedin": "", "tone": "direto"},
        product={"name": "Lima Filmes", "description": "Filmagem", "pricing": "",
                 "key_benefits": [], "objection_responses": {}},
        icp={"industries": ["Igrejas"], "company_size": "", "titles": [],
             "geography": ["Rio de Janeiro, RJ"]},
        channels={"email": {"provider": "smtp"}},
        notify={"enabled": False},
    )
    data.update(extra)
    return MarianaConfig(**data)


async def _db(tmp_path):
    sm = StateManager(str(tmp_path / "t.db"))
    await sm.init_db()
    return sm


# ── calendar ──

def test_free_slots_skip_busy_and_spread_days():
    tz = pytz.timezone("America/Sao_Paulo")
    start = tz.localize(datetime(2026, 10, 19, 8, 0))  # Monday 08:00
    busy = [(tz.localize(datetime(2026, 10, 20, 9, 0)), tz.localize(datetime(2026, 10, 20, 18, 0)))]
    slots = free_slots(busy, start=start, days=7, tzinfo=tz, working_hours="09:00-18:00",
                       working_days=[0, 1, 2, 3, 4], minutes=30, min_notice_hours=20, limit=3)
    assert len(slots) == 3
    assert all(s.date() != date(2026, 10, 20) for s in slots)  # Tuesday fully busy
    assert len({s.date() for s in slots}) == 3                  # one per day
    assert all(s >= start + timedelta(hours=20) for s in slots)


def test_format_slots_pt_and_en():
    tz = pytz.timezone("America/Sao_Paulo")
    s = [tz.localize(datetime(2026, 10, 21, 10, 0)), tz.localize(datetime(2026, 10, 22, 15, 30))]
    pt = format_slots(s, "pt-BR")
    assert pt == "quarta (21/10) às 10h ou quinta (22/10) às 15h30"
    assert "Wednesday" in format_slots(s, "en")


# ── portfolio ──

ITEMS = [
    {"title": "Conferência Luz", "url": "https://v.com/1", "segment": "igreja"},
    {"title": "Final do campeonato", "url": "https://v.com/2", "segment": "esporte"},
    {"title": "Showreel", "url": "https://v.com/3", "segment": "geral"},
]


def test_segment_of_and_match():
    assert portfolio.segment_of("Igreja Batista da Lagoinha") == "igreja"
    assert portfolio.segment_of("Baltimore Ravens", "NFL team") == "esporte"
    assert [i["url"] for i in portfolio.match("church", items=ITEMS)] == \
        ["https://v.com/1", "https://v.com/3"]
    assert portfolio.match("loja de roupas", items=ITEMS)[0]["url"] == "https://v.com/3"


# ── replies outside email ──

@pytest.mark.asyncio
async def test_whatsapp_reply_stops_email_and_drafts_answer(tmp_path):
    from harvey.agents.handler import Handler

    sm = await _db(tmp_path)
    co = await sm.add_company(Company(name="Igreja Luz", phone="(21) 99999-1111"))
    pid = await sm.add_prospect(Prospect(first_name="Bia", last_name="Souza", title="Pastora",
                                         email="bia@luz.org.br", company_id=co,
                                         company="Igreja Luz", status="contacted"))
    prospect = await sm.get_prospect(pid)
    await sm.add_outbox_item(prospect_id=pid, to_email=prospect.email, subject="s",
                             body="follow-up", send_at="2026-01-01", campaign_id="c1", step=2)
    first = await sm.add_channel_item(channel="whatsapp", target="5521999991111", body="oi",
                                      prospect_id=pid, campaign_id="c1", status="sent")
    assert first

    handler = Handler(FakeBrain(), sm, _config(), EnvConfig())
    convo_id = await handler.handle_external_reply(prospect, "Oi! Quanto custa?", "whatsapp")

    assert convo_id
    pending_email = await sm.get_outbox(status="pending_review")
    assert pending_email == []                                  # follow-up cancelled
    replies = [i for i in await sm.get_channel_items("whatsapp") if i["kind"] == "reply"]
    assert len(replies) == 1
    assert replies[0]["target"] == "5521999991111"
    assert replies[0]["opted_in"] is True
    assert (await sm.get_prospect(pid)).status == "replied"
    convo = await sm.get_conversation(convo_id)
    assert convo.channel == "whatsapp"


# ── proposal ──

@pytest.mark.asyncio
async def test_build_proposal_uses_catalog_and_creates_job(tmp_path, monkeypatch):
    from harvey import proposal
    from harvey.models.conversation import Conversation, Message

    sm = await _db(tmp_path)
    pid = await sm.add_prospect(Prospect(first_name="Bia", last_name="Souza", title="Pastora",
                                         email="bia@luz.org.br", company="Igreja Luz"))
    convo = Conversation(id="", prospect_id=pid, channel="email", status="open")
    convo.thread.append(Message(sender="prospect", content="Queremos o aftermovie da conferência dia 12/11"))
    cid = await sm.add_conversation(convo)

    monkeypatch.setattr(proposal, "OUT_DIR", tmp_path / "propostas")
    monkeypatch.setattr(proposal, "load_profile", lambda: {
        "person": {"name": "Ana Lima", "role": "Filmmaker", "email": "ana@x.com"},
        "offer": {"services": [{"name": "Aftermovie", "starting_price": "R$ 2.500"}],
                  "portfolio_items": ITEMS},
    })

    async def no_pdf(path):
        return None
    monkeypatch.setattr(proposal, "to_pdf", no_pdf)
    brain = FakeBrain(json_result={
        "project": "Aftermovie da Conferência Luz", "date": "2026-11-12", "segment": "igreja",
        "intro": "Obrigada pela conversa.", "items": [
            {"service": "Aftermovie", "details": "3 min + 3 Reels", "price": "R$ 2.500"}],
        "next_steps": ["Confirmar a data"]})
    result = await proposal.build_proposal(sm, brain, _config(), cid)

    page = open(result["html"], encoding="utf-8").read()
    assert "Aftermovie da Conferência Luz" in page and "R$ 2.500" in page
    assert "https://v.com/1" in page            # church piece for a church
    job = await sm.get_job(result["job_id"])
    assert job["status"] == "proposal" and job["event_date"] == "2026-11-12"


# ── post-job ──

def test_postjob_due_moments():
    from harvey.agents.postjob import PostJobAgent

    agent = PostJobAgent(None, None, _config())
    today = date(2026, 10, 20)
    assert agent.due({"status": "delivered", "delivered_at": "2026-10-15"}, today) == "testimonial"
    assert agent.due({"status": "delivered", "delivered_at": "2026-10-19"}, today) == ""
    assert agent.due({"status": "delivered", "delivered_at": "2026-10-01",
                      "testimonial_requested_at": "2026-10-05",
                      "next_event_date": "2026-11-20"}, today) == "reengage"
    assert agent.due({"status": "won", "next_event_date": "2027-03-01"}, today) == ""


@pytest.mark.asyncio
async def test_postjob_drafts_whatsapp_for_brazil(tmp_path):
    from harvey.agents.postjob import PostJobAgent

    sm = await _db(tmp_path)
    co = await sm.add_company(Company(name="Igreja Luz", phone="(21) 99999-1111"))
    pid = await sm.add_prospect(Prospect(first_name="Bia", last_name="Souza", title="Pastora",
                                         company_id=co, phone="(21) 99999-1111"))
    job = await sm.add_job(prospect_id=pid, status="delivered",
                           delivered_at=(date.today() - timedelta(days=5)).isoformat(),
                           company_name="Igreja Luz", contact_name="Bia Souza")
    n = await PostJobAgent(FakeBrain(text="Oi Bia, obrigada pelo projeto."), sm, _config()).run()
    assert n == 1
    items = await sm.get_channel_items("whatsapp")
    assert items[0]["kind"] == "postjob" and items[0]["target"] == "5521999991111"
    assert (await sm.get_job(job))["testimonial_requested_at"]


# ── events ──

def test_event_queries_cover_months_and_language():
    from harvey.collectors.events import build_queries

    qs = build_queries(["Igrejas"], [("Rio de Janeiro, RJ", "pt-BR"), ("Austin, TX", "en")],
                       months=2, today=date(2026, 10, 16))
    assert any("conferência igreja Rio de Janeiro, RJ outubro 2026" in q for q in qs)
    assert any("novembro 2026" in q for q in qs)
    assert any("church conference Austin, TX October 2026" in q and "eventbrite.com" in q for q in qs)


# ── notify ──

@pytest.mark.asyncio
async def test_notify_disabled_is_silent():
    from harvey.notify import notify_reply
    await notify_reply(_config(), EnvConfig(), "interested", "Bia", "whatsapp", "oi")


# ── metrics ──

@pytest.mark.asyncio
async def test_metrics_by_channel_and_market(tmp_path):
    from harvey.metrics import compute

    sm = await _db(tmp_path)
    br = await sm.add_company(Company(name="Igreja Luz", domain="luz.org.br"))
    us = await sm.add_company(Company(name="Grace Church", domain="grace.org", location="Austin, TX"))
    p1 = await sm.add_prospect(Prospect(first_name="A", last_name="B", title="Pastor",
                                        email="a@luz.org.br", company_id=br, status="replied"))
    p2 = await sm.add_prospect(Prospect(first_name="C", last_name="D", title="Pastor",
                                        email="c@grace.org", company_id=us, status="contacted"))
    i1 = await sm.add_outbox_item(prospect_id=p1, to_email="a@luz.org.br", subject="s", body="b",
                                  send_at="2026-01-01", campaign_id="c", step=1)
    i2 = await sm.add_outbox_item(prospect_id=p2, to_email="c@grace.org", subject="s", body="b",
                                  send_at="2026-01-01", campaign_id="c", step=1)
    for i in (i1, i2):
        await sm.update_outbox_item(i, status="sent")
    w = await sm.add_channel_item(channel="whatsapp", target="55", body="b", prospect_id=p1,
                                  campaign_id="c")
    await sm.update_channel_item(w, status="sent")

    m = await compute(sm)
    assert m["total"] == {"contacted": 2, "replied": 1, "won": 0, "reply_rate": 50.0, "win_rate": 0.0}
    by_market = {r["key"]: r for r in m["by_market"]}
    assert by_market["Brasil"]["reply_rate"] == 100.0 and by_market["EUA"]["replied"] == 0
    assert {r["key"] for r in m["by_channel"]} == {"email", "whatsapp"}
