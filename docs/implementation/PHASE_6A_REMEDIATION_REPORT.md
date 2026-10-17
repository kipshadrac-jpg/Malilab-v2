# Phase 6A Remediation Report

**Status: Round 1 record; verification details superseded by [Remediation Round 2](PHASE_6A_REMEDIATION_ROUND2_REPORT.md).** This historical report is retained for the earlier work. Round 2 is complete; independent Phase 6A acceptance remains required and Phase 6B remains blocked.

## 1. Findings addressed

- Protected reviewed and published editorial revisions and their revision-owned relationships from ordinary model saves, deletes, bulk updates, and bulk deletes while preserving draft editing.
- Restricted editorial lifecycle and current-revision pointer changes to the governance publication service. Publishing now refreshes the public search projection in the same transaction.
- Added validated, ordered, append-only Journey Step creation with exact target subtype, target kind, FK, and owner checks. Target registry/subtype history is frozen once referenced.
- Added RequirementEvidence validation for exact revisions, matching requirement/attempt/activity, submitted attempts, and owner identity. An accepted attempt can satisfy at most one requirement.
- Added exact-revision Module Completion evaluation and immutable explanatory snapshots. Only missing required requirements block completion.
- Validated note highlight block keys and selected quotes against the pinned LessonRevision’s structured content. Offsets remain non-authoritative hints; no cross-revision reanchoring was added.
- Made PostgreSQL search projection generation populate `tsvector`, maintain only a current published revision per editorial identity, and enforce one matching target per projection.
- Strengthened ownership checks across journeys, attempts, notes, evidence, completions, plans, calculation results, lesson completions, and awards.
- Removed unsafe production settings defaults: DEBUG is false by default and forced false in production; production requires a configured secret and explicit non-wildcard host allowlist.
- Reconciled current Phase 6A status in project and implementation documentation.

## 2. Files changed

- `PROJECT.md`
- `config/settings.py`, `config/postgres_test_settings.py`
- `content/models.py`, `content/services.py`, `content/tests.py`
- `practice/models.py`, `practice/services.py`
- `planning/models.py`, `planning/tests.py`
- `calculations/models.py`, `calculations/tests.py`
- `learning/models.py`, `learning/services.py`, `learning/tests.py`, `learning/test_phase6a.py`
- `discovery/models.py`, `discovery/services.py`, `discovery/tests.py`, `discovery/test_postgres_integration.py`
- `learning/migrations/0003_enforce_phase6a_integrity.py`
- `discovery/migrations/0002_enforce_phase6a_integrity.py`
- `scripts/inspect_migrations.py`, `scripts/verify_schema.py`
- `docs/implementation/PHYSICAL_DATA_MODEL.md`
- `docs/implementation/PHASE_5B_DECISION_BRIEF.md`
- `docs/implementation/PHASE_6A_IMPLEMENTATION_REPORT.md`
- `docs/implementation/ROADMAP.md`

## 3. Models changed

- Editorial revisions now reject non-draft content edits and deletion; reviewed revision state changes go through the editorial governance service. Draft revisions remain editable.
- `ModuleLearningRequirement`, `PlaybookModuleRecommendation`, topic assignments, source snapshots, and related-content relationships are protected by their owning revision’s lifecycle. Editorial reviews and publication events are append-only.
- `JourneyStep` has deterministic `(sequence, pk)` ordering and append-only behavior. Journey target registry rows and typed subtype links are validated and become immutable after a step references them.
- `RequirementEvidence`, `ModuleCompletion`, and `LessonCompletion` are append-only and validate historical references.
- Notes validate exact revision-local anchors. Practice attempts and submitted responses, calculation results, plan revisions, and achievement awards enforce immutable or owner-consistent snapshots.
- Search projections enforce target-kind consistency and one projection per exact target revision.

## 4. Migrations created

- `discovery.0002_enforce_phase6a_integrity`: target-kind CHECK and four conditional unique constraints, one for each projection target FK.
- `learning.0003_enforce_phase6a_integrity`: deterministic Journey Step model ordering.

## 5. Database changes

- Migrations were applied to the clean development database `malilab` as `malilab_app` after inspecting the plan and generated SQL.
- No data migration, raw SQL schema change, legacy import, or destructive operation was applied.
- PostgreSQL remains loopback-only (`listen_addresses=localhost`, port 5432). PostgreSQL 16.15 is accepting connections; Django connected to `malilab` as `malilab_app` using the existing local credential source without printing or recording the password.
- Round 1 used a separate test database. Round 2 replaced its test architecture with `malilab_phase6a_test`, which has CREATEDB solely for Django-managed isolated test database lifecycle and has no CONNECT privilege on live `malilab`. `malilab_app` remains NOCREATEDB, NOCREATEROLE, NOSUPERUSER.

## 6. Constraints added or changed

- `search_projection_target_kind_match` ensures exactly one target FK is populated and agrees with `content_kind`.
- `search_playbook_revision_uniq`, `search_module_revision_uniq`, `search_lesson_revision_uniq`, and `search_practice_revision_uniq` are conditional unique constraints on non-null target FKs.
- Existing `evidence_attempt_accepted_uniq` remains a PostgreSQL partial unique index, enforcing at most one accepted evidence association per attempt.
- Existing exact evidence, ordered requirement, unique journey sequence, foreign-key, and relationship-kind constraints remain present.

## 7. Indexes added or changed

- PostgreSQL creates one partial unique index for each new search projection conditional uniqueness constraint.
- Existing `search_vector_gin_idx` remains present and was verified as a GIN index.
- No unrelated index was removed or replaced.

## 8. Services added or changed

- `append_journey_step` validates owner, target kind, target subtype, and target reference and appends the next sequence while locking the journey.
- `record_requirement_evidence` records one explicit evidence decision for one exact requirement and eligible submitted attempt.
- `evaluate_module_completion` evaluates the exact active requirement set on the requested ModuleRevision and stores exact evidence context.
- `submit_attempt` establishes the submitted/eligible PracticeAttempt state.
- `validate_note_anchor` checks a stable key and quote against text/content in the pinned LessonRevision.
- Search rebuild services now assemble allow-listed text, populate PostgreSQL `tsvector`, delete stale/non-current projections, and admit only current published revisions. Editorial publication synchronously refreshes its projection.

## 9. Tests added

- SQLite lifecycle, ownership, journey, evidence, completion, note, and search tests were added or extended.
- PostgreSQL-only integration tests cover migration/schema state, JSONB, partial uniqueness, search target constraints, `tsvector`, current published revision eligibility, and the GIN index.
- The project traceability verifier reports 46 domain models mapped to requirements and test modules.

## 10. SQLite test results

`./.venv/bin/python manage.py test --settings=config.test_settings` — **Round 1: 46 tests run; 43 passed, 3 PostgreSQL-only tests skipped. Round 2: 56 tests run, 4 PostgreSQL-only tests skipped; all others passed.** This is the existing SQLite unit-test layer plus the new tests.

## 11. PostgreSQL test results

`./.venv/bin/python manage.py test --settings=config.postgres_test_settings` — **Round 1: 46 tests run. Round 2: 56 tests run; all passed.** Django created and dropped the dedicated PostgreSQL test database. These results include the PostgreSQL-specific integration tests and the application ownership/domain tests.

## 12. Schema verification results

- `manage.py check --database default` — passed.
- `manage.py makemigrations --check --dry-run` — no model/migration drift.
- `manage.py migrate --check` — no unapplied migrations.
- `scripts/verify_schema.py` — passed: PostgreSQL 16.15; 56 public tables exactly match Django model tables, framework/integration tables, implicit many-to-many tables, and migration bookkeeping; 16 MaliLab migration records match disk; required constraints and GIN index present; no domain seed/import data.
- `scripts/inspect_migrations.py` — generated SQL inspected for project and OTP migrations; only additive operations were accepted; no destructive SQL or project data operation was found.
- Direct inspection confirmed the search GIN index, partial search uniqueness indexes, accepted-evidence partial unique index, FK/CHECK/unique constraints, loopback listener, 56-table count, and migration records.

## 13. Ownership verification

- Journey owner, private target owner, target registry owner, and target subtype must agree.
- Evidence owner must own the submitted attempt; the attempt’s exact PracticeRevision must match the requirement’s exact PracticeRevision.
- Completion, lesson completion, plan, calculation result, note, and award references are checked against the same owner where the Phase 5 specification requires it.
- Cross-account tests pass for notes, attempts, journeys/targets, plans, calculations, evidence, and completions. No PostgreSQL RLS was introduced.

## 14. Editorial immutability verification

- Draft revisions and draft-owned requirements remain editable.
- Once review begins, editorial revision content and revision-owned records cannot be changed or deleted through model instance or bulk queryset paths. Event records are append-only.
- Lifecycle transitions and current published revision pointer updates are restricted to the editorial governance service; author/approver separation and MFA checks remain in force.
- Tests cover draft editing, rejected post-review mutation/deletion, bulk mutation, approved publication, and projection refresh.

## 15. Journey verification

- Tests cover valid targets, wrong target object/kind, cross-account private target, exact target relationship preservation, mutation/deletion rejection, deterministic order, and sequential append behavior.
- A typed target must resolve to exactly one matching subtype record. Journey steps remain append-only.

## 16. Requirement Evidence verification

- Tests cover valid evidence, wrong ModuleRevision, wrong requirement, wrong PracticeRevision, wrong attempt revision, unsubmitted attempt, and cross-user evidence.
- An accepted attempt is associated with one requirement only; evidence is explicit and does not transfer to a new ModuleRevision.

## 17. Module Completion verification

- Tests cover all required evidence present, a missing required item, absent optional and recommended items, evidence tied to another module revision, and exact-revision evaluation.
- The immutable snapshot contains the exact active requirement set and exact evidence identifiers. Optional and recommended items do not block completion.

## 18. Note anchor verification

- Tests cover valid pinned revision/block/quote, missing block, quote absent from content, and malformed offsets.
- Block keys and selected quote are authoritative; offsets remain hints. No automatic reanchoring was implemented.

## 19. Search verification

- PostgreSQL tests verify `tsvector` population and query matching, JSONB filter metadata, projection target CHECK and conditional uniqueness, the GIN index, and removal of an old revision projection when a new current published revision is rebuilt.
- Publication refreshes the projection transactionally. Unpublished or non-current revisions are removed/omitted. Search remains PostgreSQL-only; no external search service was added.

## 20. Security configuration verification

- Development defaults to `DEBUG=False`; local development can opt into debug explicitly and receives a process-generated local secret if none is configured.
- `DJANGO_ENV=production` forces `DEBUG=False`, requires `DJANGO_SECRET_KEY`, and requires explicit non-wildcard `DJANGO_ALLOWED_HOSTS` values. A production-settings check with `DJANGO_DEBUG=1` confirmed DEBUG remains false.
- Database host defaults to loopback; PostgreSQL reports `listen_addresses=localhost`. Credentials remain in the existing local source and were not printed, logged, or committed.

## 21. Deferred items

Phase 6B, full UI/public routes, subscriptions/payments, user-facing AI, voice/audio, production deployment, advanced search infrastructure, formula activation or financial formulas, media processing, full email delivery, and account export/deletion remain deferred. No unresolved product rule was invented.

## 22. Remaining risks

- Immutability and cross-row ownership guarantees are enforced at the approved Django model/service boundary. Raw privileged SQL can bypass application-level guards; Phase 5 does not require database triggers or RLS.
- Search projections are derived and synchronous. Rebuild/update services must be used after approved publication changes; a separate worker/outbox was not introduced.
- Account deletion/export and operational backup expiry remain governed by their approved later operational decisions.

## 23. Deviations from Phase 5

No architectural or product-rule deviation was made. Round 2 adds application ORM mutation guards, source identity/retrieval snapshot fields, and immutable media version metadata guards; details and current test counts are in the Round 2 report. The implementation follows the approved typed Journey target adapter, exact-revision evidence, one accepted attempt per requirement, revision-local note anchors, PostgreSQL search projection, and application-service ownership policy. No PostgreSQL RLS, external search system, new lifecycle, or Phase 6B behavior was added.

**Stopping point:** remediation and verification are complete. A separate Phase 6A acceptance audit remains required; this run did not perform it and did not begin Phase 6B.
