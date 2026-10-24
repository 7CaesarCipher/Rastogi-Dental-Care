# Role-based and per-user access — v2 demonstration

## Lifecycle

1. Staff submits `POST /api/signup` with `display_name`, `username`, `password`, `confirm_password`, `requested_role` (dentist/researcher/coordinator/receptionist).
2. Server hashes the password and creates an account with status `PENDING`. Sign-in returns HTTP 403 while pending.
3. An administrator opens **User permissions**, then approves/activates the account, optionally changing the assigned role.
4. When the user logs in, `GET /api/me` supplies their effective module `permissions`, which the GUI uses to decide which pages/actions to render.
5. The server independently authorizes every resource list and write operation. Hiding a GUI item alone never grants security.
6. When an administrator suspends the account or changes its role/permission, `session_epoch` increments and all existing signed-session cookies for that account stop working.

## Effective permissions

- Administrator has fixed comprehensive access, including **users**, **audit**, and research protocol activation. Administrator role cannot be self-registered.
- Others inherit defaults for their assigned role. For a particular module, an admin override is `none` (no view or edit), `read` (view only) or `write` (view + edit).
- Resetting the override to `default` re-enables the role-inherited setting.
- The **users** and **audit** modules cannot be delegated by user overrides.
- Research protocol activation remains administrative even if another user receives `trials: write`.
- New accounts cannot sign in until status is `ACTIVE`; suspended accounts cannot sign in either.

## Administrator REST endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/admin/catalog` | Modules and role defaults |
| GET | `/api/admin/users` | Staff directory, status, effective permissions, explicit overrides (never password hashes) |
| POST | `/api/admin/users/{id}/review` | Set role and account status |
| POST | `/api/admin/users/{id}/permission` | Set one module override (`default`, `none`, `read`, `write`) |

## Security and regulatory limitations

This prototype has role-level and module-level reads, **not record-level permissions**. For genuine healthcare operations add tenant/site/patient access checks, approval provenance, password-recovery/email verification, staff ID verification, MFA, lockout/rate limiting, logging of record reads, CSRF hardening, signed release workflows, encryption/key management, backups, data retention, and independently audited access governance. Consent documentation, ethics and trial safety reporting are NOT validated production capabilities.
