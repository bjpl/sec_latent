# Security Incident Response Playbook

## Overview

This playbook provides step-by-step procedures for responding to security incidents in the SEC Latent Signal Analysis Platform.

## Table of Contents

- [Incident Classification](#incident-classification)
- [Response Team](#response-team)
- [Incident Response Workflow](#incident-response-workflow)
- [Playbooks by Incident Type](#playbooks-by-incident-type)
- [Post-Incident Procedures](#post-incident-procedures)
- [Communication Templates](#communication-templates)

## Incident Classification

### Severity Levels

| Level | Description | Examples | Response Time | Escalation |
|-------|-------------|----------|---------------|------------|
| **P0 - Critical** | System-wide outage, data breach, active attack | Data exfiltration, ransomware, complete system down | Immediate | All hands on deck |
| **P1 - High** | Significant security impact, partial outage | Compromised credentials, DDoS attack, major vulnerability | <15 minutes | On-call + manager |
| **P2 - Medium** | Limited security impact, degraded service | Suspicious activity, minor vulnerability, phishing attempt | <1 hour | On-call engineer |
| **P3 - Low** | Minimal security impact | Policy violation, informational alert | <4 hours | Next business day |

### Incident Categories

1. **Data Breach**: Unauthorized access to sensitive data
2. **System Compromise**: Server/application compromise
3. **Denial of Service**: Service availability attacks
4. **Malware/Ransomware**: Malicious software infection
5. **Insider Threat**: Malicious or negligent insider activity
6. **Phishing/Social Engineering**: Credential theft attempts
7. **API Abuse**: Unauthorized API usage or scraping
8. **Compliance Violation**: Regulatory compliance breach

## Response Team

### Incident Response Team (IRT)

| Role | Responsibilities | Contact |
|------|------------------|---------|
| **Incident Commander** | Overall response coordination | On-call rotation |
| **Security Lead** | Security analysis and containment | security@company.com |
| **Engineering Lead** | Technical investigation and remediation | engineering@company.com |
| **Communications Lead** | Stakeholder communication | comms@company.com |
| **Compliance Officer** | Regulatory requirements | compliance@company.com |
| **Legal Counsel** | Legal implications | legal@company.com |

### On-Call Rotation

- **Primary**: Immediate response
- **Secondary**: Backup if primary unavailable
- **Escalation**: Manager/Director if no response in 15 minutes

### Contact Methods

- **PagerDuty**: Primary alert system
- **Slack**: #incident-response channel
- **Phone**: Emergency hotline +1-555-HELP-NOW
- **Email**: security-incidents@company.com

## Incident Response Workflow

```
┌─────────────────────────────────────────────┐
│         INCIDENT DETECTION                  │
│  (Automated alerts, manual reporting)       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         1. INITIAL ASSESSMENT               │
│  • Verify incident                          │
│  • Classify severity                        │
│  • Create incident ticket                   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         2. MOBILIZE TEAM                    │
│  • Page incident commander                  │
│  • Create incident channel                  │
│  • Notify stakeholders                      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         3. CONTAINMENT                      │
│  • Isolate affected systems                 │
│  • Block malicious activity                 │
│  • Preserve evidence                        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         4. INVESTIGATION                    │
│  • Root cause analysis                      │
│  • Scope determination                      │
│  • Timeline reconstruction                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         5. ERADICATION                      │
│  • Remove malicious access                  │
│  • Patch vulnerabilities                    │
│  • Verify complete removal                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         6. RECOVERY                         │
│  • Restore systems from clean backups       │
│  • Verify system integrity                  │
│  • Return to normal operations              │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         7. POST-INCIDENT                    │
│  • Post-mortem analysis                     │
│  • Lessons learned                          │
│  • Implement improvements                   │
└─────────────────────────────────────────────┘
```

## Playbooks by Incident Type

### 1. Data Breach Response

**Scenario**: Unauthorized access to customer data detected

**Immediate Actions (0-15 minutes):**

1. **Verify the Breach**
   ```bash
   # Check audit logs
   kubectl logs -l app=api --since=24h | grep "unauthorized"

   # Query database access logs
   SELECT * FROM pg_stat_activity WHERE usename NOT IN ('app_user', 'readonly');
   ```

2. **Containment**
   ```bash
   # Revoke all active sessions
   redis-cli FLUSHDB

   # Disable compromised API keys
   curl -X POST https://api.sec-analysis.com/admin/api-keys/revoke-all

   # Enable enhanced monitoring
   kubectl set env deployment/api SECURITY_LEVEL=HIGH
   ```

3. **Evidence Preservation**
   ```bash
   # Export relevant logs
   kubectl logs deployment/api > incident-logs-$(date +%Y%m%d).log

   # Database snapshot
   pg_dump $DATABASE_URL > db-snapshot-$(date +%Y%m%d).sql

   # Upload to secure storage
   aws s3 cp incident-logs-$(date +%Y%m%d).log s3://incident-evidence/
   ```

**Investigation (15 minutes - 4 hours):**

4. **Determine Scope**
   ```sql
   -- Identify affected users
   SELECT DISTINCT user_id, accessed_at, ip_address
   FROM audit_logs
   WHERE event_type IN ('data_access', 'data_export')
   AND accessed_at > '2025-10-18 00:00:00'
   AND (ip_address NOT IN (SELECT ip FROM known_ips) OR user_agent LIKE '%bot%');

   -- Count affected records
   SELECT COUNT(DISTINCT user_id) as affected_users,
          COUNT(*) as total_accesses
   FROM audit_logs
   WHERE ...
   ```

5. **Root Cause Analysis**
   - Review authentication logs for credential compromise
   - Check for SQL injection or XSS vulnerabilities
   - Analyze network traffic for data exfiltration
   - Verify encryption status of data at rest and in transit

**Eradication & Recovery (4 hours - 1 day):**

6. **Remediate Vulnerabilities**
   ```bash
   # Rotate all secrets
   ./scripts/rotate-secrets.sh

   # Force password reset for all users
   curl -X POST https://api.sec-analysis.com/admin/users/force-password-reset

   # Deploy security patches
   kubectl apply -f k8s/security-patches/
   ```

7. **Notification** (within 72 hours of discovery for GDPR)
   - Data Protection Authority
   - Affected users
   - Internal stakeholders
   - See [Communication Templates](#communication-templates)

**Post-Incident (1-7 days):**

8. **Documentation**
   - Complete incident report
   - Timeline of events
   - Lessons learned
   - Remediation actions taken

### 2. Compromised API Key

**Scenario**: API key detected in public repository or suspicious usage

**Immediate Actions:**

1. **Verify Compromise**
   ```bash
   # Check key usage
   curl https://api.sec-analysis.com/admin/api-keys/usage/$KEY_ID

   # Look for unusual patterns
   # - Requests from unfamiliar IPs
   # - High request volume
   # - Access to sensitive endpoints
   ```

2. **Revoke Key**
   ```bash
   # Immediate revocation
   curl -X DELETE https://api.sec-analysis.com/auth/api-keys/$KEY_ID \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

3. **Assess Impact**
   ```sql
   -- Query all actions taken with compromised key
   SELECT *
   FROM audit_logs
   WHERE api_key_id = 'compromised_key_id'
   ORDER BY created_at DESC;
   ```

4. **Notify Key Owner**
   ```
   Subject: URGENT: API Key Security Alert

   Your API key (slat_v1_abc123...) has been compromised and revoked.

   Actions taken:
   - Key immediately revoked
   - All associated sessions terminated

   Next steps:
   - Review usage logs (link)
   - Generate new API key (link)
   - Update applications with new key

   Please respond within 1 hour to confirm receipt.
   ```

**Recovery:**

5. **Generate Replacement Key**
   - User generates new key through secure channel
   - Implement enhanced monitoring for new key
   - Document incident in user account

### 3. DDoS Attack Response

**Scenario**: Sustained high-volume traffic targeting API

**Immediate Actions:**

1. **Verify Attack**
   ```bash
   # Check request rate
   kubectl top pods -l app=api

   # Analyze traffic patterns
   redis-cli --scan --pattern "rate_limit:*" | wc -l
   ```

2. **Enable DDoS Protection**
   ```bash
   # Activate Cloudflare "I'm Under Attack" mode
   # Via API or dashboard

   # Implement strict rate limiting
   kubectl set env deployment/api RATE_LIMIT_STRICT=true

   # Enable CAPTCHA challenges
   kubectl apply -f k8s/ddos-protection.yaml
   ```

3. **Traffic Analysis**
   ```bash
   # Identify attack sources
   kubectl logs -l app=api | grep "429\|503" | \
     awk '{print $1}' | sort | uniq -c | sort -rn | head -20

   # Block top offenders
   for ip in $(top_offender_ips); do
     iptables -A INPUT -s $ip -j DROP
   done
   ```

**Mitigation:**

4. **Scale Infrastructure**
   ```bash
   # Auto-scale API pods
   kubectl autoscale deployment api --min=10 --max=50 --cpu-percent=70

   # Scale worker capacity
   kubectl scale deployment celery-worker --replicas=20
   ```

5. **Geo-Blocking** (if attack from specific region)
   ```bash
   # Block traffic from attack region via Cloudflare
   # Rules → Firewall Rules → Add Rule
   # Expression: (ip.geoip.country eq "XX")
   # Action: Block
   ```

**Recovery:**

6. **Gradual Restoration**
   - Monitor attack cessation
   - Gradually reduce rate limits
   - Disable CAPTCHA challenges
   - Return to normal configuration

### 4. Insider Threat Response

**Scenario**: Suspicious activity by internal user/employee

**Immediate Actions:**

1. **Document Suspicion**
   - Record date/time of suspicious activity
   - Collect evidence (logs, screenshots, reports)
   - Determine severity and scope

2. **Preserve Evidence**
   ```bash
   # Export user's complete activity log
   python scripts/export_user_activity.py --user-id $USER_ID \
     --from-date "2025-10-01" --to-date "2025-10-18"

   # Backup user's data access history
   pg_dump -t audit_logs --where="user_id='$USER_ID'" > insider-evidence.sql
   ```

3. **Contain (if actively malicious)**
   ```bash
   # Suspend user account
   curl -X POST https://api.sec-analysis.com/admin/users/$USER_ID/suspend \
     -H "Authorization: Bearer $ADMIN_TOKEN"

   # Revoke all API keys
   curl -X POST https://api.sec-analysis.com/admin/users/$USER_ID/revoke-keys

   # Terminate all sessions
   redis-cli DEL "session:$USER_ID:*"
   ```

**Investigation:**

4. **Coordinate with Legal/HR**
   - Inform legal counsel BEFORE confronting employee
   - Involve HR for employment-related actions
   - Ensure compliance with employment laws

5. **Forensic Analysis**
   ```sql
   -- Unusual data access
   SELECT resource, action, COUNT(*) as access_count
   FROM audit_logs
   WHERE user_id = $USER_ID
   AND created_at > NOW() - INTERVAL '30 days'
   GROUP BY resource, action
   ORDER BY access_count DESC;

   -- After-hours activity
   SELECT DATE_TRUNC('hour', created_at) as hour, COUNT(*) as activity
   FROM audit_logs
   WHERE user_id = $USER_ID
   AND EXTRACT(HOUR FROM created_at) NOT BETWEEN 9 AND 18
   GROUP BY hour;

   -- Data exfiltration attempts
   SELECT *
   FROM audit_logs
   WHERE user_id = $USER_ID
   AND event_type IN ('data_export', 'bulk_download')
   ORDER BY created_at DESC;
   ```

**Resolution:**

6. **Appropriate Action**
   - Warning/coaching (unintentional violation)
   - Suspension (pending investigation)
   - Termination (malicious activity)
   - Law enforcement referral (criminal activity)

## Post-Incident Procedures

### Post-Mortem Meeting

**Timeline**: Within 5 business days of incident resolution

**Attendees**:
- Incident Commander
- Response team members
- Affected service owners
- Management

**Agenda**:
1. Incident timeline and facts
2. What went well
3. What could be improved
4. Action items and owners
5. Documentation and knowledge sharing

### Post-Mortem Template

```markdown
# Incident Post-Mortem: [Incident Title]

## Overview
- **Incident ID**: INC-2025-10-18-001
- **Date**: 2025-10-18
- **Duration**: 4 hours 23 minutes
- **Severity**: P0
- **Incident Commander**: Name
- **Status**: Resolved

## Timeline
| Time | Event |
|------|-------|
| 10:00 | Incident detected via monitoring alert |
| 10:05 | Incident commander paged |
| 10:15 | Response team assembled |
| 10:30 | Containment actions completed |
| 12:00 | Root cause identified |
| 13:00 | Fix deployed |
| 14:23 | Incident resolved |

## Impact
- **Users Affected**: 1,250 users
- **Services Affected**: API, Signal Extraction
- **Data Impact**: No data loss
- **Financial Impact**: Estimated $5,000 in revenue loss

## Root Cause
Detailed explanation of what caused the incident...

## Resolution
Steps taken to resolve the incident...

## What Went Well
- Fast detection (5 minutes)
- Clear communication
- Effective containment

## What Could Be Improved
- Automated rollback not triggered
- Missing runbook for this scenario
- Monitoring gaps identified

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Implement automated rollback | Engineering | 2025-10-25 | In Progress |
| Create runbook | DevOps | 2025-10-20 | Complete |
| Add monitoring for X | SRE | 2025-10-22 | Pending |

## Lessons Learned
Key takeaways for future incident prevention...
```

### Follow-Up Actions

1. **Implement Improvements**
   - Update runbooks with lessons learned
   - Add missing monitoring and alerts
   - Patch identified vulnerabilities
   - Improve automation

2. **Knowledge Sharing**
   - Share post-mortem with broader team
   - Update documentation
   - Conduct training sessions if needed

3. **Verify Effectiveness**
   - Test improvements
   - Conduct tabletop exercises
   - Review in next security meeting

## Communication Templates

### Internal Notification (Slack)

```
🚨 SECURITY INCIDENT - P0

Incident: Data Breach Detected
ID: INC-2025-10-18-001
Severity: P0 (Critical)
Status: Investigating

Impact:
- Unauthorized access to customer data
- 1,250 potentially affected users
- API service degraded

Actions Taken:
✅ All sessions revoked
✅ Compromised keys disabled
✅ Enhanced monitoring enabled

Incident Channel: #incident-2025-10-18-001
Incident Commander: @john.doe

Updates will be posted every 30 minutes.
```

### Customer Notification (Email)

```
Subject: Important Security Update

Dear Valued Customer,

We are writing to inform you of a security incident that may have affected your account.

What Happened:
On October 18, 2025, we detected unauthorized access to our systems. Our security team immediately took action to contain the incident and protect your data.

What Information Was Involved:
- Account email addresses
- Usage history (filings accessed)
- No payment information was accessed

What We're Doing:
- Implemented additional security measures
- Conducting thorough investigation
- Enhanced monitoring and alerts
- Working with cybersecurity experts

What You Should Do:
1. Reset your password (required)
2. Review recent account activity
3. Enable multi-factor authentication
4. Monitor for suspicious emails

We take this matter very seriously and apologize for any concern this may cause. If you have questions, please contact our security team at security@company.com.

Sincerely,
[Company Name] Security Team
```

### Regulatory Notification (GDPR)

```
[To: Data Protection Authority]

Subject: Personal Data Breach Notification pursuant to Article 33 GDPR

1. Describe the nature of the personal data breach
2. Name and contact details of the data protection officer
3. Describe the likely consequences of the breach
4. Describe the measures taken or proposed to address the breach

[Complete with specific incident details]
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Security Team
**Review Cycle**: Quarterly

**EMERGENCY CONTACTS**:
- **Security Hotline**: +1-555-SECURITY
- **On-Call**: PagerDuty rotation
- **Email**: security-incidents@company.com
