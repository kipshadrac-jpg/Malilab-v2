# Phase 6B.1–6B.3 Implementation Report

**Status: PHASE 6B.1–6B.3 IMPLEMENTED — READY FOR REVIEW**  
**Scope:** public application shell, exact-current-public revision delivery, and Playbook → Module → Lesson reading only.

## Implemented

- Server-rendered homepage, Playbook catalogue/detail, Module catalogue/detail, and Lesson detail routes.
- Responsive shared shell with site identity, primary navigation, skip link, main landmark, footer, visible keyboard focus, mobile layout, page titles, and breadcrumb context.
- Read-only public resolver that follows each stable identity's `current_published_revision`, then requires a published identity, a published revision, and matching revision ownership.
- Playbook recommendation resolution through the exact PlaybookRevision relationship and only the recommended ModuleRevision that is also the Module identity's current published revision.
- Module Lesson list resolution through active Lesson requirements on the exact current ModuleRevision, ordered by the approved `position` field. Only the exact current published LessonRevision is displayed.
- Paragraph-only Lesson rendering in deterministic position order. Django autoescaping protects text; invalid/unsupported stored blocks fail closed with a content-unavailable message. Empty Lessons render a useful empty state.
- Previous/next links scoped to a validated published Module context. Module and Playbook context is carried by slugs and checked against exact published relationships; without unambiguous Module context, navigation is omitted instead of guessed.
- Graceful zero-content states. No editorial content was seeded.

## Routes

- `GET /`
- `GET /playbooks/`
- `GET /playbooks/<slug>/`
- `GET /modules/`
- `GET /modules/<slug>/`
- `GET /lessons/<slug>/`

No login, logout, Practice, Notes, My Plan, Progress, search, or historical-revision route was added.

## Files changed

- `config/urls.py`
- `content/public.py`
- `content/views.py`
- `content/test_public.py`
- `content/static/content/site.css`
- `content/templates/content/base.html`
- `content/templates/content/home.html`
- `content/templates/content/playbook_list.html`
- `content/templates/content/playbook_detail.html`
- `content/templates/content/module_list.html`
- `content/templates/content/module_detail.html`
- `content/templates/content/lesson_detail.html`
- `docs/implementation/PHASE_6B_1_3_IMPLEMENTATION_REPORT.md`

## Services and presentation

`content/public.py` provides the shared exact-public resolver and query boundaries for current Playbooks, Modules, approved recommendations, and ordered Lessons. `content/views.py` composes these read-only results into Django templates. No model, field, constraint, index, migration, package, external service, or database configuration was added.

Public templates are rendered with Django's template engine and standard escaping. The current project settings contain a nonexistent `django.contrib.messages.context_processors.request` entry. To avoid changing the accepted Phase 6A settings, these public pages render without request context processors; they do not use auth, messages, or other request globals. This is a known configuration limitation if future templates require request context.

## Tests and validation

- `.venv/bin/python manage.py test content.test_public --settings=config.test_settings` — **11 passed**.
- `.venv/bin/python manage.py test --settings=config.test_settings` — **78 discovered; 73 passed, 5 PostgreSQL-only skipped; 0 failed**.
- `.venv/bin/python manage.py test --settings=config.postgres_test_settings` — **78 passed; 0 skipped, 0 failed**. The existing isolated PostgreSQL test database was destroyed after the run.
- `.venv/bin/python manage.py check` — **PASS**.
- `.venv/bin/python manage.py makemigrations --check --dry-run` — **PASS; no changes detected**.
- `.venv/bin/python scripts/verify_schema.py` — **PASS** after tests. Live development database remains `malilab` / `malilab_app`; 56 public tables match the expected schema, 18 Phase 6A migrations are present, and no domain seed/import rows exist.

The public tests cover zero-content pages, published and unavailable resolution, wrong-identity revision pointers, safe recommendation filtering, Lesson ordering and publication filtering, escaped HTML, empty and unsupported Lesson bodies, safe malformed/missing paths, validated Playbook context, and Lesson navigation boundaries.

## Security, responsive, and accessibility checks

- Public detail routes accept slugs only; no revision ID is accepted in a public URL.
- Unavailable content resolves as an ordinary 404. Related links are built from resolved model slugs and exact approved relations; there are no redirect parameters.
- Templates do not mark editorial text safe. Unsupported stored block types are not rendered.
- Core navigation is ordinary server-rendered links with no JavaScript dependency.
- Template/CSS inspection confirms semantic header/nav/main/footer landmarks, a skip link, visible focus styling, responsive narrow-screen navigation, readable line length, and reflowing lesson navigation. No browser automation or visual viewport runner is configured in this workspace, so viewport checks were source-inspected rather than browser-executed.

## Migration and database status

**No migration or schema change.** The migration check reports no model changes. Tests used the existing SQLite test settings and isolated PostgreSQL test settings only. The live schema verifier passed before and after final regression tests; no live data was modified.

## Known limitations

- The database has no published editorial seed content, so live catalogues will show empty states until content is published through the existing editorial governance.
- Lesson context is ambiguous if the same Lesson is included by multiple current Modules. The reader requires a validated `?module=<slug>` context to show Previous/Next in that case; it never guesses a Module.
- The existing messages context processor setting is invalid; public pages avoid request context processors because they do not need them. Correcting that shared Phase 6A setting is outside this slice.
- This is a first reading shell, not a finalized visual identity. Measurable accessibility/performance thresholds remain **TO-BE-DEFINED**.

## Deferred and untouched

6B.4 authentication, 6B.5 Practice submission, 6B.6 evidence/completion UI, 6B.7 Notes, 6B.8 My Plan, 6B.9 Progress, 6B.10 Search/discovery, and 6B.11 release hardening remain untouched. Formula/Lab Tools, media delivery, audio, payments, subscriptions, AI, registration/recovery, editorial workflow UI, and production deployment remain deferred. No dependency finding blocked this slice.

## Final status

**PHASE 6B.1–6B.3 IMPLEMENTED — READY FOR REVIEW**
