"""AI Generate script until creating my own"""

import os
import statistics
import time

from dotenv import load_dotenv

load_dotenv("/home/abdelaziz/Documents/PasteBin-System/.env")

from sqlalchemy import create_engine, text  # noqa: E402

url = os.environ["DATABASE_URL"]
e = create_engine(url)
with e.connect() as c:
    print("count:", c.execute(text("SELECT COUNT(*) FROM pastes")).scalar())
    print(
        "kw matches:",
        c.execute(
            text("SELECT COUNT(*) FROM pastes WHERE content ILIKE '%perfprobe%'")
        ).scalar(),
    )
    for r in c.execute(
        text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='pastes'")
    ).all():
        print("idx:", r)
    print("--- EXPLAIN search query ---")
    for r in c.execute(
        text(
            "EXPLAIN SELECT id, content FROM pastes WHERE content ILIKE '%perfprobe%' LIMIT 50 OFFSET 0"
        )
    ).all():
        print(r[0])
    print("--- db-only timing x7 ---")
    ts = []
    for _ in range(7):
        t = time.perf_counter()
        c.execute(
            text(
                "SELECT id, content FROM pastes WHERE content ILIKE '%perfprobe%' LIMIT 50 OFFSET 0"
            )
        ).all()
        ts.append((time.perf_counter() - t) * 1000)
    ts.sort()
    print("db p50=%.1f min=%.1f max=%.1fms" % (statistics.median(ts), ts[0], ts[-1]))
