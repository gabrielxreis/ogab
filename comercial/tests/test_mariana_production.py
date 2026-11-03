"""Mariana: price history, proposal follow-up, /ogab client folder, reminders."""

from datetime import date, timedelta

import pytest

from harvey import pricing
from harvey.models.conversation import Conversation, Message
from harvey.models.prospect import Prospect
from harvey.state import StateManager
from tests.test_mariana_closing import FakeBrain, _config


# ── pricing ──

@pytest.mark.parametrize("text,expected", [
    ("R$ 2.500", (2500.0, "R$")),
    ("R$ 2.500,00", (2500.0, "R$")),
    ("$1,200", (1200.0, "$")),
    ("US$ 900", (900.0, "US$")),
    ("3 mil", (3000.0, "R$")),
    ("a combinar", None),
])
def test_parse_value(text, expected):
    assert pricing.parse_value(text) == expected


def test_history_by_segment_and_service():
    jobs = [
        {"status": "won", "segment": "igreja", "service": "Aftermovie conferência", "value": "R$ 2.500"},
        {"status": "delivered", "segment": "igreja", "service": "Aftermovie", "value": "R$ 4.000"},
        {"status": "won", "segment": "marca", "service": "Anúncio", "value": "R$ 6.000"},
        {"status": "proposal", "segment": "igreja", "service": "Aftermovie", "value": "R$ 9.999"},
    ]
    h = pricing.history(jobs, "igreja", "Aftermovie do congresso")
    assert h["count"] == 2 and h["min"] == 2500 and h["max"] == 4000
    assert "R$ 2.500 e R$ 4.000" in h["text"]
    assert pricing.history(jobs, "casamento", "Highlight") is None


# ── proposal follow-up ──

def test_followup_due_rules():
    from harvey.agents.postjob import PostJobAgent

    agent = PostJobAgent(None, None, _config())
    today = date(2026, 10, 20)
    base = {"status": "proposal", "proposal_sent_at": "2026-10-16", "followups": 0}
    assert agent.followup_due(base, today, None)                       # 4 days, no answer
    assert not agent.followup_due({**base, "proposal_sent_at": "2026-10-19"}, today, None)
    assert not agent.followup_due(base, today, date(2026, 10, 18))     # they answered
    second = {**base, "followups": 1, "last_followup_at": "2026-10-17"}
    assert not agent.followup_due(second, today, None)                 # 2nd waits 5 days
    assert agent.followup_due(second, date(2026, 10, 22), None)
    assert not agent.followup_due({**base, "followups": 2}, today, None)  # max 2


@pytest.mark.asyncio
async def test_followup_and_shoot_reminder_drafts(tmp_path, monkeypatch):
    from harvey.agents import postjob as pj
    import harvey.notify as notify_mod

    sent = []

    async def fake_notify(config, env, title, message, click=""):
        sent.append(title)
    monkeypatch.setattr(notify_mod, "notify", fake_notify)

    sm = StateManager(str(tmp_path / "t.db"))
    await sm.init_db()
    pid = await sm.add_prospect(Prospect(first_name="Bia", last_name="Souza", title="Pastora",
                                         email="bia@luz.org.br", company="Igreja Luz"))
    today = date.today()
    await sm.add_job(prospect_id=pid, status="proposal", company_name="Igreja Luz",
                     proposal_sent_at=(today - timedelta(days=4)).isoformat())
    shoot = await sm.add_job(prospect_id=pid, status="won", company_name="Igreja Luz",
                             shoot_date=(today + timedelta(days=1)).isoformat(),
                             shoot_time="09:00", address="Rua A, 10", checklist="drone\nlapela")
    n = await pj.PostJobAgent(FakeBrain(text="Oi Bia, conseguiu ver a proposta?"), sm,
                              _config()).production_tick(today)
    assert n == 2
    kinds = sorted(i["kind"] for i in await sm.get_outbox(status="pending_review"))
    assert kinds == ["proposal_followup", "reminder"]
    assert sent == ["Amanhã: Igreja Luz"]
    assert (await sm.get_job(shoot))["reminder_sent_at"] == today.isoformat()
    # nothing repeats on the next tick
    assert await pj.PostJobAgent(FakeBrain(), sm, _config()).production_tick(today) == 0


# ── /ogab client folder ──

@pytest.mark.asyncio
async def test_job_won_creates_ogab_folder(tmp_path, monkeypatch):
    from harvey import production

    monkeypatch.setattr(production, "clients_dir", lambda config=None: tmp_path / "BRAIN")
    sm = StateManager(str(tmp_path / "t.db"))
    await sm.init_db()
    pid = await sm.add_prospect(Prospect(first_name="Bia", last_name="Souza", title="Pastora",
                                         email="bia@luz.org.br", company="Igreja São João!"))
    convo = Conversation(id="", prospect_id=pid, channel="whatsapp", status="closed")
    convo.thread.append(Message(sender="prospect", content="Fechado! Gravação dia 12/11 às 19h na sede."))
    cid = await sm.add_conversation(convo)
    job = await sm.add_job(prospect_id=pid, conversation_id=cid, status="won",
                           company_name="Igreja São João!", contact_name="Bia Souza",
                           service="Aftermovie", value="R$ 3.000")
    brain = FakeBrain(json_result={"shoot_date": "2026-11-12", "shoot_time": "19:00",
                                   "address": "Sede", "revisions_included": 3,
                                   "checklist": ["abertura com a fachada", "lapela no pastor"],
                                   "client_requests": ["sem música eletrônica"]})
    out = await production.on_job_won(sm, brain, _config(), job)

    folder = tmp_path / "BRAIN" / "Igreja Sao Joao"
    memory = (folder / "Igreja Sao Joao.md").read_text(encoding="utf-8")
    assert "## Pedidos diferentes do usuário" in memory and "job fechado pela Mariana" in memory
    briefing = open(out["briefing"], encoding="utf-8").read()
    assert "2026-11-12" in briefing and "sem música eletrônica" in briefing
    assert "- [ ] lapela no pastor" in briefing
    saved = await sm.get_job(job)
    assert saved["revisions_included"] == 3 and saved["project_dir"] == str(folder)

    # a second job for the same client keeps the memory and adds a line
    await production.on_job_won(sm, brain, _config(), job)
    assert (folder / "Igreja Sao Joao.md").read_text(encoding="utf-8").count("job fechado pela Mariana") == 2


def test_clients_dir_reads_ogab_config(tmp_path, monkeypatch):
    from harvey import production

    cfg = tmp_path / "config.json"
    cfg.write_text('{"pasta_saida": "~/Documents/CLAUDE BRAIN"}', encoding="utf-8")
    monkeypatch.setattr(production, "OGAB_CONFIG", cfg)
    assert production.clients_dir().parts[-2:] == ("Documents", "CLAUDE BRAIN")
    monkeypatch.setattr(production, "OGAB_CONFIG", tmp_path / "missing.json")
    assert production.clients_dir() == production.DEFAULT_CLIENTS_DIR
