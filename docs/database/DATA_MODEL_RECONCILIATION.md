# Data Model Reconciliation

## 1. Original Findings

The Phase 4 audit identified two HIGH-severity gaps:

1. Learning Journey Context held only scalar later-content references, so it could not preserve an ordered multi-step learner history.
2. Practice Attempt had no explicit logical relationship to saved Calculation Results or to the exact Module Learning Requirement it was used to satisfy.

This Phase 4B update changes only those related areas and their necessary field, constraint, lifecycle, privacy, versioning, and flow documentation. Other product and physical-design questions remain open. The original audit is retained as an audit record; its status notes now point to this reconciliation.

## 2. Learning Journey Resolution

The model distinguishes three things:

- **Learning Journey Context:** one learner-owned journey identity/header, owner, creation time, and optional compact initial scenario/assumption context.
- **Journey Step:** one ordered, append-only observation within that journey.
- **Referenced record:** the underlying editorial revision or user-owned record. The journey step points to it; it does not copy its body or become its owner.

Each Journey Step specifies:

- journey and same learner owner;
- positive sequence unique within the journey;
- extensible, allow-listed `step_type`;
- `target_kind` and reference to the exact target, with editorial targets pinned to a revision;
- observed `step_state`, such as entered, completed, skipped, or saved/relevant;
- occurrence and recording timestamps; and
- optional bounded context metadata.

A path may omit or repeat any type. A representative path can be recorded as steps referencing a Playbook Revision, followed recommendation, Module Revision, Lesson Revision, Practice Activity Revision/Attempt, Calculation Result, and Plan Revision. Steps preserve order and observed state. A state change is another step rather than a mutation of the earlier observation. New step kinds use the typed target boundary; they do not require a new field for every step kind. The exact physical integrity mechanism for typed targets is reserved for implementation, but the logical target allow-list and existence/owner/revision validation are required.

The Playbook entry and recommendation are journey steps, not duplicate copies of their editorial records. A journey may have no Playbook origin; if it does, there is one origin step, and a followed recommendation must belong to that exact Playbook Revision and point to the Module Revision represented in the subsequent path.

## 3. Practice Requirement Evidence Resolution

`Requirement Evidence` is an addressable user-scoped derived association. Each record identifies:

- the learner;
- exact Module Revision;
- exact Module Learning Requirement within that revision;
- exact Practice Activity Revision targeted by the requirement;
- exact submitted Practice Attempt pinned to that same Practice Revision;
- evidence state (Accepted or Not Accepted); and
- recorded/evaluated timestamps plus optional bounded evaluation context.

The Module Requirement remains editorial-owned; the Attempt remains user-owned; Requirement Evidence does not transfer ownership. All private references must belong to the same learner. The requirement target revision must exactly match the Attempt revision. A requirement can have evidence from multiple attempts; each attempt/requirement pair has one evidence decision. A Module Completion snapshot cites the accepted evidence that satisfies each required item, or records why it remains outstanding. Thus the system can answer both “which exact requirement did this attempt satisfy?” and “which attempt/evidence satisfied this requirement?” without consulting mutable current Module or Practice pointers.

The relationship permits an Attempt to be associated with more than one Requirement Evidence record. It does not assert that the evidence is acceptable for all such requirements. Whether one accepted attempt may satisfy multiple requirements is a curriculum/completion policy that remains open. The model preserves each specific association and the evidence state, leaving that policy explicit.

Progress consumes Requirement Evidence, Lesson Completion, Plan Revision and other learning facts. Module Completion is an explainable downstream evaluation. My Plan creates and revises its records without requiring Progress.

## 4. Practice Calculation Resolution

A Practice Attempt may use no calculator, one calculator, or several. A saved Calculation Result has an optional same-owner Practice Attempt reference; consequently one Attempt can reference zero or many saved results and each result is linked to at most one Attempt. A standalone result has no Attempt link. A saved result may also be referenced by a Plan Revision and/or Journey Step without copying it.

The Attempt-to-result relationship is contextual only. It does not make the Attempt own the result and does not require a result for attempt completion. Each Calculation Result remains immutable and preserves its exact Formula Version, inputs, assumptions, outputs, units/currency and precision/rounding policy where applicable, calculation timestamp, source/methodology, and warnings. Attaching a saved historical result never recalculates it using the current formula. Same-owner checks apply to the Attempt and result.

## 5. Historical Integrity

| Event | Historical reference/state retained | Current content can rewrite history? |
|---|---|---|
| Learner follows a Playbook recommendation | Ordered steps point to exact Playbook Revision, recommendation and Module Revision | No; revisions and steps are immutable references. |
| Learner enters later learning activities | New Journey Steps reference exact Lesson/Practice revisions, Attempt, result or plan revision | No; each step records its target and observed state at that point. |
| Practice definition changes | Attempt pins exact Practice Activity Revision; Requirement Evidence pins that revision and exact requirement | No; no “latest Practice” lookup is used. |
| Module requirement changes | New Module Revision and requirement set; old Requirement Evidence and Module Completion stay pinned to old revision | No; new evaluation is separate. |
| Attempt uses multiple calculations | Attempt links each explicitly saved Calculation Result; each result retains Formula Version and snapshots | No; formula retirement/replacement does not mutate saved results. |
| Plan changes after learning | Plan Revision predecessor chain and optional journey steps reference exact historical context | No; new revisions append without overwriting prior assumptions. |

Journey Step typed references and user-record retention are subject to the existing lifecycle policy. Account deletion/anonymization remains unresolved; its future policy must resolve references to deleted private records without deleting editorial history or leaking user data.

## 6. Cross-document Consistency

| Document | Reconciled definition |
|---|---|
| `DOMAIN_MODEL.md` | Adds Journey Step and Requirement Evidence as domain concepts; states revision-pinned ordered path, evidence rules and one-way Progress boundary. |
| `ENTITY_CATALOG.md` | Adds Journey Step and Requirement Evidence; updates logical count to 41 total (39 current/conditional + 2 future Dictionary concepts). |
| `RELATIONSHIPS.md` | Defines Journey Context→Steps→typed targets, Attempt→Requirement Evidence, Evidence→exact requirement/attempt, Attempt→optional Results, and Completion→evidence. |
| `FIELDS.md` | Specifies fields, ownership/privacy, cardinality and mutability for journey header/steps, Requirement Evidence, and optional Calculation Result Attempt link. |
| `CONSTRAINTS_AND_INDEXES.md` | Adds constraints for step order/target integrity, immutable journey observations, evidence exactness/uniqueness, completion snapshots and optional zero-to-many calculations; adds logical query indexes. |
| `VERSIONING.md` | Requires exact target revisions, append-only step observations, exact Attempt/requirement evidence, and formula-pinned calculation results. |
| `DATA_LIFECYCLE.md` | Covers journey-step/evidence deletion dependencies and same-owner links without cascading into referenced records. |
| `DATA_FLOWS.md` | Updates discovery, Practice/calculator, Plan creation/edit, and Module requirement change scenarios to create/reference ordered steps and exact evidence. |
| `OWNERSHIP_AND_PRIVACY.md` | Classifies Journey Step as user-owned and Requirement Evidence as derived/user-scoped; requires same-owner checks and excludes both from public search. |
| `IMPLEMENTATION_NOTES.md` | Gives later implementation translation rules and defers physical typed-reference strategy; preserves testing and policy TODOs. |
| `DATA_MODEL_AUDIT.md` | Retains the original audit record and marks R1/R2 as resolved; current readiness is reported here. |

No database schema, SQL, Django syntax, migration, code, or physical foreign-key strategy has been created. Existing unrelated product choices (including plan cardinality, achievement mechanics, account policy, retention, and scenario reuse) were not decided by this reconciliation.

## 7. Remaining Decisions

| Issue | Classification | Status and why |
|---|---|---|
| Whether one accepted Practice Attempt may satisfy multiple Module requirements | NON-BLOCKING | Relationship and exact evidence are representable; curriculum/completion policy determines acceptance. No automatic multi-satisfaction is inferred. |
| Physical representation and referential integrity strategy for typed Journey Step targets | NON-BLOCKING | Logical target kinds and validation rules are defined; physical implementation is explicitly deferred. |
| Evidence correction/reassessment and duplicate Lesson Completion semantics | NON-BLOCKING | Initial evidence pair is unique and states are explicit; correction/idempotency policy is needed before corresponding implementation, but does not prevent Phase 5 product/UI design. |
| One vs multiple My Plans | NON-BLOCKING | Existing one-to-many logical model remains valid without a unique-active constraint. |
| Note selection-anchor details and calculation currency/precision policy | NON-BLOCKING | Existing audit retains these as implementation prerequisites for Notes/calculators; they do not block the journey/evidence reconciliation or Phase 5 design. |
| Standalone Scenario entity versus embedded context snapshots | NON-BLOCKING | The current logical model embeds only relevant snapshots; decide whether scenarios need independent reuse/edit lifecycle before implementing that feature. |
| Media asset byte/version immutability | NON-BLOCKING | Retain versioned references if a changed asset could alter historical meaning; resolve before media persistence implementation. |
| Detailed Module completion and achievement thresholds, award deduplication/revocation | NON-BLOCKING | The product intentionally leaves detailed criteria open; conceptual evidence and completion explanation are represented without inventing thresholds. |
| Registration/authentication, staff roles and age policy | NON-BLOCKING | Preserve existing TODO status; resolve for account/editorial implementation without inferring legal requirements. |
| Account deletion, anonymization, retention and backup expiry | NON-BLOCKING for Phase 5; required before production data | Remains a production data gate under existing privacy/lifecycle documentation. |
| Full Dictionary, standalone reusable Scenario entity, advanced analytics/recommendations/payments/AI | FUTURE | Outside the initial product model unless a separately approved core requirement changes scope. |

## 8. Phase 5 Readiness

The learner journey now records multiple ordered historical steps without copying underlying content or learner records. Practice Attempts now have explicit, owner-checked relationships to saved Calculation Results and to Requirement Evidence for exact Module Revision requirements. Module Completion cites evidence against the exact requirement set; Progress remains downstream, and My Plan remains independent of Progress. Historical calculations retain their formula versions and snapshots.

The remaining questions are explicit policy or physical implementation matters and do not block the next Phase 5 product/UI design. This is a readiness assessment only; it does not authorize Phase 5 work or database implementation.

**READY FOR PHASE 5**
