# Mobile API Plan

**Status:** The initial Django API and Expo client foundation are implemented on feature branches. The API provides JWT login/refresh/logout, current-user profile, and paginated role-scoped request reads; the client in `mobile/` provides sign-in, account, and request-list screens. The remaining endpoint matrix is still a proposal. Reuse existing Django models and domain rules; do not create a second database or reimplement request/payment rules in React Native.

## Recommended approach

The API is implemented in `vehicle.api.v1` alongside the existing server-rendered routes, with Django website session behavior left intact. The mobile API uses SimpleJWT with short-lived access tokens and rotating, blacklisted refresh tokens. Native clients store tokens in platform secure storage; the browser preview uses memory-only storage. Enforce permissions and object scoping on every endpoint; client-side role-based navigation is not authorization.

Use serializers with explicit allowlists, request validation, pagination, consistent error responses, throttling on authentication/expensive operations, and versioned routes. Add tests for each role, ownership, manager scope, state transition, and anonymous access before connecting the app.

## Proposed endpoint surface

| Area | Candidate endpoint(s) | Authorization and notes |
|---|---|---|
| Authentication | `POST /api/v1/auth/login`, `/refresh`, `/logout`; registration/verification/reset endpoints as needed | Resolve role from server-side profile; rate-limit; do not disclose whether arbitrary email exists; revoke tokens on logout/reset. Reuse safe existing token/email helpers only after audit. |
| Current account | `GET/PATCH /api/v1/me`, profile-picture upload | Return role-specific DTO; allowlisted fields; never expose password, bank secrets, other roles' private fields. |
| Driver profile / vehicle | `GET/PATCH /api/v1/driver/profile`; vehicle resource only if product requirements approve a normalized model | Existing schema supports one vehicle-model/license pair, not a separate vehicle collection. Do not invent multi-vehicle persistence in API only. |
| Mechanic profile | `GET/PATCH /api/v1/mechanic/profile`; availability endpoint if approved | Separate live availability from manager approval status; protect license documents and bank data. |
| Manager profile/team | `GET/PATCH /api/v1/manager/profile`; `GET /api/v1/manager/mechanics` | Scope all results/actions to the authenticated manager using the reconciled relationship model. Manager is staff, not platform admin. |
| Service requests | `GET/POST /api/v1/requests`; `GET/PATCH /api/v1/requests/{id}` | Driver sees/creates own requests; assigned mechanic and in-scope manager see only permitted requests. Validate location, category, input bounds, and method. |
| Assignment/state transitions | Explicit action endpoints such as `accept`, `release`, `complete`, `cancel`, `assign` | Use role-scoped policies and a server-side transition table; lock/update atomically to prevent competing acceptance and invalid transitions. Preserve existing website routes while sharing service functions. |
| Location | `POST /api/v1/requests/{id}/location`, `GET .../location` or a separately authorized stream | CSRF exemptions are not relevant to token auth; require mechanic ownership/assignment, active job, rate limits and coordinate validation; limit access to the owning driver and in-scope manager. |
| Wallet/history | `GET /api/v1/driver/wallet`, `GET /api/v1/transactions` | Read-only client APIs first. Never accept a client assertion that a payment succeeded or a client-provided balance. Amount/currency are server-derived. |
| Payment initiation | `POST /api/v1/requests/{id}/checkout`, `POST /api/v1/wallet/topups` | Server creates provider session/reference; validate amount/ownership and use idempotency. Provider webhook remains authoritative. Do not port sandbox credit endpoint into production mobile API. |
| Withdrawals | `POST /api/v1/withdrawals`; `GET /api/v1/withdrawals` | Validate available funds, bank ownership/verification, positive amount and aggregate limits; reserve funds atomically, use idempotency and reconcile asynchronous result. |
| Notifications | `GET /api/v1/notifications/` (implemented, read-only history); mark-read and device-token registration deferred | Scope each role to its own profile. Future push tokens must be user-bound, revocable and never trusted to grant access. |
| Feedback/ratings | `POST /api/v1/feedback` / rating resource only after defining target, scale and ownership | Current Feedback is unlinked free-form text; current `rating` fields lack verified calculation. Define semantics before API/schema work. |
| Subscriptions | `GET /api/v1/subscription`; `POST /api/v1/subscription/checkout` | Only if current Pro plans are confirmed; expiry and entitlements must be server-enforced and transaction-verified. |

## Shared business logic

Extract only after tests establish current behavior. A narrow service layer should own request transition rules, payment verification/ledger posting, wallet credit, withdrawal reservation/reconciliation, subscription entitlement, notification event creation, and manager scope. Existing views should call those same operations where practical, preserving form/session flows. API views should not call templates, and mobile clients should not encode business rules as authority.

## Payment/webhook prerequisites

Before adding any mobile payment surface: verify the exact Korapay signature recipe against raw request bytes/provider docs; verify transaction state, currency, amount and merchant reference from provider response; process each provider reference once with a database uniqueness/atomicity guard; use a decimal-safe money representation and explicit units; avoid duplicate salary/wallet/Pro effects under retries; persist state transitions and failures; and test replay, out-of-order, malformed and mismatched events. Keep provider secrets exclusively in server environment configuration.

## Delivery sequence

1. Security and correctness baseline plus tests for existing website workflows.
2. Reconcile model/migration state and role/manager scope.
3. Introduce DRF, API schema/versioning, auth, serializers, permissions, throttling and test fixtures.
4. Deliver read-only profile/request/history APIs by role.
5. Add validated request actions and location update/read.
6. Deliver role-scoped, read-only notification history; defer mark-read and device-token registration until ownership and event lifecycle are designed.
7. Add payments, wallet, withdrawals and subscription APIs only after ledger/idempotency/provider verification.
8. Run website regression suite and API authorization matrix before mobile integration.
