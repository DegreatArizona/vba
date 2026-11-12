# Existing Feature Inventory

**Status legend:** Fully implemented = source has a coherent workflow with the evidence reviewed; Partially implemented = some code exists but workflow/completeness is unverified; Needs fixing = implemented surface has identified defects or security gaps; Not found = no implementation found in inspected source. These statuses are source-level, not production QA claims. No automated test suite was found in the inspected repository.

## Driver

| Feature | Status | Source-level notes |
|---|---|---|
| Registration and login | Implemented but needs fixing | Django form/session flow, `Driver` profile, `DRIVER` group. Registration/login exist; validation, throttling, error consistency, and email uniqueness behavior need tests. |
| Email verification / password reset | Implemented but needs fixing | Token links and emails exist. Reset flow does not visibly validate password strength or method/rate limits; verification refers to `is_active` on role profile models, although that field is not present in the inspected models. |
| Profile and picture | Partially implemented | Driver profile view and Cloudinary profile field exist; verify allowed fields, upload constraints, and update behavior. |
| Vehicle information | Partially implemented | Driver profile includes `vehicle_model` and `license_no`; no separate vehicle entity or multi-vehicle workflow found. |
| Request roadside service | Implemented but needs fixing | Request form and history/detail/edit/delete/cancel routes exist. Must validate ownership, allowed transitions, and POST-only state changes consistently before API reuse. |
| Location selection and tracking | Partially implemented | Request carries coordinates; browser tracking endpoints exist. No mobile permission, coordinate validation/range checks, ETA/distance service, or robust real-time deployment verified. |
| Mechanic/manager details | Partially implemented | Related data is available in request flows; scope and privacy serialization need review before mobile exposure. |
| Request history and invoices | Partially implemented | History/invoice views and templates exist; payment state correctness depends on the webhook path. |
| Wallet and funding history | Implemented but needs fixing | Balance and fund history exist; webhook credits without demonstrated idempotency/locking and stores money in non-decimal/inconsistent units. |
| Notifications | Partially implemented | Database notification records and OneSignal service/configuration exist; delivery, device registration, read state and event parity need verification. |
| Ratings and feedback | Not found for end users | A `Feedback` model exists; no complete rating/review flow was located. `rating` fields exist on staff profiles but update/calculation path is unclear. |
| Subscription / Pro | Partially implemented | Pro page, checkout/webhook branch and fields exist; expiration handling and transaction lifecycle need verification. |
| Settings/support | Partially implemented | Profile routes and chatbot/contact-style assets exist; no complete account-settings/support workflow established. |

## Mechanic

| Feature | Status | Source-level notes |
|---|---|---|
| Registration/login/email verification | Implemented but needs fixing | Django form/session and role group; mechanic approval required at login. Verification implementation has a role-profile `is_active` inconsistency. |
| Profile, picture, license, services | Partially implemented | Profile form/model fields and Cloudinary uploads exist. Validate upload type/size and private license-document access. |
| Manager relationship | Implemented but inconsistent | `Mechanic.my_manager` FK and `Manager.mechanics` M2M are both present in current model source; migration history includes a removal of the M2M. Confirm migration state and each assignment workflow before changes. |
| Availability/approval | Partially implemented | `status` exists and controls approval/login behavior; it appears to represent approval more than live availability. No separate online/availability state established. |
| Receiving/accepting/declining jobs | Partially implemented | Dashboard, accept/release/cancel/update views exist. Actual assignment rules and decline path require end-to-end validation; reject/accept concurrency protection not evidenced. |
| Job details and status progress | Implemented but needs fixing | Request status routes exist. Role/ownership checks are uneven across views and transitions; source-level authorization tests are absent. |
| Location/navigation | Partially implemented | HTTP location update endpoint and Channels consumer exist. CSRF is exempted on the update endpoint; validate coordinate input and user/request binding. No turn-by-turn navigation integration found. |
| Earnings/transaction history | Implemented but needs fixing | Salary/earning views and withdrawal history exist; payment webhook credits salary directly and is replayable unless separately guarded. |
| Withdrawals/bank details | Partially implemented | Account fields, bank verification and withdrawal views exist. Provider transfer semantics, balance reservation, idempotency and failure reconciliation need audit. |
| Notifications | Partially implemented | DB notification model and push service exist; delivery/device lifecycle and event parity are unclear. |
| Ratings/subscription | Partially implemented | Rating and Pro fields/webhook behavior exist, but rating collection and subscription expiry semantics need verification. |

## Manager

| Feature | Status | Source-level notes |
|---|---|---|
| Registration/login/approval | Partially implemented | Manager registration and approval/status paths exist; manager account creation and approval policy need trace/tests. |
| Profile/bank information | Partially implemented | Profile and withdrawal views/models exist; validate ownership and sensitive-field exposure. |
| View/manage assigned mechanics | Implemented but inconsistent | Manager-mechanic relation is contradictory between model source and migration history. Scope every query to an explicit manager relationship. |
| View and coordinate requests | Partially implemented | Dashboard, accept/update/release/done/cancel routes exist. Confirm which actions are allowed by policy and ensure managers can only access their assigned mechanic/request scope. |
| Attendance | Partially implemented | `Attendance` model exists; the complete workflow and user-facing manager controls were not established. |
| Earnings/withdrawals | Implemented but needs fixing | Salary, withdrawal records, bank verification and transfer code exist. Same replay, financial precision, and reconciliation risks apply. |
| Notifications | Partially implemented | Manager notification model exists; delivery and read/update behavior need verification. |
| Ratings/Pro | Partially implemented | Fields and subscription webhook branch exist; performance/rating calculation and expiry enforcement unclear. |

## Shared features

- Django session authentication, Django `User`, role groups, email, password recovery: **implemented, but needs security and correctness fixes**.
- Shared service request domain, email notifications, profile image/document storage, location data and payment processing: **implemented, but not yet safe/consistent enough to expose as a mobile API**.
- Chatbot/OpenAI call: **partially implemented**; key is environment-configured, but endpoint access, quotas, prompt/input limits, and error handling need review.
- Browser PWA/service-worker assets: **partially implemented**; not a substitute for a native app.
- Automated tests, mobile APIs, mobile push registration, role-specific API authorization: **not found**.

## Django Admin (documentation only)

Django Admin is enabled and the business models are registered in `vehicle/admin.py`, including Driver, Mechanic, Manager, Request, Attendance, Feedback, notifications, fund history, and withdrawal history. Jazzmin customizes the admin appearance. Admin is for platform-level administration, not the Manager role and not a mobile feature; preserve it and do not create a replacement admin dashboard.
