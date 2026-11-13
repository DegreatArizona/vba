# Mobile App Plan

**Status:** The native client in `mobile/` uses Expo Router for username/password sign-in, role-aware request lists, request details, a driver request-entry flow, notification inbox, and profile views for Driver, Mechanic, and Manager. Native tokens use SecureStore with refresh/logout; the app includes approval, verification, loading, empty, and error states. Driver request creation uses a verified-driver API with server-owned status and pricing; mechanics can accept, start, and complete assigned work. Managers have a scoped team view and a state-matched queue where they can claim a pending request and assign it atomically to an eligible team mechanic. Payments, location tracking, notification mutations, and other writes remain staged. The client is native-first and does not wrap the website in a WebView.

## Current first slice

- `mobile/` is a standalone Expo Router app; its routes live in `src/app/` and consume the existing `/api/v1/` endpoints.
- Configure `EXPO_PUBLIC_API_BASE_URL` with the API origin shown in `.env.example`. Production builds reject non-HTTPS API origins.
- iOS and Android store access/refresh tokens in Expo SecureStore. The web preview keeps tokens in memory only and does not persist them across reloads.
- The API supports sign-in, profile and request reads, driver request creation, assigned-mechanic work transitions, manager-scoped team reads, a state-scoped pending queue, atomic manager claim-and-assign, refresh, and logout. Driver entry, mechanic actions, and manager dispatch are connected to authenticated APIs; registration, payments, location tracking, and push notifications remain staged.

## Product shape

One Expo + React Native + TypeScript app with role-specific experiences for Driver, Mechanic, and Manager. A successful server-side sign-in returns a profile/role descriptor; the app selects a role-specific route group, while the Django API independently enforces every permission. Django Admin stays a separate platform-operations interface and is not a fourth mobile role.

## Suggested repository layout

Keep the Django website/backend at the repository root. Place mobile in an isolated folder such as `mobile/` (or a separate repository if release ownership requires independent access control), with its own `package.json`, Expo configuration and lockfile. Avoid moving the existing Django app or changing deployment root assumptions. Suggested mobile modules:

```text
mobile/
  src/app/             # Expo Router routes and authenticated tabs
  components/          # accessible reusable UI
  lib/                 # typed API client, auth refresh, secure token storage, types, theme
  assets/              # app icon and images
```

Use Expo Router if it fits the current Expo SDK and team workflow. Keep API DTOs separate from UI models. Use a small server-state/cache layer and React state for ephemeral UI state; do not make local device storage the system of record for requests or money. Store only session credentials and explicitly offline-safe non-sensitive cache data securely/appropriately.

## Navigation and screen inventory

### Shared/auth

- Welcome/role-aware entry, sign in, create account (Driver/Mechanic; Manager invitation/onboarding only according to verified policy).
- Email verification pending/resend, password reset, session-expired and network/error states.
- Authenticated role-specific navigation, notifications, profile, support and sign out.

### Driver

- Dashboard and request entry.
- Service type/problem form; vehicle fields; location permission and manual location fallback; review/submit.
- Active request detail/status timeline; mechanic details and map/tracking when assigned.
- Request history/detail, invoice/payment status, wallet/history if retained.
- Profile, picture and vehicle information; feedback/rating only after backend semantics are defined; Pro/subscription if verified.

### Mechanic

- Dashboard/job queue and availability state (separate from approval state).
- Job detail with only necessary driver/vehicle/contact/location data.
- Accept/reject or release actions per approved workflow; progress/completion updates.
- Navigation handoff and opt-in location sharing only while an eligible job is active.
- Job history, earnings/withdrawal history, bank settings, notifications, profile/license/services, Pro if confirmed.

### Manager

- Dashboard scoped to mechanics assigned to the logged-in manager.
- Team list/detail, availability/approval status, relevant job monitoring and permitted coordination actions.
- Attendance only after confirming existing rules; manager earnings/withdrawals, notifications and profile.
- No platform-wide admin controls and no access to unrelated managers' mechanics.

Every flow should define loading, empty, offline, validation, permission-denied, retry and success states. Use accessible labels, focus order, dynamic text sizing, adequate contrast and non-color status cues.

## API/session and platform integrations

- Use the planned Django API as the sole source of truth. Configure separate development/staging/production base URLs and certificate-backed HTTPS in production.
- Store refresh/access credentials with Expo SecureStore (or a current supported secure equivalent); implement refresh, expiry, logout and password-reset invalidation without logging tokens.
- Request location permission just-in-time and explain the purpose. Allow manual location entry when permission is declined. Background tracking requires explicit product/privacy review and platform permission handling; default to foreground updates only during an active job.
- Use Expo Notifications for push only after backend device-token registration and event authorization exist. Handle token rotation, sign-out revocation and notification deep links.
- Use the system maps/navigation app or an approved native map provider after provider/key, privacy, quota and platform policy review.
- Upload photos/documents through a server-authorized workflow; do not expose Cloudinary credentials in the bundle. Treat mechanic licenses and identity material as sensitive/private.
- Payment UX invokes server-created provider checkout/SDK flows. Never store card secrets or accept client-declared success. Reconcile final state from backend.

## Engineering and release practices

Use typed forms with client-side usability validation plus authoritative server validation. Add unit/component tests for role routing and form states, API tests/mock server tests for transport errors, and device E2E coverage for login, role navigation, location denial/allow, request lifecycle, token expiry, and notification deep links. Test iOS and Android independently, including small screens, permissions, app resume and poor connectivity.

Build separate development/staging/production Expo profiles with distinct API URLs and push credentials. Document Android/iOS signing, app identifiers, privacy disclosures, location/background declarations, store assets and release rollback. Do not publish builds or change production configuration without approval.
