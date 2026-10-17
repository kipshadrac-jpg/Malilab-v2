# Phase 6B.5A — Owner Decision Addendum

**Document status:** Owner decisions recorded; supplements the Phase 6B.5A planning artifact. This is a documentation-only decision record and does not authorize implementation.

## 1. Purpose and authority

This addendum records the owner's decisions for the five decision areas in the original planning document and the additional contract details required to specify them. Status labels are used as follows:

- **OWNER-APPROVED** — explicitly approved by this prompt.
- **EXISTING APPROVED** — already established in approved MaliLab architecture.
- **DEFERRED** — intentionally excluded from the initial contract.
- **IMPLEMENTATION PREREQUISITE** — must be addressed before the relevant implementation can safely proceed.
- **CONFLICT** — conflicts with existing approved material and requires owner resolution.

The task authorizes recording decisions only. It does not authorize Practice submission or evaluation implementation, a physical-model change, or any database operation.

## 2. Relationship to the original planning document

This document supplements `docs/implementation/PHASE_6B_5A_PRACTICE_RESPONSE_SCHEMA_AND_EVALUATION_CONTRACT.md`; that planning document is not modified. It resolves its open questions about answer types and schema, validation, lifecycle, acceptance/evaluation, scoring/feedback, retries, and readiness.

The original planning document's statuses such as **TO-BE-DEFINED** describe the state before this owner decision. Where this addendum explicitly decides an issue, this addendum is authoritative for the Practice contract. The broader approved architecture remains in force. Inspection found no conflict with existing approved architecture requiring the owner to resolve before recording these decisions. Existing `started`, `submitted`, and `abandoned` attempt states are preserved; this addendum does not assign new semantics to `abandoned`.

## 3. Approved answer types

The initial contract supports exactly these six types (**OWNER-APPROVED**):

1. `short_text` — one short free-text answer, stored as the original JSON string.
2. `long_text` — one longer explanatory, reflective, or descriptive answer, stored as the original JSON string.
3. `single_choice` — exactly one editorially defined option, stored by stable option identifier rather than display label.
4. `multiple_choice` — zero or more editorially defined options, stored as an array of stable option identifiers. Duplicate identifiers are invalid. Empty selection validity depends on requiredness and submission rules.
5. `integer` — a whole number stored as a JSON integer, never a floating-point value. Numeric bounds are declared explicitly when applicable; no arbitrary business bounds are imposed.
6. `decimal_amount` — a financial amount stored as a canonical decimal string, never a JSON floating-point number. Currency is explicit. KES is the initial default only when the question explicitly declares KES. Currency is not inferred from learner location, silently converted, or assumed for other answer types.

A separate `boolean` type is **DEFERRED**. Yes/no questions may use `single_choice` with two editorially defined options. Supporting any answer type permits response capture and structural validation only; it does not authorize grading or acceptance.

For `short_text` and `long_text`, the schema contract and implementation specification must define bounded maximum lengths. The product limit is intentionally not numeric in this decision phase. Exact per-type bounds and global resource limits are an **IMPLEMENTATION PREREQUISITE** before implementation; no arbitrary limits are to be introduced in code in this phase.

## 4. Exact response schema contract

The production contract is a narrow MaliLab-owned JSON object (**OWNER-APPROVED**), not arbitrary JSON Schema. The simplest deterministic representation compatible with the existing `PracticeActivityRevision.response_schema` JSON field is:

- Root keys, exactly: `schema_version`, `questions`.
- `schema_version`: JSON integer with the exact value `1` for this initial contract.
- `questions`: ordered JSON array. Array order is the question order; there is no separate position field.
- Each question has required keys `id`, `type`, `label`, `required`; it may have `constraints` only where allowed below and `options` only for choice types. No other question keys are permitted.
- `id`: stable question identifier matching `^[a-z][a-z0-9_]{0,63}$`, unique within the revision.
- `type`: exactly one of the six initial answer type identifiers in section 3.
- `label`: non-empty editorial display string. It describes the question and is not a learner answer value.
- `required`: JSON boolean.
- `options`: for `single_choice` and `multiple_choice`, a non-empty array of objects with exactly `id` and `label`. Option `id` follows the same identifier grammar, is unique within that question, and is separate from the non-empty editorial display `label`. `options` is forbidden for every other type.
- `constraints`: optional object whose keys are restricted by answer type. No defaults are permitted in the initial contract. Unknown keys at every level are rejected.

The exact allowed `constraints` vocabulary is:

| Type | Allowed constraint keys and representation |
|---|---|
| `short_text`, `long_text` | `max_length`: positive JSON integer. It must be present in the approved implementation specification before the type is implemented. |
| `single_choice`, `multiple_choice` | No constraint keys. `constraints` is omitted. |
| `integer` | `minimum`, `maximum`: optional JSON integers; either or both may be declared. If both are present, minimum must not exceed maximum. |
| `decimal_amount` | `currency`: required ISO 4217 code string, initially only `KES`; `minimum`, `maximum`: optional canonical decimal strings, never JSON numbers. If both are present, minimum must not exceed maximum. Currency is mandatory and explicit for this type. |

The schema does not contain answer values, defaults, correct-answer keys, executable behavior, renderer instructions, or arbitrary HTML, JavaScript, CSS, templates, or prose interpreted as instructions. Choice labels and question labels are editorial content; submitted values are stable identifiers or the type-specific value. A malformed or unsupported schema fails closed.

The following is an illustrative example of the owner-approved contract, not existing production data:

```json
{
  "schema_version": 1,
  "questions": [
    {
      "id": "main_observation",
      "type": "long_text",
      "label": "What did you observe?",
      "required": true,
      "constraints": {
        "max_length": 4000
      }
    },
    {
      "id": "next_step",
      "type": "single_choice",
      "label": "Which next step would you choose?",
      "required": true,
      "options": [
        {"id": "review_records", "label": "Review the records"},
        {"id": "ask_for_advice", "label": "Ask for advice"}
      ]
    },
    {
      "id": "estimated_amount",
      "type": "decimal_amount",
      "label": "Estimated amount in Kenyan shillings",
      "required": false,
      "constraints": {
        "currency": "KES",
        "minimum": "0.00"
      }
    }
  ]
}
```

The example uses only declared keys, an ordered question array, the exact version representation, allowed types, and type-specific constraints. Its numeric text bound is illustrative only, not an approved product limit. The implementation specification must set actual bounded limits before implementation.

## 5. Response validation rules

Validation and evaluation are separate domain concepts (**OWNER-APPROVED**): schema validation determines whether answers conform to the exact pinned revision's contract; evaluation determines whether a valid response meets educational requirements.

All answer validation is server-side. The server resolves the exact pinned `PracticeActivityRevision`. Only declared question identifiers may be supplied; unknown identifiers are rejected. Every supplied value must have its declared JSON type. Choice identifiers must be options declared by that pinned revision. Multiple-choice arrays cannot contain duplicate identifiers. `null` is not a valid answer. A required answer cannot be missing at explicit submission; an optional answer may be omitted. Required text containing only whitespace is invalid.

Optional unanswered values may be omitted. Optional empty strings and whitespace-only text strings are valid submitted text values and are preserved exactly as submitted; the server does not silently trim or otherwise transform learner text. Empty selection for optional `multiple_choice` may be represented as an empty array; for a required question it does not meet requiredness. A single-choice value must always identify exactly one declared option.

Constraints apply only if explicitly supported for that type and declared. Invalid input never becomes a submitted attempt. Malformed or unsupported schemas fail closed and are never treated as valid by default. Draft saves may be incomplete; completeness is enforced at explicit submission. Structural validity does not establish educational correctness or acceptance.

The exact per-type enforcement details, parser behavior, and global resource limits remain an **IMPLEMENTATION PREREQUISITE** for the implementation specification. Invalid submissions may return validation errors during interaction; persistence of validation-error history is **DEFERRED**, unless an existing approved architecture requirement is identified before implementation.

## 6. Response storage

Preserve the existing model unless a later approved physical-data-model review establishes a genuine gap (**OWNER-APPROVED**). The exact `PracticeActivityRevision` is authoritative for interpreting every response; a saved answer maps to a stable question identifier in that revision. Existing physical fields provide `PracticeResponse.prompt_key`, JSON `value`, and optional `unit`; response storage must preserve original learner values and must not normalize text in place. If normalized interpretations are needed, they must not destroy the original value.

For `decimal_amount`, persist a canonical decimal string in JSON and preserve explicit currency. The current response `unit` field is a potential physical mapping for currency, but its semantics and adequacy must be verified against the exact contract before implementation. Whether a required unit or currency can be represented unambiguously is an **IMPLEMENTATION PREREQUISITE**. If it cannot, record the exact gap for an approved physical-data-model review; do not modify models here.

Validation errors can be returned without storing their history. Persisting such history is **DEFERRED**, unless existing approved architecture explicitly requires it. If the storage model cannot represent the approved contract faithfully, report the precise gap before implementation; do not change the model in this task.

## 7. Attempt lifecycle and submission

Preserve the existing attempt states (`started`, `submitted`, `abandoned`) (**EXISTING APPROVED** physical baseline). An attempt may be in progress while the learner supplies and saves responses, and an in-progress attempt may be incomplete. Saving a response or opening a page is not submission. Submission is an explicit learner action (**OWNER-APPROVED**).

On submission, the server validates the complete submitted response against the exact pinned revision. Invalid submissions are rejected. Only after successful validation does the system record the submission timestamp and change the attempt to `submitted`. Learner edits to submitted responses are prevented; a submitted attempt is not silently reopened or overwritten.

Retry limits, deletion of unfinished attempts, abandonment semantics, and privileged reopening are **DEFERRED**. No new state is authorized. If retry is later approved, it uses a distinct attempt and preserves the earlier one; a submitted response is never mutated to simulate retry.

## 8. Acceptance and evaluation

**SUBMITTED** means the system received a response that passed structural validation and recorded the explicit submission. **ACCEPTED** means an authorized educational evaluation determined the submission satisfies the relevant activity's approved educational criteria. A valid response and a submitted response are not automatically accepted. Saving is not submission. Submission confirmation must not claim correctness or Module Requirement satisfaction.

For the initial contract, automatic acceptance and automatic grading are not permitted (**OWNER-APPROVED**). Acceptance requires an explicit decision by an authorized human evaluator. Evaluation is based on the exact submitted attempt and exact Practice revision and does not mutate the submitted response. The evaluator role and authorization checks follow existing staff access and separation-of-duties policies. If those policies do not define the exact evaluator permission needed, that permission is an **IMPLEMENTATION PREREQUISITE**; no new staff role is invented here.

The evaluation decision conceptually preserves the evaluated attempt, decision, evaluator identity, evaluation timestamp, and optional rationale or feedback. Existing `RequirementEvidence` may not preserve all provenance, particularly when a Practice activity is not a Module Requirement. A separate evaluation record is an **OWNER-APPROVED domain requirement for future evaluation if existing models cannot faithfully preserve this provenance**. Its physical design must be specified and approved before evaluation implementation. No model or migration is created here. Human evaluation, evaluation UI, reviewer feedback UI, and evaluation persistence are outside Phase 6B.5 submission implementation.

## 9. Scoring and feedback

Scoring is **DEFERRED** and out of scope for the initial Practice contract. No points, percentages, grades, weighted questions, pass marks, or implied grading scale are authorized. Future scoring requires a separate explicit product and educational-policy decision.

These terms remain distinct (**OWNER-APPROVED**):

- **Submission confirmation:** response was successfully submitted.
- **Validation error:** response violates the approved schema contract.
- **Evaluation result:** an authorized evaluator made a decision about submitted work.
- **Acceptance:** the positive educational decision satisfies relevant approved acceptance criteria.
- **Reviewer feedback:** optional explanation accompanying an evaluation decision; it does not imply a score.

Detailed reviewer feedback requirements and persistence are **DEFERRED** until evaluation is specified.

## 10. Retry and correction

Retry limits, correction rules, unfinished-attempt deletion, abandonment semantics, and privileged reopening are **DEFERRED**. No retry behavior or additional state is invented. If later approved, a retry must be a distinct attempt, and earlier submitted responses remain immutable. Existing architecture's history-preserving correction/reassessment principle remains in force for evidence decisions (**EXISTING APPROVED**).

## 11. Requirement satisfaction boundary

The existing rule is preserved (**EXISTING APPROVED**): **ONE ACCEPTED PRACTICE ATTEMPT SATISFIES ONE MODULE REQUIREMENT INITIALLY.** No inferred multi-credit is permitted. Only accepted evidence for the exact required item can satisfy that requirement. Phase 6B.5 submission implementation does not create `RequirementEvidence`, implement Module completion, or implement Phase 6B.6.

The future conceptual flow is:

`PracticeActivityRevision → PracticeAttempt → PracticeResponse → explicit human evaluation → accepted decision → RequirementEvidence for one exact Module Requirement → requirement satisfaction`

A Practice submission may exist without satisfying a Module Requirement; not every Practice activity is necessarily a requirement.

## 12. Versioning and historical integrity

Exact revision pinning and published revision immutability are **EXISTING APPROVED**. The required interpretation chain remains:

`PracticeActivityRevision → response_schema → PracticeAttempt → PracticeResponse → evaluation`

Always interpret an attempt against its pinned revision, never the current revision. A later revision cannot reinterpret a historical attempt. Do not add schema snapshots or database fields without an approved physical-model decision. Before implementation, if integrity of the pinned revision or schema cannot be proven, report the precise gap; this is an **IMPLEMENTATION PREREQUISITE**.

## 13. Security and mobile constraints

The later implementation must resolve learner ownership from authenticated server-side identity and enforce ownership on attempts and child responses; cross-account access is denied. Payloads are validated server-side; unknown fields and unsupported types are rejected; malformed schemas fail closed. Schema-supplied behavior is never executed, and published revision integrity is preserved (**OWNER-APPROVED**).

Controls must be accessible, mobile-first, and deterministically rendered. A generic arbitrary form-builder is not authorized. UI design and implementation are outside this phase. Existing ownership architecture remains the authority for account authorization (**EXISTING APPROVED**).

## 14. Existing data compatibility

The known test fixture `{"type":"object"}` is not a production-approved Practice schema and must not be automatically approved as valid content (**IMPLEMENTATION PREREQUISITE**). The original planning inspection did not query PostgreSQL; it does not establish whether production data is absent.

Before schema enforcement implementation, inspect the actual database using the established safe environment procedure and determine whether existing non-test Practice data needs compatibility handling. Do not weaken database security, alter the live database, create seed data, or perform a migration as part of this decision task.

## 15. Remaining implementation prerequisites

Before submission implementation proceeds, the implementation specification must address:

1. Safe actual-database inspection and compatibility handling for existing non-test Practice schemas/data.
2. A physical-model check that `PracticeResponse` can preserve stable question identifiers, canonical amount strings, and explicit currency or any required unit without ambiguity; any gap requires a separately approved physical-model review.
3. Proof that the exact pinned revision and its schema remain available and integrity-protected for historical attempts.
4. Numeric text bounds and all exact per-type constraint enforcement, parser behavior, plus global request/response resource limits. These must be explicitly specified before coding and must not be arbitrary business limits.
5. The empty/whitespace, optional, required, and draft-versus-submit behaviors in this contract translated to consistent service-level rules and learner-visible validation outcomes.

Before evaluation implementation, additionally specify evaluator authorization under existing staff/separation-of-duties policy and approve a physical design for a separate evaluation record if current models cannot preserve the required provenance. These are not blockers to submission-only implementation because evaluation is outside its scope.

No conflict with approved architecture was identified during this review. If implementation review later discovers one, record it as **CONFLICT** and stop for owner resolution rather than silently changing an approved source.

## 16. Phase 6B.5 submission readiness

**Phase 6B.5 submission implementation: READY, subject to the existing database compatibility and physical-model checks and the implementation-specification prerequisites in section 15.** The owner decisions specify deterministic response rendering inputs, answer representation, server-side validation, incomplete draft behavior, attempt creation and response saving, explicit validated submission, and exact revision preservation. They do not authorize evaluation, acceptance, Requirement Evidence creation, scoring, or Module completion.

This is a readiness assessment, not an implementation authorization. If the actual database or physical-model check finds a gap that affects faithful submission storage or validation, implementation is not ready until that exact gap is resolved through the approved process. The evaluation capability is **not declared ready** for implementation.

## 17. Decision traceability

| Decision area | Status | Recorded outcome |
|---|---|---|
| Initial answer types | OWNER-APPROVED | Exactly six types in section 3; boolean deferred. |
| Schema contract | OWNER-APPROVED | Versioned MaliLab JSON contract, exact keys and grammar in section 4. |
| Validation | OWNER-APPROVED | Server-side structural rules separate from educational evaluation. |
| Response storage | OWNER-APPROVED | Preserve model and learner values; confirm unit/currency mapping before implementation. |
| Attempt lifecycle/submission | OWNER-APPROVED | Preserve states; incomplete drafts; explicit validated submission and submitted immutability. |
| Acceptance/evaluation | OWNER-APPROVED | Human decision only, provenance required; evaluation outside Phase 6B.5. |
| Scoring | DEFERRED | No scoring or implied scale in initial contract. |
| Retry/correction | DEFERRED | No limits, reopening, or additional states specified. |
| Requirement satisfaction | EXISTING APPROVED | One accepted attempt satisfies one exact requirement initially. |
| Revision/history | EXISTING APPROVED | Exact revision pinning and immutable published revisions. |
| Existing data | IMPLEMENTATION PREREQUISITE | Safe database inspection and compatibility determination required. |
| Evaluator role / evaluation storage | IMPLEMENTATION PREREQUISITE | Resolve existing permission and approve separate record physical design if needed before evaluation. |
| Conflicts | No CONFLICT found | Escalate and stop if a genuine conflict appears during later implementation review. |

## 18. Final owner decision summary

The owner approves a six-type, explicitly versioned, narrow Practice response contract with server-side structural validation and explicit submission against an exact pinned revision. Submission is distinct from educational evaluation and acceptance. Human evaluation is the only initial acceptance path; scoring is deferred. Existing ownership, immutable-history, and one accepted attempt to one requirement boundaries remain in force. Submission implementation is ready for implementation-specification review subject to the stated compatibility and physical-model prerequisites; this addendum itself authorizes no implementation.

PHASE 6B.5A OWNER DECISIONS RECORDED — READY FOR IMPLEMENTATION SPECIFICATION REVIEW
