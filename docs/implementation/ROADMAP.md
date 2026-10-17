# Implementation Roadmap

Production deployment remains a separate future phase. The implementation follows the approved Phase 1–5 product, architecture, and physical specification without changing them.

## Phase 6A — Django/PostgreSQL foundation

**Status: FOUNDATION IMPLEMENTED; REMEDIATION ROUND 3 COMPLETE — 2026-10-08; PHASE 6A ACCEPTANCE SATISFIED UNDER GOV-001.** The clean Django/PostgreSQL foundation is in the `malilab` database as `malilab_app`. The earlier independent audit returned **NOT READY FOR PHASE 6B**; the later existing independent acceptance audit passed and satisfies the Phase 6A acceptance gate under the owner's ruling in GOV-001. This is not Phase 6B.5 implementation authorization. `PROJECT.md` remains unchanged and retains contradictory stale status wording; GOV-001 records the exact status-maintenance action. The current runtime is Python 3.11.13, Django 5.2.18, psycopg 3.3.6, django-otp 1.7.3, and PostgreSQL 16.15. The old PostgreSQL 13 and legacy application have been removed. The local `.pgpass` supplies credentials; none are stored in project settings or documentation.

The implemented foundation covers the custom account, email/password and verified-account boundary, staff TOTP support, editorial identities/revisions/governance/provenance/media, practice, formula/calculation structures, immutable planning revisions, journey, notes, progress/evidence, achievements, PostgreSQL search projection, ownership service boundaries, indexes and constraints. No legacy data or schema was imported. The full UI, payments, user-facing AI, voice/audio, advanced search, and Phase 6B+ work remain out of scope.

Round 3 migration inspection passed before application; the two additive remediation migrations were applied only to `malilab`. Django checks, migration drift checks, 67 SQLite tests (five PostgreSQL-only skips), 67 PostgreSQL tests, PostgreSQL schema checks, and traceability checks passed. Formula activation governance, full media pipeline, production deployment, email delivery, and registration/recovery UI remain deferred. See [round 3 remediation report](PHASE_6A_REMEDIATION_ROUND3_REPORT.md), [round 2 report](PHASE_6A_REMEDIATION_ROUND2_REPORT.md), [implementation report](PHASE_6A_IMPLEMENTATION_REPORT.md), [environment isolation](PHASE_6A_ENVIRONMENT_ISOLATION.md), and [environment audit](PHASE_6A_ENVIRONMENT_AUDIT.md).

## Production boundary

This development implementation does not approve production deployment. Production remains subject to separate capacity review, managed secrets, off-host backup, and successful database/media restore validation, as specified by the architecture. Calculator-specific definitions and formula behavior remain gated on their own approved contracts.

## Phase 6B execution status — 2026-10-13

GOV-002 records the current owner authorization to implement the planned application slices. The accepted Phase 6A foundation and its Phase 6B.1–6B.4 work were preserved. Application work in this execution added Practice schema/answer validation, pinned-revision attempt routes and lifecycle, plus Notes, My Plan, Progress, Search, and Module completion snapshot screens. No model, migration, live database, dependency, or deployment change was made.

Verification on SQLite: Django system check passed; `makemigrations --check --dry-run` reported no changes; the static migration graph loaded 39 nodes with no cycles; the integrated suite reported **114 tests, 109 passed, 5 PostgreSQL-only skipped, 0 failures**. PostgreSQL test setup could not connect to the configured host, so the required PostgreSQL suite, live catalog/migration-ledger comparison, and full physical compatibility proof remain unverified. Human evaluator authorization/UI is not established; no automatic acceptance or Practice evidence creation was implemented. Phase 6B is **in progress and not accepted**.
