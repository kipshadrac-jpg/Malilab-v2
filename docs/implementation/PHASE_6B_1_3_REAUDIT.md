# Phase 6B.1–6B.3 Fresh Independent Re-Audit

## 1. Scope

**PASS** — Audited only Phase 6B.1 application shell, 6B.2 exact public revision delivery, and 6B.3 Playbook → Module → Lesson reader. The audit included source and test inspection, focused and complete test runs, live schema checks, and PostgreSQL test isolation checks. No code, tests, migrations, settings, database content, PostgreSQL configuration, or nginx configuration were changed. This report is the only file created by this audit.

## 2. Evidence Reviewed

- `content/public.py`, `content/views.py`, `content/test_public.py`, and `content/models.py`
- `config/urls.py`, SQLite/PostgreSQL test settings, and PostgreSQL settings safety tests
- All `content/templates/content/` templates and `content/static/content/site.css`
- `scripts/verify_schema.py`, migrations, the prior acceptance audit, and the remediation report (the latter treated as a lead, not proof)
- Read-only PostgreSQL database, session, ownership, and CONNECT privilege queries
- Commands and independently observed outcomes recorded in sections 12–16

**NOT VERIFIABLE** — The workspace has no `.git` metadata, so no source-control diff or history is available. Filesystem timestamps and the complete file inventory provide the change-boundary evidence instead.

## 3. Remediation Verification

**PASS** — `public_lesson_modules()` in `content/public.py` begins with `public_modules()` and then filters that queryset by membership in `current_published_revision.learning_requirements`. `public_modules()` requires published Module status, published pointed ModuleRevision status, and `current_published_revision__module_id=F('pk')`. Therefore the ownership invariant `Module.current_published_revision.module_id == Module.id` is enforced in SQL before a Module can be considered an automatic Lesson context. The membership traversal is through that exact current revision and requires an active Lesson requirement pointing to the exact resolved LessonRevision.

**PASS** — `lesson_detail()` calls this shared path for inference. Explicit `?module=` input goes through `resolve_public_revision()`, which verifies current pointer existence, published revision status, and ownership before checking membership. No arbitrary or unrelated revision fallback exists.

**PASS** — Runtime Lesson validation calls the model-level `validate_lesson_blocks()` directly. There is no weaker duplicate validator in the reader.

## 4. Original HIGH Defect Re-Test

**PASS** — `content.test_public.PublicReaderTests.test_automatic_context_ignores_mismatched_module_pointer` uses an actual HTTP request with Module A pointing at a published ModuleRevision owned by Module B. It asserts the Lesson still returns safely, no foreign Previous/Next links appear, and explicitly supplying Module A returns 404. This demonstrates that the mismatched Module is excluded from automatic context and is rejected as explicit context; neither Module B navigation nor fallback navigation is exposed through Module A.

**PASS** — This test ran in the focused, SQLite, and PostgreSQL suites. The test creates the corrupted pointer with a direct queryset update because normal model guards reject the state, then exercises the public HTTP layer.

## 5. Exact Revision Navigation

**PASS** — Automatic contexts come only from ownership-validated public Modules and their exact current published ModuleRevision. Explicit contexts use the same public revision resolver. `public_module_lessons()` receives that exact ModuleRevision, selects only its active Lesson requirements, and admits only published Lesson identities whose current pointer equals the related published LessonRevision. Requirement position determines deterministic order.

**PASS** — `lesson_detail()` obtains Previous/Next only from that ordered result and only when the current resolved LessonRevision is in it. Stale ModuleRevisions, historical LessonRevisions, inactive relationships, and cross-Module relationships cannot supply neighbors. Multiple valid Module contexts suppress inferred navigation. Tests cover stale/current ModuleRevision separation, ambiguous membership, and the mismatched-owner case. Neighbors cannot cross ModuleRevision boundaries.

## 6. Lesson Block Validation

**PASS** — The runtime reader uses the approved `validate_lesson_blocks()` model contract, which checks that the root is a list; each block is an object with exactly `key`, `type`, `position`, and `payload`; keys parse as UUIDs and are unique; type is `paragraph`; positions are unique nonnegative integers but not booleans; payload contains exactly `text`; and text is a nonempty string. This rejects missing keys, invalid UUIDs, missing/unsupported types, missing/invalid/negative/boolean/string positions, malformed payloads, missing/empty/non-string text, unexpected fields, duplicate keys, duplicate positions, and malformed list structures.

**PASS** — On `ValidationError`, the view supplies an empty block list and the existing “temporarily unavailable” state. It does not reinterpret or render malformed data. For valid content, blocks are sorted by position. The template emits text in an ordinary Django template expression without `safe`, so HTML is escaped. Tests exercise the malformed stored shapes, fail-closed response, script-text escaping, and valid deterministic ordering. The validator’s root-list check is present in the exact function used by the view.

## 7. Application Shell

**PASS (source-level accessibility)** — `base.html` provides semantic header, navigation, main, and footer landmarks; a skip link to the focusable main target; ordinary server-rendered links; and a viewport meta element. CSS provides `:focus-visible` outlines, a revealed skip link, flexible layout rules, and a narrow-screen breakpoint that stacks header and lesson navigation. No client-side JavaScript is needed for navigation.

## 8. Playbook Delivery

**PASS** — Public catalogue and detail resolve only published Playbook identities with their exact current published, owned revision. Recommendations are drawn from the exact resolved PlaybookRevision, are active, and point only to a ModuleRevision that is itself published, owned by a published Module, and is that Module’s current pointer. Ordering is deterministic. No stale recommendation revision is exposed. Focused HTTP tests cover the public recommendation path and invalid revision ownership.

## 9. Module Delivery

**PASS** — Module catalogue uses `public_modules()` and thus enforces current revision publication and ownership. Detail resolves by slug through the same ownership-safe resolver. Lesson membership comes from the exact current ModuleRevision; only active requirements and current published LessonRevisions are returned, ordered by position. No revision identifier or historical relationship is accepted from the route.

## 10. Lesson Delivery

**PASS** — Lesson routes resolve by slug to only the Lesson identity’s current published, owned LessonRevision. Historical, draft, in-review, rejected, superseded, missing, and cross-owner revisions do not resolve. Valid content is ordered deterministically and escaped; malformed content uses the unavailable state; empty valid content uses the existing empty state.

## 11. Security

**PASS** — Public detail routes use slug converters and expose no arbitrary revision route. Missing and malformed slugs return 404. Optional Module and Playbook query contexts are resolved and checked against exact published membership. No redirect target is accepted. Stored editorial text is not marked safe and HTML is escaped.

## 12. SQLite Regression

**PASS** — Focused command: `.venv/bin/python manage.py test content.test_public --settings=config.test_settings --verbosity 2`.

**15 discovered; 15 passed; 0 failed; 0 skipped; 0 errors; 1.698 seconds.**

Complete command: `.venv/bin/python manage.py test --settings=config.test_settings --verbosity 2`.

**82 discovered; 77 passed; 0 failed; 5 skipped; 0 errors; 48.277 seconds.** The five skips are PostgreSQL-only integration tests.

## 13. PostgreSQL Regression

**PASS** — Command: `.venv/bin/python manage.py test --settings=config.postgres_test_settings --verbosity 2 --noinput`.

Before the run, read-only catalog queries found no existing disposable test database, confirmed the configured live database was owned by `malilab_app`, and confirmed `malilab_phase6a_test` had no CONNECT privilege on `malilab`. Resolved test settings use the distinct `malilab_phase6a_test` role and `test_malilab_phase6a` disposable database. Django created and destroyed only that test database.

**82 discovered; 82 passed; 0 failed; 0 skipped; 0 errors; 68.465 seconds.**

## 14. Phase 6A Regression

**PASS** — The complete suites passed under SQLite and PostgreSQL. Their discovered tests cover account/authentication foundations, MFA and governance foundations, ownership, revision immutability, publication governance, content validation, practice/evidence, journey, notes, planning, calculation, discovery/search, media metadata, source/editorial provenance, PostgreSQL test-settings safety, and PostgreSQL schema integrity. SQLite skipped only the five PostgreSQL-specific integration cases; all five passed in the PostgreSQL run.

## 15. Database and Migration Integrity

**PASS** — `.venv/bin/python manage.py check` exited 0: no issues.

**PASS** — `.venv/bin/python manage.py makemigrations --check --dry-run` exited 0: no changes detected.

**PASS** — `.venv/bin/python scripts/verify_schema.py` exited 0 before and after PostgreSQL tests. It reports PostgreSQL 16.15, 56 public tables matching expected models/framework/migration bookkeeping, 18 Phase 6A migrations, expected constraints and GIN index, and no domain seed/import data. No pending migrations or schema drift were found.

## 16. Test Isolation

**PASS** — After PostgreSQL teardown, a read-only query found only live `malilab` among `malilab`, `malilab_phase6a_test`, and `test_malilab_phase6a`; the disposable test database was gone. No sessions remained to either test database. The only observed session was this verifier’s connection to live `malilab` as `malilab_app`. The test role still had no CONNECT privilege on live `malilab`. The post-test schema verifier confirmed expected live schema and no domain seed/import rows. The live database was never a test target, and no live database content was changed by this audit.

## 17. Change Boundary

**PASS (filesystem evidence; no Git metadata)** — Remediation-era source timestamps identify `content/public.py`, `content/views.py`, and `content/test_public.py`; the remediation report is the only other remediation-era project file. `content/__pycache__/public.cpython-311.pyc`, `views.cpython-311.pyc`, and `test_public.cpython-311.pyc` are generated bytecode artifacts and are accounted for separately. No migration, model, settings, URL, template, CSS, dependency, PostgreSQL configuration, nginx, seed-content, or later-phase implementation change was observed. Existing application shell, templates, CSS, URLs, and models predate the remediation timestamps. Git-based proof is unavailable because the workspace has no `.git` directory.

## 18. Accessibility and Performance Evidence

**PASS (source-level accessibility)** — Semantic landmarks, skip link, focus styling, responsive source structure, and ordinary links were verified by inspection.

**NOT VERIFIABLE** — No browser or viewport run was performed, so visual/browser acceptance and actual keyboard traversal are not claimed. No quantitative performance measurements were made.

## 19. Findings

**PASS** — No HIGH or BLOCKER finding remains in the audited 6B.1–6B.3 scope. The original mismatched Module ownership defect is rejected by the public inference queryset and by explicit context resolution. Runtime block handling reuses the full approved validator. Focused tests, both complete suites, migration/schema checks, and PostgreSQL isolation checks passed.

**NOT VERIFIABLE** — Browser visual acceptance and performance measurements were not performed. They are not required by the stated acceptance standard when clearly disclosed; source-level shell accessibility checks pass.

## 20. Final Acceptance Decision

**PASS** — All stated acceptance criteria pass. Browser viewport verification is unavailable and disclosed; no visual/browser claim is made.

PHASE 6B.1–6B.3 ACCEPTED — READY FOR 6B.4
