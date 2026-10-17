# Phase 6A Implementation Report

**Status: FOUNDATION IMPLEMENTED; REMEDIATION ROUND 3 COMPLETE — 2026-10-08**

The implementation acceptance audit returned **NOT READY FOR PHASE 6B**. Remediation round 3 is complete; a fresh independent Phase 6A acceptance is still required and Phase 6B remains blocked until it passes. The PostgreSQL 13 environment finding is superseded: the authoritative development target is the clean PostgreSQL 16.15 `malilab` database.

Phase 6A established a clean Django/PostgreSQL foundation in the verified empty `malilab` database. The implementation follows the approved Phase 5 physical specification and does not change the Phase 1–5 architecture or requirements.

Current round 3 details and verification are in [Phase 6A Remediation Round 3](PHASE_6A_REMEDIATION_ROUND3_REPORT.md); round 2 evidence remains in [Phase 6A Remediation Round 2](PHASE_6A_REMEDIATION_ROUND2_REPORT.md). The old PostgreSQL 13 and legacy application are removed; PostgreSQL 16.15 and the clean `malilab` database are current.

## Environment and dependencies

- Oracle Linux 9.8; Python 3.11.13 in `/home/opc/malilab/.venv`.
- Django 5.2.18, psycopg 3.3.6, django-otp 1.7.3; pinned in `requirements.txt`.
- PostgreSQL 16.15 at loopback `127.0.0.1:5432`; database `malilab`, role `malilab_app`.
- The successful `psql` and Django connections used the existing local `~/.pgpass`. No password was requested, printed, or stored in this project.
- The target had zero application tables before implementation. No legacy schema, models, or data were reused.

## Implemented foundation

The Django project is split into `accounts`, `content`, `practice`, `calculations`, `planning`, `learning`, and `discovery` apps. The 46 MaliLab domain models cover:

- A custom email-identity user, normalized unique email, Django password/session primitives, verification/account state, and verified-account authorization boundary.
- Stable editorial identities and exact revisions; ordered module requirements and Playbook recommendations; typed related-content associations; topics; editorial review and publication events; source snapshots; immutable media metadata.
- Practice attempts and responses; Lab Tool, calculator definition, formula version/approval and saved result structures; no calculator is seeded or activated.
- User plans and append-only Plan Revisions; typed Learning Journey targets and ordered steps; revision-bound Notes/highlights; lesson and module evidence/completion snapshots; achievement definitions and awards.
- A PostgreSQL `tsvector` public-content projection with a GIN index and a service that admits only the current published revision.

Ownership paths use protected foreign keys and owner-scoped services for practice, notes, calculations and plans. Editorial services require Django staff roles, an MFA-verified session, a different author and approver, and append review/publication events. TOTP support is installed and the admin site uses django-otp's OTP-protected admin site. Plan Revisions reject update/delete attempts at the model boundary.

## Migrations and verification

The first database check returned zero application tables. The project migrations were inspected before each apply; all MaliLab and OTP migration operations were additive schema operations. No project data migration, legacy import, raw SQL, or destructive schema operation was applied. Migrations were applied only to `malilab`.

Post-migration verification confirmed PostgreSQL 16.15, `malilab` / `malilab_app`, 56 public tables, 16 MaliLab migrations, key ownership/version/evidence/formula constraints, and the PostgreSQL search GIN index. The domain tables remain unseeded. `scripts/verify_schema.py` performs this read-only check.

Checks completed:

- `manage.py check --database default` — passed.
- `manage.py makemigrations --check --dry-run` — passed; no model/migration drift.
- `manage.py migrate --check` — passed; no unapplied migrations.
- `manage.py test --settings=config.test_settings` — current round 2: 56 tests run, four PostgreSQL-only integration tests skipped, all others passed. `manage.py test --settings=config.postgres_test_settings` — 56 tests run, all passed against the isolated test database. `malilab_app` remains NOCREATEDB; the separate isolated test role cannot connect to live `malilab`.
- Ownership tests cover cross-account practice lookup, private notes, foreign journey/plan/calculation attachments, and unverified account denial.
- `scripts/verify_traceability.py` — all 46 domain models map to an approved requirement group and test module.
- `scripts/inspect_migrations.py` — inspected all 19 project and OTP migrations and their generated SQL before apply; no destructive project SQL or project data operation found.

## Scope boundary

No legacy data import, compatibility model, full UI, subscription/payment system, user-facing AI, voice/audio, advanced search service, or Phase 6B+ work was added. Production deployment, database backup/restore policy, email delivery configuration, email-verification user flow, detailed role grant administration, and staff TOTP enrollment UI remain future operational/UI work. The schema and services provide the foundation for those approved policies without selecting a provider or adding product behavior.

Calculator-specific formulas, ranges, units, precision and rounding remain unconfigured and no formula version is active. Age/eligibility, backup expiry, and note rendering details remain unresolved at their approved later gates.

## Traceability and environment records

- [Traceability matrix](TRACEABILITY_MATRIX.md)
- [Environment audit](PHASE_6A_ENVIRONMENT_AUDIT.md)
- [Environment isolation record](PHASE_6A_ENVIRONMENT_ISOLATION.md)
- [Implementation roadmap](ROADMAP.md)
