"""Dashboard API for the signal-confirmation gate, cohorts, and Today.

These cover the contract the UI depends on: Mariana proposes signals, nothing
is collected until a human confirms, and a confirmed set becomes a cohort
query rather than a static list.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import harvey.dashboard as dash
from harvey.signals import SIGNAL_CATALOG
from harvey.state import StateManager


@pytest.fixture
def client(monkeypatch):
    """A dashboard bound to a throwaway database."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "harvey.db"
        monkeypatch.setattr(dash, "DB_PATH", db)
        monkeypatch.setattr(dash, "WEB_DIR", Path(__file__).resolve().parent.parent / "harvey" / "web")
        with TestClient(dash.app) as c:
            c.db_path = db
            yield c


# ── The confirmation gate ──


def test_signals_seed_as_proposed_not_confirmed(client):
    """Mariana proposes. Nothing is live until a human says so."""
    data = client.get("/api/signals").json()
    assert data["total"] == len(SIGNAL_CATALOG)
    assert data["summary"]["proposed"] == len(SIGNAL_CATALOG)
    assert data["summary"]["confirmed"] == 0


def test_signals_grouped_with_plain_language(client):
    data = client.get("/api/signals").json()
    keys = [g["key"] for g in data["groups"]]
    assert keys == ["discovery", "profile", "people", "verification"]
    for group in data["groups"]:
        assert group["blurb"]  # every category explains itself
        for sig in group["signals"]:
            assert sig["description"] and sig["cost_note"]


def test_confirm_and_reject_signals(client):
    r = client.post("/api/signals/status",
                    json={"codes": ["INCUMBENT_AGENCY", "RUNNING_GOOGLE_ADS"],
                          "status": "confirmed"})
    assert r.json()["changed"] == 2 and r.json()["unknown"] == []

    r = client.post("/api/signals/status",
                    json={"code": "BLOCKS_AI_CRAWLERS", "status": "rejected"})
    assert r.json()["changed"] == 1

    summary = client.get("/api/signals").json()["summary"]
    assert summary["confirmed"] == 2
    assert summary["rejected"] == 1


def test_reseeding_never_overrides_a_users_decision(client):
    """Every /api/signals load re-seeds so upgrades add new signals. It must
    not quietly re-enable something the user turned off."""
    client.post("/api/signals/status",
                json={"code": "RUNNING_META_ADS", "status": "rejected"})
    client.get("/api/signals")  # re-seeds
    data = client.get("/api/signals").json()
    meta = next(s for g in data["groups"] for s in g["signals"]
                if s["code"] == "RUNNING_META_ADS")
    assert meta["status"] == "rejected"


def test_confirming_before_the_catalog_loads_still_works(client):
    """A confirm can arrive before anything has read /api/signals. It must
    seed the vocabulary rather than silently changing nothing."""
    r = client.post("/api/signals/status",
                    json={"codes": ["SERP_RANK"], "status": "confirmed"}).json()
    assert r["changed"] == 1


def test_unknown_codes_are_reported_not_swallowed(client):
    r = client.post("/api/signals/status",
                    json={"codes": ["SERP_RANK", "NOT_A_SIGNAL"],
                          "status": "confirmed"}).json()
    assert r["changed"] == 1
    assert r["unknown"] == ["NOT_A_SIGNAL"]


def test_invalid_status_is_rejected(client):
    r = client.post("/api/signals/status", json={"codes": ["SERP_RANK"], "status": "on"})
    assert r.status_code == 400
    r = client.post("/api/signals/status", json={"codes": [], "status": "confirmed"})
    assert r.status_code == 400


# ── Cohorts ──


@pytest.mark.asyncio
async def _seed_observations(db_path):
    state = StateManager(str(db_path))
    await state.init_db()
    from harvey.signals import seed_signal_catalog
    await seed_signal_catalog(state)
    from harvey.models import Company

    ids = []
    for n, name in enumerate(["Alpha Roofing", "Beta Roofing", "Gamma Roofing"]):
        ids.append(await state.add_company(
            Company(name=name, domain=f"{name.split()[0].lower()}.com")))
    # Alpha: agency + ads. Beta: agency only. Gamma: ads + booking already.
    await state.add_observations([
        {"company_id": ids[0], "signal_code": "INCUMBENT_AGENCY", "value_text": "Studio3"},
        {"company_id": ids[0], "signal_code": "RUNNING_GOOGLE_ADS", "value_num": 1},
        {"company_id": ids[1], "signal_code": "INCUMBENT_AGENCY", "value_text": "Etna"},
        {"company_id": ids[2], "signal_code": "RUNNING_GOOGLE_ADS", "value_num": 1},
        {"company_id": ids[2], "signal_code": "NO_ONLINE_BOOKING", "value_num": 1},
    ])
    return ids


def test_cohort_is_a_set_intersection(client):
    import asyncio
    asyncio.run(_seed_observations(client.db_path))

    both = client.post("/api/cohort", json={
        "require": ["INCUMBENT_AGENCY", "RUNNING_GOOGLE_ADS"]}).json()
    assert both["size"] == 1
    assert both["companies"][0]["name"] == "Alpha Roofing"

    one = client.post("/api/cohort", json={"require": ["RUNNING_GOOGLE_ADS"]}).json()
    assert one["size"] == 2

    excluded = client.post("/api/cohort", json={
        "require": ["RUNNING_GOOGLE_ADS"], "exclude": ["NO_ONLINE_BOOKING"]}).json()
    assert excluded["size"] == 1
    assert excluded["companies"][0]["name"] == "Alpha Roofing"


def test_cohort_with_no_requirements_is_empty_not_everything(client):
    """An empty cohort must never mean 'select all' — that would silently
    turn a mis-click into a campaign against the entire database."""
    assert client.post("/api/cohort", json={"require": []}).json()["size"] == 0


def test_signal_counts_surface_in_the_review_ui(client):
    import asyncio
    asyncio.run(_seed_observations(client.db_path))
    data = client.get("/api/signals").json()
    agency = next(s for g in data["groups"] for s in g["signals"]
                  if s["code"] == "INCUMBENT_AGENCY")
    assert agency["companies"] == 2


# ── Today ──


def test_today_leads_with_unconfirmed_signals(client):
    data = client.get("/api/today").json()
    keys = [i["key"] for i in data["items"]]
    assert "signals" in keys
    item = next(i for i in data["items"] if i["key"] == "signals")
    assert item["tab"] == "signals"
    assert str(len(SIGNAL_CATALOG)) in item["title"]


def test_today_flags_a_fully_rejected_vocabulary(client):
    codes = [s["code"] for s in SIGNAL_CATALOG]
    client.post("/api/signals/status", json={"codes": codes, "status": "rejected"})
    data = client.get("/api/today").json()
    keys = [i["key"] for i in data["items"]]
    assert "signals-none" in keys


def test_today_stats_are_present_even_on_an_empty_install(client):
    stats = client.get("/api/today").json()["stats"]
    for key in ("companies", "prospects", "signals_confirmed",
                "outbox_pending", "open_conversations"):
        assert key in stats


# ── Static assets ──


def test_dashboard_serves_its_files(client):
    assert client.get("/").status_code == 200
    assert "app.css" in client.get("/").text
    assert client.get("/static/app.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


@pytest.mark.parametrize("filename, url, media_type", [
    ("index.html", "/", "text/html"),
    ("app.css", "/static/app.css", "text/css"),
    ("app.js", "/static/app.js", "text/javascript"),
    ("icon.svg", "/static/icon.svg", "image/svg+xml"),
])
def test_dashboard_text_is_utf8_with_windows_default_encoding(
    client, monkeypatch, tmp_path, filename, url, media_type,
):
    """UTF-8 assets must survive a CP1252 host without crashes or mojibake."""
    content = "/* ═ café — 日本語 */"
    (tmp_path / filename).write_bytes(content.encode("utf-8"))
    monkeypatch.setattr(dash, "WEB_DIR", tmp_path)
    read_text = Path.read_text

    def windows_read_text(path, encoding=None, errors=None, **kwargs):
        return read_text(path, encoding=encoding or "cp1252", errors=errors, **kwargs)

    monkeypatch.setattr(Path, "read_text", windows_read_text)
    response = client.get(url)
    assert response.status_code == 200
    assert response.text == content
    assert response.content == content.encode("utf-8")
    assert response.headers["content-type"].startswith(media_type)


def test_static_route_refuses_to_escape_the_web_directory(client):
    assert client.get("/static/..%2f..%2fharvey.yaml").status_code == 404
    assert client.get("/static/nope.css").status_code == 404


# ── Catalog invariants the UI and CLI both rely on ──


def test_cost_notes_are_machine_classifiable():
    """`mariana signals --confirm free` and the dashboard's green/amber cost
    chip both key off the cost note. A signal that costs credits must not
    read as free — that is how someone accidentally turns on paid collection.
    """
    paid = {"SERP_RANK", "EMAIL_STATUS", "EMAIL_PATTERN", "FOUND_IN_SERP",
            "EVENT_ANNOUNCED", "NEW_ROLE"}
    for sig in SIGNAL_CATALOG:
        free = sig["cost_note"].lower().startswith(("free", "included", "grátis", "incluído"))
        if sig["code"] in paid:
            continue
        assert free, f"{sig['code']} has an unclassifiable cost note: {sig['cost_note']!r}"

    serp = next(s for s in SIGNAL_CATALOG if s["code"] == "SERP_RANK")
    assert not serp["cost_note"].lower().startswith(("free", "grátis"))
    email = next(s for s in SIGNAL_CATALOG if s["code"] == "EMAIL_STATUS")
    assert not email["cost_note"].lower().startswith(("free", "grátis"))


def test_every_signal_has_a_category_the_ui_renders():
    from harvey.dashboard import CATEGORY_ORDER
    for sig in SIGNAL_CATALOG:
        assert sig["category"] in CATEGORY_ORDER, (
            f"{sig['code']} is in category {sig['category']!r}, which the "
            "dashboard would silently drop")
