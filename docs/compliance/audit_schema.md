# Audit Trail Schema and Implementation

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Owner:** Compliance Analyst
**Classification:** Internal

## Executive Summary

This document defines the comprehensive audit trail schema for the sec_latent project, ensuring compliance with SOC 2, FINRA, SEC, GDPR, and CCPA audit requirements. The schema supports immutable logging, data lineage tracking, and regulatory reporting.

---

## 1. Audit Trail Requirements Summary

### 1.1 Regulatory Requirements Matrix
| Framework | Retention Period | Key Requirements | Critical Fields |
|-----------|-----------------|------------------|----------------|
| SOC 2 | 1+ years | System access, changes, incidents | User, action, timestamp, outcome |
| FINRA Rule 4510 | 6 years | Complete order lifecycle, communications | Order ID, timestamps, parties, status |
| SEC Reg SCI | 5 years | SCI events, capacity tests, changes | Event type, impact, resolution, timeline |
| GDPR Art. 30 | Ongoing | Processing activities, data flows | Purpose, legal basis, recipients, retention |
| CCPA §1798.145 | 24 months | Consumer requests, responses | Request type, verification, response date |

### 1.2 Audit Objectives
- **Accountability:** Attribute every action to a specific user or system
- **Non-repudiation:** Prevent denial of actions through cryptographic signatures
- **Forensic analysis:** Support incident investigation and root cause analysis
- **Regulatory compliance:** Meet all retention and reporting requirements
- **Data lineage:** Track data from creation through deletion
- **Performance:** Support high-volume logging without system degradation

---

## 2. Core Audit Schema

### 2.1 Universal Audit Event Structure

```json
{
  "audit_id": "string (UUID v7)",
  "timestamp": "string (ISO 8601 with microseconds)",
  "event_type": "string (enum)",
  "category": "string (enum)",
  "severity": "string (enum: INFO, WARNING, ERROR, CRITICAL)",
  "actor": {
    "id": "string (UUID)",
    "type": "string (enum: USER, SERVICE, SYSTEM, API)",
    "name": "string",
    "email": "string (nullable)",
    "ip_address": "string (IPv4/IPv6)",
    "user_agent": "string (nullable)",
    "session_id": "string (UUID, nullable)"
  },
  "resource": {
    "id": "string",
    "type": "string (enum)",
    "name": "string",
    "parent_id": "string (nullable)",
    "classification": "string (enum: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)"
  },
  "action": {
    "operation": "string (enum: CREATE, READ, UPDATE, DELETE, EXECUTE, APPROVE, REJECT)",
    "method": "string (HTTP method for API calls)",
    "endpoint": "string (API endpoint)",
    "status_code": "integer (HTTP status code)",
    "outcome": "string (enum: SUCCESS, FAILURE, PARTIAL)",
    "error_message": "string (nullable)"
  },
  "context": {
    "request_id": "string (UUID)",
    "correlation_id": "string (UUID)",
    "trace_id": "string (distributed tracing ID)",
    "environment": "string (enum: PRODUCTION, STAGING, DEVELOPMENT)",
    "service": "string",
    "version": "string"
  },
  "changes": {
    "before": "object (nullable, previous state)",
    "after": "object (nullable, new state)",
    "diff": "object (nullable, computed differences)"
  },
  "metadata": {
    "compliance_tags": ["string"],
    "retention_policy": "string",
    "data_classification": "string",
    "encryption_status": "boolean",
    "signature": "string (HMAC-SHA256)"
  }
}
```

### 2.2 Event Type Taxonomy

#### Authentication Events (AUTH)
- `AUTH.LOGIN` - User login attempt
- `AUTH.LOGOUT` - User logout
- `AUTH.MFA_CHALLENGE` - MFA challenge issued
- `AUTH.MFA_SUCCESS` - MFA verification successful
- `AUTH.MFA_FAILURE` - MFA verification failed
- `AUTH.SESSION_CREATED` - Session established
- `AUTH.SESSION_EXPIRED` - Session timeout
- `AUTH.TOKEN_ISSUED` - API token issued
- `AUTH.TOKEN_REVOKED` - API token revoked
- `AUTH.PASSWORD_CHANGE` - Password changed
- `AUTH.PASSWORD_RESET` - Password reset requested

#### Access Control Events (ACCESS)
- `ACCESS.PERMISSION_GRANTED` - Permission granted to user
- `ACCESS.PERMISSION_REVOKED` - Permission revoked
- `ACCESS.ROLE_ASSIGNED` - Role assigned to user
- `ACCESS.ROLE_REMOVED` - Role removed from user
- `ACCESS.DENIED` - Access denied (authorization failure)
- `ACCESS.ESCALATION` - Privilege escalation attempt
- `ACCESS.REVIEW_COMPLETED` - Access review completed

#### Data Events (DATA)
- `DATA.CREATED` - Data record created
- `DATA.READ` - Data record accessed
- `DATA.UPDATED` - Data record modified
- `DATA.DELETED` - Data record deleted (soft or hard)
- `DATA.EXPORTED` - Data exported
- `DATA.IMPORTED` - Data imported
- `DATA.ENCRYPTED` - Data encrypted
- `DATA.DECRYPTED` - Data decrypted
- `DATA.CLASSIFIED` - Data classification assigned
- `DATA.ANONYMIZED` - Data anonymized or pseudonymized

#### Privacy Events (PRIVACY)
- `PRIVACY.CONSENT_GIVEN` - User consent granted
- `PRIVACY.CONSENT_WITHDRAWN` - User consent withdrawn
- `PRIVACY.ACCESS_REQUEST` - GDPR/CCPA access request received
- `PRIVACY.DELETION_REQUEST` - GDPR/CCPA deletion request received
- `PRIVACY.RECTIFICATION_REQUEST` - GDPR rectification request
- `PRIVACY.PORTABILITY_REQUEST` - GDPR portability request
- `PRIVACY.OBJECTION_REQUEST` - GDPR objection to processing
- `PRIVACY.OPTOUT_REQUEST` - CCPA opt-out of sale
- `PRIVACY.REQUEST_VERIFIED` - Identity verification completed
- `PRIVACY.REQUEST_COMPLETED` - Request fulfilled

#### Security Events (SECURITY)
- `SECURITY.INCIDENT_DETECTED` - Security incident detected
- `SECURITY.INCIDENT_RESOLVED` - Security incident resolved
- `SECURITY.VULNERABILITY_FOUND` - Vulnerability discovered
- `SECURITY.VULNERABILITY_PATCHED` - Vulnerability remediated
- `SECURITY.SCAN_COMPLETED` - Security scan completed
- `SECURITY.BREACH_SUSPECTED` - Potential data breach
- `SECURITY.BREACH_CONFIRMED` - Data breach confirmed
- `SECURITY.NOTIFICATION_SENT` - Breach notification sent
- `SECURITY.FIREWALL_RULE_CHANGED` - Firewall rule modified
- `SECURITY.ENCRYPTION_KEY_ROTATED` - Encryption key rotation

#### Financial/Trading Events (TRADING)
- `TRADING.ORDER_CREATED` - Order created
- `TRADING.ORDER_MODIFIED` - Order modified
- `TRADING.ORDER_CANCELLED` - Order cancelled
- `TRADING.ORDER_EXECUTED` - Order executed
- `TRADING.ORDER_REJECTED` - Order rejected
- `TRADING.TRADE_CONFIRMED` - Trade confirmation generated
- `TRADING.SETTLEMENT_INITIATED` - Settlement process started
- `TRADING.SETTLEMENT_COMPLETED` - Settlement completed
- `TRADING.RISK_LIMIT_BREACH` - Risk limit exceeded
- `TRADING.SUSPICIOUS_ACTIVITY` - Suspicious trading activity

#### System Events (SYSTEM)
- `SYSTEM.STARTUP` - System/service started
- `SYSTEM.SHUTDOWN` - System/service stopped
- `SYSTEM.CONFIGURATION_CHANGE` - Configuration modified
- `SYSTEM.DEPLOYMENT` - Code deployment
- `SYSTEM.BACKUP_STARTED` - Backup initiated
- `SYSTEM.BACKUP_COMPLETED` - Backup completed
- `SYSTEM.RESTORE_INITIATED` - Restore from backup started
- `SYSTEM.CAPACITY_TEST` - Capacity testing performed
- `SYSTEM.FAILOVER` - System failover executed
- `SYSTEM.MAINTENANCE_MODE` - Maintenance mode enabled/disabled

#### Compliance Events (COMPLIANCE)
- `COMPLIANCE.CONTROL_TEST` - Control testing performed
- `COMPLIANCE.AUDIT_STARTED` - Audit initiated
- `COMPLIANCE.AUDIT_COMPLETED` - Audit completed
- `COMPLIANCE.POLICY_UPDATED` - Compliance policy updated
- `COMPLIANCE.TRAINING_COMPLETED` - Compliance training completed
- `COMPLIANCE.VIOLATION_DETECTED` - Compliance violation detected
- `COMPLIANCE.REPORT_GENERATED` - Regulatory report generated
- `COMPLIANCE.REPORT_FILED` - Regulatory report filed

---

## 3. Specialized Audit Schemas

### 3.1 FINRA Order Audit Trail Schema

```json
{
  "audit_id": "string (UUID v7)",
  "timestamp": "string (ISO 8601 microsecond precision)",
  "event_type": "TRADING.*",
  "order": {
    "order_id": "string",
    "client_order_id": "string",
    "parent_order_id": "string (nullable)",
    "account_id": "string",
    "account_type": "string (enum: CASH, MARGIN, IRA, etc.)",
    "symbol": "string",
    "security_type": "string (enum: EQUITY, OPTION, BOND, etc.)",
    "side": "string (enum: BUY, SELL, SHORT)",
    "quantity": "decimal",
    "order_type": "string (enum: MARKET, LIMIT, STOP, STOP_LIMIT)",
    "limit_price": "decimal (nullable)",
    "stop_price": "decimal (nullable)",
    "time_in_force": "string (enum: DAY, GTC, IOC, FOK)",
    "order_status": "string (enum: NEW, PARTIAL, FILLED, CANCELLED, REJECTED)",
    "routing_destination": "string",
    "execution_venue": "string"
  },
  "execution": {
    "execution_id": "string (nullable)",
    "trade_id": "string (nullable)",
    "execution_timestamp": "string (ISO 8601, nullable)",
    "executed_quantity": "decimal (nullable)",
    "execution_price": "decimal (nullable)",
    "commission": "decimal (nullable)",
    "fees": "decimal (nullable)",
    "contra_broker": "string (nullable)"
  },
  "supervision": {
    "reviewer_id": "string (nullable)",
    "review_timestamp": "string (ISO 8601, nullable)",
    "exception_flag": "boolean",
    "exception_reason": "string (nullable)",
    "approval_required": "boolean",
    "approval_status": "string (enum: PENDING, APPROVED, REJECTED, nullable)"
  },
  "compliance": {
    "best_execution_review": "boolean",
    "trade_surveillance_flag": "boolean",
    "suspicious_activity_flag": "boolean",
    "regulatory_tags": ["string"]
  }
}
```

### 3.2 SEC Reg SCI Event Schema

```json
{
  "audit_id": "string (UUID v7)",
  "timestamp": "string (ISO 8601 microsecond precision)",
  "event_type": "SYSTEM.*",
  "sci_classification": "string (enum: SYSTEMS_COMPLIANCE_ISSUE, SYSTEMS_DISRUPTION, SYSTEMS_INTRUSION, INDIRECT_SCI_EVENT)",
  "severity": "string (enum: CRITICAL, MAJOR, MINOR)",
  "systems_affected": [{
    "system_name": "string",
    "system_type": "string (enum: SCI_SYSTEM, SUPPORT_SYSTEM)",
    "impact_level": "string (enum: HIGH, MEDIUM, LOW)"
  }],
  "incident": {
    "detection_timestamp": "string (ISO 8601)",
    "resolution_timestamp": "string (ISO 8601, nullable)",
    "duration_seconds": "integer",
    "root_cause": "string",
    "corrective_action": "string",
    "impact_assessment": "string"
  },
  "notification": {
    "notification_required": "boolean",
    "notification_sent": "boolean",
    "notification_timestamp": "string (ISO 8601, nullable)",
    "notification_method": "string (enum: EMAIL, FORM, PHONE)",
    "recipient": "string"
  },
  "capacity_test": {
    "test_type": "string (enum: STRESS, PERFORMANCE, FAILOVER, nullable)",
    "test_result": "string (enum: PASS, FAIL, PARTIAL, nullable)",
    "metrics": "object (nullable)"
  }
}
```

### 3.3 GDPR Processing Activity Schema

```json
{
  "audit_id": "string (UUID v7)",
  "timestamp": "string (ISO 8601 microsecond precision)",
  "event_type": "DATA.* or PRIVACY.*",
  "processing_activity": {
    "activity_id": "string",
    "activity_name": "string",
    "controller": "string",
    "processor": "string (nullable)",
    "dpo_contact": "string"
  },
  "data_subjects": {
    "categories": ["string (e.g., customers, employees, prospects)"],
    "count_estimate": "integer (nullable)"
  },
  "personal_data": {
    "categories": ["string (e.g., name, email, financial data)"],
    "special_categories": ["string (e.g., health, biometric)"],
    "data_origin": "string"
  },
  "purpose": {
    "processing_purpose": "string",
    "legal_basis": "string (enum: CONSENT, CONTRACT, LEGAL_OBLIGATION, VITAL_INTEREST, PUBLIC_INTEREST, LEGITIMATE_INTEREST)",
    "legitimate_interest": "string (nullable)"
  },
  "recipients": {
    "categories": ["string (e.g., service providers, affiliates)"],
    "third_country_transfers": [{
      "country": "string",
      "safeguard": "string (enum: ADEQUACY_DECISION, STANDARD_CLAUSES, BCR, DEROGATION)"
    }]
  },
  "retention": {
    "retention_period": "string",
    "deletion_date": "string (ISO 8601, nullable)",
    "retention_justification": "string"
  },
  "security_measures": {
    "technical_measures": ["string"],
    "organizational_measures": ["string"],
    "encryption": "boolean",
    "pseudonymization": "boolean"
  }
}
```

### 3.4 CCPA Consumer Request Schema

```json
{
  "audit_id": "string (UUID v7)",
  "timestamp": "string (ISO 8601 microsecond precision)",
  "event_type": "PRIVACY.*",
  "request": {
    "request_id": "string",
    "request_type": "string (enum: ACCESS, DELETION, OPTOUT, DO_NOT_SELL)",
    "submission_method": "string (enum: WEB_FORM, EMAIL, PHONE, MAIL)",
    "submission_timestamp": "string (ISO 8601)"
  },
  "consumer": {
    "consumer_id": "string (nullable)",
    "email": "string",
    "name": "string",
    "authorized_agent": "boolean",
    "agent_documentation": "string (nullable)"
  },
  "verification": {
    "verification_method": "string (enum: EMAIL, PHONE, KNOWLEDGE_BASED, TWO_FACTOR)",
    "verification_attempts": "integer",
    "verification_status": "string (enum: PENDING, VERIFIED, FAILED)",
    "verification_timestamp": "string (ISO 8601, nullable)"
  },
  "processing": {
    "assigned_to": "string",
    "status": "string (enum: RECEIVED, IN_PROGRESS, COMPLETED, DENIED, EXTENDED)",
    "response_due_date": "string (ISO 8601)",
    "response_date": "string (ISO 8601, nullable)",
    "extension_granted": "boolean",
    "extension_reason": "string (nullable)",
    "denial_reason": "string (nullable)"
  },
  "data_disclosed": {
    "categories": ["string"],
    "sources": ["string"],
    "business_purposes": ["string"],
    "third_parties": ["string"],
    "data_package_url": "string (nullable)"
  }
}
```

---

## 4. Data Lineage Tracking

### 4.1 Lineage Event Schema

```json
{
  "lineage_id": "string (UUID v7)",
  "timestamp": "string (ISO 8601 microsecond precision)",
  "data_entity": {
    "entity_id": "string",
    "entity_type": "string (enum: DATASET, TABLE, FILE, FIELD, RECORD)",
    "name": "string",
    "schema": "string (nullable)"
  },
  "operation": {
    "operation_type": "string (enum: INGESTION, TRANSFORMATION, AGGREGATION, EXPORT, DELETION)",
    "operation_id": "string",
    "job_id": "string (nullable)",
    "pipeline": "string (nullable)"
  },
  "upstream": [{
    "entity_id": "string",
    "entity_type": "string",
    "name": "string"
  }],
  "downstream": [{
    "entity_id": "string",
    "entity_type": "string",
    "name": "string"
  }],
  "transformation": {
    "logic": "string",
    "version": "string",
    "quality_checks": [{
      "check_name": "string",
      "result": "string (enum: PASS, FAIL)",
      "details": "string"
    }]
  },
  "metadata": {
    "row_count": "integer",
    "size_bytes": "integer",
    "data_quality_score": "decimal",
    "pii_fields": ["string"],
    "sensitive": "boolean"
  }
}
```

### 4.2 Lineage Graph Construction

**Graph Model:**
```
Node Types:
- DataSource (databases, APIs, files)
- DataEntity (tables, datasets, files)
- Transformation (ETL jobs, queries)
- Consumer (applications, reports, users)

Edge Types:
- READS (entity → transformation)
- WRITES (transformation → entity)
- DERIVES (entity → entity via transformation)
- CONSUMES (consumer → entity)

Properties:
- timestamp
- operation_id
- data_volume
- latency
- quality_score
```

---

## 5. Audit Storage and Retention

### 5.1 Storage Architecture

**Primary Storage:**
- PostgreSQL for structured audit events (hot data, last 90 days)
- Optimized for real-time queries and compliance reporting
- Partitioned by date for efficient querying and archival

**Long-term Storage:**
- AWS S3 for archived audit logs (warm/cold data, >90 days)
- Compressed and encrypted with lifecycle policies
- Glacier for deep archive (>3 years)

**Search and Analytics:**
- Elasticsearch for full-text search and real-time analytics
- 90-day retention in hot tier
- Kibana dashboards for visualization

**Immutable Backup:**
- Write-once-read-many (WORM) storage for compliance evidence
- Cross-region replication for disaster recovery
- Legal hold capability for litigation support

### 5.2 Retention Policies

| Event Category | Hot Storage | Warm Storage | Cold Storage | Total Retention | Compliance Driver |
|---------------|-------------|--------------|--------------|----------------|-------------------|
| Authentication | 90 days | 1 year | 6 years | 7 years | SOC 2, SEC |
| Access Control | 90 days | 1 year | 6 years | 7 years | SOC 2, SEC |
| Data Operations | 90 days | 6 months | 6.5 years | 7 years | GDPR, SOC 2 |
| Trading/Orders | 90 days | 1 year | 5 years | 6 years | FINRA Rule 4510 |
| SCI Events | 90 days | 1 year | 4 years | 5 years | SEC Reg SCI |
| Privacy Requests | 90 days | 21 months | N/A | 24 months | CCPA |
| Security Incidents | 90 days | 1 year | 6 years | 7 years | SOC 2, SEC |
| System Changes | 90 days | 1 year | 6 years | 7 years | SOC 2, FINRA |

### 5.3 Database Schema (PostgreSQL)

```sql
-- Main audit events table (partitioned by month)
CREATE TABLE audit_events (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,

    -- Actor information
    actor_id UUID,
    actor_type VARCHAR(50),
    actor_name VARCHAR(255),
    actor_email VARCHAR(255),
    actor_ip INET,
    actor_user_agent TEXT,
    session_id UUID,

    -- Resource information
    resource_id VARCHAR(255),
    resource_type VARCHAR(100),
    resource_name VARCHAR(255),
    resource_parent_id VARCHAR(255),
    resource_classification VARCHAR(50),

    -- Action details
    action_operation VARCHAR(50),
    action_method VARCHAR(10),
    action_endpoint TEXT,
    action_status_code INTEGER,
    action_outcome VARCHAR(20),
    action_error_message TEXT,

    -- Context
    request_id UUID,
    correlation_id UUID,
    trace_id VARCHAR(255),
    environment VARCHAR(20),
    service VARCHAR(100),
    version VARCHAR(50),

    -- Changes (JSONB for flexibility)
    changes_before JSONB,
    changes_after JSONB,
    changes_diff JSONB,

    -- Metadata
    compliance_tags TEXT[],
    retention_policy VARCHAR(50),
    data_classification VARCHAR(50),
    encryption_status BOOLEAN,
    signature VARCHAR(512),

    -- Additional data
    additional_data JSONB
) PARTITION BY RANGE (timestamp);

-- Indexes for performance
CREATE INDEX idx_audit_timestamp ON audit_events (timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_events (event_type);
CREATE INDEX idx_audit_actor_id ON audit_events (actor_id);
CREATE INDEX idx_audit_resource_id ON audit_events (resource_id);
CREATE INDEX idx_audit_correlation_id ON audit_events (correlation_id);
CREATE INDEX idx_audit_compliance_tags ON audit_events USING GIN (compliance_tags);
CREATE INDEX idx_audit_additional_data ON audit_events USING GIN (additional_data);

-- Specialized tables for regulatory requirements

-- FINRA order audit trail
CREATE TABLE finra_order_audit (
    audit_id UUID PRIMARY KEY REFERENCES audit_events(audit_id),
    order_id VARCHAR(255) NOT NULL,
    client_order_id VARCHAR(255),
    account_id VARCHAR(255) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    routing_destination VARCHAR(100),
    execution_venue VARCHAR(100),
    execution_id VARCHAR(255),
    execution_timestamp TIMESTAMPTZ,
    execution_price DECIMAL(18, 8),
    commission DECIMAL(18, 8),
    reviewer_id UUID,
    exception_flag BOOLEAN DEFAULT FALSE,
    additional_data JSONB
);

CREATE INDEX idx_finra_order_id ON finra_order_audit (order_id);
CREATE INDEX idx_finra_account_id ON finra_order_audit (account_id);
CREATE INDEX idx_finra_symbol ON finra_order_audit (symbol);
CREATE INDEX idx_finra_exception_flag ON finra_order_audit (exception_flag) WHERE exception_flag = TRUE;

-- SEC SCI events
CREATE TABLE sec_sci_events (
    audit_id UUID PRIMARY KEY REFERENCES audit_events(audit_id),
    sci_classification VARCHAR(50) NOT NULL,
    systems_affected JSONB NOT NULL,
    detection_timestamp TIMESTAMPTZ NOT NULL,
    resolution_timestamp TIMESTAMPTZ,
    duration_seconds INTEGER,
    root_cause TEXT,
    corrective_action TEXT,
    impact_assessment TEXT,
    notification_required BOOLEAN DEFAULT FALSE,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_timestamp TIMESTAMPTZ,
    additional_data JSONB
);

CREATE INDEX idx_sci_classification ON sec_sci_events (sci_classification);
CREATE INDEX idx_sci_detection_time ON sec_sci_events (detection_timestamp DESC);
CREATE INDEX idx_sci_notification_required ON sec_sci_events (notification_required) WHERE notification_required = TRUE;

-- GDPR processing activities
CREATE TABLE gdpr_processing_activities (
    audit_id UUID PRIMARY KEY REFERENCES audit_events(audit_id),
    activity_id VARCHAR(255) NOT NULL,
    activity_name VARCHAR(255) NOT NULL,
    controller VARCHAR(255) NOT NULL,
    processor VARCHAR(255),
    data_subject_categories TEXT[],
    personal_data_categories TEXT[],
    special_categories TEXT[],
    processing_purpose TEXT NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    recipients JSONB,
    retention_period VARCHAR(100),
    deletion_date DATE,
    security_measures JSONB,
    additional_data JSONB
);

CREATE INDEX idx_gdpr_activity_id ON gdpr_processing_activities (activity_id);
CREATE INDEX idx_gdpr_legal_basis ON gdpr_processing_activities (legal_basis);
CREATE INDEX idx_gdpr_deletion_date ON gdpr_processing_activities (deletion_date) WHERE deletion_date IS NOT NULL;

-- CCPA consumer requests
CREATE TABLE ccpa_consumer_requests (
    audit_id UUID PRIMARY KEY REFERENCES audit_events(audit_id),
    request_id VARCHAR(255) NOT NULL UNIQUE,
    request_type VARCHAR(50) NOT NULL,
    submission_method VARCHAR(50) NOT NULL,
    submission_timestamp TIMESTAMPTZ NOT NULL,
    consumer_id UUID,
    consumer_email VARCHAR(255) NOT NULL,
    authorized_agent BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(20) NOT NULL,
    verification_timestamp TIMESTAMPTZ,
    processing_status VARCHAR(50) NOT NULL,
    response_due_date DATE NOT NULL,
    response_date DATE,
    extension_granted BOOLEAN DEFAULT FALSE,
    data_disclosed JSONB,
    additional_data JSONB
);

CREATE INDEX idx_ccpa_request_id ON ccpa_consumer_requests (request_id);
CREATE INDEX idx_ccpa_request_type ON ccpa_consumer_requests (request_type);
CREATE INDEX idx_ccpa_consumer_email ON ccpa_consumer_requests (consumer_email);
CREATE INDEX idx_ccpa_response_due ON ccpa_consumer_requests (response_due_date) WHERE response_date IS NULL;

-- Data lineage tracking
CREATE TABLE data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    data_entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    operation_id VARCHAR(255),
    upstream_entities JSONB,
    downstream_entities JSONB,
    transformation_logic TEXT,
    quality_checks JSONB,
    row_count BIGINT,
    size_bytes BIGINT,
    pii_fields TEXT[],
    sensitive BOOLEAN DEFAULT FALSE,
    additional_data JSONB
);

CREATE INDEX idx_lineage_timestamp ON data_lineage (timestamp DESC);
CREATE INDEX idx_lineage_entity_id ON data_lineage (data_entity_id);
CREATE INDEX idx_lineage_operation_type ON data_lineage (operation_type);
CREATE INDEX idx_lineage_sensitive ON data_lineage (sensitive) WHERE sensitive = TRUE;
```

---

## 6. Audit Log Integrity and Security

### 6.1 Immutability Mechanisms

**Cryptographic Signatures:**
- Each audit event signed with HMAC-SHA256
- Secret key stored in AWS KMS or Hardware Security Module (HSM)
- Signature verification on retrieval

```python
import hashlib
import hmac
import json

def sign_audit_event(event_data, secret_key):
    """Generate HMAC-SHA256 signature for audit event"""
    canonical_json = json.dumps(event_data, sort_keys=True)
    signature = hmac.new(
        secret_key.encode(),
        canonical_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_audit_event(event_data, signature, secret_key):
    """Verify audit event signature"""
    expected_signature = sign_audit_event(event_data, secret_key)
    return hmac.compare_digest(signature, expected_signature)
```

**Merkle Tree for Batch Verification:**
- Hourly Merkle tree construction of audit events
- Root hash stored in blockchain or immutable storage
- Enables efficient verification of large audit logs

**Database-Level Protection:**
- PostgreSQL row-level security (RLS) policies
- Audit tables: INSERT-only, no UPDATE or DELETE
- Soft deletion with tombstone records for required deletions

### 6.2 Access Control for Audit Logs

**Role-Based Access Control (RBAC):**
- **Audit Administrator:** Full read access, no write/delete
- **Compliance Officer:** Read access to compliance-tagged events
- **Security Analyst:** Read access to security-tagged events
- **System Auditor:** Read access for SOC 2 audit scope
- **Data Protection Officer:** Read access to privacy-tagged events

**Attribute-Based Access Control (ABAC):**
- Access based on event classification level
- Restricted access to personally identifiable information (PII)
- Dynamic filtering based on user clearance level

**Audit Log Access Auditing:**
- All access to audit logs is itself audited
- Separate meta-audit table for audit log queries
- Alerts for unusual access patterns

---

## 7. Audit Reporting and Analytics

### 7.1 Standard Compliance Reports

#### SOC 2 Type II Evidence Report
**Frequency:** Continuous (for annual audit)
**Content:**
- Access control changes and reviews
- Security incident summary
- System change log
- Backup and recovery testing
- Monitoring and alerting effectiveness

#### FINRA Regulatory Reporting
**Frequency:** Various (daily, monthly, as-needed)
**Content:**
- Order Audit Trail System (OATS) data
- Large Trader Reporting (LTR)
- Suspicious Activity Reports (SARs)
- Customer complaint log
- Trade surveillance exception reports

#### SEC Reg SCI Reporting
**Frequency:** Event-driven + quarterly
**Content:**
- SCI event notifications (within required timeframes)
- Quarterly SCI systems review
- Annual capacity planning report
- Change management summary

#### GDPR Article 30 Records
**Frequency:** Continuous (on-demand for DPA)
**Content:**
- Register of processing activities
- Data subject request log
- Data breach register
- Data transfer documentation
- DPIA summary

#### CCPA Consumer Request Report
**Frequency:** Monthly
**Content:**
- Consumer request volume by type
- Average response time
- Request fulfillment rate
- Verification failure rate

### 7.2 Real-Time Monitoring Dashboards

**Security Operations Center (SOC) Dashboard:**
- Failed authentication attempts (last 24h)
- Access denied events by resource
- Security incident timeline
- Anomalous access patterns
- High-severity events requiring attention

**Compliance Monitoring Dashboard:**
- Outstanding data subject requests (SLA tracking)
- Unreviewed trade surveillance exceptions
- System changes pending approval
- Access reviews overdue
- Training completion status

**Operational Health Dashboard:**
- Audit log ingestion rate
- Storage utilization and growth
- Data quality metrics
- Lineage graph completeness
- Report generation performance

### 7.3 Anomaly Detection and Alerting

**Statistical Anomaly Detection:**
- Baseline normal behavior per user/system
- Standard deviation alerts for unusual activity
- Time-series analysis for trend detection
- Machine learning models for advanced detection

**Rule-Based Alerting:**
- Failed MFA attempts exceeding threshold
- Access to sensitive data outside business hours
- Privilege escalation attempts
- Bulk data export operations
- Critical system changes without approval

**Integration with SIEM:**
- Forward audit events to Splunk/Datadog
- Correlation with infrastructure logs
- Threat intelligence integration
- Automated incident response workflows

---

## 8. Audit Schema Implementation Guide

### 8.1 Application Integration

**Logging Library (Python Example):**
```python
import uuid
import datetime
from typing import Optional, Dict, Any
from enum import Enum

class EventType(Enum):
    AUTH_LOGIN = "AUTH.LOGIN"
    DATA_CREATED = "DATA.CREATED"
    PRIVACY_ACCESS_REQUEST = "PRIVACY.ACCESS_REQUEST"
    # ... additional event types

class AuditLogger:
    def __init__(self, service_name: str, environment: str):
        self.service_name = service_name
        self.environment = environment

    def log_event(
        self,
        event_type: EventType,
        actor_id: str,
        actor_type: str,
        resource_id: str,
        resource_type: str,
        action_operation: str,
        action_outcome: str,
        changes_before: Optional[Dict[str, Any]] = None,
        changes_after: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        compliance_tags: Optional[List[str]] = None
    ) -> str:
        """
        Log an audit event

        Returns:
            audit_id (str): Unique identifier for the audit event
        """
        audit_id = str(uuid.uuid7())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        audit_event = {
            "audit_id": audit_id,
            "timestamp": timestamp,
            "event_type": event_type.value,
            "category": event_type.value.split(".")[0],
            "actor": {
                "id": actor_id,
                "type": actor_type
            },
            "resource": {
                "id": resource_id,
                "type": resource_type
            },
            "action": {
                "operation": action_operation,
                "outcome": action_outcome
            },
            "context": {
                "request_id": str(uuid.uuid4()),
                "service": self.service_name,
                "environment": self.environment
            },
            "changes": {
                "before": changes_before,
                "after": changes_after
            },
            "metadata": {
                "compliance_tags": compliance_tags or []
            }
        }

        # Sign the event
        signature = self._sign_event(audit_event)
        audit_event["metadata"]["signature"] = signature

        # Write to database
        self._write_to_database(audit_event)

        return audit_id

    def _sign_event(self, event: Dict[str, Any]) -> str:
        """Generate cryptographic signature for event"""
        # Implementation using HMAC-SHA256
        pass

    def _write_to_database(self, event: Dict[str, Any]):
        """Persist audit event to PostgreSQL"""
        # Implementation using SQLAlchemy or psycopg2
        pass

# Usage example
audit_logger = AuditLogger(service_name="api", environment="production")

audit_id = audit_logger.log_event(
    event_type=EventType.DATA_CREATED,
    actor_id="user-123",
    actor_type="USER",
    resource_id="record-456",
    resource_type="CUSTOMER_PROFILE",
    action_operation="CREATE",
    action_outcome="SUCCESS",
    changes_after={"name": "John Doe", "email": "john@example.com"},
    compliance_tags=["GDPR", "CCPA", "SOC2"]
)
```

### 8.2 Microservices Integration

**Distributed Tracing:**
- Propagate `trace_id` and `correlation_id` across services
- Use OpenTelemetry for distributed tracing
- Link audit events across service boundaries

**Event Streaming:**
- Publish audit events to Kafka/Kinesis
- Real-time processing with stream processors
- Fan-out to multiple consumers (SIEM, analytics, compliance)

**API Gateway Integration:**
- Capture all API requests at gateway level
- Enrich with authentication/authorization context
- Forward to audit service

### 8.3 Performance Optimization

**Asynchronous Logging:**
- Non-blocking audit event emission
- Queue-based processing (RabbitMQ, SQS)
- Batch insertions for high throughput

**Database Optimization:**
- Table partitioning by date (monthly)
- Appropriate indexing strategy
- Regular VACUUM and ANALYZE operations
- Read replicas for reporting queries

**Caching Strategy:**
- Cache frequently accessed audit data
- Invalidation on new event insertion
- Redis for distributed caching

---

## 9. Audit Trail Validation and Testing

### 9.1 Validation Procedures

**Completeness Checks:**
- Verify no gaps in audit_id sequence (UUID v7 time-based)
- Cross-reference application events with audit log
- Reconcile transaction counts

**Integrity Checks:**
- Verify HMAC signatures for all events
- Validate Merkle tree root hashes
- Check for unauthorized modifications (should be impossible)

**Accuracy Checks:**
- Sample testing of audit event content
- Comparison with source system records
- User acceptance testing

### 9.2 Testing Strategy

**Unit Tests:**
- Audit logger functionality
- Signature generation and verification
- Event serialization/deserialization

**Integration Tests:**
- End-to-end audit event flow
- Database persistence and retrieval
- Cross-service audit correlation

**Performance Tests:**
- Load testing at peak volumes
- Audit log query performance
- Archival and retrieval latency

**Compliance Tests:**
- SOC 2 control validation
- FINRA audit trail completeness
- GDPR data subject request simulation
- Retention policy enforcement

---

## 10. Incident Response for Audit System Issues

### 10.1 Failure Scenarios

| Scenario | Impact | Detection | Response | Recovery Time |
|----------|--------|-----------|----------|---------------|
| Audit database unavailable | Critical - No audit logging | Health check failure | Failover to secondary, queue events | <5 minutes |
| Signature key compromise | Critical - Integrity breach | Security monitoring | Rotate keys, re-sign affected events | <1 hour |
| Audit log corruption | High - Evidence loss | Integrity checks | Restore from backup, investigate cause | <4 hours |
| Performance degradation | Medium - Slow queries | APM alerts | Scale resources, optimize queries | <30 minutes |
| Archival failure | Medium - Retention violation | Monitoring alert | Manual intervention, retry archival | <24 hours |

### 10.2 Disaster Recovery

**Backup Strategy:**
- Continuous replication to standby database
- Daily snapshots to S3 with versioning
- Cross-region backup for disaster recovery

**Recovery Procedures:**
- Point-in-time recovery capability
- Tested recovery runbooks
- RTO: 4 hours, RPO: 15 minutes

---

## 11. Continuous Improvement

### 11.1 Audit Schema Evolution

**Version Control:**
- Schema changes tracked in version control
- Backward compatibility maintained
- Migration scripts for schema updates

**Feedback Loop:**
- Regular review with compliance team
- Incorporate auditor recommendations
- Update based on regulatory changes

### 11.2 Metrics and KPIs

- **Audit log completeness:** Target 100% (no missing events)
- **Signature verification rate:** Target 100% valid signatures
- **Query performance:** P95 response time <500ms for recent events
- **Storage efficiency:** Compression ratio >5:1 for archived logs
- **Compliance report generation:** Automated reports <5 minutes

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-19 | Compliance Analyst | Initial audit schema definition |

**Approval:**
- [ ] Chief Compliance Officer
- [ ] Chief Information Security Officer
- [ ] Data Protection Officer
- [ ] Chief Technology Officer

**Next Review Date:** 2025-Q2
