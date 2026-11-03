"""Mariana: dossier from the user's AIs, LinkedIn kit, lead sheet, remake samples."""

import json

import pytest

from harvey import dossie, ficha, linkedin_kit, portfolio, samples
from harvey.models.company import Company
from harvey.models.prospect import Prospect
from tests.test_mariana_closing import FakeBrain, _config, _db


def test_merge_replaces_same_source(tmp_path):
    path = tmp_path / "sobre.md"
    dossie.merge("ChatGPT", "primeira versão", path)
    dossie.merge("Claude", "memória", path)
    dossie.merge("ChatGPT", "segunda versão", path)
    text = path.read_text(encoding="utf-8")
    assert text.count("## Fonte: ChatGPT") == 1
    assert "segunda versão" in text and "primeira versão" not in text
    assert "memória" in text


def test_read_claude_memory_strips_frontmatter(tmp_path):
    (tmp_path / "MEMORY.md").write_text("- [x](x.md)", encoding="utf-8")
    (tmp_path / "x.md").write_text("---\nname: x\ndescription: Filmmaker no Rio\n---\n\nFaz reels.\n", encoding="utf-8")
    (tmp_path / "f.md").write_text("---\nname: f\ndescription: regra\nmetadata:\n  type: feedback\n---\nNunca X.\n", encoding="utf-8")
    text = dossie.read_claude_memory(tmp_path)
    assert "### Filmmaker no Rio" in text and "Faz reels." in text
    assert "Nunca X." not in text
    assert "name: x" not in text


def test_gaps_counts_unknowns():
    assert dossie.gaps("Cidade: NÃO SEI\nIdade: nao sei") == 2


def test_prompt_has_tastes_and_doors():
    text = dossie.prompt_text()
    assert "Gostos" in text and "abrem portas" in text and "—" not in text


@pytest.mark.asyncio
async def test_profile_is_rendered_without_dashes(tmp_path, monkeypatch):
    knowledge = tmp_path / "pk.md"
    knowledge.write_text("Ana, filmmaker de igrejas no Rio.", encoding="utf-8")
    monkeypatch.setattr(linkedin_kit, "KNOWLEDGE_FILE", knowledge)
    monkeypatch.setattr(linkedin_kit, "SOBRE_FILE", tmp_path / "nada.md")
    monkeypatch.setattr(linkedin_kit, "OUT_DIR", tmp_path / "li")
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [])
    brain = FakeBrain(json_result={
        "headlines": [{"pt": "Filmmaker — igrejas", "en": "Filmmaker for churches", "why": "busca"}],
        "about": {"pt": "Sobre PT", "en": "About EN"},
        "experience": [{"title": "Filmmaker", "company": "Lima Filmes", "period": "2020",
                        "location": "Rio", "description": {"pt": "fiz", "en": "did"}}],
        "skills": ["Edição", "DaVinci"], "custom_url": "analima", "missing": ["foto"],
    })
    path = await linkedin_kit.build_profile(brain)
    text = path.read_text(encoding="utf-8")
    assert "Filmmaker , igrejas" in text and "—" not in text
    assert "About EN" in text and "linkedin.com/in/analima" in text and "- foto" in text
    assert json.loads((tmp_path / "li" / "perfil.json").read_text(encoding="utf-8"))["custom_url"] == "analima"


@pytest.mark.asyncio
async def test_profile_needs_material(tmp_path, monkeypatch):
    monkeypatch.setattr(linkedin_kit, "KNOWLEDGE_FILE", tmp_path / "a.md")
    monkeypatch.setattr(linkedin_kit, "SOBRE_FILE", tmp_path / "b.md")
    with pytest.raises(ValueError):
        await linkedin_kit.build_profile(FakeBrain())


async def _linkedin_items(sm, n):
    ids = []
    for i in range(n):
        ids.append(await sm.add_channel_item(
            channel="linkedin", target=f"https://www.linkedin.com/in/p{i}", body=f"Oi {i}",
            prospect_id=f"p{i}", campaign_id=f"c{i}"))
    return ids


@pytest.mark.asyncio
async def test_queue_respects_daily_cap_and_marks_sent(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    await _linkedin_items(sm, 4)
    assert await linkedin_kit.approve_pending(sm) == 4
    monkeypatch.setattr(linkedin_kit.webbrowser, "open", lambda url: None)
    monkeypatch.setattr(linkedin_kit, "copy_to_clipboard", lambda t: True)
    config = _config(channels={"email": {"provider": "smtp"},
                               "linkedin": {"max_daily_messages": 2}})
    answers = iter(["", "p"])
    sent = await linkedin_kit.queue(sm, config, ask=lambda _: next(answers), out=lambda *a: None)
    assert sent == 1
    assert await sm.count_channel_sent_today("linkedin") == 1
    assert len(await sm.get_channel_items("linkedin", "approved")) == 3


@pytest.mark.asyncio
async def test_ficha_writes_sheet_and_feeds_notes(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    cid = await sm.add_company(Company(name="Igreja Vida", domain="vida.org", industry="igreja"))
    pid = await sm.add_prospect(Prospect(company_id=cid, first_name="Bia", last_name="Souza",
                                         title="Pastora", company="Igreja Vida",
                                         personalization_notes="culto jovem às sextas"))
    monkeypatch.setattr(ficha, "OUT_DIR", tmp_path / "fichas")
    monkeypatch.setattr(ficha, "KNOWLEDGE_FILE", tmp_path / "x.md")
    monkeypatch.setattr(ficha, "SOBRE_FILE", tmp_path / "y.md")
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [])
    brain = FakeBrain(json_result={
        "summary": "Igreja com culto jovem forte.",
        "interests": [{"what": "louvor", "evidence": "site, página Ministérios"}],
        "icebreakers": ["Vi o culto jovem de sexta — muito vivo"],
        "works": [{"title": "Reel Conferência", "url": "https://vimeo.com/1", "why": "mesmo público"}],
    })
    path = await ficha.build(sm, brain, pid, crawl=False)
    text = path.read_text(encoding="utf-8")
    assert "louvor" in text and "Reel Conferência" in text and "—" not in text
    notes = (await sm.get_prospect(pid)).personalization_notes
    assert notes.startswith("culto jovem às sextas") and ficha.NOTE_TAG in notes
    await ficha.build(sm, brain, pid, crawl=False)
    assert (await sm.get_prospect(pid)).personalization_notes.count(ficha.NOTE_TAG) == 1


@pytest.mark.asyncio
async def test_remake_brief_and_folder(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    cid = await sm.add_company(Company(name="Studio Fit", domain="fit.com", industry="academia"))
    pid = await sm.add_prospect(Prospect(company_id=cid, first_name="Leo", last_name="Reis",
                                         title="Dono", company="Studio Fit", score=90,
                                         status="contacted"))
    from harvey.signals import seed_signal_catalog
    await seed_signal_catalog(sm)
    await sm.add_observation("INSTAGRAM_PROFILE", company_id=cid, collector="test",
                             value_text="https://instagram.com/studiofit")
    monkeypatch.setattr(samples, "OUT_DIR", tmp_path / "amostras")
    import harvey.production as production
    monkeypatch.setattr(production, "clients_dir", lambda config=None: tmp_path / "clientes")
    path, leads = await samples.write_briefs(sm, top=3, mode="remake", config=_config())
    text = open(path, encoding="utf-8").read()
    assert path.endswith("-remake.md") and "antes e depois" in text and "--modo remake" in text
    folder = tmp_path / "clientes" / "Studio Fit (amostra)"
    assert leads[0]["folder"] == str(folder)
    assert "instagram.com/studiofit" in (folder / "briefing-amostra.md").read_text(encoding="utf-8")
    assert pid


# ── 0.6.0: warm-up, moment, oi video, calendar, score, account care ──

from datetime import date as _date, datetime as _dt0, timedelta as _td, timezone as _tz


class _dt:
    @staticmethod
    def utcnow():
        return _dt0.now(_tz.utc).replace(tzinfo=None)

from harvey import linkedin_growth as growth
from harvey.agents.channels import trigger_of


async def _invite(sm, i=0, **fields):
    iid = await sm.add_channel_item(channel="linkedin", target=f"https://www.linkedin.com/in/p{i}",
                                    body=f"msg {i}", note=f"convite {i}", prospect_id=f"p{i}",
                                    campaign_id=f"c{i}", contact_name=f"P{i}", company_name=f"E{i}")
    if fields:
        await sm.update_channel_item(iid, **fields)
    return iid


def _li_config(**li):
    return _config(channels={"email": {"provider": "smtp"}, "linkedin": li})


@pytest.mark.asyncio
async def test_invite_waits_for_warmup_then_message_after_accept(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    old = (_dt.utcnow() - _td(days=3)).isoformat()
    cold = await _invite(sm, 0, status="approved")
    warm = await _invite(sm, 1, status="approved", warmed_at=old)
    skip = await _invite(sm, 2, status="approved", warmed_at="skip:" + old)
    monkeypatch.setattr(linkedin_kit.webbrowser, "open", lambda url: None)
    monkeypatch.setattr(linkedin_kit, "copy_to_clipboard", lambda t: True)
    cfg = _li_config(warmup_days=2)
    seen = []
    sent = await linkedin_kit.queue(sm, cfg, ask=lambda _: "", out=seen.append)
    assert sent == 2
    assert (await sm.get_channel_item(cold))["status"] == "approved"
    assert (await sm.get_channel_item(warm))["status"] == "sent"
    assert any("esperando o aquecimento" in s for s in seen)
    # accepted → the message goes in the next pass, the invite is not resent
    await sm.update_channel_item(warm, accepted_at=_dt.utcnow().isoformat())
    assert await linkedin_kit.queue(sm, cfg, ask=lambda _: "", out=lambda *a: None) == 1
    assert (await sm.get_channel_item(warm))["msg_sent_at"]
    assert not (await sm.get_channel_item(skip))["msg_sent_at"]


@pytest.mark.asyncio
async def test_weekly_cap_and_stale_invites(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    long_ago = (_dt.utcnow() - _td(days=25)).isoformat()
    for i in range(3):
        await _invite(sm, i, status="sent", sent_at=(_dt.utcnow() - _td(days=2)).isoformat())
    await _invite(sm, 9, status="sent", sent_at=long_ago)
    await _invite(sm, 10, status="approved", warmed_at="skip:x")
    cfg = _li_config(max_weekly_connections=3, withdraw_after_days=21)
    seen = []
    assert await linkedin_kit.queue(sm, cfg, ask=lambda _: "", out=seen.append) == 0
    assert any("retirar" in s for s in seen)
    assert len(await linkedin_kit.stale_invites(sm, cfg.channels.linkedin)) == 1
    monkeypatch.setattr("webbrowser.open", lambda url: None)
    assert await growth.withdraw(sm, cfg, ask=lambda _: "", out=lambda *a: None) == 1
    assert not await linkedin_kit.stale_invites(sm, cfg.channels.linkedin)


@pytest.mark.asyncio
async def test_warmup_writes_comment_and_marks(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    a = await _invite(sm, 0)
    b = await _invite(sm, 1)
    monkeypatch.setattr("webbrowser.open", lambda url: None)
    copied = []
    monkeypatch.setattr(growth, "copy_to_clipboard", copied.append)
    brain = FakeBrain(json_result={"comments": ["Que montagem — linda", "Outra"]})
    answers = iter(["Post sobre o culto de jovens", "1", "", ""])
    n = await growth.warmup(sm, brain, _li_config(), ask=lambda _: next(answers), out=lambda *x: None)
    assert n == 1 and copied == ["Que montagem , linda"]
    assert (await sm.get_channel_item(a))["warmed_at"]
    assert (await sm.get_channel_item(b))["warmed_at"].startswith("skip:")
    assert growth.activity_url("https://www.linkedin.com/in/ana/") == \
        "https://www.linkedin.com/in/ana/recent-activity/all/"


@pytest.mark.asyncio
async def test_moments_put_trigger_in_notes(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    cid = await sm.add_company(Company(name="Igreja Vida", domain="vida.org"))
    pid = await sm.add_prospect(Prospect(company_id=cid, first_name="Bia", last_name="Souza",
                                         title="Pastora", company="Igreja Vida", status="queued",
                                         personalization_notes="culto jovem"))

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"organic": [{"title": "Vaga social media Igreja Vida", "link": "https://x/vaga"}]}

    class FakeClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, *a, **k): return FakeResp()

    monkeypatch.setattr(growth.httpx, "AsyncClient", FakeClient)
    brain = FakeBrain(json_result={"moments": [
        {"type": "hiring", "summary": "Vaga aberta de social media", "url": "https://x/vaga"},
        {"type": "invented", "summary": "nada"}]})
    env = type("E", (), {"serper_api_key": "k"})()
    n = await growth.find_moments(sm, brain, _config(), env, out=lambda *a: None)
    assert n == 1
    notes = (await sm.get_prospect(pid)).personalization_notes
    assert notes.startswith("culto jovem") and trigger_of(notes) == "Vaga aberta de social media"
    rows = await sm.get_observations(company_id=cid, signal_code="HIRING_ROLE")
    assert rows and rows[0]["evidence_url"] == "https://x/vaga"


def test_moment_queries_cover_three_triggers():
    kinds = [k for k, _ in growth.moment_queries("Igreja Vida", "Bia Souza")]
    assert kinds == ["hiring", "event", "new_role"]
    assert [k for k, _ in growth.moment_queries("Igreja Vida", " ")] == ["hiring", "event"]


@pytest.mark.asyncio
async def test_video_brief_and_ready_message(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    cid = await sm.add_company(Company(name="Studio Fit", domain="fit.com"))
    pid = await sm.add_prospect(Prospect(company_id=cid, first_name="Leo", last_name="Reis",
                                         title="Dono", company="Studio Fit"))
    iid = await sm.add_channel_item(channel="linkedin", target="https://www.linkedin.com/in/leo",
                                    body="msg", note="convite", prospect_id=pid, campaign_id="c",
                                    company_name="Studio Fit", contact_name="Leo Reis")
    await sm.update_channel_item(iid, status="sent", accepted_at=_dt.utcnow().isoformat())
    monkeypatch.setattr(growth, "VIDEO_DIR", tmp_path / "videos")
    import harvey.production as production
    monkeypatch.setattr(production, "clients_dir", lambda config=None: tmp_path / "clientes")
    brain = FakeBrain(text="Oi Leo — vi o studio")
    path, done = await growth.video_briefs(sm, brain, _config())
    assert len(done) == 1 and "Oi Leo , vi o studio" in path.read_text(encoding="utf-8")
    assert (tmp_path / "clientes" / "Studio Fit (oi)" / "briefing-oi.md").exists()
    brain.text = "Valeu por conectar, gravei um vídeo pra você"
    await growth.video_ready(sm, brain, pid, "https://vimeo.com/9")
    assert "https://vimeo.com/9" in (await sm.get_channel_item(iid))["body"]


def test_schedule_rotates_three_kinds_mon_wed_fri():
    slots = growth.schedule(2, start=_date(2026, 10, 22))
    assert [d.weekday() for d, _ in slots] == [0, 2, 4, 0, 2, 4]
    assert {k for _, k in slots[:3]} == set(growth.KINDS)
    assert slots[0][0] == _date(2026, 10, 26)


@pytest.mark.asyncio
async def test_calendar_only_uses_permitted_remakes(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    pid = await sm.add_prospect(Prospect(first_name="Leo", last_name="R", title="Dono", company="Fit"))
    await growth.grant_permission(sm, pid, "https://vimeo.com/1")
    monkeypatch.setattr(growth, "OUT_DIR", tmp_path / "li")
    monkeypatch.setattr(growth, "_material", lambda: "")
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [])
    brain = FakeBrain(json_result={"posts": [{"date": "2026-10-26", "kind": "antes_depois",
                                              "piece": "Fit", "text": "Antes — depois", "media": "vídeo"}]})
    path = await growth.build_calendar(sm, brain, weeks=1)
    assert "https://vimeo.com/1" in brain.prompts[-1]
    assert "Antes e depois" in path.read_text(encoding="utf-8") and "—" not in path.read_text(encoding="utf-8")


def test_score_before_and_after(tmp_path, monkeypatch):
    monkeypatch.setattr(growth, "SCORES_FILE", tmp_path / "notas.json")
    weak = growth.score({"headline": "Gabriel", "about": "", "has_photo": True})
    strong = growth.score({
        "headline": "Filmmaker e editor de vídeo para igrejas e eventos | Reels, cultos e conferências",
        "about": "Filmmaker: edição de vídeo e filmagem " * 50 + " 120 projetos. Fale comigo pelo email.",
        "has_photo": True, "has_banner": True, "featured_count": 4,
        "experience": [{"has_description": True}] * 3, "skills_count": 15,
        "custom_url": "gabrielxreis", "services": ["Filmagem"], "recommendations_count": 3,
    }, audience=["Igrejas"])
    assert strong["total"] == 100 and weak["total"] < 30
    assert growth.score({"custom_url": "joao-silva-3a9b2c1d"})["parts"]["url"] == 0
    growth.save_score("perfil atual", weak)
    text = growth.report(growth.save_score("proposta", strong))
    assert "Antes:" in text and "100" in text


@pytest.mark.asyncio
async def test_openers_metrics(tmp_path):
    from harvey.metrics import openers
    sm = await _db(tmp_path)
    pid = await sm.add_prospect(Prospect(first_name="A", last_name="B", title="C", company="D",
                                         status="replied"))
    a = await sm.add_channel_item(channel="linkedin", target="u", body="x", note="n",
                                  prospect_id=pid, campaign_id="c1", opener="gatilho")
    await sm.update_channel_item(a, status="sent", accepted_at="2026-10-01")
    rows = await openers(sm)
    assert rows[0]["opener"] == "gatilho" and rows[0]["accept_rate"] == 100.0
    assert rows[0]["reply_rate"] == 100.0
