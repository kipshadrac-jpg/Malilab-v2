# Phase 6A Independent Acceptance Audit

**Audit time:** 2026-10-08 04:38 UTC  
**Auditor:** Independent acceptance pass  
**Verdict:** PHASE 6A ACCEPTED — READY FOR PHASE 6B

## Scope and method

This was a read-only acceptance audit of the approved Phase 6A Django/PostgreSQL foundation after Remediation Round 3. No implementation, migration, configuration, test, live database, or project-structure changes were made. The isolated PostgreSQL test runner created and dropped its configured temporary test database; the live `malilab` database remained unchanged. The only file created was this audit artifact. No Phase 6B work was started.

The required initial `git status --short` command returned `fatal: not a git repository`; no `.git` directory exists in or immediately below the workspace. The initial tracked/untracked working-tree state therefore could not be recorded. This audit relied on direct workspace inspection. PostgreSQL test cleanup was verified, and the live schema verifier passed again afterward.

## Environment

- OS: Oracle Linux Server 9.8, x86_64; Linux kernel 6.12.0.
- System Python: 3.9.25, without Django installed. Project virtualenv Python: 3.11.13.
- Django 5.2.18; psycopg 3.3.6; django-otp 1.7.3.
- PostgreSQL service: `postgresql.service` active; `pg_isready` reports accepting connections on port 5432.
- Listener addresses: `127.0.0.1:5432` and `[::1]:5432` only.
- Live database/role/owner: `malilab` / `malilab_app` / `malilab_app`.
- Server version: PostgreSQL 16.15 (`160015`). The application role is not SUPERUSER, CREATEDB, or CREATEROLE. The isolated test role cannot CONNECT to `malilab`.
- Credentials were not displayed or copied into this report. Project settings read the database credentials and production secret from environment variables; the Round 3 environment documentation records `.pgpass` as the local credential source.

## Evidence inspected

Read the requested `PROJECT.md`, `ROADMAP.md`, Phase 5 physical implementation specifications and traceability matrix, plus the Phase 6A implementation, Round 2, and Round 3 reports. Inspected the Django settings, PostgreSQL test settings and their safety tests; model and service code across all seven domain apps; migration files; traceability, migration, and schema verification scripts; relevant account, editorial, ownership, evidence, journey, planning, search, and PostgreSQL integration tests; and current status documentation.

The independent model traceability verifier reported 46 Phase 6A models mapped to requirements and tests. The installed app/model inventory and source were checked directly; the count is not accepted solely on the prior report's claim.

## Commands executed and results

- `git status --short` — unable to run successfully: workspace is not a Git repository.
- `python --version` — Python 3.9.25; system Python does not contain Django. Project commands were rerun with `.venv/bin/python`.
- `.venv/bin/python scripts/verify_traceability.py` — PASS, 46 models mapped.
- `.venv/bin/python scripts/inspect_migrations.py` — PASS, 21 project/OTP migrations inspected; no project data operations or destructive SQL.
- `.venv/bin/python manage.py check` — PASS, no issues.
- `.venv/bin/python manage.py makemigrations --check --dry-run` — PASS, no changes detected.
- `.venv/bin/python scripts/verify_schema.py` — PASS before and after tests; PostgreSQL 16.15, expected live DB/role, exact table set, migration records, required constraints and search GIN index, and no domain seed/import rows.
- `.venv/bin/python manage.py test --settings=config.test_settings` — 67 discovered; 62 passed, 5 PostgreSQL-only skipped, 0 failed.
- Resolved PostgreSQL test settings — configured DB `malilab_phase6a_test`, test DB `test_malilab_phase6a`, role `malilab_phase6a_test`; none equals the live database or application role. The schema verifier independently confirmed the test role cannot CONNECT to live `malilab`.
- `.venv/bin/python manage.py test --settings=config.postgres_test_settings` — 67 discovered; 67 passed, 0 skipped, 0 failed. Django reported destruction of the temporary test database after the run. The subsequent live schema check passed and found no domain rows.
- `systemctl is-active postgresql.service`, `pg_isready -h 127.0.0.1 -p 5432`, and `ss -ltnp` — active, accepting connections, loopback-only listeners.
- Read-only source searches for legacy imports/database assumptions and secret settings — no legacy application imports or embedded database credentials found in application source. Legacy mentions are documentation context only.

The commands initially run with system `python` failed because Django is only installed in the project virtualenv. The same checks were rerun with the virtualenv interpreter and passed. No database migration was applied during this audit.

## PostgreSQL and migration findings

The read-only verifier matched the Django/framework model table set to all 56 public tables and matched 18 MaliLab app migration records to migration files. Required classification, evidence, plan revision, journey, search target, and formula-version constraints exist. The search vector GIN index exists. No domain rows are present in the live development database. The migration loader and `inspect_migrations.py` completed without graph errors; generated SQL inspection found only additive operations. No unapplied Phase 6A migration was indicated by the database/disk comparison.

The PostgreSQL test configuration resolves to its dedicated database and role, rejects live database/application role overrides, and includes tests for safe defaults and rejected overrides. PostgreSQL integration tests exercised the classification CHECK constraint, search projection/vector/index behavior, target constraints, uniqueness, and schema assumptions in the isolated test database.

## Acceptance matrix

| Area | Status | Evidence | Severity |
|---|---|---|---|
| Environment | PASS | OL 9.8, Python 3.11.13 virtualenv, Django 5.2.18, psycopg 3.3.6, django-otp 1.7.3; PostgreSQL 16.15 active on loopback | — |
| Project structure | PASS | Seven approved domain apps; app/model inventory and source inspected | — |
| Model traceability | PASS | Independent verifier maps 46 models; no unexpected legacy domain app found | — |
| Authentication | PASS | Active custom `accounts.UserAccount`; normalized email, Django password primitives, session auth and verified-account service gates | — |
| MFA | PASS | django-otp TOTP support; staff editorial services require verified MFA and the required staff group; tests cover missing MFA | — |
| Ownership | PASS | Owner-scoped services and same-owner reference validation; cross-owner tests pass; no false RLS claim | — |
| Editorial versioning | PASS | Stable identities and exact immutable revision references; draft editing and lifecycle services inspected | — |
| Revision immutability | PASS | Stored and proposed parents checked; instance edits/deletes and queryset update/bulk/delete guards inspected; regression tests pass | — |
| Reviewer/Approver governance | PASS | Author submission, role/MFA checks, exact-revision review event, distinct reviewer and publisher, and prior-review requirement; governance tests pass | — |
| Lesson block validation | PASS | Only allow-listed paragraph structure; keys, payload, type and unique nonnegative positions validated; empty list accepted; validation runs on save and publication | — |
| Requirement classification | PASS | Exactly required/optional/recommended in model choices/validation and PostgreSQL CHECK; invalid DB value rejected in integration test | — |
| Practice/evidence | PASS | Distinct definitions/attempts, exact revision links, submitted-attempt eligibility, owner checks, immutable evidence, and one accepted attempt per requirement enforced/tested | — |
| Learning journey | PASS | Ordered append-only steps with exact typed target associations and private-target ownership checks; sequence/history tests pass | — |
| Notes/anchors | PASS | Owner-scoped note service; exact LessonRevision/block key and quote validation; offsets are hints; no cross-revision auto-reanchor | — |
| Planning | PASS | Immutable append-only PlanRevision snapshots, sequence/predecessor validation, same-owner context references; tests confirm prior history retained and no Progress dependency | — |
| Calculation foundation | PASS | Formula/version/result structures and version uniqueness/active-version constraints; historical result snapshots; no formula catalog or financial behavior required | — |
| Search | PASS | Derived projection service accepts only published current revisions; allow-listed text construction; exact-target uniqueness, target-kind CHECK, tsvector and GIN integration verified | — |
| Media foundation | PASS | Immutable metadata/version rows and queryset mutation guards; referenced rows protected; byte storage/delivery correctly deferred | — |
| Migrations | PASS | 21 migrations inspected; additive schema operations; graph/load and applied-vs-disk history match | — |
| PostgreSQL schema | PASS | `malilab` / `malilab_app`, owner correct, role lacks elevated flags, 56 exact tables, required constraints/indexes, no domain data | — |
| PostgreSQL isolation | PASS | Dedicated DB/role resolved; override safety tests present; test role denied CONNECT to live DB; temporary DB cleaned up | — |
| Tests | PASS | SQLite: 67 run, 62 pass, 5 skipped; PostgreSQL: 67 pass, none skipped or failed | — |
| Security | PASS | Production secret required from environment; debug defaults off; database credentials external to settings; no embedded credentials found | — |
| Legacy contamination | PASS | No legacy imports, old DB dependencies, or PostgreSQL 13 assumptions in application source/migrations | — |
| Documentation consistency | PASS with LOW note | Current PROJECT/ROADMAP and Round 3 report state acceptance pending and Phase 6B blocked; no false claim that formulas, media pipeline, or production are complete | LOW |

## Findings

### BLOCKER / HIGH

None identified in the approved Phase 6A scope.

### MEDIUM / LOW

- **LOW — stale historical environment note.** `docs/implementation/PHASE_6A_ENVIRONMENT_ISOLATION.md` still describes Round 2-era verification and a 56-test count. Its dated environment/status context is historical and does not claim Phase 6A acceptance; current project/roadmap and Round 3 status are accurate. No documentation was changed during this audit.
- **Audit limitation — no Git metadata.** The required initial working-tree snapshot was unavailable because the workspace is not a Git repository. This limits provenance comparison but did not prevent direct source, migration, database, and test verification.

### Deferred / out of scope

Formula activation governance and real financial formulas, full media byte storage/delivery, product UI/routes, production infrastructure/deployment, payment/subscription implementation, user-facing AI, voice/audio, advanced search, email delivery infrastructure, and registration/recovery UI remain deferred as specified. These are not Phase 6A rejection findings.

## Documentation reconciliation

The current `PROJECT.md`, `ROADMAP.md`, Phase 6A implementation report, and Round 3 report consistently say Round 3 remediation is complete, fresh acceptance was pending before this audit, and Phase 6B is gated. No current document falsely says Phase 6A was accepted, Phase 6B started, financial formulas are complete, the media pipeline is complete, or production deployment is complete. Older reports retain their historical dates and prior findings.

## Final verdict

PHASE 6A ACCEPTED — READY FOR PHASE 6B

This acceptance applies only to the scoped Phase 6A foundation. Stop here; Phase 6B work requires explicit owner authorization.
