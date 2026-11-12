# Project Audit

**Scope:** Phase 1 repository audit for the planned VBA mobile extension. This is a documentation-only audit; no backend, website, schema, or mobile implementation has been changed. Findings describe the checked-in source, not verified production behavior. Areas that could not be established from source are marked for validation.

## Executive summary

At the Phase 1 audit commit, the repository contained a Django 5.1.4 server-rendered website for the AutoAid/vehicle-breakdown product, with `vehicle` as its only first-party app. DRF was already listed in `requirements.txt` but was not installed in `INSTALLED_APPS` and no API routes existed. The website has driver, mechanic, and manager page/view workflows and uses Django sessions and built-in `User`, role profiles and groups, a relational DB configured from environment variables, Cloudinary media, Korapay payment flows, SMTP email, OneSignal push setup, and Django Channels/WebSocket code for live location. This implementation branch now adds an initial `/api/v1/` mobile API and focused API tests; no mobile client is included.

A mobile client should be added as a separate Expo/React Native/TypeScript application and consume a new, authenticated API on this same Django backend and database. First resolve security and correctness blockers—especially committed Cloudinary credential material, public/CSRF-exempt state-changing flows, payment webhook replay/double-credit risk, and inconsistent role/relationship logic—before exposing those flows through APIs. Preserve the current site and existing records; do not apply schema changes until migration state and production data are verified.

## Repository structure

- `manage.py` — Django management entry point.
- `vehiclebreakdown/` — Django project settings, root URL configuration, ASGI and WSGI entry points.
- `vehicle/` — the sole first-party Django application: models, views, forms, role decorators, admin registration, signals, WebSocket consumer/routing, utility/service code, and migrations.
- `vehicle/migrations/` — 91 numbered migrations (`0001` through `0091`) describing a substantial evolving schema.
- `template/` — server-rendered HTML pages and email templates for shared, driver, mechanic and manager workflows.
- `static/` — authored static assets, including JS/CSS/images.
- `staticfiles/` — collected/vendor static assets; not a second application source tree.
- `api/cron.py` — subscription-expiry handler; deployment wiring and authentication need verification.
- `requirements.txt` — Python dependencies.
- `Procfile` — Gunicorn WSGI startup command.
- `vercel.json` — Vercel deployment/build routing configuration.
- `banks.json` — bank reference data.
- `README.md` — currently minimal and not an operational setup guide.

There is no Expo/React Native project or package manifest. This implementation branch adds a DRF serializer/view/router layer and role/ownership API tests. The Django template directory is configured as `template` (singular).

## Technologies and integrations found

- Python / Django 5.1.4; Django template rendering, forms, auth, admin, sessions and ORM.
- Relational database configured with `ENGINE`, `NAME`, `USER`, `PASSWORD`, `HOST`, and `PORT` environment variables; the actual production engine and deployment connection must be confirmed from deployment configuration, not inferred from source.
- Django Channels/WebSocket consumer and ASGI routing for request/mechanic location updates. `Procfile` starts the WSGI app; production ASGI/channel-layer deployment is not established by the checked-in Procfile.
- Cloudinary model fields and media storage.
- Korapay charge/virtual-account operations and webhook processing; bank verification/transfer paths also appear in views. Exact provider contracts and production/test mode must be confirmed.
- SMTP email; OneSignal configuration and notification service; browser service-worker/PWA files.
- OpenAI key configuration and chatbot view/client code.
- WhiteNoise, Gunicorn, Jazzmin, widget-tweaks, django-pwa, sitemap, and decouple.
- DRF 3.15.2 and SimpleJWT are now enabled for the initial API on this implementation branch; no Expo/React Native client is included.

## Django applications

First-party apps:

1. `vehicle` — business domain and website.

Installed apps include `django.contrib.admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `rest_framework`, `rest_framework_simplejwt.token_blacklist`, `django.contrib.sitemaps`, `jazzmin`, `widget_tweaks`, `cloudinary`, `pwa`, and `vehicle`. Channels-related code is present; confirm its installed app/configuration and runtime deployment before relying on it. This inventory is based on `INSTALLED_APPS` and imports, not a claim that each integration has been fully exercised.

## Main request lifecycle (source-level)

1. A driver registers through a Django form; a `Driver` profile and `DRIVER` auth group membership are created, and an email verification message is sent.
2. The driver signs in through Django session authentication and can submit a service request through a server-rendered form. The request stores driver/vehicle/problem/location and workflow/payment fields.
3. Managers and mechanics use separate page workflows to view and act on requests. Manager assignment/onboarding/approval and mechanic acceptance/release/completion are implemented in view functions; request relations store mechanic and optional manager.
4. The mechanic can update coordinates associated with a request; the driver can retrieve coordinates for an owned request. A consumer/routing implementation also exists, but its authorization and deployment path need reconciliation with the HTTP endpoints.
5. Payment completion is processed in `korapay_webhook`, which mutates request status/earnings, credits wallet balances, or marks subscriptions active, then creates notifications and emails.

This is a map of source code paths, not confirmation of end-to-end provider behavior. In particular, webhook signature canonicalization, idempotency, amount/currency/reference verification, and actual payment/transfer settlement need provider-backed tests before financial records are trusted.

## Deployment and operations

`Procfile` launches `gunicorn vehiclebreakdown.wsgi`. `vercel.json` and `api/cron.py` indicate a Vercel deployment/cron path, but the production runtime, database, channel layer, static/media configuration, cron authorization, and environment-variable coverage need confirmation. Settings hard-code `DEBUG = False` and a host allowlist; environment-specific settings and security-header configuration should be reviewed before API rollout.

## Audit limitations and next validation

This remains a source inspection, not a production database migration check or live integration test. Before further implementation, inspect the deployed database engine, migration-applied state, representative non-sensitive records, provider webhook documentation, Vercel cron invocation/authentication, channels layer, and actual payment/withdrawal provider behavior. The API branch adds focused authorization tests; the legacy website and external integrations still need broader regression/provider-backed coverage.
