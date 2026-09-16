"""
AI Generate script until creating my own
Bulk-seed 20,000+ pastes for Q5 perf proof.

Uses psycopg2 executemany in batches (default 2000). Varied content /
expiry / tags. ~1/3 of rows contain the searchable keyword ``perfprobe``.
Idempotent-ish: skips work if pastes table already holds >= TARGET rows.

Usage:  uv run python scripts/seed_20k.py [--total 20000] [--batch 2000]
"""
import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import psycopg2  # noqa: E402

KEYWORD = "perfprobe"
TAG_NAMES = ["python", "perf", "notes", "snippet", "q5", "draft", "log", "seed"]
WORDS = [
    "lorem", "ipsum", "dolor", "fastapi", "sqlmodel", "paste", "bin",
    "server", "index", "query", "alpha", "bravo", "charlie", "delta",
    "echo", "foxtrot", "benchmark", "sample", "text", "content",
]


def gen_content(i: int, rng: random.Random) -> str:
    body = " ".join(rng.choice(WORDS) for _ in range(12))
    if i % 3 == 0:
        return f"{KEYWORD} paste number {i} {body} {KEYWORD}"
    return f"paste number {i} {body}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=20000)
    ap.add_argument("--batch", type=int, default=2000)
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    # SQLAlchemy-style URL (postgresql+psycopg2://...) -> plain libpq DSN
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://").replace(
        "postgres+psycopg2://", "postgresql://"
    )

    rng = random.Random(42)
    now = datetime.now(timezone.utc)
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM pastes;")
    existing = cur.fetchone()[0]
    print(f"existing pastes: {existing}")
    if existing >= args.total:
        print(f"already at target ({existing} >= {args.total}), nothing to do")
        return

    need = args.total - existing

    # Ensure seed tags exist
    for name in TAG_NAMES:
        cur.execute("INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (name,))
    conn.commit()
    cur.execute("SELECT id, name FROM tags;")
    tag_ids = [r[0] for r in cur.fetchall()]

    PASTE_SQL = (
        "INSERT INTO pastes (content, created_at, expires_at, view_count, is_private)"
        " VALUES (%s, %s, %s, %s, %s) RETURNING id;"
    )
    LINK_SQL = 'INSERT INTO "PasteTag" (paste_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;'

    inserted = 0
    t0 = datetime.now()
    batch_rows: list = []
    for i in range(need):
        n = existing + i
        # varied expiry: ~70% NULL, ~20% future, ~10% past
        r = rng.random()
        if r < 0.7:
            exp = None
        elif r < 0.9:
            exp = now + timedelta(days=rng.randint(1, 365))
        else:
            exp = now - timedelta(days=rng.randint(1, 30))
        batch_rows.append((
            gen_content(n, rng),
            now - timedelta(minutes=rng.randint(0, 525600)),
            exp,
            rng.randint(0, 100),
            rng.random() < 0.1,
        ))
        if len(batch_rows) >= args.batch or i == need - 1:
            ids = []
            for row in batch_rows:
                cur.execute(PASTE_SQL, row)
                ids.append(cur.fetchone()[0])
            links = []
            for pid in ids:
                k = rng.randint(0, 2)
                for tid in rng.sample(tag_ids, k):
                    links.append((pid, tid))
            if links:
                cur.executemany(LINK_SQL, links)
            conn.commit()
            inserted += len(batch_rows)
            print(f"  inserted {inserted}/{need}", flush=True)
            batch_rows = []

    dt = (datetime.now() - t0).total_seconds()
    cur.execute("SELECT COUNT(*) FROM pastes;")
    print(f"done: total pastes={cur.fetchone()[0]} inserted={inserted} in {dt:.1f}s")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
