#!/bin/bash

# Configuration
BASE_URL="http://127.0.0.1:8000"

# Helper function to run curl and print result
run_test() {
    local test_name=$1
    local curl_cmd=$2
    echo -n "Testing $test_name... "

    # Execute curl and capture output
    result=$(eval "$curl_cmd -o /dev/null -s -w \"HTTP %{http_code} | Time: %{time_total}s\"")
    echo "$result"
}

echo "Starting API Automated Tests..."
echo "====================================================="

# 1. Root endpoint
run_test "Root Endpoint (GET /)" "curl $BASE_URL/"

# 2. Create Pastebin (Success)
echo -n "Testing Create Pastebin (Success)... "
# Explicitly define headers to avoid expansion issues
create_resp=$(curl -s -H "Content-Type: application/json" -H "Accept: application/json" -d '{"text": "Hello from automated tests!"}' "$BASE_URL/pastebin")
PASTE_ID=$(echo $create_resp | grep -oP '(?<="paste_id":")[^"]*')

if [ -n "$PASTE_ID" ]; then
    TIME=$(curl -o /dev/null -s -w "%{time_total}s" -H "Content-Type: application/json" -H "Accept: application/json" -d '{"text": "Hello from automated tests!"}' "$BASE_URL/pastebin")
    echo "HTTP 201 | Time: $TIME | ID: $PASTE_ID"
else
    echo "FAILED to create paste. Response: $create_resp"
    exit 1
fi

# 3. Create Pastebin (Fail - Wrong Content-Type)
run_test "Create Pastebin (Fail - Content-Type)" "curl -H \"Content-Type: text/plain\" -H \"Accept: application/json\" -d '{\"text\": \"fail\"}' $BASE_URL/pastebin"

# 4. Create Pastebin (Fail - Wrong Accept)
run_test "Create Pastebin (Fail - Accept)" "curl -H \"Content-Type: application/json\" -H \"Accept: text/html\" -d '{\"text\": \"fail\"}' $BASE_URL/pastebin"

# 5. Read Pastebin (Success)
run_test "Read Pastebin (Success)" "curl $BASE_URL/pastebin/$PASTE_ID"

# 6. Update Pastebin (Success)
run_test "Update Pastebin (Success)" "curl -X PUT -H \"Content-Type: application/json\" -H \"Accept: application/json\" -d '{\"text\": \"Updated content!\"}' $BASE_URL/pastebin/$PASTE_ID"

# 7. Update Pastebin (Fail - Header)
run_test "Update Pastebin (Fail - Header)" "curl -X PUT -H \"Content-Type: text/plain\" -d '{\"text\": \"fail\"}' $BASE_URL/pastebin/$PASTE_ID"

# 8. Read Pastebin (Verify Update)
run_test "Read Pastebin (Verify Update)" "curl $BASE_URL/pastebin/$PASTE_ID"

# 9. Delete Pastebin (Success)
run_test "Delete Pastebin (Success)" "curl -X DELETE $BASE_URL/pastebin/$PASTE_ID"

# 10. Read Pastebin (Verify 404 after delete)
run_test "Read Pastebin (Verify 404 after delete)" "curl $BASE_URL/pastebin/$PASTE_ID"

# 11. Delete Pastebin (Verify 404)
run_test "Delete Pastebin (Verify 404)" "curl -X DELETE $BASE_URL/pastebin/$PASTE_ID"

echo "====================================================="
echo "Tests Completed."
