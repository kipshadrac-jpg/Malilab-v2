# Phase 6B.5A — Practice Response Schema & Evaluation Contract

**Document status:** Planning artifact for owner review. This document does not authorize Practice implementation or physical schema changes.

## 1. Purpose

This document records the existing Practice baseline and exposes the decisions required for a deterministic first Practice implementation. It does not silently approve a new response vocabulary or evaluation policy. Statuses are **APPROVED** (supported by existing approved decisions), **PROPOSED — REQUIRES OWNER APPROVAL**, **TO-BE-DEFINED**, or **OUT OF SCOPE**.

## 2. Scope

Planning only. No models, forms, views, services, templates, JavaScript, CSS, migrations, tests, URLs, database contents, or dependencies are changed by this artifact. It covers response shape, validation/evaluation distinction, attempt lifecycle, acceptance, feedback, retries, evidence boundary, historical interpretation, editorial responsibility, security, mobile constraints, and readiness.

## 3. Existing Practice Baseline

| Topic | Existing approved fact | Inference / missing decision |
|---|---|---|
| PracticeActivityRevision | Editorial revision with title, prompt/instructions and `response_schema`; attempts reference the exact revision. Published editorial revisions follow the general immutable-revision architecture. | The `response_schema` contract and supported answer types are **TO-BE-DEFINED**. |
| Current response_schema | Django JSONField, default `{}`. Existing Practice test fixture sets `{"type":"object"}`. | The fixture does not establish a production schema. No formal schema-to-form contract exists. |
| PracticeAttempt | Stores owner, exact Practice revision, optional same-owner journey, `state`, `started_at`, optional `submitted_at`, and `response_summary`. Current states are `started`, `submitted`, `abandoned`. | Meaning and transitions for `abandoned`, and whether persisted drafts are in scope, are not settled by logical design. |
| PracticeResponse | Child of attempt; stores `prompt_key`, JSON `value`, optional `unit`, and `answered_at`; one row per attempt/prompt key. | Whether values are raw, normalized, or both; payload shape; schema validation; null/empty semantics remain **TO-BE-DEFINED**. |
| Current service behavior | Creates attempt for active verified account; saves arbitrary JSON by prompt key while attempt is started; submit marks started attempt submitted and sets timestamp. | Service does not validate against response_schema, require answers, or evaluate educational correctness. `response_summary` is caller-provided and not a defined answer contract. |
| Mutability | Model/service paths permit response editing while started; submitted attempt/response mutation is guarded. Submitted timestamp is recorded. | These implementation facts do not settle whether submission must be irreversible in all trusted paths or how invalid input is handled. |
| Submitted | Current implementation changes state to `submitted` and records `submitted_at`. Phase 6B describes explicit submission and received/submitted feedback. | Logical field specification says save/submit semantics TBD. The act's acceptance meaning is explicitly separate and **TO-BE-DEFINED**. |
| Accepted | Requirement Evidence has accepted/rejected state; accepted evidence can satisfy one exact requirement. Tests create accepted evidence directly. | There is no Practice attempt acceptance state or decision service. What grounds acceptance, who decides, and whether automatic evaluation is permitted are **TO-BE-DEFINED**. |
| Evaluation / scoring / feedback | No Practice evaluation/scoring/feedback entity or service is present. Product/domain sources do not define a scoring algorithm. | Educational acceptance criteria, evaluator, result vocabulary, reviewer feedback and timing are **TO-BE-DEFINED**. |
| Retry / correction | Multiple attempts are structurally possible. Submitted records are intended to preserve history. | Retry limits, correction, reopening and which accepted attempt is selected are **TO-BE-DEFINED**. |
| Requirement relationship | ModuleLearningRequirement may target an exact PracticeActivityRevision and has required/optional/recommended classification. Requirement Evidence identifies exact requirement, Module revision, Practice revision and submitted attempt. | Only an accepted evidence association satisfies the required Practice item; the decision that creates the association must be explicitly specified. |
| One attempt / requirements | Owner decision DB-019: **one accepted Practice Attempt satisfies one Module Requirement initially; no inferred multi-credit**. | This bounds evidence association for initial policy; it does not define evaluation. |
| Tests | `practice/tests.py` establishes verified-account gate, ownership isolation, arbitrary JSON save, edit-before-submit, submitted immutability, and timestamp/state transition. `learning/tests.py` establishes exact matching/accepted evidence behavior and one-requirement satisfaction. | Tests are not a response schema, input validation specification, evaluation contract, or proof that `{"type":"object"}` is valid production content. |

**Baseline conclusion:** Current code offers persistence primitives, not a schema-driven Practice product contract. This conclusion is an inspection finding, not a newly approved requirement.

## 4. Approved Practice Concepts

- **APPROVED:** Practice Activity has editorial revisions; learner attempts pin the exact revision.
- **APPROVED:** Attempt and response are learner-owned/private records; ownership is enforced in current service/model paths.
- **APPROVED:** An explicit submission is distinct from acceptance/evaluation (Phase 6B plan).
- **APPROVED:** Requirement Evidence refers to an exact submitted attempt and exact requirement/revision; only accepted evidence satisfies a required item.
- **APPROVED:** One accepted Practice Attempt satisfies one Module Requirement initially (DB-019); no inferred multi-credit.
- **TO-BE-DEFINED:** What makes an answer educationally acceptable and which actor or deterministic rule decides it.

## 5. Initial Supported Answer Types

No answer type is established by approved Practice product or architecture materials. The entries below are deliberately small candidate vocabulary for owner decision, not approved production behavior.

### Candidate: `short_text`

- **Identifier:** `short_text` — **PROPOSED — REQUIRES OWNER APPROVAL**.
- **Meaning:** One bounded textual answer.
- **Stored representation:** Proposed JSON string; whether canonical trimming or raw-value retention is required is **TO-BE-DEFINED**.
- **Required behavior:** Requiredness semantics **TO-BE-DEFINED**.
- **Validation behavior:** Proposed Unicode text with explicit owner-approved maximum length; limit and whitespace/empty semantics **TO-BE-DEFINED**.
- **Evaluation behavior:** No automatic correctness inference. Human review or explicit non-scored acceptance policy **TO-BE-DEFINED**.
- **Mobile rendering requirement:** Single-line text control with accessible label; exact rendering and length feedback **PROPOSED**.
- **Status:** **PROPOSED — REQUIRES OWNER APPROVAL**.

### Candidate: `long_text`

- **Identifier:** `long_text` — **PROPOSED — REQUIRES OWNER APPROVAL**.
- **Meaning:** One bounded free-form response.
- **Stored representation:** Proposed JSON string; raw/normalized persistence **TO-BE-DEFINED**.
- **Required behavior:** Requiredness and empty-answer semantics **TO-BE-DEFINED**.
- **Validation behavior:** Maximum length and whitespace semantics **TO-BE-DEFINED**.
- **Evaluation behavior:** No automatic correctness; human review/acceptance policy **TO-BE-DEFINED**.
- **Mobile rendering requirement:** Multiline control with accessible label; exact bounds **PROPOSED**.
- **Status:** **PROPOSED — REQUIRES OWNER APPROVAL**.

### Candidate: `single_choice`

- **Identifier:** `single_choice` — **PROPOSED — REQUIRES OWNER APPROVAL**.
- **Meaning:** Select one editorially defined option.
- **Stored representation:** Proposed stable option identifier string, not display label.
- **Required behavior:** Requiredness **TO-BE-DEFINED**.
- **Validation behavior:** Value must equal one option identifier in the pinned revision; option lifecycle/edit rules **TO-BE-DEFINED**.
- **Evaluation behavior:** Correct-option keys and automatic acceptance are not specified; no auto-grading approved.
- **Mobile rendering requirement:** Clearly labelled, touch-friendly radio controls; exact option limits **PROPOSED**.
- **Status:** **PROPOSED — REQUIRES OWNER APPROVAL**.

### Candidate: `multiple_choice`

- **Identifier:** `multiple_choice` — **PROPOSED — REQUIRES OWNER APPROVAL**.
- **Meaning:** Select one or more editorially defined options.
- **Stored representation:** Proposed array of stable option identifier strings.
- **Required behavior:** Requiredness and whether zero selections are allowed **TO-BE-DEFINED**.
- **Validation behavior:** Unique identifiers, all present in pinned revision; ordering and minimum/maximum selections **TO-BE-DEFINED**.
- **Evaluation behavior:** No approved answer key or grading behavior.
- **Mobile rendering requirement:** Touch-friendly checkbox controls; exact option limits **PROPOSED**.
- **Status:** **PROPOSED — REQUIRES OWNER APPROVAL**.

### Candidate: `integer`, `decimal_amount`, `boolean`

- **Identifier:** `integer`, `decimal_amount`, `boolean` — candidates only.
- **Meaning / representation:** Integer JSON number; decimal amount as canonical decimal string; boolean JSON true/false, respectively, are possible representations, but none are approved for Practice.
- **Required behavior:** **TO-BE-DEFINED**.
- **Validation behavior:** Numeric bounds, precision, scale, currency/unit, decimal grammar and boolean labels have no Practice-specific approval. General financial calculation decisions do not establish a Practice answer contract.
- **Evaluation behavior:** No automatic evaluation authorized.
- **Mobile rendering requirement:** Numeric input affordances and yes/no controls are candidates; exact presentation **TO-BE-DEFINED**.
- **Status:** **TO-BE-DEFINED**. Do not implement until explicitly approved.

**Initial type set:** No initial set is approved by this phase's source material. Owner approval is required before implementation can safely select even the proposed text/choice subset.

## 6. Practice Response Schema Contract

**Current approved contract:** None. `response_schema` is opaque JSONField data and has no formal root shape, schema version, field vocabulary, validation semantics, or renderer mapping.

**Proposed owner-review direction (not approved):** A narrow MaliLab-owned JSON object rather than arbitrary JSON Schema, containing an explicit schema version and ordered array of uniquely identified questions. Each question would contain only a stable identifier, approved type identifier, editorial label, required flag, and type-specific constraints/options. Choice options would have stable identifiers and separate display labels. Defaults would be prohibited initially. Unknown root/question/constraint keys would be rejected. No renderer would interpret arbitrary JSON Schema keywords.

The foregoing is a **PROPOSED** direction only. The following exact details remain unresolved and must not be inferred by implementation:

- Root key names and schema-version format.
- Question identifier grammar, uniqueness scope and ordering mechanism (array order versus explicit position).
- Approved type identifiers and exact JSON types for answers.
- Label/help/instruction fields and localization policy.
- Required-field representation and empty/null semantics.
- Choice option structure, stable identifier grammar, uniqueness and whether option sets are single/multiple selection.
- Allowed constraints by type, inclusive/exclusive range behavior, text length bounds and error semantics.
- Defaults (candidate recommendation: none in initial contract), numeric encoding and monetary unit/currency handling.
- Whether partial responses may be saved and how missing fields are represented.
- Published-schema immutability and schema evolution policy within a content revision.
- Exact contract versioning and support/retirement policy.

No production schema example is provided because no exact structure has been approved. `{"type":"object"}` is not a production-approved schema.

## 7. Response Validation Contract

**Conceptual distinction — APPROVED:**

- **Schema validation** asks whether the payload has the permitted structure and answer types for the exact Practice revision.
- **Evaluation** asks whether a schema-valid answer meets educational or activity-specific criteria. Validation alone does not establish correctness, acceptance, or requirement satisfaction.

Detailed rules are **TO-BE-DEFINED** pending schema/type approval:

| Condition | Current rule/status | Blocking versus evaluation |
|---|---|---|
| Required field absent | **TO-BE-DEFINED** whether permitted in saved draft; must be decided for submit. | If requiredness is approved, missing required answer should block submission (**PROPOSED**). |
| Wrong JSON type / malformed payload | No current service check. Exact parser and error handling **TO-BE-DEFINED**. | Submission-blocking (**PROPOSED**) for malformed or type-invalid response. |
| Invalid choice identifier | Choice types not approved. | Submission-blocking if choice types approved (**PROPOSED**). |
| Out-of-range / overlength value | Constraints not approved. | Submission-blocking only for explicitly approved schema constraints (**PROPOSED**). |
| Unknown field injection | Current service accepts arbitrary prompt keys. Unknown-key behavior **TO-BE-DEFINED**. | Reject unknown keys at submit (**PROPOSED**); draft behavior also needs decision. |
| Invalid schema / unsupported type | No schema validator exists. | Publishing/serving policy and fail-closed behavior **TO-BE-DEFINED**; never silently treat unsupported data as valid. |
| Null, empty string, whitespace-only, omitted answer | **TO-BE-DEFINED** per approved type. | Must be resolved before submission validation implementation. |
| Educationally unsatisfactory answer | Not a schema error. | Evaluation-time judgment; must not be silently converted into a structural validation error. |

The raw submitted payload, normalized value policy, persistence of validation errors, error vocabulary, and whether drafts may be partially incomplete remain **TO-BE-DEFINED**. Invalid payload must not become a submitted attempt under the proposed gate; this requires owner approval alongside the final validation contract.

## 8. Practice Attempt Lifecycle

Existing code states: `started` → `submitted`; `abandoned` is also an allowed model value, but its transition and meaning are not defined by an approved user-facing contract. Phase 5 logical design says in-progress draft persistence is TODO; Phase 6B proposes start, save response, then explicit submit.

- **APPROVED:** Attempt references an exact PracticeActivityRevision and has a learner owner.
- **APPROVED:** Submitted history is intended to be immutable; submission timestamp is stored by current implementation.
- **TO-BE-DEFINED:** Whether `started` is a persisted draft, how abandonment works, whether attempts can be deleted before submit, and permitted transitions.
- **TO-BE-DEFINED:** Whether retry creates a new attempt and any retry limits.
- **OUT OF SCOPE:** Adding states beyond those needed to express an owner-approved lifecycle.

## 9. Submitted Semantics

**APPROVED concept:** Submission is a learner action distinct from acceptance/evaluation. Phase 6B calls for explicit submission and feedback that distinguishes received/submitted from accepted/evaluated.

Current implementation records `submitted_at`, changes state to `submitted`, and guards edits to submitted responses. Proposed operational meaning for owner approval: an explicit learner submit action commits the payload that passed schema validation for the exact pinned revision; it records a timestamp; subsequent learner edits are disallowed; the attempt can then be evaluated. Whether an invalid response blocks submit, whether submit can be reversed by privileged correction, and whether all submission paths are irreversible remain **TO-BE-DEFINED**. A later Practice revision must not change the meaning of an already submitted attempt.

## 10. Accepted Semantics

**APPROVED:** Accepted is not synonymous with submitted or schema-valid. Requirement Evidence has an accepted/rejected decision state; only accepted evidence satisfies a required item. Phase 6B requires received/submitted to be distinguished from accepted/evaluated.

**TO-BE-DEFINED:** Whether acceptance means educational satisfaction by a human, a defined automatic rule, or an explicitly approved combination; accepted/rejected result vocabulary; authority to decide; and whether acceptance can be revised. No candidate answer type is automatically accepted under the current approved sources. Structural validity alone must not produce acceptance.

## 11. Evaluation Contract

An explicit evaluation concept is necessary at the domain level because submission and acceptance are distinct and Requirement Evidence records an evaluated accepted/rejected decision. The current implementation has no Practice evaluation model/service; RequirementEvidence stores state and optional evaluated timestamp but does not identify a Practice evaluator/result detail or carry a defined feedback contract.

| Concept | Current/proposed status |
|---|---|
| Evaluated object | Exact submitted PracticeAttempt and its immutable responses (**APPROVED relationship direction**). |
| Evaluator identity/type | Human staff vs deterministic rule vs combination: **TO-BE-DEFINED**. |
| Result | Accepted/rejected evidence decision exists; detailed result lifecycle and whether a separate evaluation record is needed: **TO-BE-DEFINED**. |
| Timestamp | `RequirementEvidence.evaluated_at` exists in the current physical model; when/how set is **TO-BE-DEFINED**. |
| Feedback | Optional evaluation rationale/feedback location, content, access and mutability: **TO-BE-DEFINED**. |
| Separate entity | Not approved. Existing RequirementEvidence may capture the requirement-level outcome, but current fields do not establish full evaluation provenance. Gap must be assessed in implementation specification before implementation; no model change here. |

Do not infer that writing RequirementEvidence by itself defines evaluation or that any submitted response is accepted.

## 12. Scoring Decision

**SCORING: TO-BE-DEFINED / OUT OF SCOPE FOR INITIAL PRACTICE CONTRACT.** No points, percentages, grades, pass marks, weighted questions, or scoring algorithm are authorized by approved source material.

## 13. Feedback Contract

- **Submission confirmation:** Means the system received a submitted attempt; it does not claim correctness or acceptance. **APPROVED distinction.**
- **Validation error:** Means the payload failed a structural/schema rule; exact rules and error format **TO-BE-DEFINED**.
- **Evaluation result:** Means an authorized evaluator/rule made a decision about a valid submitted response; criteria and result provenance **TO-BE-DEFINED**.
- **Acceptance:** Educational/evidence decision distinct from receipt and structural validity. **APPROVED distinction; decision criteria TO-BE-DEFINED.**
- **Reviewer feedback:** Optional explanatory material, not a score by implication; whether required, stored, and visible **TO-BE-DEFINED**.

No feedback or retry UI is specified or implemented in this planning phase.

## 14. Retry / Correction Decision

**APPROVED:** One accepted Practice Attempt satisfies one Module Requirement initially; reassessment preserves history (DB-019).

**TO-BE-DEFINED:** Whether retry is allowed; whether rejected work can be corrected; whether each retry is a new attempt; whether submitted attempts can ever be reopened by staff; retry limits; whether the newest/any accepted attempt is selected; and how a prior acceptance is corrected or revoked. Existing structural ability to create multiple attempts is not a product decision. Do not mutate prior submitted responses to implement correction.

## 15. Requirement Satisfaction Boundary

The approved conceptual flow is:

`PracticeAttempt (submitted)` → `evaluation / accepted decision` → `accepted attempt` → `RequirementEvidence for one exact ModuleLearningRequirement` → satisfaction of that exact requirement.

Only accepted evidence satisfies a required item. The attempt's revision must match the Practice revision targeted by the requirement; owner, ModuleRevision and requirement must match. One accepted attempt satisfies one requirement initially; no inferred multi-requirement satisfaction. This section does not implement Phase 6B.6, create evidence, or redesign Module completion.

## 16. Revision and Historical Integrity

**APPROVED:** `PracticeActivityRevision` is immutable when published in the editorial revision architecture. `PracticeAttempt.practice_revision` is a foreign key to the exact revision, and responses are children of that attempt. The approved versioning specification says attempts pin exact revision and response prompt keys; editing the activity does not reinterpret prior responses. Thus the intended chain is:

`PracticeActivityRevision → response_schema → PracticeAttempt → PracticeResponse → evaluation`.

**Gap:** The current model stores the exact revision reference, but no approved schema version/contract or evaluation provenance is recorded in PracticeResponse/PracticeAttempt. The schema's exact structure is unresolved. The implementation must validate and interpret against the pinned revision, not the current activity pointer. Whether immutable publishing and database-level protection are fully enforced is outside this document's changes and must be verified at implementation time.

## 17. Editorial Responsibilities

Practice revision editors control the activity prompt/instructions and, once approved, would control each question identifier, type, label, required status, option identifiers/labels and permitted validation constraints. Those fields and the exact schema format are **PROPOSED — REQUIRES OWNER APPROVAL**. Published revisions must contain a deterministic supported contract and cannot be silently edited to alter historical responses (**APPROVED general revision principle**). No editorial workflow or publisher functionality is added here.

## 18. Security Boundary

- **APPROVED direction:** Attempts/responses are private learner-owned data; resolve owner from authenticated server-side identity, never client-supplied owner IDs. Current service gates personal persistence to active verified accounts.
- **APPROVED direction:** Cross-account access must be denied; access checks apply to attempt and child response operations.
- **PROPOSED:** Treat all submitted payloads and schema JSON as untrusted. Validate server-side against a bounded allow-listed schema vocabulary; reject unsupported/malformed schemas and unknown fields; never execute schema-supplied code or arbitrary renderer instructions.
- **TO-BE-DEFINED:** Staff roles permitted to evaluate which attempts, audit/provenance requirements for evaluation, sensitive answer retention, payload size/length limits, and review access policy.
- **PROPOSED:** No hidden field can be treated as trusted or accepted merely because a client sends it; editorial schema controls only visible declared questions, and server validation rejects undeclared fields.
- **APPROVED architecture principle:** Published revision integrity and exact historical references must be preserved. Exact implementation controls remain for implementation design.

## 19. Mobile Rendering Constraints

The project constitution and frontend direction require a mobile-first, readable server-rendered experience. The contract should expose only enough editorial information for a deterministic presenter to render approved types with accessible labels and touch-usable controls. Type-specific control, option count, label/help text limits, ordering, error presentation and accessibility details are **TO-BE-DEFINED**. Do not turn Practice into an arbitrary generic form-builder or let JSON specify HTML, scripts, CSS or executable behavior.

## 20. Existing Data Compatibility

The known test value `{"type":"object"}` is a test placeholder, not an approved production Practice schema. The repository scan found no evidence that published production Practice content exists; this planning inspection did not query PostgreSQL or alter it. Existing migrations establish a JSONField default, not valid seed content. Compatibility for any existing non-placeholder values must be assessed before enforcement. If data exists, migration/backfill or explicit compatibility handling is an implementation prerequisite, not authorized here. No migration is made.

## 21. Open Decisions / TO-BE-DEFINED Items

1. Select the initial answer type vocabulary; confirm whether any candidate type is required.
2. Approve exact schema root, schema version, question keys, ordering, type-specific option/constraint shape, and defaults policy.
3. Define required, absent, null, empty, whitespace, partial draft and unknown-field semantics.
4. Define per-type validation constraints and numeric/decimal/currency representation if numeric types are included.
5. Decide whether valid submission alone can ever lead to acceptance; define evaluation authority, criteria/result, provenance and correction policy.
6. Decide if a separate evaluation record is required or if requirement-level evidence is sufficient, including how non-requirement Practice attempts are evaluated.
7. Define draft persistence, abandonment, invalid-submit behavior, irreversibility and retry/correction policy.
8. Define feedback semantics beyond receipt/validation/accepted distinction, including whether reviewer comments are stored.
9. Define schema validation timing and behavior for malformed, unsupported, oversized, or legacy schemas.
10. Determine whether any existing non-test Practice data requires compatibility handling before enforcement.

## 22. Phase 6B.5 Implementation Readiness

**NOT READY FOR PHASE 6B.5 IMPLEMENTATION.** A later developer cannot implement schema-driven rendering, validation, valid submission, and evaluation/acceptance without selecting answer types, schema shape, validation rules, and unresolved lifecycle/evaluation behavior. Exact revision preservation is structurally supported by the revision foreign key and approved versioning model, but it does not resolve the missing contract. Owner decisions below are required before implementation can proceed without inventing behavior.

## 23. Traceability to Existing MaliLab Architecture

| Existing source | Relevant constraint captured here |
|---|---|
| `PROJECT.md` | Product/architecture/model sequence; unresolved requirements remain TODO/TO-BE-DEFINED; no implementation before phase gate. |
| `docs/implementation/PHASE_6B_PLAN.md` | Explicit attempt, response save, explicit submission and received-versus-accepted distinction; Practice response schema contract left unresolved. |
| `docs/implementation/PHYSICAL_DATA_MODEL.md`; `MODEL_SPECIFICATIONS.md`; `FIELD_SPECIFICATIONS.md`; `CONSTRAINT_SPECIFICATIONS.md` | PracticeAttempt/Response, response_schema and RequirementEvidence fields/constraints exist; schema, save/submit details and several lifecycle rules remain unspecified. |
| `docs/implementation/PHASE_5B_DECISION_BRIEF.md`; `DECISIONS.md` DB-019 | One accepted attempt satisfies one requirement; evidence and reassessment preserve history. |
| `docs/implementation/TRACEABILITY_MATRIX.md` | Practice and evidence model/service/test traceability. |
| `docs/product/PRACTICE.md`; `docs/database/DOMAIN_MODEL.md`; `ENTITY_CATALOG.md`; `RELATIONSHIPS.md`; `FIELDS.md`; `DATA_FLOWS.md`; `VERSIONING.md` | Practice is exploratory, submitted work is evidence, exact revision references, accepted evidence boundary, no assumed correctness score, and unresolved completion/evaluation policies. |
| Current `practice/models.py`, `services.py`, `tests.py`; `learning/models.py`, `services.py` | Current field/state/ownership/immutability behavior and test limits described in the baseline. |

## 24. Decision Summary

- **APPROVED:** Exact revision pinning; private owner-scoped attempts/responses; explicit submission distinct from acceptance; accepted Requirement Evidence satisfies one exact requirement; one accepted attempt satisfies one requirement initially; no scoring system is authorized.
- **TO-BE-DEFINED:** Initial answer types, exact schema, validation, evaluator/criteria, acceptance semantics, feedback, retry/correction, draft and abandonment semantics, legacy data handling.
- **Implementation readiness:** **NOT READY FOR PHASE 6B.5 IMPLEMENTATION**.

# OWNER DECISIONS REQUIRED

1. **Initial answer types and schema contract.** Options: approve a deliberately narrow subset from the proposed text/choice candidates; choose a different bounded set with precise rules; or defer all Practice answer types pending further product specification. **Recommended:** approve only types tied to defined learning activities, with a narrow versioned schema rather than arbitrary JSON Schema. **Consequence:** rendering and validation cannot begin until the type set and schema keys/semantics are exact.
2. **Submission and validation rules.** Options: define required/type/unknown/null/empty/constraint behavior now; or defer submission implementation. **Recommended:** require server-side validation of all declared answers and reject undeclared fields, with explicit partial-draft semantics. **Consequence:** determines which responses may be submitted and what historical payload means.
3. **Evaluation and acceptance authority.** Options: explicit human review; a separately specified deterministic rule for selected types; or defer acceptance/evidence until criteria are approved. **Recommended:** keep acceptance explicit and evaluator-authorized; approve no automatic grading absent defined educational criteria. **Consequence:** determines whether a submitted attempt can produce accepted Requirement Evidence and what provenance is required.
4. **Attempt lifecycle and correction.** Options: define draft/abandon/retry/reopen/correction policy now; or keep those operations out of initial implementation until decided. **Recommended:** preserve submitted attempts as immutable history and make any retry a distinct attempt, subject to an explicit policy. **Consequence:** affects attempt state transitions, learner expectations and evidence selection.
5. **Evaluation record and feedback.** Options: use requirement-level evidence as the sole persisted decision; add a separate evaluation concept in a later approved physical specification; or defer feedback/provenance. **Recommended:** decide evaluator identity, result timestamp and rationale needs before choosing persistence representation. **Consequence:** current model may not fully record evaluation provenance or non-requirement outcomes.

PHASE 6B.5A PLANNING COMPLETE — READY FOR OWNER REVIEW
