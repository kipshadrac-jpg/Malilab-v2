# Phase 6B.1–6B.3 Remediation Report

**Status: Remediation complete; ready for independent re-audit.** This report records the acceptance-blocker work only. No Phase 6B.4 or later work was performed.

## 1. Scope

Addressed the HIGH Lesson context ownership defect, aligned runtime Lesson block validation with the Phase 6A model contract, added focused public-reader regression tests, investigated the incomplete test runs, and reran the relevant SQLite and PostgreSQL suites. No schema or infrastructure changes were needed.

## 2. Audit Findings Addressed

- **HIGH:** Automatic Lesson context inference could use a Module whose current pointer referenced another Module's revision.
- **MEDIUM:** Runtime validation could display malformed paragraph-shaped stored blocks that the model validator rejects.
- **Test verification blocker:** The audit's SQLite and PostgreSQL test processes did not return results and reported uninterruptible filesystem waits.

## 3. Root Cause of the HIGH Ownership Defect

`lesson_detail` previously issued its own `Module.objects.filter(...)` query for automatic context. It checked publication status and Lesson membership but did not check that the pointed `ModuleRevision.module_id` equaled the candidate `Module.id`. That query bypassed the ownership condition already enforced by the shared public Module catalogue/resolver path. A corrupted pointer could therefore supply an unrelated revision as the source of Previous/Next links.

## 4. Exact Code Changes

- Added `public_lesson_modules()` in `content/public.py`. It starts from `public_modules()`, which requires a published Module, a published pointed revision, and `current_published_revision.module_id == Module.id`, then filters membership of the exact LessonRevision.
- Changed automatic context discovery in `content/views.py::lesson_detail` to use that shared public resolver/query path. Existing behavior for zero or multiple valid contexts remains fail-safe: no inferred navigation is selected.
- Changed runtime block validation to call the shared `validate_lesson_blocks()` model/content validator. Invalid stored JSON produces the existing unavailable-content state and an empty rendered block list. Valid blocks remain sorted by `position` and Django template escaping remains in force.
- Added public behavior tests for mismatched current Module pointers, invalid supplied Module context, multiple valid Module contexts, stale ModuleRevision navigation, malformed block shapes, escaped HTML, and valid block ordering.

No model, migration, settings, URL, template, route, dependency, database, or PostgreSQL configuration changes were made.

## 5. Ownership Invariant Implemented

Whenever an automatic public Lesson context is considered, the candidate comes through `public_modules()`, whose query enforces:

```text
Module.current_published_revision.module_id == Module.id
```

The pointed revision and Module must also be published. A mismatched pointer is ignored for inferred context. An explicitly supplied `?module=` still goes through `resolve_public_revision()` and returns 404 when its current pointer is mismatched. No data is repaired and no unrelated revision fallback is attempted.

## 6. Lesson Navigation Invariant

Navigation is calculated only from the validated Module object's exact current published revision. `public_module_lessons()` selects active Lesson requirements from that revision and only current published Lesson revisions. The target LessonRevision must occur in that ordered result before either neighbor is exposed. Ambiguous inferred Module membership suppresses navigation; it does not choose one arbitrarily.

## 7. Runtime Block-Validation Correction

The reader now uses the approved `validate_lesson_blocks()` allow-list directly. It rejects missing/invalid UUID keys, missing or unsupported types, missing/invalid/negative positions, malformed payloads, missing or empty text, extra fields, and duplicate keys or positions. A malformed revision is not reinterpreted as a paragraph. The public response follows the existing unavailable-content policy and renders no malformed block. Valid blocks retain deterministic position ordering; text continues to be autoescaped by Django.

## 8. Tests Added

Added tests assert actual rendered public behavior for:

- A deliberately corrupted Module A pointer to Module B's published revision: no unrelated Previous/Next links appear, and explicitly supplying the invalid Module slug is rejected.
- Multiple valid current Module memberships: no arbitrary context or cross-Module links appear.
- A stale ModuleRevision with a different neighbor from the current revision: only the current revision's neighbor is rendered.
- Corrupt stored blocks with missing/invalid keys, missing/unsupported type, missing and invalid position, unexpected fields, malformed/missing/empty/non-text payload text, and duplicate keys/positions. Malformed content shows the existing unavailable state and is not rendered; markup is not executed.
- Existing valid block ordering and escaped HTML behavior remain covered.

Focused new regression run: **4 discovered, 4 passed, 0 failed, 0 skipped, 0 errors; 0.563 seconds**.

## 9. Test-Execution Problem Investigation

The audit report said its test commands printed test-database creation and then remained in `D` state in `folio_wait_bit_common`. That report did not preserve process stacks or establish whether those exact processes were in migration, test execution, or teardown, so their precise internal phase cannot be recovered from the audit alone.

This remediation reproduced two related symptoms:

1. The targeted SQLite public-reader suite created its in-memory test database, applied migrations, ran tests, and tore down normally. The complete SQLite suite also completed.
2. PostgreSQL initially refused to start because the configured isolated `test_malilab_phase6a` database already existed. Read-only checks showed it was owned by `malilab_phase6a_test`, had no active sessions, and was not `malilab`. The first command exited at test database setup rather than deleting it interactively. After confirming the target and isolation, the run used Django's `--noinput` option to replace only that configured disposable test database. Migrations, execution, and teardown then completed successfully.

During simultaneous Django system/migration/schema commands, two short-lived Python processes printed successful results but entered `D` state at `folio_wait_bit_common`. The workspace is on the root XFS volume. At that time the environment reported about 14 MiB free memory, roughly 438 MiB swap in use, high swap-in and disk-I/O wait, and host CPU steal. After stopping those stuck checks, rerunning migration drift and schema verification **serially** returned exit code 0. This supports transient environment memory/page-I/O pressure as the likely source of the observed filesystem waits; it does not prove the precise cause of the earlier audit processes. No project test setting, PostgreSQL security/isolation policy, or server configuration was weakened.

## 10. SQLite Results

Command: `.venv/bin/python manage.py test --settings=config.test_settings --verbosity 2`

**82 discovered; 77 passed; 0 failed; 5 skipped (PostgreSQL-only); 0 errors; 55.699 seconds.** The complete suite exercised Phase 6A regression tests and the Phase 6B.1–6B.3 public-reader tests.

## 11. PostgreSQL Results

Command: `.venv/bin/python manage.py test --settings=config.postgres_test_settings --verbosity 2 --noinput`

**82 discovered; 82 passed; 0 failed; 0 skipped; 0 errors; 83.789 seconds.** This included all PostgreSQL integration tests and Phase 6A regression tests. Django reported successful destruction of `test_malilab_phase6a` after the run.

## 12. Phase 6A Regression Results

The complete supported application suite ran under both backends. All account, content governance/integrity, calculation, discovery, learning/evidence/journey/note, planning, practice, PostgreSQL test-settings safety, and PostgreSQL schema/search integration tests passed. The SQLite run skipped only the five PostgreSQL-only integration tests; those five passed in the PostgreSQL run.

## 13. Django, Migration, and Schema Checks

- `manage.py check`: **PASS**, no issues.
- `manage.py makemigrations --check --dry-run`: **PASS**, no changes detected; final serial invocation exited 0.
- `scripts/verify_schema.py`: **PASS**, final post-test invocation exited 0. PostgreSQL 160015; 56 public tables match expected models/framework/bookkeeping; 18 Phase 6A migrations; expected constraints and search GIN index present; no domain seed/import data.
- No migration was required or created.

## 14. Test-Isolation Evidence

- SQLite uses the configured in-memory database.
- PostgreSQL tests used the existing dedicated `malilab_phase6a_test` role and the disposable `test_malilab_phase6a` database. The role was not created or modified in this remediation.
- PostgreSQL settings safety tests passed in both complete suites.
- After PostgreSQL teardown, a direct check found no `test_malilab_phase6a` database and no sessions to it. The test role still has no CONNECT privilege on live `malilab`.
- No PostgreSQL server configuration, application-role privilege, `pg_hba.conf`, or isolation guard was changed.

## 15. Live Database Safety Verification

The post-test schema verifier connected to `malilab` as `malilab_app` and passed. It confirmed the expected 56-table schema, migration set, required constraints/index, and zero domain seed/import rows. The live database was never a test target. No production/live content was created or changed.

## 16. Files Changed

- `content/public.py`
- `content/views.py`
- `content/test_public.py`
- `docs/implementation/PHASE_6B_1_3_REMEDIATION_REPORT.md`

The workspace has no Git metadata. Before editing, the relevant implementation files and modification times were recorded through direct filesystem inspection; the inspected source files predated this remediation. The existing implementation report and acceptance audit also had timestamps preceding this remediation and were read without modification. Test execution regenerated Python bytecode under `content/__pycache__/` for the three imported modules. No unrelated modification was overwritten or cleaned up.

## 17. Files Intentionally Not Changed

`content/models.py`, migrations, settings, URL configuration, templates, CSS, PostgreSQL server configuration, the live database, project/roadmap documents, and all later-phase features were left unchanged. No dependency or seed content was added.

## 18. Remaining Findings

No known code, schema, test, or isolation blocker remains for this remediation. The earlier filesystem wait cause is not provable for the specific vanished audit processes; this run established that the supported suites complete serially and that resource-pressure waits can occur in this environment. Browser, viewport, and performance verification were not performed and are not claimed.

## 19. Acceptance Readiness

The ownership boundary, exact-revision navigation, malformed-block fail-closed behavior, focused regressions, full SQLite suite, full isolated PostgreSQL suite, migration drift check, Django check, schema verification, test-database cleanup, and live database safety verification all passed. This is remediation evidence for independent re-audit; it is not an acceptance decision.
