#!/bin/bash

# Configuration
BASE_URL="http://127.0.0.1:8000"
LOG_FILE="api_tests.log"

# Clear the log file at the start of each run
> "$LOG_FILE"

# Redirect all stdout and stderr to both the console and the log file
exec > >(tee -a "$LOG_FILE") 2>&1

# Counters for test results
PASSED_COUNT=0
TOTAL_COUNT=0

# Helper function to run curl and validate the HTTP status code and capture latency
# Usage: run_test "Test Name" expected_code "curl_command"
run_test() {
    local test_name="$1"
    local expected_code="$2"
    local curl_cmd="$3"

    ((TOTAL_COUNT++))
    echo -n "Testing $test_name... "

    # Execute curl and capture both the HTTP status code and the total time
    # -o /dev/null: discard body
    # -s: silent mode
    # -w "%{http_code}|%{time_total}": output status code and total time separated by a pipe
    result=$(eval "$curl_cmd -o /dev/null -s -w \"%{http_code}|%{time_total}\"")

    # Split the result by the pipe character
    actual_code=$(echo "$result" | cut -d'|' -f1)
    latency=$(echo "$result" | cut -d'|' -f2)

    if [ "$actual_code" -eq "$expected_code" ]; then
        echo "PASSED (HTTP $actual_code, Time: ${latency}s)"
        ((PASSED_COUNT++))
        return 0
    else
        echo "FAILED (Expected $expected_code, got $actual_code, Time: ${latency}s)"
        return 1
    fi
}

echo "Starting API Automated Tests..."
echo "====================================================="

# --- HAPPY PATHS (Sequential Flow) ---

# 1. Health Check
run_test "Health Check (GET /health)" 200 "curl $BASE_URL/health"

# 2. Create Paste
echo "Creating paste..."
CREATE_BODY='{"content": "Hello, this is a test paste!", "tag": "test-tag"}'
CREATE_RESP=$(curl -s -H "Content-Type: application/json" -H "Accept: application/json" -d "$CREATE_BODY" "$BASE_URL/pastebin")
PASTE_ID=$(echo "$CREATE_RESP" | grep -oP '"(id|paste_id)":\s*[^,}]+' | head -1 | cut -d':' -f2 | tr -d ' "')

if [ -z "$PASTE_ID" ]; then
    echo "CRITICAL: Failed to create paste or extract ID. Response: $CREATE_RESP"
    exit 1
fi
echo "Paste created with ID: $PASTE_ID"

# 3. Read Paste
run_test "Read Paste (GET /pastebin/$PASTE_ID)" 200 "curl -H \"Accept: application/json\" $BASE_URL/pastebin/$PASTE_ID"

# 4. Update Paste
UPDATE_BODY='{"content": "This content has been updated!", "tag": "updated-tag"}'
run_test "Update Paste (PUT /pastebin/$PASTE_ID)" 202 "curl -X PUT -H \"Content-Type: application/json\" -H \"Accept: application/json\" -d '$UPDATE_BODY' $BASE_URL/pastebin/$PASTE_ID"

# 5. Verify Update
run_test "Verify Update (GET /pastebin/$PASTE_ID)" 200 "curl -H \"Accept: application/json\" $BASE_URL/pastebin/$PASTE_ID"

# 6. Delete Paste
run_test "Delete Paste (DELETE /pastebin/$PASTE_ID)" 204 "curl -X DELETE $BASE_URL/pastebin/$PASTE_ID"

# 7. Verify Deletion (Should be 404)
run_test "Verify Deletion (GET /pastebin/$PASTE_ID)" 404 "curl -H \"Accept: application/json\" $BASE_URL/pastebin/$PASTE_ID"

echo "-----------------------------------------------------"
echo "Sequential Happy Path Tests Completed."
echo "-----------------------------------------------------"

# --- EXPIRED CONTENT TESTS ---

echo "Testing Expired Content..."
# Create a paste that expired in 2000-01-01
EXPIRED_BODY='{"content": "This is an expired paste", "expires_at": "2000-01-01T00:00:00Z"}'
EXPIRED_RESP=$(curl -s -H "Content-Type: application/json" -H "Accept: application/json" -d "$EXPIRED_BODY" "$BASE_URL/pastebin")
EXP_PASTE_ID=$(echo "$EXPIRED_RESP" | grep -oP '"(id|paste_id)":\s*[^,}]+' | head -1 | cut -d':' -f2 | tr -d ' "')

if [ -n "$EXP_PASTE_ID" ]; then
    run_test "Read Expired Paste (GET /pastebin/$EXP_PASTE_ID)" 410 "curl -H \"Accept: application/json\" $BASE_URL/pastebin/$EXP_PASTE_ID"

    UPDATE_EXPIRED_BODY='{"content": "Trying to update expired"}'
    run_test "Update Expired Paste (PUT /pastebin/$EXP_PASTE_ID)" 410 "curl -X PUT -H \"Content-Type: application/json\" -H \"Accept: application/json\" -d '$UPDATE_EXPIRED_BODY' $BASE_URL/pastebin/$EXP_PASTE_ID"

    # Cleanup expired paste
    curl -s -X DELETE $BASE_URL/pastebin/$EXP_PASTE_ID > /dev/null
else
    echo "CRITICAL: Failed to create expired paste for testing."
fi

echo "-----------------------------------------------------"

# --- BAD PATHS (Negative Testing) ---

# POST /pastebin
run_test "POST - Missing Content-Type (422)" 422 "curl -d '{\"content\": \"test\"}' $BASE_URL/pastebin"
run_test "POST - Wrong Content-Type (422)" 422 "curl -H \"Content-Type: text/plain\" -d '{\"content\": \"test\"}' $BASE_URL/pastebin"
run_test "POST - Wrong Accept (400)" 400 "curl -H \"Content-Type: application/json\" -H \"Accept: text/html\" -d '{\"content\": \"test\"}' $BASE_URL/pastebin"
run_test "POST - Missing/Null Content (422)" 422 "curl -H \"Content-Type: application/json\" -d '{\"content\": null}' $BASE_URL/pastebin"

# GET /pastebin/{id}
run_test "GET - Wrong Accept (400)" 400 "curl -H \"Accept: text/html\" $BASE_URL/pastebin/123"
run_test "GET - Invalid ID (Non-numeric 422)" 422 "curl -H \"Accept: application/json\" $BASE_URL/pastebin/abc"
run_test "GET - Not Found (404)" 404 "curl -H \"Accept: application/json\" $BASE_URL/pastebin/999999"

# PUT /pastebin/{id}
run_test "PUT - Missing Content-Type (422)" 422 "curl -X PUT -H \"Accept: application/json\" -d '{\"content\": \"test\"}' $BASE_URL/pastebin/123"
run_test "PUT - Missing/Wrong Accept (400)" 400 "curl -X PUT -H \"Content-Type: application/json\" -d '{\"content\": \"test\"}' $BASE_URL/pastebin/123"
run_test "PUT - Invalid ID (Non-numeric 422)" 422 "curl -X PUT -H \"Content-Type: application/json\" -H \"Accept: application/json\" -d '{\"content\": \"test\"}' $BASE_URL/pastebin/abc"
run_test "PUT - Not Found (404)" 404 "curl -X PUT -H \"Content-Type: application/json\" -H \"Accept: application/json\" -d '{\"content\": \"test\"}' $BASE_URL/pastebin/999999"

# DELETE /pastebin/{id}
run_test "DELETE - Invalid ID (Non-numeric 422)" 422 "curl -X DELETE $BASE_URL/pastebin/abc"
run_test "DELETE - Not Found (404)" 404 "curl -X DELETE $BASE_URL/pastebin/999999"

echo "====================================================="
echo "Tests Summary: $PASSED_COUNT / $TOTAL_COUNT passed"
echo "====================================================="
echo "All Tests Completed."
