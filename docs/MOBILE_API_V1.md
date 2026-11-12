# Mobile API v1

The API lives alongside the existing Django website under `/api/v1/` and uses the existing database and role-profile models. The first native Expo client is in `mobile/` and consumes the authentication, profile, and read-only request/notification endpoints documented here.

## Authentication

- `POST /api/v1/auth/login/` — username/password; returns `access`, `refresh`, and a minimal `user` object containing role, email verification, and approval state.
- `POST /api/v1/auth/refresh/` — rotates refresh tokens; prior refresh tokens are blacklisted.
- `POST /api/v1/auth/logout/` — requires a valid access token and the current user's refresh token; blacklists it.
- Access tokens expire after 5 minutes. Refresh tokens expire after 7 days.
- Send access tokens as `Authorization: Bearer <access>` and store tokens only in platform secure storage.
- Login is limited to five attempts per minute per throttle identity; refresh is limited to twenty per minute.
- Login is allowed only for active accounts with exactly one Driver, Mechanic, or Manager profile. Admin/staff-only users and ambiguous multi-profile accounts are not mobile API accounts.

## Read endpoints

- `GET /api/v1/me/` — returns only the authenticated Django user identity and mobile role state; bank details, account numbers, mobile numbers, and uploaded documents are not included.
- `GET /api/v1/requests/` — paginated (20 per page), read-only request data. Drivers see requests linked to their profile; mechanics see only requests assigned to their profile; managers see only requests whose manager field is their profile. Email must be verified, and mechanics/managers must be approved to read requests.
- `GET /api/v1/requests/{id}/` — returns the same allowlisted DTO for one request, using the same role, verification, and approval scope. Requests outside the caller's scope return 404.
- `GET /api/v1/notifications/` — paginated notifications for the authenticated account's single eligible mobile profile, newest first. The response includes only `id`, `message`, `timestamp`, and `is_read`; email verification and approval are not required so onboarding notices remain visible.

The request DTO is explicitly allowlisted and excludes transaction references, invoice status, payment credentials, and unrelated profile records. This phase includes no request creation, assignment, location update, wallet, payment, subscription, notification mutation (including mark-as-read or device-token registration), or withdrawal API. Request detail and notification history are read-only; viewing notifications does not change `is_read`.

## Deployment notes

- The SimpleJWT blacklist app is enabled. Run the normal Django migration command in each environment before using refresh rotation/logout so its blacklist tables exist.
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` are now read from environment variables. Replace the previously source-controlled Cloudinary credentials with newly rotated values before relying on uploads; empty defaults allow non-media API routes to start but do not enable uploads.
- Existing Django/database/provider environment variables are still required by project settings; deployment readiness was not established by this code change.

## Known follow-up

Add an OpenAPI schema and deployed-environment API checks. Registration, password reset, write actions, and financial flows remain unimplemented. If the app is exported for web and hosted on a different origin, configure a narrow CORS allowlist rather than enabling wildcard origins. Before exposing write or financial actions, reconcile migration/model state and add atomic transition, ownership, webhook idempotency, and ledger tests as laid out in `API_PLAN.md` and `MIGRATION_PLAN.md`.
