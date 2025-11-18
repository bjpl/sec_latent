#!/bin/bash
# Smoke Test Script for SEC Latent Application
# Validates critical functionality after deployment

set -euo pipefail

# Configuration
BASE_URL="${1:-http://localhost:8000}"
TIMEOUT=30
MAX_RETRIES=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging functions
log_test() {
    echo -e "\n${YELLOW}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

# Health check endpoint
test_health_endpoint() {
    log_test "Health check endpoint"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time $TIMEOUT \
        "$BASE_URL/health")

    if [ "$response" = "200" ]; then
        log_pass "Health endpoint returned 200"
    else
        log_fail "Health endpoint returned $response (expected 200)"
    fi
}

# Root endpoint
test_root_endpoint() {
    log_test "Root endpoint"

    response=$(curl -s --max-time $TIMEOUT "$BASE_URL/")

    if echo "$response" | grep -q "SEC Latent Analysis API"; then
        log_pass "Root endpoint responded correctly"
    else
        log_fail "Root endpoint response unexpected"
    fi
}

# API documentation
test_api_docs() {
    log_test "API documentation endpoint"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time $TIMEOUT \
        "$BASE_URL/docs")

    if [ "$response" = "200" ]; then
        log_pass "API docs accessible"
    else
        log_fail "API docs returned $response (expected 200)"
    fi
}

# Filings API endpoint
test_filings_api() {
    log_test "Filings API endpoint"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time $TIMEOUT \
        "$BASE_URL/api/v1/filings/?limit=1")

    if [ "$response" = "200" ]; then
        log_pass "Filings API responded successfully"
    else
        log_fail "Filings API returned $response (expected 200)"
    fi
}

# Signals API endpoint
test_signals_api() {
    log_test "Signals API endpoint"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time $TIMEOUT \
        "$BASE_URL/api/v1/signals/types")

    if [ "$response" = "200" ]; then
        log_pass "Signals API responded successfully"
    else
        log_fail "Signals API returned $response (expected 200)"
    fi
}

# WebSocket endpoint
test_websocket() {
    log_test "WebSocket endpoint"

    # Simple connection test using websocat or wscat if available
    if command -v wscat >/dev/null 2>&1; then
        timeout 5 wscat -c "${BASE_URL/http/ws}/ws/filings" --execute "ping" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            log_pass "WebSocket connection successful"
        else
            log_fail "WebSocket connection failed"
        fi
    else
        log_pass "WebSocket test skipped (wscat not installed)"
    fi
}

# Database connectivity
test_database_connection() {
    log_test "Database connectivity"

    response=$(curl -s --max-time $TIMEOUT "$BASE_URL/health")

    if echo "$response" | grep -q '"redis"'; then
        redis_status=$(echo "$response" | grep -o '"redis":"[^"]*"' | cut -d'"' -f4)
        if [ "$redis_status" = "connected" ]; then
            log_pass "Redis connected"
        else
            log_fail "Redis not connected: $redis_status"
        fi
    else
        log_fail "Redis status not found in health check"
    fi
}

# Response time test
test_response_time() {
    log_test "API response time"

    start_time=$(date +%s%N)
    curl -s --max-time $TIMEOUT "$BASE_URL/health" >/dev/null
    end_time=$(date +%s%N)

    response_time=$(( (end_time - start_time) / 1000000 ))

    if [ $response_time -lt 1000 ]; then
        log_pass "Response time: ${response_time}ms (< 1000ms)"
    elif [ $response_time -lt 2000 ]; then
        log_pass "Response time: ${response_time}ms (< 2000ms, acceptable)"
    else
        log_fail "Response time: ${response_time}ms (> 2000ms, too slow)"
    fi
}

# Concurrent connections test
test_concurrent_connections() {
    log_test "Concurrent connections handling"

    local concurrent_requests=10
    local pids=()

    for i in $(seq 1 $concurrent_requests); do
        curl -s --max-time $TIMEOUT "$BASE_URL/health" >/dev/null &
        pids+=($!)
    done

    local failed=0
    for pid in "${pids[@]}"; do
        wait "$pid" || ((failed++))
    done

    if [ $failed -eq 0 ]; then
        log_pass "Handled $concurrent_requests concurrent requests"
    else
        log_fail "$failed/$concurrent_requests concurrent requests failed"
    fi
}

# Error handling test
test_error_handling() {
    log_test "Error handling (404)"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time $TIMEOUT \
        "$BASE_URL/nonexistent/endpoint")

    if [ "$response" = "404" ]; then
        log_pass "404 error handled correctly"
    else
        log_fail "404 error returned $response (expected 404)"
    fi
}

# CORS headers test
test_cors_headers() {
    log_test "CORS headers"

    headers=$(curl -s -I --max-time $TIMEOUT \
        -H "Origin: http://example.com" \
        "$BASE_URL/health")

    if echo "$headers" | grep -q "access-control-allow-origin"; then
        log_pass "CORS headers present"
    else
        log_fail "CORS headers missing"
    fi
}

# Security headers test
test_security_headers() {
    log_test "Security headers"

    headers=$(curl -s -I --max-time $TIMEOUT "$BASE_URL/health")

    if echo "$headers" | grep -q "x-content-type-options"; then
        log_pass "Security headers present"
    else
        log_fail "Security headers missing"
    fi
}

# Wait for service to be ready
wait_for_service() {
    log_test "Waiting for service to be ready..."

    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s --max-time 5 "$BASE_URL/health" >/dev/null 2>&1; then
            log_pass "Service is ready"
            return 0
        fi

        ((retries++))
        echo "Retry $retries/$MAX_RETRIES..."
        sleep 5
    done

    log_fail "Service failed to become ready after $MAX_RETRIES retries"
    exit 1
}

# Print summary
print_summary() {
    echo ""
    echo "================================"
    echo "Smoke Test Summary"
    echo "================================"
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -gt 0 ]; then
        echo ""
        echo "Failed tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}- $test${NC}"
        done
        echo ""
        echo "================================"
        exit 1
    else
        echo ""
        echo "================================"
        echo -e "${GREEN}All smoke tests passed!${NC}"
        echo "================================"
        exit 0
    fi
}

# Main execution
main() {
    echo "================================"
    echo "SEC Latent Smoke Tests"
    echo "Base URL: $BASE_URL"
    echo "================================"

    wait_for_service

    # Run all tests
    test_health_endpoint
    test_root_endpoint
    test_api_docs
    test_filings_api
    test_signals_api
    test_websocket
    test_database_connection
    test_response_time
    test_concurrent_connections
    test_error_handling
    test_cors_headers
    test_security_headers

    print_summary
}

# Run main function
main
