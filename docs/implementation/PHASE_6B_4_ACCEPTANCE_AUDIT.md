# Phase 6B.4 Independent Acceptance Audit

## 1. Audit Scope

**PASS** — This is an independent, read-only audit of the existing-account authentication boundary and public-reader regression. No application code, tests, models, migrations, database configuration, PostgreSQL configuration, or deployment files were changed. This report is the only file created.

The workspace has no `.git` metadata. A before/after changed-file diff could not be independently obtained; file-boundary conclusions below are based on the current source tree, migration files, and the supplied implementation report.

## 2. Authoritative Requirements

**PASS** — The Phase 6B plan explicitly defines 6B.4 as the existing-account login boundary: session login/logout, safe sign-in prompt/return behavior, and active verified eligibility. Section 5 and section 22 exclude registration, recovery, and email delivery. The plan therefore supports the report's deferral claim; their absence is not a 6B.4 defect.

The plan uses Django-rendered forms, CSRF-protected writes, Django's `UserAccount.can_use_personal_features`, and anonymous public reading. The Phase 5B brief and account/ownership specifications confirm the existing custom email identity, verified-email eligibility, and Django-managed sessions.

## 3. Implementation Boundary

**PASS, with diff limitation** — The current implementation contains the reported sign-in form/view, sign-out view, URL routes, shared shell changes, request-user propagation for public templates, CSS, and authentication UI tests. No 6B.4 migration or model edit exists; `makemigrations --check --dry-run` reports no changes. No registration, verification delivery, recovery, payments, subscriptions, AI, media/audio delivery, public API/frontend framework, background jobs, production deployment, or nginx configuration was found in the 6B.4 routes/templates.

Practice, planning, calculations, learning, and discovery domain models/services are present as part of the Phase 6A foundation described in the Phase 6B plan. This audit found no corresponding 6B.5+ user-facing routes or flows added in the inspected implementation. With no Git metadata, the exact historical changed-file set cannot be proven (**NOT VERIFIABLE — no repository history/diff was available**); no source evidence of 6B.4 scope creep was found.

## 4. Existing Account Model

**PASS** — `accounts.UserAccount` remains `AUTH_USER_MODEL`; it is the sole custom user model. `AccountManager.normalize_identity()` strips and case-folds the normalized email, the model normalizes on save, and the unique email field preserves one identity. Password creation uses Django `set_password()`. `can_use_personal_features` requires authenticated, active, `account_status == 'active'`, and verified email. The configured `NormalizedEmailBackend` delegates to Django `ModelBackend`. No second user model or parallel authentication mechanism was introduced. Migration drift check passes; no schema change is required.

## 5. Sign-In

**PASS** — `/sign-in/` renders a GET form and accepts credentials by POST only; unsupported methods return 405. The view invokes Django `authenticate()` and `login()`, then redirects only after the eligibility check. Credentials and account identity are not selected through an account ID or query parameter. Passwords are not placed in URLs. CSRF is enforced by middleware and `@csrf_protect` (see section 8).

## 6. Authentication Eligibility

**PASS** — The sign-in view checks `user.can_use_personal_features` after authentication. That property enforces active state, active account status, and verified email. Django `ModelBackend` rejects inactive users through its standard `user_can_authenticate` check. The audit's additional isolated endpoint check confirmed an `is_active=False` verified account is not logged in. Existing tests cover successful verified/active sign-in, wrong password, unknown email, unverified email, and disabled account status.

Authentication failures share the generic message “We could not sign you in with those details.” They do not reveal account existence. Form validation errors for malformed/missing input are ordinary input errors, not account-existence disclosures.

## 7. Password Handling

**PASS** — Password submission goes to Django authentication and Django-managed hashing. No custom cryptography, plaintext storage/logging, URL credential, or rendered password value was found. The password widget uses `autocomplete="current-password"`; the form is reconstructed empty after authentication failure, so the password is not prefilled. Tests verify the password is absent from failure output and not prefilled on form render.

## 8. CSRF

**PASS** — Sign-in and sign-out are explicitly CSRF-protected, and global `CsrfViewMiddleware` remains enabled. With `Client(enforce_csrf_checks=True)`, POST sign-in and POST sign-out without a valid token returned 403; valid-token requests succeeded. Sign-out form includes a CSRF token. No CSRF bypass or setting change was found.

## 9. Session Behavior

**PASS** — Successful login uses Django `login(request, user)` and the tested session contains the correct `_auth_user_id`; subsequent requests render the signed-in identity. Django's standard login/session-key cycling and logout mechanisms are retained; no custom session store or client-controlled authentication state was added. Logout removes authentication from the session and public reading remains available. Session-key rotation itself is not asserted by a dedicated test, but the implementation delegates to Django's standard login function.

## 10. Logout

**PASS** — `/sign-out/` accepts POST only; GET returns 405. It invokes Django `logout()` and always redirects to `/`, ignoring submitted return targets. CSRF enforcement was tested. After logout the authenticated session key is absent and the public home route remains accessible.

## 11. Return Target / Open Redirect Security

**PASS** — `_safe_destination()` uses Django `url_has_allowed_host_and_scheme()` with only `request.get_host()` allowed and requires HTTPS for secure requests; invalid or absent values fall back to `/`. The same-site path `/playbooks/` was accepted, while an external absolute URL was rejected by the project test. Additional direct endpoint checks confirmed protocol-relative `//attacker.example/x`, a dangerous `javascript:` scheme, external absolute URL, and a backslash protocol-relative form resolve to `/`. A same-host HTTPS URL is permitted by Django's safety check. Sign-out does not use `next`. No arbitrary external redirect was identified.

## 12. Shared Application Shell

**PASS** — Anonymous navigation contains public Playbooks/Modules and a sign-in link. Eligible authenticated users see `request.user.email` and a POST sign-out form with CSRF. The shell does not render password/hash, tokens, MFA material, or database ID. Both the authentication view and public page presenter supply `request.user`; identity is not client-selected. The template uses normal Django escaping and no unsafe rendering filter was found.

## 13. Public Reading Regression

**PASS** — Focused public tests pass, including anonymous Home, Playbook list/detail, Module list/detail, Lesson access/missing-slug behavior. Existing exact-public-revision resolution and public reader tests pass in the focused and complete suites. Sign-in is not required for public reading. The live database has no seed content, so meaningful live content traversal was not possible; route behavior is covered with test data and source inspection.

## 14. Account Ownership Boundary

**PASS** — The authenticated identity is Django `request.user`, available to future owner-scoped services. No owner-selection query parameter, `user_id` input, or client-supplied account ID is used to establish identity. There are no private feature routes in 6B.4. Direct cross-account object authorization is **DEFERRED / OUT OF SCOPE**, not a defect in this slice.

## 15. Authentication UI

**PASS, source-level** — The form is semantic HTML with a page heading, explicit email/password labels and associations, email/current-password autocomplete, useful generic failure messaging, alert semantics, and no password prefill. It extends the MaliLab shared shell and uses existing CSS; no JavaScript or frontend framework is required. `novalidate` is present, so browser-native validation prompts are disabled; server-side Django form validation remains active. No unsafe template rendering was found.

## 16. Accessibility

**PASS, source-level. NOT VERIFIABLE — browser/viewport testing not performed.** Labels, heading hierarchy, form controls, alert region, keyboard-operable submit/sign-out controls, visible focus styling, skip link, landmarks, responsive viewport metadata, and readable structure are present in source. No WCAG certification is claimed. Performance testing was not performed.

## 17. Test Quality

**PASS, with coverage notes** — `accounts/test_auth_ui.py` genuinely exercises successful sign-in/session identity, normalized email, wrong password, unknown account, unverified account, disabled account status, generic errors, safe same-site/external return, POST-only logout, session termination, CSRF, anonymous shell, password non-prefill, and continued anonymous public route access. `content.test_public` covers public reader routes and revision behavior. The independent focused suite passed all 25 tests.

Coverage gaps: the checked-in auth tests do not separately assert an `is_active=False` account (the endpoint was independently exercised and rejected it), protocol-relative/dangerous-scheme/malformed return targets (additional endpoint checks rejected the tested dangerous targets), session-key rotation, or exact POST password non-prefill after a failed submission. The relevant implementation paths use Django's standard backend/session/safety primitives. These omissions do not reveal a defect or block acceptance.

## 18. Regression Testing

**PASS** — Independently run results:

- `manage.py check`: no issues.
- `makemigrations --check --dry-run`: no changes detected.
- Focused `accounts.test_auth_ui content.test_public` using `config.test_settings`: **25 discovered, 25 passed, 0 failed, 0 skipped, 0 errors**.
- Full suite using `config.test_settings`: **92 discovered, 87 passed, 5 skipped (PostgreSQL-only), 0 failed, 0 errors**.
- Full suite using `config.postgres_test_settings`: **92 discovered, 92 passed, 0 skipped, 0 failed, 0 errors**.

The additional one-off isolated endpoint check for inactive account and dangerous return targets passed (1 test, 0 failures/errors); it did not modify repository tests.

## 19. Database Safety

**PASS** — The PostgreSQL suite used the configured isolated database and role. After completion, `test_malilab_phase6a` did not exist and had zero active sessions. The read-only schema verifier confirmed the test role lacks CONNECT on live `malilab`. The live `accounts_useraccount` row count is zero, and the schema verifier found no domain seed/import data. No test account or test database remained in the live database.

## 20. Migration / Schema Integrity

**PASS** — Migration drift check reports no changes. `scripts/verify_schema.py` passed against PostgreSQL 16.15 as `malilab_app` on `malilab`: 56 expected public tables, 18 Phase 6A migration records, required constraints and GIN index present, and no domain data. No 6B.4 migration, field, or table was added.

## 21. Security Regression

**PASS** — No HIGH/BLOCKER issue found. Tested/inspected protections include safe return validation, POST and CSRF for state changes, Django authentication and sessions, generic auth failures, password non-disclosure, no account impersonation input, escaped templates, and no sensitive account attributes in the shell. GET logout is rejected. No unsafe redirect or authentication bypass was identified.

## 22. Phase Boundary

**PASS** — No 6B.5 Practice UI/submission, 6B.6 evidence/completion UI, 6B.7 Notes UI, 6B.8 My Plan UI, 6B.9 Progress UI, 6B.10 Search UI, or 6B.11 release-hardening feature was found. Existing Phase 6A domain models/services are not evidence that these later user-facing slices were implemented. No payment, subscription, AI, media delivery, audio, production deployment, or nginx change was found. Registration, verification delivery, and recovery remain deferred as authorized by the Phase 6B plan.

## 23. Findings

- **No acceptance-blocking findings.**
- **NOT VERIFIABLE — historical changed-file diff:** the workspace has no `.git` metadata. Current source and migration inspection found no scope creep or schema edit, but exact comparison to the pre-6B.4 tree was unavailable.
- **NOT VERIFIABLE — visual/browser and performance results:** no browser/viewport or performance testing was performed. Source-level accessibility was inspected; these are not blockers under the stated acceptance standard absent an explicit 6B.4 browser acceptance requirement.
- Test coverage could be expanded for dedicated inactive-user, protocol-relative/dangerous-scheme return, and session-key rotation assertions. Independent behavior checks and Django primitives support the audited behavior; this is not a defect.

## 24. Final Acceptance Decision

**PHASE 6B.4 ACCEPTED — READY FOR 6B.5**

All specified acceptance criteria passed: existing-account authentication and session behavior, active/verified eligibility, POST-only CSRF-protected logout, safe return handling, no account impersonation or secret leakage, anonymous public reading, focused and complete regression suites, migration/schema integrity, isolated PostgreSQL cleanup, and no detected later-phase scope creep. The unavailable historical Git diff and browser/performance evidence are recorded above and do not block acceptance under the stated criteria.
