# Mobile API v1

The API lives alongside the existing Django website under `/api/v1/` and uses the existing database and role-profile models. The native Expo client is in `mobile/` and consumes the authentication, profile, request, and notification endpoints documented here.

## Authentication

- `POST /api/v1/auth/login/` — username/password; returns `access`, `refresh`, and a minimal `user` object containing role, email verification, and approval state.
- `POST /api/v1/auth/register/` — creates Driver or Mechanic accounts only. It validates the password, username, and email; sends the existing email-verification link; returns no session tokens. Mechanic accounts start unverified and pending approval. Registration is limited to five attempts per hour.
- `POST /api/v1/auth/resend-verification/` — accepts an email and always returns the same `202` response to avoid account enumeration; sends a link only for a single unverified Driver or Mechanic profile. Limited to five attempts per hour.
- `POST /api/v1/auth/refresh/` — rotates refresh tokens; prior refresh tokens are blacklisted.
- `POST /api/v1/auth/logout/` — requires a valid access token and the current user's refresh token; blacklists it and, when `push_token` is supplied, revokes that token for the current account in the same transaction.
- Access tokens expire after 5 minutes. Refresh tokens expire after 7 days.
- Send access tokens as `Authorization: Bearer <access>` and store tokens only in platform secure storage.
- Login is limited to five attempts per minute per throttle identity; refresh is limited to twenty per minute.
- Login is allowed only for active accounts with exactly one Driver, Mechanic, or Manager profile. Admin/staff-only users and ambiguous multi-profile accounts are not mobile API accounts.

## Profile, request, and notification endpoints

- `GET /api/v1/me/` — returns only the authenticated Django user identity and mobile role state; bank details, account numbers, mobile numbers, and uploaded documents are not included.
- `GET /api/v1/requests/` — paginated (20 per page), role-scoped request data. Drivers see requests linked to their profile; mechanics see only requests assigned to their profile; managers see only requests whose manager field is their profile. Email must be verified, and mechanics/managers must be approved to read requests.
- `POST /api/v1/requests/` — verified drivers only. Accepts an allowlisted service category, vehicle details, description, contact phone, and street/state location. The server supplies the authenticated driver and `Pending` status, sets the initial cost to zero, and leaves the invoice pending; clients cannot assign a mechanic/manager or set status, invoice, cost, or payment references. Existing active requests or pending invoices return `409`; creation is limited to five requests per hour. Optional coordinates must be supplied together; omitted coordinates are stored as `null` rather than using the model's Lagos defaults.
- `GET /api/v1/requests/{id}/` — returns the same allowlisted DTO for one request, using the same role, verification, and approval scope. Requests outside the caller's scope return 404.
- `POST /api/v1/requests/{id}/actions/` — verified, approved mechanics assigned to the request may accept, start, or complete work. Allowed transitions are `Approved → Accepted → Repairing → Done`; invalid transitions and competing active jobs return `409`, and unassigned requests return `404`. The client cannot set a raw status, mechanic identity, cost, invoice, or release/payment state. Actions are limited to 30 per hour.
- `GET /api/v1/manager/mechanics/` — approved, verified managers see only mechanics linked through the existing `Mechanic.my_manager` relationship. The paginated response includes limited identity/service-area fields, manager-owned request counts, and a safe `can_be_assigned` flag; contact, license, and banking data are excluded.
- `GET /api/v1/manager/queue/` — approved, verified managers see only unassigned `Pending` requests whose state matches their manager profile (case-insensitive). Queue cards omit driver contact, coordinates, and billing fields. A manager profile without a state is denied queue access. New requests also create an in-app inbox notice only for approved, verified managers in that state; the queue refreshes automatically every 30 seconds while open.
- `POST /api/v1/manager/queue/{id}/claim/` — accepts `{ "mechanic_id": <id> }`; the manager must be approved and verified, the request must still be pending/unassigned and in the manager's state, and the mechanic must be approved, verified, linked to that manager, and free of an active job. A transaction locks the manager/request/mechanic, sets manager and mechanic, and transitions `Pending → Accepted`; competing claims and active-job conflicts return `409`. Manager, mechanic, and driver notifications are created atomically; the driver acceptance email is dispatched after commit.
- `GET /api/v1/notifications/` — paginated notifications for the authenticated account's single eligible mobile profile, newest first. The response includes only `id`, `message`, `timestamp`, and `is_read`; email verification and approval are not required so onboarding notices remain visible.
- `POST /api/v1/notifications/{id}/read/` — marks one notification as read only when it belongs to the authenticated profile; otherwise returns 404. The operation is idempotent.
- `POST /api/v1/notifications/read-all/` — marks all unread notifications for the authenticated profile as read and returns `updated_count`.
- `POST /api/v1/push-tokens/register/` — authenticated mobile accounts register `{ "token": "<ExpoPushToken>", "platform": "ios|android", "previous_token": "<optional prior token>" }`. Token registration is idempotent and limited to 30 requests per hour; supplying a previous token deactivates it for the same account while activating the current token. Tokens are globally unique to prevent a device token being active for multiple accounts.

The request DTOs are explicitly allowlisted and exclude transaction references, invoice status, payment credentials, and unrelated profile records. Driver request creation, mechanic work transitions, manager claim-and-assign, account registration, verification resend, and scoped notification read actions are the mobile writes in this stage. New-request in-app and SMS alerts are limited to verified, approved managers in the request's state; unscoped push broadcasts are disabled to avoid exposing request details to unrelated subscribers. Cancellations, release, cost changes, location updates, wallets, payments, subscriptions, password reset, and withdrawals remain unavailable. Viewing notifications does not change `is_read`.

## Deployment notes

- The SimpleJWT blacklist app is enabled. Run the normal Django migration command in each environment before using refresh rotation/logout so its blacklist tables exist. Expo push-token acquisition requires an EAS project ID and the platform push credentials in a development or production build; the client skips registration until an EAS project ID is configured.
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` are now read from environment variables. Replace the previously source-controlled Cloudinary credentials with newly rotated values before relying on uploads; empty defaults allow non-media API routes to start but do not enable uploads.
- Existing Django/database/provider environment variables are still required by project settings; deployment readiness was not established by this code change.

## Schema and compatibility

- `GET /api/v1/schema/` serves the public OpenAPI 3.0.3 contract. It is scoped to the mobile v1 URL configuration and uses `/api/v1` as its server base, so website routes are not included.
- The schema endpoint contains route and type information only; it does not expose user data. The contract documents the login token pair and boolean profile verification/approval fields explicitly. Protected API operations continue to enforce their own authentication and role-scoping rules.
- Keep v1 changes backward-compatible and additive. Put breaking path, field, or behavior changes in a new major API prefix, and communicate a deprecation window before retiring an older version.

## Known follow-up

Deployed-environment API checks still need a configured target URL and valid environment. Password reset, location tracking, push delivery, and financial flows remain unimplemented. Driver request creation, mechanic work transitions, manager claim/assignment, and notification read actions use ownership checks and server-owned state; manager queue access is state-scoped and team reads use the existing `my_manager` relation. Before exposing additional write or financial actions, reconcile migration/model state and add transition, ownership, webhook idempotency, and ledger tests as laid out in `API_PLAN.md` and `MIGRATION_PLAN.md`. If the app is exported for web and hosted on a different origin, configure a narrow CORS allowlist rather than enabling wildcard origins.
