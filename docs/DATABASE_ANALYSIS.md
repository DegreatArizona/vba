# Database Analysis

**Source of truth:** `vehicle/models.py` plus `vehicle/migrations/`. This document records current source definitions and migration-history signals; it does not claim that production has every migration applied. The configured database engine and live schema must be verified before any migration.

## Django identity and role profiles

Django's built-in `auth.User` is the identity record. `Driver`, `Mechanic`, and `Manager` each have a one-to-one relation to `User`; role/group membership is separately created during website registration (`DRIVER` and `MECHANIC` groups are visible; manager group flow should be verified). A user can therefore be linked to one profile of each type unless application rules prevent it. API role resolution must be explicit and reject ambiguous/missing profiles rather than trusting client-supplied role values.

## Business models

| Model | Important data / relations |
|---|---|
| `Driver` | One-to-one User; Cloudinary profile image; address/mobile/license/vehicle model; integer balance; virtual account number/bank; Pro/verification/expiry fields. |
| `Mechanic` | One-to-one User; nullable `my_manager` FK to Manager; profile and license Cloudinary files; services, salary/charge, approval `status`, address/union/contact/bank/location/rating/Pro/verification/expiry. |
| `Manager` | One-to-one User; `mechanics` many-to-many field in current model source; profile/business/contact/bank/region/rating/Pro and guarantor fields. |
| `Request` | Required Driver FK; optional Mechanic and Manager FKs; category, vehicle data, customer and mechanic locations/contacts, latitude/longitude, ETA, description, timestamps, currency/cost/tax/reference, payment method/invoice and status choices. Indexed by status and date. |
| `Attendance` | Nullable Mechanic FK, date, free-form present status. No uniqueness constraint for mechanic/date is declared in the model. |
| `Feedback` | Date, free-form author string, message. No relation to User/Request or numeric score. |
| `DriverFundHistory` | Optional Driver FK, unique transaction reference, currency, Decimal received amount, integer charges, status/date/narration. |
| `MechanicWithdrawalHistory` | Optional Mechanic FK, unique transaction reference, bank snapshot, Decimal received amount, integer withdrawal amount, status/date. |
| `ManagerWithdrawalHistory` | Optional Manager FK, similar bank/amount/status fields and unique reference. |
| `DriverNotification` | Driver FK, message, timestamp, read boolean. |
| `MechanicNotification` | Mechanic FK, message, timestamp, read boolean. |
| `ManagerNotification` | Manager FK, message, timestamp, read boolean. |

## Relationship map

```text
auth.User 1──1 Driver
          1──1 Mechanic ──0..1 my_manager── Manager
          1──1 Manager  *──* mechanics      (declared in models.py)
Driver 1──* Request *──0..1 Mechanic
                       *──0..1 Manager
Mechanic 1──* Attendance
Driver/Mechanic/Manager 1──* respective notifications/history rows
```

`Request.driver` is required; request rows can exist before mechanic/manager assignment. The manager/mechanic representation has two paths: `Mechanic.my_manager` and `Manager.mechanics`. Migration `0074` is named as removing the M2M, while the currently inspected `models.py` declares it. This is a material model/migration state mismatch to resolve with `showmigrations`, migration state inspection, and a database backup before any schema operation. Do not remove or consolidate either relation based only on apparent duplication.

## Financial and workflow fields

- `Request.status` and `Request.invoice` are free-form-at-runtime fields constrained by model choices, used to represent workflow and payment state separately.
- `Request.cost`, `tax`, balances, salaries, charges and withdrawal amount use integer fields while history's received amount uses `DecimalField`. Currency units/rounding are therefore not uniform in the schema; document whether values are minor or major currency units before changing clients or calculations.
- `transaction_reference` on Request has a non-unique default. Payment histories have unique references, but there is no single ledger/settlement model tying every charge, salary allocation, withdrawal and reversal together.
- `Attendance` lacks a declared uniqueness rule. Feedback is not tied to the rated party or request. Rating fields are floating-point numbers without a verified aggregation path.
- Defaults involving `date.today()` / computed date values are evaluated at import/migration definition time when set as values; confirm whether expiry defaults remain correct for new rows.

## Migrations and preservation

There are 91 numbered migrations, documenting repeated field alterations and business-domain expansion. The mobile introduction should be additive and backward-compatible. Before changing schema:

1. Confirm engine and database snapshot/backup restore procedure.
2. Compare `models.py` to migration state and production `showmigrations` output.
3. Inspect real nullability, indexes, constraints and representative data (without exporting PII).
4. Add only reversible/additive migrations unless an approved, data-preserving migration plan exists.
5. Test migrations on a scrubbed copy and rehearse rollback/restore; never delete historical financial or request records.

No schema migration is proposed or run in Phase 1.
