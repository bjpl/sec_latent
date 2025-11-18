#!/bin/bash
# Deployment Monitoring Script
# Monitors application health and metrics during deployment

set -e
set -u

ENVIRONMENT="${1:-staging}"
DURATION="${2:-300}"  # Monitor for 5 minutes by default
INTERVAL=10  # Check every 10 seconds

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')]${NC} $1"
}

# Get application URL based on environment
get_app_url() {
    case "$ENVIRONMENT" in
        production)
            echo "https://sec-latent.example.com"
            ;;
        staging)
            echo "https://staging.sec-latent.example.com"
            ;;
        *)
            echo "http://localhost:8000"
            ;;
    esac
}

APP_URL=$(get_app_url)

# Monitor health endpoint
monitor_health() {
    local response=$(curl -s "${APP_URL}/health" || echo '{"status":"unavailable"}')
    local status=$(echo "$response" | jq -r '.status')

    if [ "$status" = "healthy" ]; then
        log_info "✓ Application healthy"
        return 0
    elif [ "$status" = "degraded" ]; then
        log_warn "⚠ Application degraded"

        # Check which services are unhealthy
        local unhealthy=$(echo "$response" | jq -r '.services | to_entries[] | select(.value.status != "healthy") | .key')
        if [ -n "$unhealthy" ]; then
            log_warn "  Unhealthy services: $unhealthy"
        fi
        return 1
    else
        log_error "✗ Application unhealthy: $status"
        return 2
    fi
}

# Monitor error rate from Prometheus
monitor_error_rate() {
    if ! command -v kubectl &> /dev/null; then
        return 0
    fi

    # Query Prometheus for HTTP 5xx error rate
    local error_rate=$(kubectl exec -n monitoring deployment/prometheus -- \
        curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[1m])' | \
        jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")

    if (( $(echo "$error_rate > 0.05" | bc -l) )); then
        log_error "✗ High error rate: ${error_rate}"
        return 1
    elif (( $(echo "$error_rate > 0.01" | bc -l) )); then
        log_warn "⚠ Elevated error rate: ${error_rate}"
        return 0
    else
        log_info "✓ Error rate normal: ${error_rate}"
        return 0
    fi
}

# Monitor response time
monitor_response_time() {
    local response_time=$(curl -s -o /dev/null -w "%{time_total}" "${APP_URL}/health")
    local response_time_ms=$(echo "$response_time * 1000" | bc)

    if (( $(echo "$response_time_ms > 5000" | bc -l) )); then
        log_error "✗ Slow response: ${response_time_ms}ms"
        return 1
    elif (( $(echo "$response_time_ms > 2000" | bc -l) )); then
        log_warn "⚠ Slow response: ${response_time_ms}ms"
        return 0
    else
        log_info "✓ Response time: ${response_time_ms}ms"
        return 0
    fi
}

# Monitor CPU and memory usage
monitor_resources() {
    if ! command -v kubectl &> /dev/null; then
        return 0
    fi

    local cpu=$(kubectl top pods -n "$ENVIRONMENT" -l app=sec-latent-backend --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum}' || echo "0")
    local memory=$(kubectl top pods -n "$ENVIRONMENT" -l app=sec-latent-backend --no-headers 2>/dev/null | awk '{sum+=$3} END {print sum}' || echo "0")

    if [ -n "$cpu" ] && [ -n "$memory" ]; then
        log_info "✓ Resources - CPU: ${cpu}m, Memory: ${memory}Mi"
    fi

    return 0
}

# Main monitoring loop
main() {
    log_info "==================================="
    log_info "Starting deployment monitoring"
    log_info "Environment: $ENVIRONMENT"
    log_info "Duration: ${DURATION}s"
    log_info "==================================="

    local start_time=$(date +%s)
    local end_time=$((start_time + DURATION))
    local failures=0
    local checks=0

    while [ $(date +%s) -lt $end_time ]; do
        ((checks++))

        log_info "Check #${checks}"

        # Run all monitoring checks
        monitor_health || ((failures++))
        monitor_error_rate || ((failures++))
        monitor_response_time || ((failures++))
        monitor_resources

        echo ""

        # If too many failures, abort
        if [ $failures -gt 5 ]; then
            log_error "Too many failures detected - aborting monitoring"
            exit 1
        fi

        sleep $INTERVAL
    done

    # Summary
    log_info "==================================="
    log_info "Monitoring Summary"
    log_info "==================================="
    log_info "Total checks: $checks"
    log_info "Failures: $failures"

    local failure_rate=$(echo "scale=2; $failures / $checks * 100" | bc)
    log_info "Failure rate: ${failure_rate}%"

    # Deployment is successful if failure rate < 10%
    if (( $(echo "$failure_rate < 10" | bc -l) )); then
        log_info "✓ Deployment monitoring passed"
        exit 0
    else
        log_error "✗ Deployment monitoring failed"
        exit 1
    fi
}

main
