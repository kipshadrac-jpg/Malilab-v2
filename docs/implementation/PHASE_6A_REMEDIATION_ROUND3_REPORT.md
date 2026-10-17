# Phase 6A Remediation Round 3 Report

**Status: REMEDIATION COMPLETE; fresh independent acceptance is pending — 2026-10-08.** This report records the six targeted blocker fixes and verification. It does not declare Phase 6A accepted and does not authorize Phase 6B.

## Scope

Only the six reported remediation areas were changed: local PostgreSQL verification, reviewer-before-publication workflow, revision-owned record immutability, requirement classification, lesson-block validation, and PostgreSQL test isolation. No legacy repository/data, financial formulas, formula activation, production deployment, or unrelated UI/product feature was introduced. No domain rows were seeded in `malilab`.

## Blockers and fixes

1. **PostgreSQL verification.** Confirmed from the host: PostgreSQL 16.15 is active under `postgresql.service`; `pg_isready -h 127.0.0.1 -p 5432` accepts connections; listeners are loopback only (`127.0.0.1` and `::1`). Django connects as `malilab_app` to `malilab`. The application role is not superuser, CREATEDB, or CREATEROLE; it owns `malilab`. No PostgreSQL security or authentication configuration was changed. Sandbox access was not needed for host checks.
2. **Reviewer before publication.** Added `review_revision`, requiring authenticated MFA staff with the Reviewer role and recording an append-only `reviewed` event on the exact revision. `approve_and_publish` now requires that event on its exact revision and rejects the same person as Reviewer and Approver/Publisher. Existing author/approver separation remains. Publication without review and review of a different revision fail.
3. **Revision-owned record immutability.** `RevisionRecord` now checks the stored parent and proposed parent before save and delete. A record under a reviewed/published revision cannot be reparented to a draft; editing or deletion after an attempted reparent remains blocked. Existing queryset bulk update/delete guards remain. This is supported ORM/application-path protection, not a claim of raw SQL protection. The guard applies to module requirements, playbook recommendations, topic assignments, source snapshots, and related content records through their parent-resolution methods.
4. **Requirement classification.** `ModuleLearningRequirement.classification` now has only `required`, `optional`, and `recommended` model choices, model validation, and PostgreSQL `CHECK requirement_classification_valid`. Existing completion evaluation blocks only on unsatisfied `required` records; optional and recommended remain non-blocking.
5. **Lesson blocks.** `LessonRevision` validates block payloads before save, and submission/publication validate lesson blocks again. Following the approved field specification and existing paragraph type, a supported block has `key` (UUID), `type: paragraph`, nonnegative unique `position`, and a `payload` object containing non-empty string `text`. Empty lists remain valid. Unsupported types, extra/missing fields, malformed objects, and invalid structured values fail. Search and note-anchor readers consume the validated payload. No new block type or editor was created.
6. **PostgreSQL test isolation.** `config.postgres_test_settings` now defaults to a dedicated database and role and rejects `malilab` under either database override, the configured development database, `malilab_app`, and the configured development role. Tests cover safe settings and unsafe overrides. The test role cannot connect to the live `malilab` database. PostgreSQL tests used `test_malilab_phase6a`, which was dropped by Django after the run; the live database was never a test target.

## Migrations

Created `content.0007_phase6a_remediation_round3` and `content.0008_phase6a_remediation_round3`. Both were inspected with `sqlmigrate` before application. 0007 adds only the classification check (the `choices` alteration is migration state); 0008 changes only Django validation metadata to permit the already supported empty block list. There are no destructive operations, data migrations, legacy imports, or unrelated schema changes. Both were applied to `malilab`; historical migrations were not modified.

## Tests and checks

- `manage.py check` — passed.
- `manage.py makemigrations --check --dry-run` — passed; no model/migration drift.
- `scripts/verify_traceability.py` — passed; all 46 domain models mapped.
- `scripts/inspect_migrations.py` — passed; 21 project/framework migrations inspected, no project data operations or destructive SQL.
- `scripts/verify_schema.py` — passed after migration.
- SQLite: `manage.py test --settings=config.test_settings` — 67 discovered; 62 passed; 5 PostgreSQL-only tests skipped; 0 failed.
- PostgreSQL: `manage.py test --settings=config.postgres_test_settings` — 67 discovered; 67 passed; 0 skipped; 0 failed. This included five PostgreSQL integration tests, including the invalid-classification database-constraint check.

## PostgreSQL verification

After migration and after PostgreSQL tests: PostgreSQL 16.15 (`160015`); database `malilab`; role `malilab_app`; owner `malilab_app`; application role is NOSUPERUSER/NOCREATEDB/NOCREATEROLE. `malilab_phase6a_test` has no CONNECT or CREATE privilege on live `malilab`. The temporary test database was absent after test cleanup. The live database has 56 public tables, exactly matching expected Django/framework/migration tables; no unexpected public tables; 18 MaliLab app migration records match disk migrations; and no domain data. Required classification, evidence, plan-revision, journey-step, and search constraints were present, as was the search-vector GIN index. The read-only schema verifier also checks PostgreSQL version, application role privileges, table set, migration set, and absence of domain rows.

## Remaining limitations and deferred functionality

- Immutability applies to supported Django instance/queryset/service operations. No database triggers or universal raw-SQL protection were added.
- The only currently supported lesson block type is paragraph; other types described as possible in the logical specification remain unsupported until separately specified and implemented.
- Empty lesson block arrays are accepted by the current schema/model; no publish checklist requirement for non-empty lessons was invented.
- Formula catalog, financial formulas, formula approval/activation, UI/editor functionality, email delivery and registration/recovery flows, media-byte storage/delivery, and production deployment remain deferred.
- This work has not performed an independent acceptance audit. Phase 6A acceptance remains pending; Phase 6B remains blocked.

## Status

**PHASE 6A REMEDIATION ROUND 3 COMPLETE.** Ready for a fresh independent Phase 6A acceptance audit.
