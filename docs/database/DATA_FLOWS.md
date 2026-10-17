# Data Flow Scenarios

These scenarios describe conceptual records and revision effects, not endpoints or transaction implementation. Editorial content remains distinct from user-owned work. Progress consumes durable facts; it is not an upstream dependency of My Plan.

## A. User discovers a Playbook and starts a Module

1. Search/discovery reads the derived projection for an eligible published Playbook Revision.
2. User opens that exact Playbook Revision and selects one active Playbook–Module Recommendation.
3. System creates the owner-scoped Learning Journey Context and appends ordered Journey Steps for the exact Playbook Revision and, as followed, the exact Playbook–Module Recommendation and target Module Revision. Each step stores type, target reference, observed state, occurrence/recording time, and only necessary context metadata.
4. Module opens at that exact revision; current editorial publication may later change without altering this journey. No Module copy is created. Later Lesson, Practice, Calculation Result, and Plan Revision activity appends further steps referencing the exact underlying records.

**Remains:** editorial revisions and recommendation are retained; journey belongs to user. If user/account policy disallows tracking anonymous discovery, no context is persisted until authentication/consent policy permits it (TODO).

## B. User reads a Lesson and creates a Note

1. Reader resolves the Lesson Revision included by the chosen Module Revision.
2. Note is created with user owner, kind/text, exact Lesson Revision, optional block ID/selection anchor, and journey context; a Journey Step may record the Lesson Revision and note/annotation event where relevant.
3. Note is private and does not enter public search. If the Lesson is revised, the note remains attached to its original revision/block; UI may indicate newer content but cannot retarget silently.

**Remains:** old revision and anchor persist. User editing/deletion/retention follows unresolved account policy.

## C. User completes Practice using a calculator

1. Practice Activity Revision is presented; user begins/submits a Practice Attempt pinned to it and linked to the same-owner journey where applicable. The journey receives a step for the exact Practice revision/attempt and observed state.
2. Responses are validated against the prompt schema from that revision and saved under the same owner.
3. If no calculator is used, no Calculation Result is required. If one or more calculators are used, the server resolves each active Formula Version and validates inputs/assumptions; calculation logic runs in the calculation domain, outside templates/client/database models.
4. Each explicitly saved Calculation Result retains Formula Version, inputs, assumptions, output, units/currency and precision/rounding methodology where applicable, timestamp, source/methodology and warnings. It optionally links to the same-owner Practice Attempt. An attempt may link to zero, one, or multiple results; a result remains independently identifiable and immutable.
5. For a Practice requirement, create Requirement Evidence identifying the exact Module Revision, requirement, Practice Revision and submitted Attempt, learner, evidence state and relevant timestamps. Each pair is explicit. A Module Completion later cites the accepted evidence for the required item; policy on whether one attempt can satisfy multiple requirements remains open.

**Remains:** Attempt, Requirement Evidence and saved results preserve historical context. No correctness score is assumed. Progress consumes accepted evidence; My Plan does not depend on Progress.

## D. User creates My Plan from learning

1. Authenticated user creates a My Plan identity and first Plan Revision.
2. Snapshot contains user-defined target, timeframe and assumptions, possible path, optional Practice Attempt and Calculation Result references, Learning Journey Context, and relevant exact Playbook/Module/Lesson revisions. The journey appends a step referencing this exact Plan Revision.
3. Plan write succeeds independently of Progress; it emits evidence/fact that Progress may consume.

**Remains:** first revision immutable; My Plan points to current revision. One-versus-many plan policy remains open.

## E. User edits the Plan six months later

1. System reads current Plan Revision and user submits changes.
2. Create new immutable Plan Revision with predecessor, changed target/assumptions/path, current learning context and any new result references; append a Journey Step referencing the new revision when the plan is part of that journey.
3. Old Calculation Results remain tied to original Formula Versions and values. Recalculation creates a new Calculation Result. Current plan pointer advances; old revision remains comparable.

**Remains:** all snapshots retained subject to eventual user deletion/retention policy. No previous result is silently rewritten.

## F. A Lesson is revised after completion

1. Editor creates a new Lesson Revision and passes human review/publication.
2. Current publication pointer changes and search projection is rebuilt for the new revision.
3. Existing Lesson Completion, Note anchors, Practice Attempts and journeys keep references to old Lesson/Practice revisions.
4. Studying the new revision may create new Lesson Completion evidence; whether it supersedes/carries prior completion is unresolved.

**Remains:** old revision/provenance accessible for history. Old notes do not jump to new blocks.

## G. A Formula Version is retired and replaced

1. New Formula Version is authored and transitions Draft→Tested→Reviewed→Approved→Active only after evidence exists and explicit activation is recorded.
2. Active pointer changes; former version transitions to Retired.
3. New calculation uses new version. Saved old results continue to reference and reproduce the old version and input snapshot.

**Remains:** formula approval/test/source history and all saved results. No automatic recalculation occurs.

## H. A Module's completion requirements change

1. Editor creates a new Module Revision with a new ordered learning requirement set and exact Lesson/Practice revision targets.
2. Review/publication makes the new revision current.
3. Prior Module Completion remains tied to previous Module Revision and retains its immutable requirement/evidence explanation. Requirement Evidence itself remains pinned to that exact requirement and attempt.
4. Evaluation under the new curriculum creates a distinct completion decision. Carry-forward/recognition rules require product decision.

**Remains:** old and new requirement sets; existing progress is never recalculated in place.

## I. A user earns an achievement

1. Progress evaluates exact Module Completion evidence and a Plan Revision that constitutes an attempt under approved criteria.
2. If eligibility rule (still TODO) is met, create User Achievement referencing exact Achievement Definition Revision, Module Completion, Plan Revision, and award time.
3. Award is not a financial outcome claim; it records learning evidence.

**Remains:** evidence and definition revision explain award. Deduplication/revocation policy remains open.

## J. A user deletes their account

1. Deletion request/status is recorded according to a policy not yet selected.
2. Enumerate attempts/responses, journeys, calculations, plans/revisions, notes, progress/completions and achievements owned by the account; remove or anonymize according to approved per-entity rules.
3. Resolve dependencies: awards/progress cannot retain an identifiable private plan reference if that plan is removed; editorial records/revisions must remain untouched.
4. Handle authentication identity, operational audit references, backups and deletion propagation under explicit policy.

**Remains:** exact hard-delete/anonymize/retain outcome, timing and backup expiry are TODO/TO-BE-DEFINED. No deletion behavior is implemented in this specification.
