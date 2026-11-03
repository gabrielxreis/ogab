"""Instagram kit: profile with diagnosis, score, posts queue and calendar."""

import json
from datetime import date

import pytest

from harvey import instagram_kit as ig
from harvey import portfolio
from tests.test_mariana_closing import FakeBrain


@pytest.fixture
def out(tmp_path, monkeypatch):
    knowledge = tmp_path / "pk.md"
    knowledge.write_text("Ana Lima, filmmaker de igrejas no Rio.", encoding="utf-8")
    monkeypatch.setattr(ig, "KNOWLEDGE_FILE", knowledge)
    monkeypatch.setattr(ig, "SOBRE_FILE", tmp_path / "nada.md")
    monkeypatch.setattr(ig, "OUT_DIR", tmp_path / "ig")
    monkeypatch.setattr(ig, "CURRENT_FILE", tmp_path / "ig" / "perfil-atual.txt")
    monkeypatch.setattr(ig, "SCORES_FILE", tmp_path / "ig" / "notas.json")
    monkeypatch.setattr(ig, "QUEUE_FILE", tmp_path / "ig" / "fila.json")
    return tmp_path / "ig"


@pytest.mark.asyncio
async def test_profile_has_every_field_and_no_dash(out, monkeypatch):
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [])
    brain = FakeBrain(json_result={
        "diagnosis": [{"item": "Bio", "status": "ajustar", "now": "só emojis", "fix": "serviço e público"}],
        "usernames": [{"handle": "@analimafilms", "why": "curto"}],
        "names": [{"pt": "Ana Lima — Filmmaker de Igrejas", "en": "Ana Lima | Church Filmmaker", "why": "busca"}],
        "category": "Videógrafo",
        "bios": [{"pt": "Filmo cultos e eventos de igrejas no Rio", "en": "Church films", "why": "clara"}],
        "link_in_bio": {"title": "Ana Lima", "buttons": [{"label": "WhatsApp", "url": "wa.me/55", "why": "fecha"}]},
        "contact_buttons": ["WhatsApp"],
        "highlights": [{"name": "Igrejas", "content": ["cultos"], "cover_brief": "ícone de câmera"}],
        "pinned": [{"piece": "Culto de Páscoa", "format": "reels", "cover_text": "Páscoa", "why": "case"}],
        "photo_tips": "rosto no centro", "grid": "capas pretas", "missing": ["showreel"],
    })
    path = await ig.build_profile(brain, current="@ana 🎥🎬")
    text = path.read_text(encoding="utf-8")
    assert "—" not in text and "Ana Lima , Filmmaker" in text
    assert "Diagnóstico" in text and "@analimafilms" in text and "Videógrafo" in text
    assert "WhatsApp" in text and "### Igrejas" in text and "Culto de Páscoa" in text
    assert "- showreel" in text
    assert "@ana" in brain.prompts[-1]


@pytest.mark.asyncio
async def test_profile_needs_material(out, monkeypatch):
    monkeypatch.setattr(ig, "KNOWLEDGE_FILE", out / "x.md")
    with pytest.raises(ValueError):
        await ig.build_profile(FakeBrain())


def test_score_before_and_after():
    weak = ig.score({"name": "Ana", "bio": "🎥", "has_photo": True})
    strong = ig.score({"name": "Ana Lima | Filmmaker de Igrejas",
                       "bio": "Filmmaker de igrejas no Rio de Janeiro. 120 cultos e conferências filmados. Orçamento no link abaixo",
                       "has_photo": True, "link": "x", "category": "Videógrafo", "has_contact": True,
                       "highlights_count": 6, "pinned_count": 3, "posts_last_30": 9},
                      audience=["igrejas evangélicas"])
    assert strong["total"] == 100
    assert weak["total"] < 30
    assert sum(ig.MAX_PARTS.values()) == 100


def test_report_shows_gain(out):
    ig.save_score("perfil atual", ig.score({"name": "Ana", "has_photo": True}))
    history = ig.save_score("proposta do Gab", ig.score({"name": "Ana filmmaker", "has_photo": True,
                                                         "link": "x", "highlights_count": 5}))
    text = ig.report(history)
    assert "Antes:" in text and "Para subir:" in text


@pytest.mark.asyncio
async def test_posts_fill_the_queue_and_walk(out, monkeypatch):
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [{"title": "Páscoa", "url": "http://v"}])
    brain = FakeBrain(json_result={"posts": [
        {"piece": "Páscoa", "format": "reels", "hook": "3 câmeras", "cover_text": "Páscoa",
         "beats": ["abertura", "coral"], "pt": "Legenda PT", "en": "Caption EN", "hashtags": ["igreja"]},
        {"piece": "Natal", "format": "carrossel", "pt": "Natal PT", "hashtags": []}]})
    path = await ig.build_posts(brain)
    assert "Para o Gab montar" in path.read_text(encoding="utf-8")
    await ig.build_posts(brain)
    assert len(ig.load_queue()) == 2
    monkeypatch.setattr(ig.webbrowser, "open", lambda url: None)
    copied = []
    monkeypatch.setattr(ig, "copy_to_clipboard", lambda t: copied.append(t) or True)
    assert ig.queue(ask=lambda _: "", out=lambda *a: None, per_day=1) == 1
    assert "#igreja" in copied[0]
    queue = ig.load_queue()
    assert queue[0]["status"] == "publicado" and queue[0]["posted_at"] == date.today().isoformat()
    assert ig.queue(ask=lambda _: "", out=lambda *a: None, per_day=1) == 0


def test_schedule_tue_thu_sat():
    slots = ig.schedule(2, start=date(2026, 11, 3))
    assert [d.weekday() for d, _ in slots[:3]] == [1, 3, 5]
    assert len(slots) == 6 and {k for _, k in slots} == set(ig.KINDS)


def test_proposal_profile_scores(out):
    d = {"names": [{"pt": "Ana | Filmmaker"}], "bios": [{"pt": "Filmmaker. 50 eventos. Link"}],
         "link_in_bio": {"buttons": [{"label": "WhatsApp"}]}, "category": "Videógrafo",
         "contact_buttons": ["WhatsApp"], "highlights": [{}] * 5, "pinned": [{}] * 3}
    profile = ig.profile_from_proposal(d, has_photo=True)
    assert ig.score(profile)["total"] >= 70
    json.dumps(profile)
