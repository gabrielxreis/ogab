"""Mariana additions: signature, market, phones, channel outbox, onboarding."""

import pytest

from harvey import market
from harvey.config import MarianaConfig
from harvey.integrations.whatsapp import is_probably_mobile, normalize_phone, wa_link
from harvey.models.company import Company
from harvey.models.prospect import Prospect
from harvey.onboard import Onboarding, build_config, render_knowledge
from harvey.signature import compose, render_html, render_text
from harvey.state import StateManager


def _config(**persona_extra) -> MarianaConfig:
    persona = {
        "name": "Ana Lima", "company": "Lima Filmes", "role": "Filmmaker",
        "email": "ana@limafilmes.com.br", "linkedin": "", "tone": "direto",
        "signature": {"whatsapp": "+55 (21) 99999-8888", "website": "limafilmes.com.br",
                      "instagram": "@limafilmes", "portfolio": "vimeo.com/limafilmes"},
    }
    persona.update(persona_extra)
    return MarianaConfig(
        persona=persona,
        product={"name": "Lima Filmes", "description": "Filmagem", "pricing": "",
                 "key_benefits": [], "objection_responses": {}},
        icp={"industries": ["Igrejas"], "company_size": "", "titles": [],
             "geography": []},
    )


# ── signature ──

def test_signature_text_has_links_and_whatsapp():
    text = render_text(_config())
    assert "Ana Lima" in text
    assert "limafilmes.com.br" in text
    assert "instagram.com/limafilmes" in text
    assert "WhatsApp: +5521999998888" in text


def test_compose_appends_delimiter_and_html():
    text, html = compose(_config(), "Oi Bia,\n\nTudo certo?")
    assert text.startswith("Oi Bia,")
    assert "\n-- \nAna Lima" in text
    assert html and "wa.me/5521999998888" in html and "<p" in html


def test_compose_disabled_returns_body_untouched():
    cfg = _config(signature={"enabled": False})
    assert compose(cfg, "corpo") == ("corpo", None)


def test_signature_html_escapes():
    cfg = _config(name="Ana <script>")
    assert "<script>" not in render_html(cfg)


# ── market ──

@pytest.mark.parametrize("phone,domain,location,expected", [
    ("+55 21 99999-8888", "", "", market.BR),
    ("+1 512 555 0100", "", "", market.INTL),
    ("(21) 99999-8888", "", "", market.BR),          # local number, pt default
    ("", "igreja.org.br", "", market.BR),
    ("", "church.org", "Austin, TX", market.INTL),
    ("", "", "Niterói, RJ", market.BR),
])
def test_market_detect(phone, domain, location, expected):
    assert market.detect(phone, domain, location, "pt-BR") == expected


def test_market_default_follows_language():
    assert market.detect(default_language="en") == market.INTL
    assert market.language(market.BR) == "pt-BR"


# ── phones ──

@pytest.mark.parametrize("raw,expected", [
    ("(21) 99999-8888", "5521999998888"),
    ("+55 21 99999-8888", "5521999998888"),
    ("021 99999-8888", "5521999998888"),
    ("5521999998888", "5521999998888"),
    ("(55) 99999-8888", "5555999998888"),   # DDD 55 (RS) without country code
    ("123", ""),
])
def test_normalize_phone_br(raw, expected):
    assert normalize_phone(raw, "55") == expected


def test_normalize_phone_us():
    assert normalize_phone("(512) 555-0100", "1") == "15125550100"


def test_mobile_heuristic_and_link():
    assert is_probably_mobile("5521999998888")
    assert not is_probably_mobile("552133334444")
    assert wa_link("5521999998888", "oi tudo bem?") == \
        "https://wa.me/5521999998888?text=oi%20tudo%20bem%3F"


# ── channel outbox ──

@pytest.mark.asyncio
async def test_channel_outbox_roundtrip(tmp_path):
    sm = StateManager(str(tmp_path / "t.db"))
    await sm.init_db()
    item = await sm.add_channel_item(channel="whatsapp", target="5521999998888",
                                     body="oi", prospect_id="p1", campaign_id="c1")
    assert item
    # double-draft guard
    assert await sm.add_channel_item(channel="whatsapp", target="x", body="y",
                                     prospect_id="p1", campaign_id="c1") is None
    # another channel for the same prospect is allowed
    assert await sm.add_channel_item(channel="linkedin", target="https://li", body="hi",
                                     prospect_id="p1", campaign_id="c1")
    assert await sm.channel_drafted("whatsapp") == {"p1"}
    await sm.update_channel_item(item, opted_in=True, status="approved")
    got = await sm.get_channel_item(item)
    assert got["opted_in"] is True and got["status"] == "approved"
    assert await sm.cancel_pending_channels_for_prospect("p1") == 2


@pytest.mark.asyncio
async def test_channels_agent_picks_by_market(tmp_path):
    from harvey.agents.channels import ChannelsAgent

    sm = StateManager(str(tmp_path / "t.db"))
    await sm.init_db()
    br_co = await sm.add_company(Company(name="Igreja Luz", domain="igrejaluz.com.br",
                                         phone="(21) 99999-1111"))
    us_co = await sm.add_company(Company(name="Grace Church", domain="grace.org",
                                         location="Austin, TX", phone="+1 512 555 0100"))
    cfg = _config()
    agent = ChannelsAgent(brain=None, state=sm, config=cfg)

    br = Prospect(first_name="Bia", last_name="Souza", title="Pastora", company_id=br_co)
    us = Prospect(first_name="John", last_name="Doe", title="Pastor", company_id=us_co,
                  linkedin_url="https://linkedin.com/in/johndoe")
    assert (await agent.choose(br))[:2] == ("whatsapp", "5521999991111")
    assert (await agent.choose(us))[:2] == ("linkedin", "https://linkedin.com/in/johndoe")

    # Abroad with no LinkedIn and no Instagram: no manual channel (email only)
    nobody = Prospect(first_name="Jo", last_name="Roe", title="Owner", company_id=us_co)
    assert await agent.choose(nobody) is None


# ── onboarding ──

PROFILE = {
    "person": {"name": "Ana Lima", "company": "Lima Filmes", "role": "Filmmaker",
               "email": "ana@limafilmes.com.br", "whatsapp": "5521999998888",
               "portfolio": "https://vimeo.com/lima", "bio": "Filmo eventos no Rio.",
               "country": "Brasil"},
    "offer": {"services": [{"name": "Aftermovie", "description": "evento",
                            "starting_price": "R$ 2.500"}],
              "past_clients": ["Igreja Luz"]},
    "targets": {"industries": ["Igrejas"], "titles": ["Pastor"],
                "markets": [{"place": "Rio de Janeiro, RJ", "lat": -22.9, "lng": -43.2,
                             "radius_km": 40, "language": "pt-BR"}],
                "avoid": ["política"]},
    "voice": {"tone": "leve"},
    "goals": {"main_offer": "aftermovie do próximo evento"},
    "timezone": "America/Sao_Paulo",
}


def test_build_config_validates_and_keeps_operational_settings():
    existing = {"channels": {"email": {"provider": "gmail"}}, "brain": {"provider": "claude"}}
    cfg_dict = build_config(PROFILE, existing)
    cfg = MarianaConfig(**cfg_dict)
    assert cfg.persona.name == "Ana Lima"
    assert cfg.persona.signature.whatsapp == "5521999998888"
    assert cfg.icp.geo_coordinates["Rio de Janeiro, RJ"] == "-22.9,-43.2,40"
    assert cfg.channels.email.provider == "gmail"
    assert cfg.usage.quiet_hours.timezone == "America/Sao_Paulo"
    assert "R$ 2.500" in cfg.product.pricing


def test_knowledge_lists_only_given_facts():
    md = render_knowledge(PROFILE)
    assert "Aftermovie" in md and "R$ 2.500" in md
    assert "Igreja Luz" in md and "política" in md


def test_pending_questions_skip_answered():
    extracted = {"profile": PROFILE, "questions": [{"key": "x", "question": "Algo mais?"}]}
    keys = [k for k, _ in Onboarding.pending_questions(extracted)]
    assert "person.name" not in keys and "x" in keys
    assert "offer.packages" not in keys


# ── idioma pelo país da empresa ──

@pytest.mark.parametrize("phone,domain,location,country,lang", [
    ("+52 55 1234 5678", "", "", "MX", "es"),
    ("+34 911 234 567", "", "", "ES", "es"),
    ("+33 1 23 45 67 89", "", "", "FR", "fr"),
    ("+1 512 555 0100", "", "", "US", "en"),
    ("+351 21 123 4567", "", "", "PT", "pt-PT"),
    ("+598 2 123 4567", "", "", "UY", "es"),
    ("", "iglesia.com.mx", "", "MX", "es"),
    ("", "eglise.fr", "", "FR", "fr"),
    ("", "studio.co.uk", "", "GB", "en"),
    ("", "", "Buenos Aires", "AR", "es"),
    ("", "", "Austin, TX", "US", "en"),
    ("", "", "Niterói, RJ", "BR", "pt-BR"),
    ("(21) 99999-8888", "", "", "BR", "pt-BR"),
])
def test_language_follows_company_country(phone, domain, location, country, lang):
    mk = market.detect(phone, domain, location, "pt-BR")
    assert mk.country == country
    assert market.language(mk) == lang
    assert (mk == market.BR) == (country == "BR")   # channel rule unchanged


def test_language_names_and_pick():
    mx = market.detect("+52 55 1234 5678")
    assert "Spanish" in market.language_name(mx) and "México" in market.language_name(mx)
    assert market.language_name(market.detect(location="London")) == "British English"
    assert market.pick(mx, pt="oi", es="hola", en="hi") == "hola"
    assert market.pick("fr", pt="oi", en="hi") == "hi"          # falls back to English
    assert market.pick(market.BR, pt="oi", en="hi") == "oi"


def test_writer_batches_never_mix_languages():
    from harvey.agents.writer import Writer
    w = Writer.__new__(Writer)
    w.config = _config()
    w._markets = {"a": market.detect("+52 55 1"), "b": market.detect("+1 512 5"),
                  "c": market.detect("+55 21 99999 8888")}
    w.config.channels.email.provider = "smtp"
    groups = w._group_prospects([Prospect(id=i, industry="Igrejas") for i in "abc"])
    assert len(groups) == 3
    assert any(k.startswith("es-") for k in groups) and any(k.startswith("en-") for k in groups)
