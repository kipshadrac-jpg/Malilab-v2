# Phase 6A Remediation Round 2 Report

**Status: Remediation and verification complete — 2026-10-07.** This report records implementation work and evidence only. The independent Phase 6A acceptance audit has not been performed. Phase 6B remains blocked until acceptance passes.

## 1. Audit findings addressed

- Closed supported ORM bulk mutation paths for PracticeAttempt, PracticeResponse, RequirementEvidence, editorial revisions, revision-owned editorial records, review/publication events, and media version metadata.
- Preserved editable editorial drafts and the approved rule that one accepted Practice Attempt satisfies one Module Requirement.
- Completed source provenance snapshots with independent source identity and retrieval/access time fields, retaining source identity, title, URL/reference, publication date, version/reference, reviewer, and review time where available.
- Made MediaAsset rows immutable versions; protected referenced media through the existing revision foreign keys.
- Added isolated PostgreSQL integration test infrastructure without changing `malilab_app` privileges.
- Verified search projection behavior without adding domain seed data to `malilab`.
- Reconciled current Phase 6A status and deferred scope in implementation records.

## 2. Code changes

- Practice history querysets reject bulk create, update, bulk update, and delete. Submitted attempts and responses reject instance mutation/deletion. `delete_response` is an owner-scoped service for started attempts. Evidence remains append-only. Evidence creation reloads the owner-scoped persisted attempt state to avoid trusting stale in-memory state.
- Editorial event querysets reject bulk mutation/deletion. Existing revision and revision-owned record queryset guards remain in force; draft instance editing remains available. Supported lifecycle changes continue through editorial governance services.
- SourceSnapshot fills catalog values into independent snapshot fields at creation. Catalog edits do not alter snapshots.
- MediaAsset metadata cannot be updated through model save or queryset update. Referenced assets cannot be deleted because the revision reference uses `PROTECT`; unreferenced asset removal remains possible under the existing model policy.
- PostgreSQL test settings use a dedicated role/database configuration and fail if the configured test database name equals the configured development database name.
- Added practice, evidence, editorial history, provenance, media, and PostgreSQL schema/search regression tests.

Application immutability applies to supported Django model, queryset, and service paths. Arbitrary SQL executed with database credentials can bypass application guards; Django does not intercept every SQL statement. No PostgreSQL trigger, RLS, or database security weakening was introduced.

## 3. Models changed

- `PracticeAttempt`, `PracticeResponse`
- `RequirementEvidence` (existing append-only behavior retained and verified)
- `EditorialReview`, `PublicationEvent` (queryset guards)
- Existing `EditorialRevision` and revision-owned records (queryset/service boundary tests)
- `SourceSnapshot`
- `MediaAsset`
- PostgreSQL integration coverage for `SearchProjection` and schema constraints

## 4. Migrations

Created `content.0006_phase6a_remediation_provenance` with two nullable additions to SourceSnapshot: `source_identity_snapshot` and `retrieved_at`. Nullable columns avoid fabricating historical provenance for any pre-existing row. New snapshots copy the source identity and current catalog details when saved.

The migration was inspected before application. It has the existing `content.0005_relatedcontentrelationship` dependency and contains no data migration, legacy reference, destructive operation, or raw SQL. It was applied only to the clean development database `malilab` after reviewing the migration plan.

## 5. Immutability changes

Practice history queryset bulk operations are restricted. Submission still works through `submit_attempt`; started responses can be saved and deleted through owner-scoped services. A submitted response cannot be saved or deleted, and a submitted attempt cannot be deleted. Cross-owner service access is rejected. RequirementEvidence cannot be updated or deleted through instance, queryset, or service paths.

Editorial drafts remain editable. After review starts, revision content and its requirements/recommendations/other revision-owned records cannot be changed or deleted through supported instance or queryset paths. EditorialReview and PublicationEvent are append-only through instance and queryset paths. Historical relationship tests verify the exact referenced target remains intact after review begins.

The approved cardinality remains **one accepted Practice Attempt satisfies one Module Requirement**. A database partial unique constraint and service/model validation prevent one attempt from being accepted for a second requirement.

## 6. Source provenance changes

Re-read `docs/database/FIELDS.md`, `docs/database/DOMAIN_MODEL.md`, `docs/database/DATA_MODEL_AUDIT.md`, and the approved Phase 5 implementation specifications. SourceSnapshot now independently retains source identity, title, URL/reference, publication date, retrieval/access date, source version/reference, reviewer, and review timestamp fields. Values available from the mutable Source catalog are copied at snapshot creation; reviewer and review time must be present together when a snapshot claims review. Unknown publication/access dates remain nullable. A test mutates the Source catalog and confirms the historical snapshot retains its original values.

No legal or regulatory retention requirement was introduced. The current schema has no formula source snapshots because formula activation and financial formulas remain deferred.

## 7. Media integrity changes

`MediaAsset` is treated as the approved immutable asset/version row. Existing asset metadata cannot be changed by model save or queryset bulk update. A changed version requires a new row/key. Existing `PROTECT` foreign keys prevent deletion while a Playbook revision references the asset; tests verify reference integrity and mutation/deletion rejection.

This work does not add upload UI, byte storage, processing, transcoding, CDN, object storage, or delivery infrastructure. Historical byte retention is not claimed because the Phase 6A implementation stores metadata and references only.

## 8. PostgreSQL test architecture

The PostgreSQL test runner uses the separate `malilab_phase6a_test` role. That role has `CREATEDB` for Django’s disposable test database lifecycle, is `NOSUPERUSER` and `NOCREATEROLE`, and has no CONNECT privilege on live `malilab`. The development database is owned by `malilab_app`, not the test role. The test role cannot connect to or alter `malilab`; Django creates and drops only `test_malilab_phase6a`. The test credential is stored in the local `/home/opc/.pgpass` with mode 0600, not in project files. After the test run, the test database was absent.

`malilab_app` remains `NOSUPERUSER`, `NOCREATEDB`, and `NOCREATEROLE`. No application role privilege was changed. The test role is explicitly test-only and is not used by application settings.

## 9. SQLite test results

`./.venv/bin/python manage.py test --settings=config.test_settings` — **56 tests run; 52 passed and 4 PostgreSQL-only integration tests skipped; overall OK.** SQLite is the application behavior test layer, not PostgreSQL schema evidence.

## 10. PostgreSQL test results

`./.venv/bin/python manage.py test --settings=config.postgres_test_settings` — **56 tests run; all passed** against the isolated PostgreSQL test database. Django applied the migrations to the isolated database, executed schema and search integration checks plus all application tests, and dropped the test database afterward.

The PostgreSQL-specific checks verified migrations and expected public tables, no unexpected tables, JSONB, the partial unique evidence index, revision uniqueness/constraints, search target constraints, search vector generation/querying, and the search GIN index. Search tests create temporary fixtures only in the isolated test database.

## 11. Database verification

- PostgreSQL 16.15; database `malilab`; connection role `malilab_app`.
- `scripts/verify_schema.py`: **56 public tables exactly match expected Django/framework/migration tables**, 16 MaliLab migration records match migration files, required constraints and GIN search index present, and no domain seed/import data.
- The database has 37 total `django_migrations` rows after adding `content.0006`.
- `scripts/inspect_migrations.py`: all 19 project and OTP migrations inspected; additive schema operations only; no project data migrations or destructive SQL found.
- `manage.py check` passed. `makemigrations --check --dry-run` reported no changes. `migrate --plan` showed only `content.0006_phase6a_remediation_provenance` before it was applied.
- The isolated test database was dropped after tests. `test_malilab_phase6a` was absent at final inspection.

## 12. Ownership verification

Practice service tests reject cross-owner response writes/deletes and attempt lookup. Evidence validation requires the evidence owner to own the submitted attempt and requires the exact practice revision/requirement references. Existing ownership tests cover notes, journeys/targets, plans, calculations, evidence, completions, and awards. No RLS was introduced.

## 13. Search verification

PostgreSQL tests create a current published LessonRevision and verify projection creation, populated `tsvector`, and a matching text search. They verify projection target/revision uniqueness, reject invalid target kind/FK combinations, and confirm unpublished or non-current revisions are not exposed. Schema checks verify the GIN index. All search fixtures are temporary test data; the live `malilab` database remains free of domain rows. No external search infrastructure or seeded search projection was added.

## 14. Documentation reconciliation

Updated `PROJECT.md`, the Phase 6A implementation and round 1 remediation reports, `TRACEABILITY_MATRIX.md`, environment audit/isolation records, and both roadmap documents. Current records now state that PostgreSQL 16 is current, PostgreSQL 13 and the old legacy application are removed, `malilab` is the clean development database, remediation round 2 is complete, independent acceptance is pending, and Phase 6B is blocked. Traceability explicitly defers formula activation governance, full media pipeline, production deployment, complete email delivery, and registration/recovery UI. The one-attempt/one-requirement rule is consistently stated.

## 15. Remaining deferred items

Formula activation governance, formula seeding and real financial formulas; product UI and public routes; subscriptions/payments; user-facing AI; voice/audio; full media storage/processing/delivery; external search; production deployment; complete email delivery and registration/recovery UI remain out of scope. No formulas were seeded or activated.

## 16. Remaining risks

- Application guards do not protect against arbitrary raw SQL executed with a database role that has write access. The approved boundary is Django’s supported application path; this report does not claim universal SQL immutability.
- The test role has CREATEDB to create disposable test databases but cannot CONNECT to `malilab`; its credential remains local and outside the repository.
- Media bytes are not stored by this foundation, so historical byte retention/delivery has not been verified.
- Search projections are synchronous and PostgreSQL-specific; no background rebuild infrastructure exists.
- Independent acceptance has not yet evaluated this remediation.

## 17. Deviations from Phase 5

No product or architectural decision was changed. The migration adds only approved source provenance snapshot fields that were missing from the implementation. The dedicated isolated PostgreSQL test role is test infrastructure and leaves the application role privileges unchanged. No formula governance, RLS, production deployment, legacy compatibility, or later-phase feature was added.

## 18. Independent acceptance status

This report submits the implementation and verification evidence for a separate independent acceptance audit. It does not perform that audit and makes no Phase 6A acceptance verdict. Phase 6B must remain blocked until independent acceptance passes.
