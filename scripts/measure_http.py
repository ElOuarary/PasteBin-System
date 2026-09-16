"""
AI Generate script until creating my own
Stabilized HTTP timing for GET /pastes?search= (warmup + 11 samples).
"""
import statistics
import time
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path: str, n: int = 11):
    # warmup
    for _ in range(2):
        req = urllib.request.Request(BASE + path, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req) as r:
            r.read()
    ts = []
    size = 0
    for _ in range(n):
        req = urllib.request.Request(BASE + path, headers={"Accept": "application/json"})
        t = time.perf_counter()
        with urllib.request.urlopen(req) as r:
            size = len(r.read())
        ts.append((time.perf_counter() - t) * 1000)
    ts.sort()
    return ts, size


for path in [
    "/pastes?search=perfprobe&limit=50&offset=0",
    "/pastes?search=perfprobe&limit=50&offset=100",
    "/pastes?search=perfprobe&limit=100&offset=0",
]:
    ts, ln = get(path)
    print(
        "%s n=11 min=%.1f p50=%.1f p90=%.1f max=%.1fms bytes=%d"
        % (path, ts[0], statistics.median(ts), ts[9], ts[-1], ln)
    )
