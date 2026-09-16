"""
AI Generate script until creating my own
Hardened API coverage: happy-path + bad-path (Group 2, no src/ changes).

Covers: create+read roundtrip, tag-filter list shape, single-read
view_count bump vs list-read no bump, expired 410, PUT tags
null/empty/replace, DELETE expired (pastes+links gone, shared tags kept),
search hit + 404 miss, pagination stable pages + 422 over-limit,
missing Accept 400, invalid Content-Type 422.

Each test asserts status + body shape and records client-side latency.
Run: .venv/bin/python -m pytest tests/test_api_hardened.py -v
"""

import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

load_dotenv()

from ..main import app  # noqa: E402
from src.config.database import engine, get_session  # noqa: E402
from src.models import Paste, PasteTagLink, Tag  # noqa: E402

JSON = {"Content-Type": "application/json", "Accept": "application/json"}
TIMINGS: list[tuple[str, int, float]] = []  # (name, status, seconds)

PASTE_KEYS = {"id", "content", "created_at", "view_count", "is_private"}


def timed(name, func, *args, limit=5.0, **kwargs):
    start = time.perf_counter()
    resp = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    TIMINGS.append((name, resp.status_code, elapsed))
    assert elapsed < limit, f"{name}: took {elapsed:.2f}s (>{limit}s sanity bound)"
    return resp


def tag(prefix="t"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def client():
    session = next(get_session())
    app.dependency_overrides[get_session] = lambda: session
    created_paste_ids: list[int] = []
    created_tag_names: set[str] = set()
    with TestClient(app, raise_server_exceptions=False) as c:
        # Drop httpx's default `accept: */*` so "missing Accept" tests are real.
        c.headers.pop("accept", None)
        yield c, session, created_paste_ids, created_tag_names
    # --- cleanup: only rows created by this test, via a fresh session
    # (the test session may hold an aborted txn after a 500) ---
    session.rollback()
    cleanup = Session(engine)
    try:
        if created_paste_ids:
            cleanup.exec(
                delete(PasteTagLink).where(
                    PasteTagLink.paste_id.in_(created_paste_ids)
                )
            )
            cleanup.exec(delete(Paste).where(Paste.id.in_(created_paste_ids)))
        for tname in created_tag_names:
            t = cleanup.exec(select(Tag).where(Tag.name == tname)).first()
            if t is not None and not cleanup.exec(
                select(PasteTagLink).where(PasteTagLink.tag_id == t.id)
            ).first():
                cleanup.delete(t)
        cleanup.commit()
    except Exception:
        cleanup.rollback()
        raise
    finally:
        cleanup.close()
        session.close()
        app.dependency_overrides.clear()


def make_paste(c, session, ids, tags_set, content, **extra):
    body = {"content": content}
    body.update(extra)
    r = timed("POST /paste", c.post, "/paste", json=body, headers=JSON)
    assert r.status_code == 201, f"setup POST failed: {r.status_code} {r.text}"
    data = r.json()
    ids.append(data["id"])
    for t in data.get("tags") or []:
        tags_set.add(t)
    return data


def past_lifetime():
    return (datetime.now(UTC) - timedelta(days=1)).isoformat()


# ---------- 1. create + read roundtrip ----------

def test_create_read_roundtrip(client):
    c, session, ids, tags = client
    tname = tag("rt")
    content = f"roundtrip-{uuid.uuid4().hex}"
    created = make_paste(c, session, ids, tags, content, tags=[tname])

    assert PASTE_KEYS <= set(created), f"POST shape: {sorted(created)}"
    assert created["content"] == content
    assert created["view_count"] == 0
    assert created["tags"] == [tname]

    r = timed("GET /paste/{id}", c.get, f"/paste/{created['id']}",
              headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and len(items) == 1
    assert PASTE_KEYS <= set(items[0]), f"GET shape: {sorted(items[0])}"
    assert items[0]["id"] == created["id"]
    assert items[0]["content"] == content
    assert items[0]["tags"] == [tname]


# ---------- 2. tag filter list shape ----------

def test_tag_filter_list_shape(client):
    c, session, ids, tags = client
    tname = tag("flt")
    for i in range(2):
        make_paste(c, session, ids, tags, f"filterme-{tname}-{i}", tags=[tname])

    r = timed("GET /paste?tag=", c.get, "/paste",
              params={"tag": tname}, headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and len(items) == 2, r.text
    for item in items:
        assert PASTE_KEYS <= set(item), f"item shape: {sorted(item)}"
        assert tname in (item.get("tags") or []), f"missing tag in {item}"


# ---------- 3. view_count: single-read bumps, list-read does not ----------

def test_single_read_bumps_view_count(client):
    c, session, ids, tags = client
    created = make_paste(c, session, ids, tags, f"bump-{uuid.uuid4().hex}")
    assert created["view_count"] == 0

    r1 = timed("GET single #1", c.get, f"/paste/{created['id']}",
               headers={"Accept": "application/json"})
    r2 = timed("GET single #2", c.get, f"/paste/{created['id']}",
               headers={"Accept": "application/json"})
    assert r1.status_code == r2.status_code == 200
    v1, v2 = r1.json()[0]["view_count"], r2.json()[0]["view_count"]
    assert (v1, v2) == (1, 2), f"expected (1,2), got ({v1},{v2})"


def test_list_read_does_not_bump_view_count(client):
    c, session, ids, tags = client
    tname = tag("nobump")
    for i in range(2):
        make_paste(c, session, ids, tags, f"nobump-{tname}-{i}", tags=[tname])

    def list_views():
        r = c.get("/paste", params={"tag": tname},
                  headers={"Accept": "application/json"})
        assert r.status_code == 200, r.text
        return sorted(i["view_count"] for i in r.json())

    timed("GET list #1", c.get, "/paste", params={"tag": tname},
          headers={"Accept": "application/json"})
    assert list_views() == [0, 0], "list read must not bump view_count"
    assert list_views() == [0, 0], "second list read must be stable"


# ---------- 4. expired -> 410 ----------

def test_expired_single_read_410(client):
    c, session, ids, tags = client
    created = make_paste(c, session, ids, tags, f"expired-{uuid.uuid4().hex}",
                         expires_at=past_lifetime())
    r = timed("GET expired", c.get, f"/paste/{created['id']}",
              headers={"Accept": "application/json"})
    assert r.status_code == 410, f"expected 410, got {r.status_code} {r.text}"
    assert "detail" in r.json(), f"error shape: {r.text}"


# ---------- 5. PUT tags: null / empty / replace ----------

def test_put_tags_null_leaves_tags_unchanged(client):
    c, session, ids, tags = client
    tname = tag("keep")
    created = make_paste(c, session, ids, tags, f"keeptags-{tname}", tags=[tname])

    r = timed("PUT tags=null", c.put, f"/paste/{created['id']}",
              json={"tags": None}, headers=JSON)
    assert r.status_code == 202, r.text
    assert r.json()["tags"] == [tname], f"null must not touch tags: {r.text}"

    r = timed("PUT no-tags-key", c.put, f"/paste/{created['id']}",
              json={"content": f"keeptags-{tname}-edited"}, headers=JSON)
    assert r.status_code == 202, r.text
    assert r.json()["tags"] == [tname]


def test_put_tags_empty_clears_tags(client):
    c, session, ids, tags = client
    tname = tag("clear")
    created = make_paste(c, session, ids, tags, f"cleartags-{tname}", tags=[tname])

    r = timed("PUT tags=[]", c.put, f"/paste/{created['id']}",
              json={"tags": []}, headers=JSON)
    assert r.status_code == 202, r.text
    assert r.json()["tags"] == [], f"empty list must clear tags: {r.text}"

    g = c.get(f"/paste/{created['id']}", headers={"Accept": "application/json"})
    assert g.status_code == 200
    assert g.json()[0]["tags"] in ([], None)


def test_put_tags_replace(client):
    c, session, ids, tags = client
    old, new_a, new_b = tag("old"), tag("newA"), tag("newB")
    created = make_paste(c, session, ids, tags, f"reptags-{old}", tags=[old])

    r = timed("PUT tags=replace", c.put, f"/paste/{created['id']}",
              json={"tags": [new_a, new_b]}, headers=JSON)
    assert r.status_code == 202, r.text
    got = sorted(r.json()["tags"] or [])
    assert got == sorted([new_a, new_b]), f"replace failed: {r.text}"
    tags.update([new_a, new_b])


# ---------- 6. DELETE expired: pastes+links gone, shared tags kept ----------

def test_delete_expired_removes_pastes_and_links_keeps_shared_tags(client):
    c, session, ids, tags = client
    shared = tag("shared")
    live_content = f"live-{shared}"
    live = make_paste(c, session, ids, tags, live_content, tags=[shared])
    exp_ids = []
    for i in range(2):
        d = make_paste(c, session, ids, tags, f"exp-{shared}-{i}",
                       tags=[shared], expires_at=past_lifetime())
        exp_ids.append(d["id"])
    tags.add(shared)

    # Bulk delete scans all expired rows; ambient row count in shared dev_db
    # varies, so capture timing here without the 5s interactive bound.
    r = timed("DELETE /pastes/expired", c.delete, "/pastes/expired", limit=120.0)
    assert r.status_code == 204, f"expected 204, got {r.status_code} {r.text}"

    for eid in exp_ids:
        g = c.get(f"/paste/{eid}", headers={"Accept": "application/json"})
        assert g.status_code in (404, 410), f"expired {eid}: {g.status_code}"
        links = session.exec(
            select(PasteTagLink).where(PasteTagLink.paste_id == eid)).all()
        assert links == [], f"orphan links remain for paste {eid}"
        ids.remove(eid)  # already gone server-side; drop from cleanup

    g = c.get(f"/paste/{live['id']}", headers={"Accept": "application/json"})
    assert g.status_code == 200, f"live paste affected: {g.text}"
    assert shared in (g.json()[0].get("tags") or [])
    assert session.exec(select(Tag).where(Tag.name == shared)).first() is not None


# ---------- 7. search: matches + 404 on no-match ----------

def test_search_returns_matches(client):
    c, session, ids, tags = client
    kw = f"kw{uuid.uuid4().hex[:10]}"
    for i in range(2):
        make_paste(c, session, ids, tags, f"needle {kw} doc{i}")

    r = timed("GET /pastes?search=", c.get, "/pastes",
              params={"search": kw, "limit": 100, "offset": 0},
              headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and len(items) == 2, r.text
    for item in items:
        assert PASTE_KEYS <= set(item)
        assert kw in item["content"]


def test_search_no_match_404(client):
    c, session, ids, tags = client
    r = timed("GET /pastes?search=nomatch", c.get, "/pastes",
              params={"search": f"zzz-no-such-{uuid.uuid4().hex}", "limit": 100},
              headers={"Accept": "application/json"})
    assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text}"
    assert "detail" in r.json()


# ---------- 8. pagination: stable pages + 422 over-limit ----------

def test_pagination_stable_pages(client):
    c, session, ids, tags = client
    kw = f"pg{uuid.uuid4().hex[:10]}"
    for i in range(5):
        make_paste(c, session, ids, tags, f"page {kw} doc{i}")

    def page(limit, offset):
        r = c.get("/pastes", params={"search": kw, "limit": limit, "offset": offset},
                  headers={"Accept": "application/json"})
        assert r.status_code == 200, f"offset={offset}: {r.status_code} {r.text}"
        return [i["id"] for i in r.json()]

    t0 = time.perf_counter()
    p0, p1, p2 = page(2, 0), page(2, 2), page(2, 4)
    TIMINGS.append(("GET /pastes pages 2+2+1", 200, time.perf_counter() - t0))
    assert len(p0) == 2 and len(p1) == 2 and len(p2) == 1, (p0, p1, p2)
    assert len(set(p0 + p1 + p2)) == 5, f"pages overlap or repeat: {p0} {p1} {p2}"
    assert page(2, 0) == p0, "same page request must be stable"


def test_pagination_over_limit_422(client):
    c, *_ = client
    r = timed("GET /pastes limit=1001", c.get, "/pastes",
              params={"search": "x", "limit": 1001, "offset": 0},
              headers={"Accept": "application/json"})
    assert r.status_code == 422, f"expected 422, got {r.status_code} {r.text}"
    assert "detail" in r.json()


# ---------- 9. missing Accept -> 400 ----------

def test_missing_accept_400(client):
    c, session, ids, tags = client
    created = make_paste(c, session, ids, tags, f"noaccept-{uuid.uuid4().hex}")

    r = timed("GET no-Accept", c.get, f"/paste/{created['id']}")
    assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text}"
    assert "detail" in r.json()

    r = timed("POST no-Accept", c.post, "/paste",
              content='{"content": "x"}',
              headers={"Content-Type": "application/json"})
    assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text}"


# ---------- 10. invalid Content-Type -> 422 ----------

def test_invalid_content_type_422(client):
    c, *_ = client
    r = timed("POST text/plain", c.post, "/paste",
              content="just text",
              headers={"Content-Type": "text/plain", "Accept": "application/json"})
    assert r.status_code == 422, f"expected 422, got {r.status_code} {r.text}"
    assert "detail" in r.json()


def test_timing_summary():
    print("\n--- per-case timings (client-side) ---")
    for name, status, secs in TIMINGS:
        print(f"{secs * 1000:8.1f}ms  HTTP {status}  {name}")
    assert TIMINGS, "no timed requests recorded"
