#!/bin/bash
# Automated Rollback Script
# Rolls back deployment to previous stable version

set -e
set -u
set -o pipefail

ENVIRONMENT="${1:-production}"
REASON="${2:-manual rollback}"

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

# Confirm rollback
confirm_rollback() {
    log_warn "==================================="
    log_warn "ROLLBACK REQUESTED"
    log_warn "==================================="
    log_warn "Environment: $ENVIRONMENT"
    log_warn "Reason: $REASON"

    if [ "$ENVIRONMENT" = "production" ]; then
        read -p "Are you sure you want to rollback PRODUCTION? (yes/no): " confirmation
        if [ "$confirmation" != "yes" ]; then
            log_error "Rollback cancelled"
            exit 1
        fi
    fi
}

# Get current deployment version
get_current_version() {
    local current=$(kubectl get deployment sec-latent-backend -n "$ENVIRONMENT" \
        -o jsonpath='{.spec.template.metadata.labels.version}')
    echo "$current"
}

# Get previous stable version
get_previous_version() {
    local previous=$(kubectl rollout history deployment/sec-latent-backend -n "$ENVIRONMENT" \
        | tail -2 | head -1 | awk '{print $1}')
    echo "$previous"
}

# Create pre-rollback backup
create_backup() {
    log_info "Creating pre-rollback database backup..."

    if [ -f "./scripts/backup/backup-database.sh" ]; then
        ./scripts/backup/backup-database.sh "$ENVIRONMENT" "rollback"
        log_info "Backup created successfully"
    else
        log_warn "Backup script not found - skipping backup"
    fi
}

# Switch traffic to blue environment
switch_to_blue() {
    log_info "Switching traffic to blue environment..."

    kubectl patch service sec-latent-backend -n "$ENVIRONMENT" \
        -p '{"spec":{"selector":{"version":"blue"}}}'
    kubectl patch service sec-latent-frontend -n "$ENVIRONMENT" \
        -p '{"spec":{"selector":{"version":"green"}}}'

    log_info "Traffic switched to blue environment"
}

# Scale blue environment
scale_blue_environment() {
    log_info "Scaling blue environment..."

    kubectl scale deployment/sec-latent-backend-blue -n "$ENVIRONMENT" --replicas=3
    kubectl scale deployment/sec-latent-frontend-blue -n "$ENVIRONMENT" --replicas=2
    kubectl scale deployment/sec-latent-worker-blue -n "$ENVIRONMENT" --replicas=2

    # Wait for blue environment to be ready
    kubectl wait --for=condition=available --timeout=300s \
        deployment/sec-latent-backend-blue -n "$ENVIRONMENT"
    kubectl wait --for=condition=available --timeout=300s \
        deployment/sec-latent-frontend-blue -n "$ENVIRONMENT"

    log_info "Blue environment scaled and ready"
}

# Rollback deployments
rollback_deployments() {
    log_info "Rolling back deployments..."

    kubectl rollout undo deployment/sec-latent-backend -n "$ENVIRONMENT"
    kubectl rollout undo deployment/sec-latent-frontend -n "$ENVIRONMENT"
    kubectl rollout undo deployment/sec-latent-worker -n "$ENVIRONMENT"

    # Wait for rollback to complete
    kubectl rollout status deployment/sec-latent-backend -n "$ENVIRONMENT" --timeout=5m
    kubectl rollout status deployment/sec-latent-frontend -n "$ENVIRONMENT" --timeout=5m
    kubectl rollout status deployment/sec-latent-worker -n "$ENVIRONMENT" --timeout=5m

    log_info "Deployments rolled back successfully"
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."

    # Get application URL
    case "$ENVIRONMENT" in
        production)
            APP_URL="https://sec-latent.example.com"
            ;;
        staging)
            APP_URL="https://staging.sec-latent.example.com"
            ;;
        *)
            APP_URL="http://localhost:8000"
            ;;
    esac

    # Run smoke tests
    if [ -f "./scripts/health-checks/smoke-test.sh" ]; then
        ./scripts/health-checks/smoke-test.sh "$APP_URL"
    else
        log_warn "Smoke test script not found"

        # Manual health check
        health_status=$(curl -s "$APP_URL/health" | jq -r '.status')
        if [ "$health_status" = "healthy" ]; then
            log_info "✓ Application health check passed"
        else
            log_error "✗ Application health check failed: $health_status"
            return 1
        fi
    fi

    log_info "Rollback verification passed"
}

# Scale down green environment
scale_down_green() {
    log_info "Scaling down green environment..."

    kubectl scale deployment/sec-latent-backend-green -n "$ENVIRONMENT" --replicas=0
    kubectl scale deployment/sec-latent-frontend-green -n "$ENVIRONMENT" --replicas=0
    kubectl scale deployment/sec-latent-worker-green -n "$ENVIRONMENT" --replicas=0

    log_info "Green environment scaled down"
}

# Notify stakeholders
send_notifications() {
    log_info "Sending notifications..."

    # Slack notification
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"⚠️ Deployment Rollback\",
                \"attachments\": [{
                    \"color\": \"warning\",
                    \"fields\": [
                        {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                        {\"title\": \"Reason\", \"value\": \"$REASON\", \"short\": true},
                        {\"title\": \"Executed By\", \"value\": \"$(whoami)\", \"short\": true},
                        {\"title\": \"Timestamp\", \"value\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"short\": true}
                    ]
                }]
            }"
    fi

    # Sentry notification
    if [ -n "${SENTRY_AUTH_TOKEN:-}" ] && [ -n "${SENTRY_ORG:-}" ]; then
        curl -X POST "https://sentry.io/api/0/organizations/${SENTRY_ORG}/releases/" \
            -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
            -H 'Content-Type: application/json' \
            -d "{
                \"version\": \"rollback-$(date +%Y%m%d-%H%M%S)\",
                \"projects\": [\"sec-latent\"],
                \"environment\": \"$ENVIRONMENT\",
                \"refs\": []
            }"
    fi

    log_info "Notifications sent"
}

# Main rollback procedure
main() {
    log_info "==================================="
    log_info "Starting Rollback Procedure"
    log_info "==================================="

    # Confirm rollback
    confirm_rollback

    # Get version information
    CURRENT_VERSION=$(get_current_version)
    log_info "Current version: $CURRENT_VERSION"

    # Create backup
    create_backup

    # Execute rollback based on environment strategy
    if [ "$ENVIRONMENT" = "production" ]; then
        # Blue-green rollback
        switch_to_blue
        scale_blue_environment
    else
        # Standard rollback
        rollback_deployments
    fi

    # Verify rollback
    if verify_rollback; then
        log_info "✓ Rollback successful"

        # Scale down failed deployment
        if [ "$ENVIRONMENT" = "production" ]; then
            scale_down_green
        fi

        # Send notifications
        send_notifications

        log_info "==================================="
        log_info "Rollback Completed Successfully"
        log_info "==================================="
        exit 0
    else
        log_error "✗ Rollback verification failed"
        log_error "Manual intervention required"
        exit 1
    fi
}

# Execute main procedure
main
