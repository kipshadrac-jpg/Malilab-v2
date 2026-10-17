# Phase 6B.5B — Practice Submission Implementation Specification

**Status:** Implementation underway under owner authorization GOV-002. This specification remains incomplete where consequential PRS decisions or PostgreSQL compatibility evidence are outstanding; the current execution record below distinguishes implemented behavior from unverified gates. Owner-supplied live inspection verifies database identity, read-only state, the presence/inspection of the Practice catalog objects, and zero Practice rows. Full database compatibility, including model/migration/catalog parity and migration drift, remains unverified; see the companion report and readiness report.

## 1. Purpose, boundaries, and authority

Specify the future Practice submission vertical slice: current eligible published content, pinned-revision form rendering, owner-scoped attempts, incomplete draft saves, explicit validated submission, accessible learner outcomes, and tests. This text described the earlier planning state; GOV-002 is the current implementation authorization.

Authority order: (1) `PHASE_6B_5A_OWNER_DECISION_ADDENDUM.md` for the Practice contract; (2) accepted project decisions and architecture, including `DECISIONS.md`, account/ownership and content versioning specifications; (3) approved model/field/constraint/index and migration specifications; (4) recommendations explicitly labelled below; (5) unresolved prerequisites/owner decisions. The owner addendum supersedes the earlier proposal statuses in `PHASE_6B_5A_PRACTICE_RESPONSE_SCHEMA_AND_EVALUATION_CONTRACT.md` where it explicitly decides an item. No conflicting approved decision was found in inspected materials.

In scope: render six response types; create, save, and submit attempts; validate exact schema and learner answers; preserve history and owner boundaries. Submission means receipt after structural validation only. Separate and out of scope for this Practice slice: educational evaluation, scoring, acceptance decisions, learner feedback, Requirement Evidence, Module completion, retries/reopening, registration/recovery, content-authoring UI, new infrastructure, model/migration/database changes. GOV-002 separately authorizes the planned later Phase 6B application slices.

**Governance status:** GOV-001 satisfies Phase 6A acceptance. GOV-002 authorizes Phase 6B application implementation; schema changes, live data changes, and production operations retain their separate authorization boundaries. `PROJECT.md` and the roadmap now reflect these decisions. Historical readiness reports describe the earlier state.

## 2. Existing implementation and architectural baseline

Verified by source inspection:

- `PracticeActivity` has a slug, status, and `current_published_revision` pointer. `PracticeActivityRevision` has activity, revision number, status, title/instructions/prompt, `response_schema` JSON, and immutable-after-review behavior inherited from `EditorialRevision`.
- `PracticeAttempt` stores owner, exact revision FK, optional journey, state, start/submission timestamps, and `response_summary`. Owner and revision deletion is protected. Model states are exactly `started`, `submitted`, `abandoned`.
- `PracticeResponse` stores attempt FK, `prompt_key` (max 120), JSON `value`, `unit` (max 48, blank allowed), and timestamp; `(attempt,prompt_key)` is unique.
- Service functions currently gate active/verified account for create/save/read; `create_attempt` accepts a revision object from its caller without resolving publication eligibility. `save_response` accepts arbitrary `prompt_key`, JSON, and `unit`; `submit_attempt` changes state and stores caller-provided `response_summary` without validating answers. `get_owned_attempt` filters by owner but is not locked. Existing ORM/model guards do not secure direct SQL or every manager/bulk path.
- `config/urls.py` has no Practice routes. The four routes in the prompt are planned only. Practice tests use `{"type":"object"}` as a fixture; the addendum expressly says this is not approved production schema.
- Current public resolver helpers cover Playbook, Module and Lesson, not Practice. The service layer must supply a Practice-specific eligible-revision resolver or an approved shared extension.

Approved precedent: server-rendered same-origin Django application, anonymous public reading, personal persistence only for authenticated, active, verified accounts, owner-scoped services, exact immutable revisions, CSRF-protected POST, PostgreSQL as production database, isolated PostgreSQL test database/role.

## 3. Exact schema grammar

The schema is a narrow MaliLab contract, not general JSON Schema. JSON object means a mapping with string keys. Reject unknown keys at every level. Reject duplicate keys during raw JSON decoding if schema is loaded from textual JSON. Treat booleans as distinct from integers (`true` is not schema version 1, a length, or a bound).

### Root

Exactly `schema_version` and `questions` are required; no optional root keys. `schema_version` is a JSON integer exactly `1`, not boolean. `questions` is an ordered array with unique question IDs. The 100-question ceiling is proposed under **PRS-03**, pending owner approval.

### Every question

Required keys: `id`, `type`, `label`, `required`. Optional keys are type-dependent: `constraints` for `short_text`, `long_text`, `integer`, and `decimal_amount`; `options` only for `single_choice` and `multiple_choice`. No other keys.

- `id`: string matching exactly `^[a-z][a-z0-9_]{0,63}$`; unique within schema.
- `type`: exactly one of `short_text`, `long_text`, `single_choice`, `multiple_choice`, `integer`, `decimal_amount`.
- `label`: non-empty string after testing that it contains a non-whitespace code point; preserve editorial string as authored. Proposed maximum 500 Unicode code points under **PRS-02**, pending owner approval.
- `required`: JSON boolean, exact type.

### Type-specific schema keys

| Type | `constraints` grammar | `options` |
|---|---|---|
| `short_text` | Required object with exactly `max_length`; positive JSON integer. | Forbidden |
| `long_text` | Required object with exactly `max_length`; positive JSON integer. | Forbidden |
| `single_choice` | Forbidden | Required non-empty array; each option is exactly `{id,label}` |
| `multiple_choice` | Forbidden | Required non-empty array; each option is exactly `{id,label}` |
| `integer` | Optional object with only `minimum` and/or `maximum`; each JSON integer (not boolean); if both, minimum ≤ maximum | Forbidden |
| `decimal_amount` | Required object with `currency` and optional `minimum`/`maximum`; currency exactly `KES` initially; bounds canonical decimal strings; minimum ≤ maximum | Forbidden |

Choice option `id` follows the same identifier pattern and is unique within that question; IDs are stable for that immutable revision. Option `label` follows the non-empty label rule. Proposed maximum 100 options per choice question under **PRS-03**, pending owner approval.

`max_length: 4000` in the 6B.5A example is illustrative, explicitly not an approved product limit. A schema that uses `max_length` must be bounded by the configured per-type ceiling. Proposed bounds are 280 Unicode code points for `short_text` and 10,000 for `long_text` under **PRS-01**, pending owner approval. The configured ceilings must be finite and no schema may exceed them.

No defaults, answer keys, executable expressions, HTML, renderer directives, or arbitrary prose interpreted as instructions. Unsupported `schema_version`, malformed JSON/object/array, missing/extra keys, duplicate IDs, wrong JSON types, unsupported type/key, invalid bound, empty choices, or schema over configured resource ceilings fail closed. A malformed schema is unavailable content: do not create an attempt or accept a submission against it; return a generic unavailable-content outcome and log a sanitized schema/revision identifier for staff diagnosis.

## 4. Answer wire/storage contract and per-type validation

Request payload is exactly `{"responses": {"question_id": value, ...}}`; no owner ID, revision ID, state, timestamp, summary, arbitrary metadata, or other top-level keys. `responses` must be a JSON object. Unknown question IDs and `null` are rejected. Duplicate question keys in raw JSON are rejected before mapping construction. For draft save, request contains exactly one `question_id` and `value` envelope (or an explicitly approved batch of that same mapping); the service validates one declared question value but does not require completeness. Omission means unanswered; empty value is not omission.

| Type | Accepted submitted JSON value | Validation |
|---|---|---|
| `short_text` | String | Exact string type; Unicode code-point length ≤ schema max and configured short ceiling. No trimming/normalization. Requiredness checks `value.strip()` is non-empty; optional `""` and whitespace-only strings are retained exactly. |
| `long_text` | String | Same rules, with long ceiling. Unicode preserved; reject non-string including numbers and null. |
| `single_choice` | String option ID | Exact string and exact membership in pinned revision option IDs. Required answer must be present; a missing ID is invalid. |
| `multiple_choice` | Array of strings | Every element exact string and allowed option ID; no duplicate IDs; empty array is allowed for optional unanswered, but fails requiredness at submission. Preserve learner-supplied array order in stored JSON as a proposed serialization detail under **PRS-06**, pending owner approval. |
| `integer` | JSON integer | Exact integer, not bool or float; no coercion from strings. Apply optional inclusive integer minimum/maximum. |
| `decimal_amount` | Proposed: amount string in JSON `value`; currency in `unit` as `KES`, per **PRS-05** | Canonical base-10 decimal string. Proposed PRS-04 grammar rejects exponent notation, commas, whitespace, leading plus, unnecessary leading zeroes and negative zero; proposed KES maximum two fractional digits. No amount range is invented. |

Under **PRS-04**, the proposed grammar accepts `0` or an integer without unnecessary leading zeroes, optionally followed by one or two fractional digits; a negative sign is permitted only for nonzero negative values. Examples proposed as valid: `0`, `12`, `12.3`, `12.30`, `-0.50`; proposed invalid examples: `.5`, `01.00`, `+1`, `1.`, `1e2`, `-0`, `-0.00`, whitespace, commas, and more than two fractional digits. These remain pending owner approval. No amount range is recommended or inferred. KES may be used only when explicitly declared by the pinned schema; never infer it from location or silently convert.

The proposed mapping under **PRS-05** is JSON string in `value` and `unit="KES"` for `decimal_amount`, conditional on confirmed model/migration/live compatibility. The meaning of `unit` for other types remains unresolved. This is not an established current convention.

### Completeness and draft semantics

Draft may have zero or some responses. Each supplied response must be structurally valid for its question; invalid individual draft values are not persisted. On submit, validate the *entire stored response set*, plus any request-supplied final response set if the submit request carries one, against the pinned schema. Reject unknown saved question IDs and required omissions. Required text containing only Unicode whitespace is missing. Required multiple choice with `[]` is missing. Optional question omission is valid. Optional empty/whitespace text is valid and preserved. No server-side trimming or silent rewrite. `null` is invalid, never equivalent to omission.

**PRS-06 recommendation:** submit carries the complete final response mapping, validates it against the pinned revision, then atomically persists that mapping and the submitted state. Validation failure leaves saved draft rows and attempt state unchanged. Pending owner approval; implementation must not select this behavior until resolved.

## 5. Bounds, parser safety, and unresolved numeric decisions

Finite resource bounds are required to cap parsing, memory, rendering, database row/JSON size, and validation CPU. The proposed values below are not owner-approved policy. Every limit is mapped to PRS-01, PRS-02 or PRS-03 and remains pending. If approved, the exact boundary must be enforced before persistence and independent of browser validation.

| Limit | Recommendation | Class / approval |
|---|---:|---|
| Short-text max | 280 code points | PRS-01; pending owner approval |
| Long-text max | 10,000 code points | PRS-01; pending owner approval |
| Schema questions | 100 | Resource-control ceiling; owner approval to make implementation constant/config choice |
| Choice options/question | 100 | Resource-control ceiling; owner approval to make implementation constant/config choice |
| Label length | 500 code points | PRS-02; pending owner approval |
| Encoded schema | 256 KiB | PRS-03; pending owner approval and enforcement-boundary verification |
| Request body | 256 KiB | PRS-03; pending owner approval; verify actual request boundary before implementation |
| Serialized response set | 128 KiB | Resource-control ceiling; enforced before DB write, owner approval before implementation |
| JSON depth | 8 | Parser/resource-control ceiling; schema/value structures are shallow by contract, owner approval before implementation |
| Decimal scale | 2 fractional digits proposed | PRS-04; pending owner approval |
| Decimal magnitude | finite bound required; no default supplied | PRS-04; no amount range proposed; do not invent one |
| Integer bounds | optional per schema, exact JSON integer | Owner contract; if no bound, technical representability still bounded by request bytes and Python integer digit limit |

The database `JSONField` does not impose these input limits. Reverse proxy/server request caps are not confirmed by inspected source and must be confirmed in the existing deployment contract before implementation; do not add infrastructure in this phase. Django request parsing errors, malformed UTF-8/JSON, duplicate keys, invalid top-level shape, and over-limit body return a generic 400/413 class response without echoes of sensitive learner input. Set a reasonable maximum numeric token length/depth in the parser; do not parse unbounded integer/decimal strings. Unicode labels/text are preserved; length is code points, not bytes, and request byte ceilings cap encoded size. No regex with catastrophic backtracking; identifier regex is anchored and bounded.

Configuration can tune operational ceilings only within a reviewed maximum; it cannot enable unknown types/keys, weaken identifier/choice rules, raise text values above approved ceilings, or bypass server-side checks. If limits become product-visible schema fields, changing them requires a schema-contract version decision rather than silently changing version 1.

## 6. Exact revision resolution and historical interpretation

For `GET /practice/<slug>/`, resolve by identity slug, requiring activity status `published`, non-null `current_published_revision`, pointed revision status `published`, and `revision.activity_id == activity.id`. Exclude draft, in-review, superseded/retired, mismatched-pointer, and any otherwise ineligible revision. The current pointer, not a client-supplied revision ID, chooses the revision. Validate the revision schema before rendering. If invalid, fail closed with unavailable content; never render a partial generic form.

`create_attempt` receives activity slug/identity, not a revision identifier. Inside an atomic transaction, lock/read the eligible identity and pointer, re-check pointed revision ownership and publication state, validate the schema, then create `PracticeAttempt(owner=request.user, practice_revision=resolved_revision, state='started')`. The FK is the historical pin. No response may choose or change the revision. Choice IDs are always checked against this FK's revision schema, not the latest pointer.

Later publication changes the activity's pointer; it does not rewrite old attempts. `EditorialRevision` prevents ordinary updates/deletes of non-draft revisions and attempts/requirements use `PROTECT`; the FK therefore provides a stable reference when normal service paths are used. Direct SQL and privileged database actions are outside Django model guards; least-privilege runtime DB role and operational controls remain important. If current content governance permits a pinned revision to become ineligible for new access, the existing attempt must remain interpretable. Whether learners can resume a started attempt after retirement is **PRS-08**. Proposed behavior: owner-scoped resumption against the exact pinned revision, even when a newer revision is current; new attempts resolve the eligible current revision. Pending owner approval.

Every attempt read/write first resolves authenticated `request.user`, requires active account, `is_active`, verified email and `account_status == 'active'`, then fetches `PracticeAttempt` by both PK and owner. Child responses are only fetched through that owner-scoped attempt. Never reveal whether a foreign attempt ID exists; return the same not-found outcome. No client owner, journey, revision, or state is trusted. If an optional journey is supported in create request, resolve it server-side and require same owner; its acceptance in this slice should be omitted unless needed by an approved flow.

## 7. Services and route contract

Planned routes from the task are **not present** in `config/urls.py` and must be treated as future routes. Route methods below are recommendations consistent with same-origin server-rendered architecture; final response negotiation must match the selected HTML/form interaction.

### `GET /practice/<slug>/`

Public display of currently eligible exact revision; no learner data. Authentication is not required for reading, consistent with anonymous public reading. Resolve eligible published revision and validate schema. 404 for unknown/ineligible identity; sanitized unavailable-content response for malformed schema. Include CSRF token for authenticated start/save/submit forms. No revision selector from query parameters.

### `POST /practice/<slug>/attempts/` — `create_attempt`

Preconditions: POST, valid CSRF/session, active verified user; eligible public revision/schema. Ignore/reject owner/revision/state fields. Validate in order: method/CSRF and authenticated eligibility; request encoding/body cap; exact request keys; slug resolution and eligibility; schema validation; optional validated journey ownership; atomic locked attempt creation. New attempt is `started` and pins exact revision. Duplicate create POST behavior is **PRS-09**: use redirect-after-POST and do not silently reuse an attempt. No idempotency key is selected. The exact repeated-create outcome remains pending owner approval. Audit event is operational/security log with actor ID, attempt ID, revision ID, action and outcome only; never response content.

Success: redirect to owner-scoped attempt/form page or return the new attempt URL. Invalid body returns 400; no eligible revision 404; malformed schema unavailable response; unverified/disabled user uses sign-in/authorization flow without creating attempt. DB failure rolls back.

### `POST /practice/attempts/<id>/responses/` — `save_response`

Resolve verified owner; lock attempt row with `select_for_update`; require state `started`; load exact pinned revision and validated schema. Parse strict request, reject unknown keys/question IDs and validate supplied value against question type and constraints. Save only that question's row, keyed by stable schema question ID in `prompt_key`; use upsert only after validation, with attempt lock held. Omission is not a delete. Explicit clearing of an optional saved answer is **PRS-07** and must be distinct from an intentionally empty value. Pending owner approval; do not use omission, null, or an empty value as an implicit clear action. For an atomic batch save, validate all entries before any write, then apply all in the same transaction. Any validation error writes nothing. Return question-associated field errors; do not return stored response values for unrelated questions.

Concurrent saves serialize on attempt row. Same-question last-writer-wins only among requests serialized by the lock; return a conflict or retry response if stale-version detection is later added. No version token exists now. Audit only event metadata, not answer content.

### `POST /practice/attempts/<id>/submit/` — `submit_attempt`

Resolve verified owner and lock attempt row `select_for_update`; require `started`; load pinned revision and validate schema. Under **PRS-06**, the proposed operation receives the complete final mapping, validates all types/options/constraints/completeness against the pinned revision before mutation, then atomically persists responses and transitions state. Validation failure preserves the saved draft exactly. `response_summary` must not be accepted from the caller. Under **PRS-09**, repeated submit cannot mutate responses or change `submitted_at`; use redirect-after-POST. Exact response/status semantics remain pending owner approval. Never imply correctness, acceptance, score, or completion.

Lock ordering is attempt first, then response rows, consistently for save and submit. PostgreSQL `select_for_update` and atomic transactions are required for production. SQLite unit tests do not prove this concurrency behavior; test against isolated supported PostgreSQL.

### Error contract

Field errors identify stable question IDs and a safe error code/message, e.g. required, invalid type/format, unavailable option, out of range, too long. Do not include submitted values in errors. Unknown question IDs can be reported as a generic invalid response rather than echoing attacker-controlled identifiers. Malformed schema is a server/content availability error, not a learner answer error. Unauthorized foreign IDs map to not-found. 403/sign-in applies to an authenticated but ineligible account; 400 for malformed payload; 409 for already submitted/stale state; 413 for body/size limit; 404 for unavailable resource. HTML pages must preserve entered values only for the current safe validation response and escape them normally; do not log payloads.

## 8. Data model adequacy and integrity findings

### Existing verified capability (source-level)

- Exact revision FK exists and is `PROTECT`; owner FK is `PROTECT`; stable response key and unique attempt/question key exist.
- JSON value can represent all six types without float for decimal; absent row, empty string, and whitespace-only string remain distinguishable. JSON null exists physically but must be rejected by validators.
- `unit` can hold `KES` within 48 characters. Existing approved financial policy is KES-first and explicit currency. It can safely store currency if the service contract assigns it exclusively that meaning for decimal amounts and requires exact `KES`; however the current field is generic and code does not enforce this. Proposed PRS-05 mapping: canonical amount string in `value`, `unit='KES'` for decimal. The meaning of `unit` for every other type remains unresolved. This recommendation is conditional on physical compatibility and owner approval; current implementation does not enforce it.
- Published revision immutability is guarded in ordinary model save/delete paths; protected FKs preserve referenced rows. This is not database-level immutability against SQL/superuser operations.

### Gaps implementable without schema change

Schema/response validation, exact resolver, owner filters, row locks, transaction boundaries, fixed unit convention, atomic submit, and field errors can be implemented in services/views using existing columns. Model JSONField alone does not enforce these rules. Ensure no mass assignment and never trust `response_summary`.

Submitted immutability has existing ORM guard intentions, but is incomplete as a universal invariant: `PracticeAttempt.save` guards submitted changes, response instance save/delete guard state, and queryset overrides block update/bulk operations. Direct SQL bypasses them; related managers/raw SQL/admin/custom code may also bypass. `PracticeHistoryQuerySet.bulk_create` is blocked, but instance-level paths and custom manager/base manager behavior require review. At minimum all application writes must go through locked services, add tests for every project write path, exclude unrestricted admin, and ensure app DB role is not schema owner/superuser. A hard database-enforced immutable submitted-child rule would require database trigger/constraint architecture not currently specified and would need separate approval. Do not represent ordinary model guards as impossible-to-bypass immutability.

### Physical-model limitation / decision

Whether the schema is adequate is **PRS-10** and remains unresolved. Source-level shapes appear capable of representing the six values if the PRS-05 mapping is approved: JSON preserves strings/arrays/integers; `prompt_key` length 120 can hold the approved max-64 ID; `unit` length 48 can hold `KES`; omission/empty/whitespace distinctions survive. This is not evidence of live compatibility or proof that no schema change is needed. Owner-supplied live inspection reports that Practice columns and catalog objects were inspected and found no Practice rows, but this documentation does not record a full field-by-field model/migration/catalog comparison or a data convention check. The physical design does not itself make decimal currency semantics explicit or constrained. The addendum requires a physical-model adequacy check. The mapping decision and full live catalog/migration comparison remain prerequisites. If audit finds `unit` already has conflicting semantics or a DB mismatch, stop for approved physical-model review; do not add columns or migrations here.

Concurrency consistency requires service-level row locking on the attempt for every draft save and submission. Current `save_response` does not lock the attempt; current submit locks but doesn't validate. Without lock discipline, a response write can race submission. PostgreSQL row locks plus one transaction per operation are implementable without schema change.

## 9. Learner behavior and accessibility

- Render only the six supported controls with semantic labels and help text from safely escaped editorial content; choice values are stable IDs, labels visible to learner.
- Display exact currently published revision; show clear unavailable state for invalid/ineligible content. Preserve the revision on an attempt page.
- Allow incomplete drafts; make “Save draft” distinct from “Submit Practice”. Indicate saved/pending status without claiming correctness.
- Show required unanswered and invalid fields adjacent to controls, summarize errors at top, link summary entries to fields, move focus to error summary after failed submit, and retain user-entered values without trimming. Use `aria-describedby`, `aria-invalid`, semantic fieldsets/legends for choices, keyboard-operable buttons, visible focus, and responsive single-column mobile layout consistent with existing MaliLab shell/CSS.
- Expired sessions should preserve no private data in the URL; direct learner to sign in and then re-authorize owner access. Do not leak whether an attempt exists across accounts.
- After successful submit, confirm “submitted” only, display no score/acceptance/correctness/Module completion implication. Disable/edit controls and render immutable response view. Outcome after refresh uses stored state.
- Whether a learner can resume an attempt whose pinned revision is no longer current is **PRS-08**: proposed owner-scoped resume on that exact pinned revision, while new attempts use the eligible current revision; pending owner approval.

No general redesign or JavaScript dependency is required. Browser-native constraints are progressive enhancement only; server validation is authoritative.

## 10. Security, ownership, and privacy controls

Threat controls required by existing owner-scoped architecture and Django session design:

- Cross-account/IDOR: every attempt and response query includes authenticated owner; nested child lookup through owner-scoped attempt; foreign/not-found indistinguishable; test alternate IDs on GET/save/submit.
- Revision tampering: client cannot send revision ID; resolver selects published current exact revision on create; attempt FK immutable; all answer and option validation uses pinned revision.
- Mass assignment: explicit field allowlists and exact JSON keys; never bind raw JSON to model fields; ignore or reject owner/state/timestamps/summary/foreign keys.
- CSRF/session: POST-only state changes, Django CSRF middleware/token, same-origin session cookies and standard login/session behavior; no GET mutation. Preserve existing sign-in flow.
- Account eligibility: use existing `UserAccount.can_use_personal_features` equivalent and server-side active, verified, active-status checks on every private operation. Do not create accounts or alter authentication in this phase.
- Response tampering: immutable submitted state at service and model path; lock and validate at submission; block ordinary save/delete after submission; never trust caller summary. Close admin/maintenance paths that bypass service. Database-owner or raw SQL tampering remains privileged and must be outside runtime role capability where currently configured.
- Resource abuse: finite bytes/count/depth/text/numeric token caps; reject before persistence; bounded validator and option membership lookup; generic errors, rate-control only if already available (no new infrastructure authorized).
- Privacy: do not place answer content, financial amounts, or raw bodies in logs, analytics, exception reports, URLs, or staff/admin pages. Sanitized event metadata only. Staff roles do not imply automatic learner response access. Any future evaluator access belongs to future approved scope.

Do not introduce PostgreSQL RLS, new authentication, infrastructure, or database permission changes in this phase.

## 11. Test specification

No tests were run for this documentation task. The matrix below is a future implementation requirement; PostgreSQL-specific cases require the isolated test role/database from `config.postgres_test_settings`, and must never target live MaliLab.

| Layer | Test cases |
|---|---|
| Schema validator unit | All six types valid/invalid; exact keys; wrong JSON types/bools; required/optional; IDs regex boundaries and duplicates; option IDs duplicate/unknown; malformed schema; unsupported version/type/key; bad constraint combinations; `max_length` positive/bounds; question/option/schema-size/depth limits; Unicode labels/text; whitespace. |
| Value validator unit | String exact type and limits; integer no bool/float/string coercion and inclusive bounds; choice membership; duplicate multi-selection; optional `[]`; required empty; decimal canonical grammar, KES, precision/scale/range, exponent/commas/leading zeros/negative zero rejection; null rejection; no float acceptance; oversized numeric token. |
| Service | Create pins correct published revision; rejects draft/unpublished/mismatched/retired; unverified/disabled/anonymous denied; incomplete draft accepted; invalid draft does not write; unknown ID rejects; empty/whitespace semantics preserved; submit all required checks; invalid submission leaves all rows/state/timestamp unchanged; submitted response edit/delete/save rejected; duplicate submit stable; no caller summary trust; journey same-owner if retained. |
| Routes/UI | Planned route methods and names; public GET anonymous/current revision only; CSRF; method restrictions; valid POST and redirects; field errors; no owner/revision mass assignment; invalid schema unavailable; foreign attempt indistinguishable 404; expired session; rendered labels/fieldset/error focus/keyboard and responsive source checks; no acceptance wording. |
| Database/PostgreSQL | Model/migration/live catalog agreement before implementation; unique `(attempt,prompt_key)`; FK/protect behavior; JSON representation; exact transaction rollback; `select_for_update` concurrent save-versus-submit and double-submit; pinned revision survives pointer publication change; run only supported PostgreSQL 16 target confirmed by current project authority, with isolated DB+role unable to connect to live app database. |
| Regression/integration | Existing sign-in/session behavior and anonymous public content reads unchanged; Practice vertical flow end-to-end; no evaluation/scoring/acceptance/evidence/module completion; no seed content or unrelated behavior; full prior suite remains green in authorized test environment. |

Before migration approval (if a separately approved model gap emerges), test migration against a sanitized representative copy of verified existing data and document rollback/compatibility plan. No migration is presently authorized or asserted necessary.

## 12. Traceability and unresolved items

The versioned schema grammar and six allowed types are defined above from the 6B.5A addendum. Stable question/choice identifiers, required/optional behavior, whitespace preservation, null/unknown-ID rejection, and the separation of submission from evaluation are also defined by that addendum. The contract deliberately does not complete unresolved operational/product behavior by assumption:

| Specification area | Current status and decision link |
|---|---|
| Short/long text maximums | **PENDING OWNER APPROVAL — PRS-01:** 280 and 10,000 Unicode code points proposed. |
| Question/option label maximums | **PENDING OWNER APPROVAL — PRS-02:** 500 Unicode code points proposed. |
| Schema/request/serialized-response byte limits, question/option counts, JSON nesting/parser bounds | **PENDING OWNER APPROVAL — PRS-03:** 256 KiB / 256 KiB / 128 KiB / 100 / 100 / depth 8 proposed. Verify actual enforcement boundaries before implementation. |
| Decimal canonical syntax and scale | **PENDING OWNER APPROVAL — PRS-04:** base-10 strings, maximum two fractional digits for KES, listed invalid forms; no amount range proposed. |
| Decimal currency wire/storage mapping and meaning of `unit` across types | **PENDING OWNER APPROVAL — PRS-05:** prefer amount string in `value`, `unit="KES"`, conditional on verified physical compatibility; define other types. |
| Full response mapping at submit; atomic response/state transition; unchanged draft after validation failure | **PENDING OWNER APPROVAL — PRS-06:** complete final mapping, pinned validation, atomic persistence and no draft mutation on invalid submit. |
| Intentionally clearing an optional saved answer | **PENDING OWNER APPROVAL — PRS-07:** explicit clear distinct from intentionally empty value. |
| Resuming a started attempt after its pinned revision is no longer current | **PENDING OWNER APPROVAL — PRS-08:** owner-scoped resume against exact pinned revision proposed. |
| Duplicate submission and retry/create-attempt safety | **PENDING OWNER APPROVAL — PRS-09:** immutable repeat submit/timestamp, redirect-after-POST, no silent attempt reuse proposed. |
| Adequacy of existing fields/constraints and need for schema change | **NOT VERIFIED / PENDING OWNER APPROVAL — PRS-10.** Requires live catalog/model/migration reconciliation and owner review of the resulting mapping. No schema change is authorized. |
| `response_summary` relationship to response persistence | **NOT VERIFIED — PRS-06/PRS-10.** Existing source accepts caller-provided summary; no approved submission-summary contract establishes it as canonical response storage. Do not trust it or claim it is compatible. Its treatment must be resolved as part of the submission contract and physical adequacy review before implementation. |
| Relationship of attempt state to persisted responses | Existing state names are settled (`started`, `submitted`, `abandoned`). **PENDING OWNER APPROVAL — PRS-06:** exact write/transition boundary; atomic final mapping/state transition is the recommendation, not approved policy. |
| Educational boundary | **DEFINED / OUT OF SCOPE.** Submission confirms receipt after structural validation only. No scoring, automatic acceptance, learner evaluation/feedback, or Requirement Evidence creation. |
| Tests and acceptance evidence | Required future tests are enumerated in §11; their execution and acceptance results are **NOT APPLICABLE YET**. Live compatibility tests/review must use an isolated approved environment, never the live database. |

No final implementation contract exists for PRS-01 through PRS-10. All remain pending owner approval in the consolidated register. Resolve them and revise this specification after owner review; do not translate recommendations into policy.

| Rule | Trace |
|---|---|
| Six types, schema v1, key allowlist, identifiers, requiredness, null rejection, no trim, decimal string/explicit currency, fail-closed schema | Owner addendum §§3–6 |
| Three existing attempt states; draft incomplete; explicit submit; no edit after submit | Owner addendum §7 and existing Practice model |
| No automatic acceptance/scoring/evaluation/evidence/module completion | Owner addendum §§8–11; DB-019 / Phase 6B plan boundary |
| Exact revision and owner pin | Owner addendum §§12–13; approved content versioning and ownership specifications |
| Active verified user; same-origin session/CSRF; public anonymous reading | Approved account decisions, `accounts.UserAccount`, Phase 6B.4 audit, Django middleware |
| Decimal currency representation and meaning of `unit` | **PENDING OWNER APPROVAL — PRS-05**; proposed value string plus `unit="KES"` is conditional on confirmed compatibility. |
| Proposed limits, decimal grammar, unit mapping, submit/clear/resume/retry behaviors | **PENDING OWNER APPROVAL — PRS-01 through PRS-09**, mapped individually above; recommendations are not approved policy. |
| Actual live table/data/migration compatibility | Owner-reported partial identity/catalog/zero-row observations only; complete catalog/model/migration parity, migration drift, and physical-spec discrepancies remain unverified; see companion report and bounded operator checklist. |

### Owner decisions still required before implementation

The PRS register remains the authority for which recommendations are pending. Implement only behaviors specified by the owner directive or settled addendum; do not convert remaining proposals into approved product policy. PostgreSQL compatibility remains unverified in this execution, and consequential unresolved decisions remain acceptance gates. GOV-002 supplies the current application implementation authorization.

These decisions affect contract/business-visible behavior or implementation-specific request/storage semantics and must not be silently assumed. The actual live database compatibility prerequisite is separately a technical blocker.

## 13. Factual/documentation defect

The 6B.5A example includes `max_length: 4000`; it labels the number illustrative and not an approved product limit. No defect in owner authority; this specification preserves that caveat. The practice fixture `{"type":"object"}` is not a production schema. Route paths in the prompt are planned and absent from current URL configuration. These facts do not change owner decisions, but implementation must not mistake either example or route list for existing approved runtime behavior.


## Execution record — 2026-10-13

The owner’s current execution directive supersedes this document’s earlier statement that Phase 6B.5 implementation was unauthorized. Existing schema and migration authorization boundaries remain in force. Application work now present includes strict version-1 schema validation, typed answer validation against the attempt’s pinned Practice revision, published exact-revision activity reading, authenticated attempt creation/resumption, owner-scoped draft save/clear, atomic complete submission, safe repeat submission, and server-rendered forms. No model or migration was changed. The same execution added learner-facing Notes, immutable My Plan revision, evidence-derived Progress, public projection Search, and Module completion snapshot screens. See the source and tests listed in the final execution report.

This does **not** establish Phase 6B acceptance. PostgreSQL test setup and live catalog/migration-ledger comparison could not be performed because the configured PostgreSQL host was unavailable. The evaluator permission/UI prerequisite remains unresolved; no automatic acceptance or Practice evidence creation was added. PRS recommendations that the owner directive did not expressly resolve remain pending rather than being treated as approved policy.

The validator currently applies the documented PRS recommendations for text/label limits and operational payload/count limits, and the recommended decimal string plus `unit="KES"` mapping. It does not set an amount range. The remaining retry/create-attempt policy is not resolved; repeated submission itself is idempotent. These implementation behaviors are not evidence of live PostgreSQL physical compatibility.
