# Migration and Coexistence Plan

**Principle:** Add a native client alongside the existing Django website. Django and its current database remain the source of truth. This is a rollout plan, not authorization to change production, schema, credentials, or deployment.

## Guardrails

- Keep current Django session routes, templates, static assets and Admin operational.
- Add a versioned API alongside existing URL routes; do not replace or redirect the website to a WebView/mobile interface.
- Reuse the existing database and records; do not create a separate mobile database.
- Prefer additive, reversible schema changes only when documented needs are established. No destructive migration without explicit approval, tested backup and rollback/recovery plan.
- Share tested domain services between website and API rather than forking business rules.
- Do not expose secrets in the mobile bundle or documentation. Rotate credentials already committed to source and move runtime credentials to managed environment configuration as a separately approved operational action.

## Staged rollout

### 0. Baseline and containment

1. Confirm exact production DB engine, migration state, deploy configuration, channels runtime, environment variables by name (never values), provider modes, and backup/restore procedure.
2. Address committed credential exposure, payment webhook idempotency/verification, unauthorized state-changing routes, role-profile inconsistencies, and PII leakage before mobile API access.
3. Capture current website behavior with focused automated tests and a deployment smoke checklist. Record current error/availability baseline.
4. Reconcile model source with migrations, especially manager/mechanic assignment history, using a production backup and staging copy.

### 1. Compatible backend foundation

 1. Initial DRF `/api/v1/` namespace and read-only foundation are implemented on `v0/mobile-api-foundation`; retain existing page URLs and complete the remaining API phases only after the security/data prerequisites below.

2. Add mobile-specific authentication while retaining session auth for the website. Define revocation, expiry, password-reset behavior and rate limits.
3. Add explicit profile/role serialization and permission matrix; test anonymous, wrong-role, wrong-owner and cross-manager cases.
4. Publish an API schema and API compatibility policy. Add error envelope, pagination and throttling.
5. Use feature flags or staged release configuration; initially leave endpoints unavailable to public clients until security tests pass.

### 2. Read surfaces and coexistence

Introduce role-scoped read endpoints for profile, permitted requests, history and notifications. Compare API data with website pages using the same test fixtures and database. Add monitoring for API error rate, latency and permission denials without logging personal data or tokens.

### 3. State-changing workflows

Add request creation and explicit status actions, then location updates, only after service-layer extraction and transition tests. Keep old website forms calling the same tested domain operations. Run website regression checks after each endpoint/action release.

### 4. Financial, notification and subscription flows

Treat payments, balance, earnings, withdrawals and subscriptions as a separate gated release. Require provider verification, unique idempotency references, atomic ledger effects, decimal-safe amounts/units, reconciliation of provider failures and audit trail before exposing them. Add push registration and deep linking after backend events and device-token revocation are tested. No client-side optimistic state may be authoritative for financial outcomes.

### 5. Mobile beta and rollout

Release internal iOS/Android builds against staging first. Test all three roles, token expiry, denied permissions, offline/retry behavior, and cross-platform website/mobile updates. Then invite a limited cohort with production monitoring and a rollback switch. Expand gradually only after security, data-integrity and support criteria pass.

### 6. Production release and maintenance

Document signing/builds, privacy disclosures, app permissions, provider configuration, API version support, incident response, backup/restore, rollback and store release. Keep previous API versions compatible while supported clients are in use; deprecate only with usage telemetry and notice. Never perform an irreversible production operation without explicit approval.

## Data and schema migration protocol

For each schema proposal: state the reason; identify affected rows and null/default behavior; backup and test restore; rehearse forward migration on a scrubbed production-like copy; verify constraints/index impact; provide reverse migration or recovery-from-backup steps; deploy compatible code before/after migration in a safe order; verify data invariants; retain historical records. Avoid dual writes. If dual-read/write is unavoidable, specify a short, monitored transition and reconciliation job before implementation.

## Rollback and incident response

Keep mobile API routes independently disableable. A mobile rollback should not require rolling back the website or deleting data. Prefer code/config rollback for additive releases; restore from tested backup only when data corruption demands it. For credential compromise, rotate/revoke at provider and deployment level and assess access logs; do not merely remove secrets from the latest commit while leaving exposed credentials valid.
