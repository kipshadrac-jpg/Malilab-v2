# Phase 6B.1–6B.3 Independent Acceptance Audit

## 1. Audit Scope

**PASS (source inspection)** — Reviewed the implementation report, plan, public routes, resolver/views, templates/CSS, public tests, settings, models, migrations, and the Phase 6A audit artifacts. Ran the system check, migration drift check, and schema verifier. Test commands were started under the prescribed settings but did not complete in this environment; details are in sections 11–12.

The audit is limited to 6B.1–6B.3. No application code, model, migration, settings, test, or live data was changed. This report is the only audit artifact created.

## 2. Evidence Reviewed

- `docs/implementation/PHASE_6B_1_3_IMPLEMENTATION_REPORT.md` and `docs/implementation/PHASE_6B_PLAN.md`
- `config/urls.py`, `config/settings.py`, `config/test_settings.py`, `config/postgres_test_settings.py`, `config/test_postgres_test_settings.py`
- `content/public.py`, `content/views.py`, `content/models.py`, `content/test_public.py`, `content/tests.py`
- All `content/templates/content/*.html` templates and `content/static/content/site.css`
- Migration files and `scripts/verify_schema.py`
- Commands: `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python scripts/verify_schema.py`; public, full SQLite, and PostgreSQL test commands (the last three did not finish; see section 12).

**NOT VERIFIABLE** — The workspace has no `.git` directory (`git status` reports “not a git repository”). Therefore a source-control diff, commit history, and authoritative changed-file list could not be independently inspected. File modification times and the implementation report were used as weaker evidence.

## 3. Project Boundary

**PASS, with evidence limitation** — The reported and inspected 6B files are the public URL configuration, content resolver/views, reader templates/CSS, public tests, and implementation report. The inspected URL table contains only the six requested public routes plus admin. No authentication, practice submission, notes, plans, progress, search, media delivery, audio, payments, subscriptions, AI, editorial workflow UI, or production deployment routes/features were found in this slice. No migration file was reported as part of implementation, and migration drift check passed.

**NOT VERIFIABLE** — No git history/status is available to prove the full change boundary or detect unreported file changes. The implementation report asserts only its listed files changed.

**DEFERRED / OUT OF SCOPE** — 6B.4 onward and all other excluded systems remain outside this audit.

## 4. Application Shell

**PASS (source inspection)** — `base.html` supplies a shared layout, semantic header/nav/main/footer, skip link, page title blocks, and normal Django URL links. Detail/list templates provide relevant breadcrumb context. CSS includes visible `:focus-visible` styles, a narrow-screen breakpoint that stacks the header and lesson navigation, a reading width cap, and flexible/wrapping breadcrumb/navigation behavior. Core navigation is ordinary server-rendered anchors; no JavaScript is required. Editorial text is interpolated in normal Django template context and is not marked safe.

**NOT VERIFIABLE** — No browser automation or visual viewport runner was available, so actual viewport rendering, keyboard traversal, and visual behavior were not independently browser-tested. Source declarations do not establish visual success.

## 5. Exact Public Revision Resolution

**PASS for direct resolution and catalogues** — `content/public.py::resolve_public_revision` resolves by identity slug and published identity status, follows `current_published_revision`, and requires a non-null published revision owned by that identity. Catalogues likewise require published identity/revision and matching ownership. Public detail URLs contain slugs only. There is no public revision-ID route or historical-revision fallback. Invalid/missing content raises 404.

**FAIL — HIGH, blocks acceptance** — Automatic Lesson context discovery in `content/views.py::lesson_detail` (the `published_modules` query) does not apply the shared Module resolver’s ownership check to the Module identity’s `current_published_revision`. It filters Module status and pointed revision status, then derives Lesson membership from that revision. If a published Module identity has a mismatched current-revision pointer, this query can infer it as Lesson context and use that unrelated revision to select Previous/Next links. This bypasses the exact identity/revision boundary specifically for inferred context and can surface unrelated Lesson navigation. It violates the requirement that navigation context resolve to the correct current published Module. The explicit `?module=` path does use the resolver, but this does not close the no-parameter automatic inference path.

## 6. Playbook Delivery

**PASS (source inspection)** — Playbook list/detail use published identities and exact current published revisions. Detail resolution rejects missing, unavailable, null-pointer, and wrong-owner pointers. Recommendations are selected from the exact resolved PlaybookRevision and require an active relationship, published ModuleRevision, published Module identity, identity pointer equality, and matching ModuleRevision ownership. This prevents stale recommendation rows or unrelated/historical/unpublished Module revisions from being shown.

**NOT VERIFIABLE** — Public tests cover a happy-path recommendation, an unavailable recommendation, and a wrong Playbook pointer, but no independent completed test run was obtained. No explicit test covers stale recommendation replacement, an unrelated ModuleRevision, or a mismatched Module pointer in the recommendation query.

## 7. Module Delivery

**PASS for direct route and query boundary (source inspection)** — Module detail resolves its stable slug through the shared exact-current resolver. Lesson rows are drawn from the exact resolved ModuleRevision and require active Lesson requirements plus published Lesson identity/revision and identity-pointer equality. Rows are ordered by the unique requirement position field. Historical ModuleRevision IDs are not selectable from URL input.

**NOT VERIFIABLE** — Existing public tests exercise position ordering and unpublished Lesson exclusion. They do not directly exercise a stale/current ModuleRevision mix or a mismatched Module pointer. Automated test execution was incomplete.

## 8. Lesson Delivery

**PASS for public revision and escaping** — Lesson detail resolves only the slug’s exact current published LessonRevision with matching ownership. The template renders only paragraph payload text and does not use `safe`; normal Django autoescaping applies. Supported blocks are sorted by position, empty blocks have an explicit empty state, and unknown block types/non-text payloads fail closed to an unavailable message. The test source includes an escaped script-text case and an unsupported-type corruption case.

**NOT VERIFIABLE / test gap** — The view’s runtime shape check does not revalidate the full model allow-list (required UUID key, exact field sets, nonnegative position, nonempty text, unique keys/positions). Thus some malformed database-stored blocks with paragraph type and string text would still be displayed, although Django escaping prevents executable HTML. Tests do not cover malformed/missing key/fields, duplicate positions, or extra payload fields through the corrupted-storage path. This is a content-integrity fail-closed gap, not an observed script-execution path.

## 9. Lesson Context and Navigation

**FAIL — HIGH, blocks acceptance** — Explicit `?module=<slug>` context is resolved through the public Module resolver and requires active membership of this exact published LessonRevision in that exact ModuleRevision; ordered neighbors are then derived from that same revision. First/last Lesson boundaries are handled. However, absent `module`, the inferred context query described in section 5 omits Module pointer-ownership validation. The requirement that inferred context be a validated current Module is therefore not met. A Lesson included by multiple matching Modules suppresses navigation rather than guessing, which is correct.

**NOT VERIFIABLE** — Tests cover explicit navigation, first/last boundaries, and a missing module slug. They do not cover multiple current Modules, a Lesson outside the supplied Module, a mismatched Module pointer under automatic inference, cross-revision links, or unavailable Module context. The acceptance-critical inference case is not tested.

## 10. Route/Input Security

**PASS (source inspection)** — `config/urls.py` defines the requested GET routes with slug converters and no revision-ID route. Detail views use stable identity resolution; there are no redirect parameters or JavaScript-only links. Query parameters only provide optional Playbook/Module context and are validated against published relations; malformed/unknown slugs return ordinary 404s. Templates do not mark stored editorial fields safe.

**FAIL — HIGH, blocks acceptance** — The automatic Module context query is a route-context boundary bypass as described in sections 5 and 9. No arbitrary revision ID is accepted, but a query-free Lesson request can still infer context from an invalid identity pointer.

## 11. Database/Migration Safety

**PASS for observed read-only checks** — `manage.py check` completed successfully: “System check identified no issues (0 silenced).” `makemigrations --check --dry-run` completed successfully: “No changes detected.” `scripts/verify_schema.py` completed successfully and reported PostgreSQL 160015, database/role `malilab`/`malilab_app`, 56 public tables matching expected schema, 18 Phase 6A migrations, expected constraints/index, and no domain seed/import data. These are consistent with no Phase 6A physical-schema change and no live content seed change.

**PASS for test-target configuration by inspection** — SQLite test settings use an in-memory database. PostgreSQL test settings force a separate test database and role and reject the configured live database name or application role. `config/test_postgres_test_settings.py` contains explicit isolation tests.

**NOT VERIFIABLE** — A before/after live-data snapshot was not available. Schema verification is read-only and reports no domain seed/import data, but cannot prove that no unrelated live row was modified before this audit. No test suite completed, so post-test schema verification could not be confirmed. The implementation report claims a post-test verification; that claim could not be reproduced in this audit.

## 12. Regression Testing

**PASS** — Django system check completed (0 issues).

**PASS** — Migration drift check completed (“No changes detected”).

**PASS** — Schema verification completed successfully as recorded in section 11.

**NOT VERIFIABLE** — The following test commands were started but did not complete or return test counts during this audit:

- `.venv/bin/python manage.py test content.test_public --settings=config.test_settings`
- `.venv/bin/python manage.py test --settings=config.test_settings`
- `.venv/bin/python manage.py test --settings=config.postgres_test_settings`

The processes remained in uninterruptible filesystem wait (`D`, `folio_wait_bit_common`) for over ten minutes after printing “Creating test database for alias 'default'...”; consequently discovered/passed/skipped/failed/error counts are unavailable and no phase 6A regression pass can be asserted. The PostgreSQL settings isolate the test DB by source inspection, but the run’s completion and teardown could not be verified. The prior implementation report’s counts (11 public; 78 full; 78 PostgreSQL) are reported claims, not independently reproduced evidence.

## 13. Phase 6A Regression

**NOT VERIFIABLE** — The test commands intended to exercise Phase 6A foundations did not finish. No Phase 6A model or migration edits were observed in the inspected 6B source scope, and schema/migration checks pass, but regression behavior for account/authentication, ownership, governance, immutability, practice/evidence, journey, notes, planning, calculations, discovery, provenance, and PostgreSQL isolation cannot be certified without completed tests.

## 14. Configuration Limitation

**PASS (classification)** — `config/settings.py` includes `django.contrib.messages.context_processors.request`, which is not the standard messages context processor path; the standard messages processor is `django.contrib.messages.context_processors.messages`. This is present in shared settings and is therefore a pre-existing Phase 6A configuration issue. The public `_page` helper uses `render_to_string(template, context)` without a request, so Django does not evaluate request context processors for these public pages; inspected templates do not depend on request/auth/messages context. `manage.py check` passes. It does not currently block 6B.1–6B.3 acceptance; retain it as later shared-settings cleanup. No configuration was changed.

## 15. Seed Content / Data Integrity

**PASS for current state** — The live schema verifier reports no domain seed/import data. No seed scripts or content fixtures were found in the inspected 6B scope. Empty catalogue states are implemented and expected.

**NOT VERIFIABLE** — No independent before/after row snapshot exists. No live data write was performed by this audit. Browser testing against realistic published editorial content was not possible because the live database has no published seed content.

## 16. Test Quality

**PASS (partial source coverage)** — `content/test_public.py` includes zero-content states; wrong Playbook pointer; unavailable Playbook revisions; recommendation filtering; Lesson ordering; unpublished Lesson exclusion; HTML escaping; empty Lessons; unsupported block fail-closed behavior; malformed/missing URL paths; explicit Playbook context; explicit Module navigation and first/last boundaries.

**FAIL (important gaps; contributes to acceptance blocker)** — Tests do not cover automatic Lesson context inference from a mismatched Module current-revision pointer, multiple current Module membership, stale/cross-revision Lesson navigation, unrelated ModuleRevision recommendations, malformed block shapes (missing key/extra fields/invalid positions), or unavailable supplied Module context. These omissions leave the acceptance-critical inferred-context defect undetected. The separate test run limitation is recorded in section 12.

## 17. Architectural Conformance

**PASS (routes and presentation boundary)** — The implementation follows the plan’s server-rendered, public, slug-based routes for Home, Playbooks, Modules, and Lessons. It adds no arbitrary historical-revision route, API, write form, or later-phase feature. Templates use ordinary navigation and public current-revision reads.

**FAIL** — The plan requires exact current revision resolution and validated context. Automatic Lesson context inference does not reuse the resolver’s ownership validation, so the implementation materially falls short of that boundary (sections 5 and 9).

## 18. Accessibility/Performance Evidence

**PASS (source-level only)** — Source includes semantic landmarks, a skip link, focus-visible styling, responsive CSS rules, readable measure, and lesson-navigation reflow.

**NOT VERIFIABLE** — No actual browser/viewport test or automated accessibility test was run. No performance measurement was run. Measurable accessibility/performance thresholds remain TO-BE-DEFINED; no quantitative claim is made.

## 19. Findings

1. **HIGH — Invalid inferred Module context can select Lesson neighbors.** `content/views.py::lesson_detail`, `published_modules` query. It filters status and membership but does not ensure `current_published_revision.module_id` matches the Module identity. A mismatched pointer can infer an unrelated ModuleRevision and provide its Previous/Next Lesson links. This breaches current-revision ownership and navigation-context requirements. **Blocks acceptance.**
2. **MEDIUM — Runtime Lesson block checks are narrower than the model allow-list.** `content/views.py::lesson_detail` block validation. Certain malformed paragraph-shaped stored blocks can render escaped text instead of failing closed. Escaping prevents executable HTML in the inspected path, but this weakens content-integrity behavior and is untested. **Not independently an acceptance blocker for unsafe rendering; carry forward.**
3. **AUDIT LIMITATION — Tests did not complete.** The SQLite and PostgreSQL test processes remained blocked in filesystem wait after test DB creation, so test counts and Phase 6A regressions are not independently verified. **Blocks acceptance under the stated standard requiring Phase 6A regression tests to pass.**
4. **AUDIT LIMITATION — No git metadata.** Changed-file boundary and source history could not be independently verified. This reduces confidence but is not by itself a demonstrated implementation blocker.
5. **NON-BLOCKING — Existing invalid messages context processor setting.** Pre-existing shared settings issue; current public render path avoids context processors. Later cleanup, no change made.
6. **NON-BLOCKING — No published live content/browser viewport run.** Empty states are implemented; realistic reader behavior and actual viewport appearance were not browser-verified.

## 20. Acceptance Decision

**FAIL — NOT ACCEPTED.** The automatic Lesson context query can bypass Module current-revision ownership checks and choose neighbors from an unrelated revision. In addition, required regression test suites did not complete, so Phase 6A test success cannot be established independently.

PHASE 6B.1–6B.3 NOT ACCEPTED — automatic Lesson context inference does not validate Module revision ownership, and required regression tests did not complete
