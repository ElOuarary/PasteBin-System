#!/bin/bash
# Port of tests/test_api_hardened.py (16 pytest cases) to curl+jq shell.
# Covers: create+read roundtrip, tag-filter list shape, single-read view bump
# vs list-read no bump, expired single 410, PUT tags null/empty/replace,
# DELETE expired (pastes+links gone, shared tags kept), search hit + 404 miss,
# pagination stable pages + 422 over-limit, missing Accept 400,
# invalid Content-Type 422.
# Style: curl + jq, Accept: application/json, colored pass/fail + summary.
# Run: bash tests/test_api.sh   (server: http://127.0.0.1:8000)

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
LOG_FILE="api_tests.log"
> "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; NC='\033[0m'
PASSED_COUNT=0; FAILED_COUNT=0; TOTAL_COUNT=0
FAILED_NAMES=()
CREATED_IDS=()
REQ_MS="" # last request latency, e.g. "23.4ms" — consumed by expect_status

J() { echo "$1" | jq -r "$2" 2>/dev/null; }

fmt_ms() { awk "BEGIN {printf \"%.1fms\", $1 * 1000}"; }

pass() { local tag=""; [ -n "$REQ_MS" ] && tag=" [$REQ_MS]"; ((TOTAL_COUNT++)); ((PASSED_COUNT++)); echo -e "${GREEN}PASS${NC} $1$tag"; }
fail() { local tag=""; [ -n "$REQ_MS" ] && tag=" [$REQ_MS]"; ((TOTAL_COUNT++)); ((FAILED_COUNT++)); FAILED_NAMES+=("$1"); echo -e "${RED}FAIL${NC} $1$tag -- $2"; }

# expect_status "Name" expected actual [extra_detail] — pass()/fail() append [REQ_MS]
expect_status() {
    if [ "$2" = "$3" ]; then pass "$1 (HTTP $3)"; else fail "$1" "expected $2, got $3${4:+ ($4)}"; fi
}

req() { # req METHOD URL [DATA] [EXTRA_CURL_ARGS...] -> sets REQ_BODY/REQ_CODE/REQ_MS
    local method="$1" url="$2" data="$3"; shift 3
    local tmp; tmp=$(mktemp)
    local out secs
    if [ -n "$data" ]; then
        out=$(curl -s -o "$tmp" -w "%{http_code} %{time_total}" -X "$method" "$url" \
            -H "Content-Type: application/json" -H "Accept: application/json" \
            -d "$data" "$@" 2>/dev/null)
    else
        out=$(curl -s -o "$tmp" -w "%{http_code} %{time_total}" -X "$method" "$url" \
            -H "Accept: application/json" "$@" 2>/dev/null)
    fi
    REQ_CODE="${out% *}"; secs="${out#* }"; REQ_MS="$(fmt_ms "$secs")"
    REQ_BODY=$(cat "$tmp"); rm -f "$tmp"
}

track() { [ -n "$1" ] && [ "$1" != "null" ] && CREATED_IDS+=("$1"); }
cleanup() { for id in "${CREATED_IDS[@]}"; do curl -s -X DELETE "$BASE_URL/paste/$id" >/dev/null 2>&1; done; }
trap cleanup EXIT

command -v jq >/dev/null || { echo "jq is required"; exit 1; }

SUFFIX="$(date +%s)-$RANDOM"
echo "Starting API Tests (hardened port, suffix=$SUFFIX)..."
echo "====================================================="

# ---------- 0. health ----------
HOUT=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" "$BASE_URL/health")
CODE="${HOUT% *}"
REQ_MS="$(fmt_ms "${HOUT#* }")"
expect_status "Health Check (GET /health)" 200 "$CODE"

# ---------- 1. create + read roundtrip ----------
CONTENT_RT="roundtrip-$SUFFIX"; TAG_RT="rt-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"$CONTENT_RT\", \"tags\": [\"$TAG_RT\"]}"
expect_status "Create+Read: POST /paste 201" 201 "$REQ_CODE" "$REQ_BODY"
RT_ID=$(J "$REQ_BODY" '.id'); track "$RT_ID"
[ "$(J "$REQ_BODY" '.content')" = "$CONTENT_RT" ] && pass "Create+Read: POST echoes content" || fail "Create+Read: POST echoes content" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.view_count')" = "0" ] && pass "Create+Read: POST view_count=0" || fail "Create+Read: POST view_count=0" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.tags[0]')" = "$TAG_RT" ] && pass "Create+Read: POST tags roundtrip" || fail "Create+Read: POST tags roundtrip" "$REQ_BODY"
SHAPE_FAIL=0
for k in id content created_at view_count is_private; do
    if J "$REQ_BODY" ".$k" | grep -q null; then fail "Create+Read: POST has key $k" "$REQ_BODY"; SHAPE_FAIL=1; fi
done
[ "$SHAPE_FAIL" = "0" ] && pass "Create+Read: POST shape keys present"

req GET "$BASE_URL/paste/$RT_ID" ""
expect_status "Create+Read: GET /paste/{id} 200" 200 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.[0].id')" = "$RT_ID" ] && pass "Create+Read: GET id matches" || fail "Create+Read: GET id matches" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.[0].content')" = "$CONTENT_RT" ] && pass "Create+Read: GET content matches" || fail "Create+Read: GET content matches" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.[0].tags[0]')" = "$TAG_RT" ] && pass "Create+Read: GET tags match" || fail "Create+Read: GET tags match" "$REQ_BODY"

# ---------- 2. tag-filter list shape ----------
TAG_FLT="flt-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"filterme-$TAG_FLT-0\", \"tags\": [\"$TAG_FLT\"]}"
F1=$(J "$REQ_BODY" '.id'); track "$F1"
req POST "$BASE_URL/paste" "{\"content\": \"filterme-$TAG_FLT-1\", \"tags\": [\"$TAG_FLT\"]}"
F2=$(J "$REQ_BODY" '.id'); track "$F2"
req GET "$BASE_URL/paste?tag=$TAG_FLT" ""
expect_status "Tag-filter: GET /paste?tag= 200" 200 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" 'length')" = "2" ] && pass "Tag-filter: list has 2 items" || fail "Tag-filter: list has 2 items" "$REQ_BODY"
if echo "$REQ_BODY" | jq -e --arg t "$TAG_FLT" 'type=="array" and (map(.tags // [] | index($t) != null) | all)' >/dev/null 2>&1; then
    pass "Tag-filter: every item carries the tag"
else
    fail "Tag-filter: every item carries the tag" "$REQ_BODY"
fi
if echo "$REQ_BODY" | jq -e 'map(has("id") and has("content") and has("created_at") and has("view_count") and has("is_private")) | all' >/dev/null 2>&1; then
    pass "Tag-filter: item shape keys present"
else
    fail "Tag-filter: item shape keys present" "$REQ_BODY"
fi

# ---------- 3. single-read bumps view_count ----------
req POST "$BASE_URL/paste" "{\"content\": \"bump-$SUFFIX\"}"
BUMP_ID=$(J "$REQ_BODY" '.id'); track "$BUMP_ID"
req GET "$BASE_URL/paste/$BUMP_ID" ""; V1=$(J "$REQ_BODY" '.[0].view_count')
req GET "$BASE_URL/paste/$BUMP_ID" ""; V2=$(J "$REQ_BODY" '.[0].view_count')
expect_status "View-bump: two single reads 200" 200 "$REQ_CODE" "$REQ_BODY"
if [ "$V1" = "1" ] && [ "$V2" = "2" ]; then pass "View-bump: single reads bump 0->1->2"; else fail "View-bump: single reads bump 0->1->2" "got ($V1,$V2)"; fi

# ---------- 4. list-read does not bump ----------
TAG_NB="nobump-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"nobump-$TAG_NB-0\", \"tags\": [\"$TAG_NB\"]}"
N1=$(J "$REQ_BODY" '.id'); track "$N1"
req POST "$BASE_URL/paste" "{\"content\": \"nobump-$TAG_NB-1\", \"tags\": [\"$TAG_NB\"]}"
N2=$(J "$REQ_BODY" '.id'); track "$N2"
req GET "$BASE_URL/paste?tag=$TAG_NB" ""; L1=$(J "$REQ_BODY" 'map(.view_count) | sort | join(",")')
req GET "$BASE_URL/paste?tag=$TAG_NB" ""; L2=$(J "$REQ_BODY" 'map(.view_count) | sort | join(",")')
expect_status "No-bump: list reads 200" 200 "$REQ_CODE" "$REQ_BODY"
[ "$L1" = "0,0" ] && pass "No-bump: first list read leaves 0,0" || fail "No-bump: first list read leaves 0,0" "got $L1"
[ "$L2" = "0,0" ] && pass "No-bump: second list read stable 0,0" || fail "No-bump: second list read stable 0,0" "got $L2"

# ---------- 5. expired single -> 410 ----------
req POST "$BASE_URL/paste" "{\"content\": \"expired-$SUFFIX\", \"expires_at\": \"2000-01-01T00:00:00Z\"}"
EXP_ID=$(J "$REQ_BODY" '.id'); track "$EXP_ID"
req GET "$BASE_URL/paste/$EXP_ID" ""
expect_status "Expired: GET single 410" 410 "$REQ_CODE" "$REQ_BODY"
J "$REQ_BODY" '.detail' | grep -q null && fail "Expired: error has detail" "$REQ_BODY" || pass "Expired: error has detail"

# ---------- 6. PUT tags null / empty / replace ----------
# 6a. null leaves unchanged
TAG_KEEP="keep-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"keeptags-$TAG_KEEP\", \"tags\": [\"$TAG_KEEP\"]}"
KEEP_ID=$(J "$REQ_BODY" '.id'); track "$KEEP_ID"
req PUT "$BASE_URL/paste/$KEEP_ID" '{"tags": null}'
expect_status "PUT tags=null: 202" 202 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.tags[0]')" = "$TAG_KEEP" ] && pass "PUT tags=null: tags unchanged" || fail "PUT tags=null: tags unchanged" "$REQ_BODY"
req PUT "$BASE_URL/paste/$KEEP_ID" "{\"content\": \"keeptags-$TAG_KEEP-edited\"}"
expect_status "PUT no-tags-key: 202" 202 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.tags[0]')" = "$TAG_KEEP" ] && pass "PUT no-tags-key: tags unchanged" || fail "PUT no-tags-key: tags unchanged" "$REQ_BODY"
# 6b. empty clears
TAG_CLEAR="clear-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"cleartags-$TAG_CLEAR\", \"tags\": [\"$TAG_CLEAR\"]}"
CLEAR_ID=$(J "$REQ_BODY" '.id'); track "$CLEAR_ID"
req PUT "$BASE_URL/paste/$CLEAR_ID" '{"tags": []}'
expect_status "PUT tags=[]: 202" 202 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" '.tags | length')" = "0" ] && pass "PUT tags=[]: clears tags" || fail "PUT tags=[]: clears tags" "$REQ_BODY"
req GET "$BASE_URL/paste/$CLEAR_ID" ""
TAGS_AFTER=$(J "$REQ_BODY" '.[0].tags')
if [ "$TAGS_AFTER" = "null" ] || [ "$TAGS_AFTER" = "[]" ]; then pass "PUT tags=[]: GET shows empty/null"; else fail "PUT tags=[]: GET shows empty/null" "$REQ_BODY"; fi
# 6c. replace
TAG_OLD="old-$SUFFIX"; TAG_NA="newA-$SUFFIX"; TAG_NB2="newB-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"reptags-$TAG_OLD\", \"tags\": [\"$TAG_OLD\"]}"
REP_ID=$(J "$REQ_BODY" '.id'); track "$REP_ID"
req PUT "$BASE_URL/paste/$REP_ID" "{\"tags\": [\"$TAG_NA\", \"$TAG_NB2\"]}"
expect_status "PUT tags=replace: 202" 202 "$REQ_CODE" "$REQ_BODY"
GOT=$(echo "$REQ_BODY" | jq -r '.tags | sort | join(",")')
WANT=$(printf "%s\n%s" "$TAG_NA" "$TAG_NB2" | sort | paste -sd, -)
[ "$GOT" = "$WANT" ] && pass "PUT tags=replace: tags replaced" || fail "PUT tags=replace: tags replaced" "got $GOT want $WANT"

# ---------- 7. DELETE expired: pastes+links gone, shared tags kept ----------
TAG_SHARED="shared-$SUFFIX"
req POST "$BASE_URL/paste" "{\"content\": \"live-$TAG_SHARED\", \"tags\": [\"$TAG_SHARED\"]}"
LIVE_ID=$(J "$REQ_BODY" '.id'); track "$LIVE_ID"
req POST "$BASE_URL/paste" "{\"content\": \"exp-$TAG_SHARED-0\", \"tags\": [\"$TAG_SHARED\"], \"expires_at\": \"2000-01-01T00:00:00Z\"}"
E1=$(J "$REQ_BODY" '.id'); track "$E1"
req POST "$BASE_URL/paste" "{\"content\": \"exp-$TAG_SHARED-1\", \"tags\": [\"$TAG_SHARED\"], \"expires_at\": \"2000-01-01T00:00:00Z\"}"
E2=$(J "$REQ_BODY" '.id'); track "$E2"
tmp=$(mktemp)
DOUT=$(curl -s -o "$tmp" -w "%{http_code} %{time_total}" -X DELETE "$BASE_URL/pastes/expired"); rm -f "$tmp"
DEL_CODE="${DOUT% *}"
REQ_MS="$(fmt_ms "${DOUT#* }")"
expect_status "DELETE /pastes/expired 204" 204 "$DEL_CODE"
for eid in "$E1" "$E2"; do
    req GET "$BASE_URL/paste/$eid" ""
    if [ "$REQ_CODE" = "404" ] || [ "$REQ_CODE" = "410" ]; then pass "DELETE expired: paste $eid gone ($REQ_CODE)"; else fail "DELETE expired: paste $eid gone" "got $REQ_CODE $REQ_BODY"; fi
done
req GET "$BASE_URL/paste/$LIVE_ID" ""
expect_status "DELETE expired: live paste survives 200" 200 "$REQ_CODE" "$REQ_BODY"
echo "$REQ_BODY" | jq -e --arg t "$TAG_SHARED" '.[0].tags | index($t) != null' >/dev/null 2>&1 \
    && pass "DELETE expired: shared tag kept on live paste" \
    || fail "DELETE expired: shared tag kept on live paste" "$REQ_BODY"

# ---------- 8. search matches + no-match [] ----------
KW="kw${SUFFIX//-/}x"
req POST "$BASE_URL/paste" "{\"content\": \"needle $KW doc0\"}"
S1=$(J "$REQ_BODY" '.id'); track "$S1"
req POST "$BASE_URL/paste" "{\"content\": \"needle $KW doc1\"}"
S2=$(J "$REQ_BODY" '.id'); track "$S2"
req GET "$BASE_URL/pastes?search=$KW&limit=100&offset=0" ""
expect_status "Search: matches 200" 200 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" 'length')" = "2" ] && pass "Search: returns 2 matches" || fail "Search: returns 2 matches" "$REQ_BODY"
echo "$REQ_BODY" | jq -e --arg k "$KW" 'map(.content | contains($k)) | all' >/dev/null 2>&1 \
    && pass "Search: every hit contains keyword" \
    || fail "Search: every hit contains keyword" "$REQ_BODY"
req GET "$BASE_URL/pastes?search=zzz-no-such-$SUFFIX&limit=100" ""
expect_status "Search: no-match 200" 200 "$REQ_CODE" "$REQ_BODY"
[ "$(J "$REQ_BODY" 'length')" = "0" ] && pass "Search: no-match returns empty list" || fail "Search: no-match returns empty list" "$REQ_BODY"

# ---------- 9. pagination stable pages + over-limit 422 ----------
PG="pg${SUFFIX//-/}y"
for i in 0 1 2 3 4; do
    req POST "$BASE_URL/paste" "{\"content\": \"page $PG doc$i\"}"
    track "$(J "$REQ_BODY" '.id')"
done
req GET "$BASE_URL/pastes?search=$PG&limit=2&offset=0" ""; P0=$(J "$REQ_BODY" 'map(.id) | join(",")')
req GET "$BASE_URL/pastes?search=$PG&limit=2&offset=2" ""; P1=$(J "$REQ_BODY" 'map(.id) | join(",")')
req GET "$BASE_URL/pastes?search=$PG&limit=2&offset=4" ""; P2=$(J "$REQ_BODY" 'map(.id) | join(",")')
expect_status "Pagination: pages 200" 200 "$REQ_CODE" "$REQ_BODY"
C0=$(echo "$P0" | tr ',' '\n' | wc -l); C1=$(echo "$P1" | tr ',' '\n' | wc -l); C2=$(echo "$P2" | tr ',' '\n' | wc -l)
[ "$C0" = "2" ] && [ "$C1" = "2" ] && [ "$C2" = "1" ] && pass "Pagination: page sizes 2+2+1" || fail "Pagination: page sizes 2+2+1" "got $C0,$C1,$C2 ($P0 | $P1 | $P2)"
UNIQ=$(echo "$P0,$P1,$P2" | tr ',' '\n' | sort -u | wc -l)
[ "$UNIQ" = "5" ] && pass "Pagination: 5 distinct ids, no overlap" || fail "Pagination: 5 distinct ids, no overlap" "got $UNIQ ($P0 | $P1 | $P2)"
req GET "$BASE_URL/pastes?search=$PG&limit=2&offset=0" ""
[ "$(J "$REQ_BODY" 'map(.id) | join(",")')" = "$P0" ] && pass "Pagination: repeat page stable" || fail "Pagination: repeat page stable" "$REQ_BODY"
req GET "$BASE_URL/pastes?search=x&limit=1001&offset=0" ""
expect_status "Pagination: limit=1001 422" 422 "$REQ_CODE" "$REQ_BODY"
J "$REQ_BODY" '.detail' | grep -q null && fail "Pagination: 422 has detail" "$REQ_BODY" || pass "Pagination: 422 has detail"

# ---------- 10. missing Accept -> 400 ----------
tmp=$(mktemp)
M1=$(curl -s -o "$tmp" -w "%{http_code} %{time_total}" -H "Accept:" "$BASE_URL/paste/$RT_ID"); rm -f "$tmp"   # no Accept at all
C1="${M1% *}"
REQ_MS="$(fmt_ms "${M1#* }")"
expect_status "Missing Accept: GET no-Accept 400" 400 "$C1"
tmp=$(mktemp)
M2=$(curl -s -o "$tmp" -w "%{http_code} %{time_total}" -X POST "$BASE_URL/paste" -H "Accept:" -H "Content-Type: application/json" -d '{"content": "x"}'); rm -f "$tmp"
C2="${M2% *}"
REQ_MS="$(fmt_ms "${M2#* }")"
expect_status "Missing Accept: POST no-Accept 400" 400 "$C2"

# ---------- 11. invalid Content-Type -> 422 ----------
tmp=$(mktemp)
M3=$(curl -s -o "$tmp" -w "%{http_code} %{time_total}" -X POST "$BASE_URL/paste" -H "Content-Type: text/plain" -H "Accept: application/json" -d 'just text'); BOD=$(cat "$tmp"); rm -f "$tmp"
C3="${M3% *}"
REQ_MS="$(fmt_ms "${M3#* }")"
expect_status "Invalid Content-Type: text/plain 422" 422 "$C3" "$BOD"
echo "$BOD" | jq -e 'has("detail")' >/dev/null 2>&1 \
    && pass "Invalid Content-Type: 422 has detail" \
    || fail "Invalid Content-Type: 422 has detail" "$BOD"

echo "====================================================="
echo -e "Tests Summary: ${GREEN}$PASSED_COUNT passed${NC}, ${RED}$FAILED_COUNT failed${NC}, $TOTAL_COUNT total"
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Failed cases:${NC}"
    for n in "${FAILED_NAMES[@]}"; do echo "  - $n"; done
    exit 1
fi
echo "All Tests Completed."
