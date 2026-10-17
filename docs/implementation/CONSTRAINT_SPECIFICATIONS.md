# Constraint Specifications

`CHECK` and unique constraints below are logical requirements to express in the eventual Django/PostgreSQL migration where supported. Cross-row/cross-table rules require domain services and transaction tests; a SQL CHECK cannot safely express them.

| Constraint | Physical expression | Enforcement / rationale |
|---|---|---|
| Unique identity slug | Unique normalized slug within model/type | DB unique; public resolution |
| Account email identity | Unique normalized email for the custom account identity; email verification state/time internally consistent | DB unique plus service validation; email must be verified before personal-feature authorization |
| Positive revision sequence | CHECK `revision_number > 0`; unique `(identity, revision_number)` | DB |
| One current published revision | Nullable FK on stable identity plus service validates same parent/state; optionally partial unique only if separate publication table used | Transactional service + FK |
| Revision immutability | No ordinary update/delete path for published revision | Service permissions + tests; DB trigger not proposed initially |
| Requirement target kind | Exactly one of LessonRevision/PracticeRevision FK set and matching kind | DB CHECK for null pattern; service validates target matches kind and expected active state |
| Required/optional/recommended set | Controlled enum values; item target type has matching allowed values | DB choices/check plus validation |
| Ordered requirements/recommendations/blocks | Unique `(revision, position)` and nonnegative/positive check | DB unique/check |
| Unique target membership | Unique `(module_revision, target_kind, target_revision)`; recommendation unique exact module target per Playbook revision | DB unique |
| Lesson block key/order | Unique within revision; block schema/type allow-list | JSON payload validator; DB unique if normalized child rows chosen |
| Same owner on private relationships | owner equals owner of journey/attempt/plan/result/evidence | Mandatory service validation inside transaction; DB composite FK only if deliberately added later; cross-user test |
| Public vs personal access | Anonymous principal can read only public published content; personal persistence requires authenticated and email-verified account | Route/service access policy and tests for all persistent personal features |
| Journey ordered append-only | Unique `(journey, sequence)`, sequence > 0; target association is resolvable and owner compatible | DB sequence check/unique + service-controlled append only |
| Journey target registry | Unique target registry per concrete target; target kind matches association subtype; step has exactly one target registry FK | FK/unique; subtype presence invariant is service enforced and audited |
| Requirement Evidence exactness | Unique `(attempt, requirement)`; module revision owns requirement; PracticeRevision matches requirement and attempt | DB pair unique + service cross-row validation |
| One accepted attempt satisfies one requirement | At most one accepted RequirementEvidence per PracticeAttempt in the initial policy; a requirement is evaluated against its exact ModuleRevision | Conditional unique constraint or transactional domain check; rejected/ superseded decisions remain history; no automatic multi-credit |
| Reassessment history | A corrected/reassessed evidence decision references its predecessor and never overwrites the prior decision or completion snapshot | Immutable evidence records plus supersession relationship; service transaction |
| Attempt-to-calculation | Result has optional attempt FK; many results per attempt; owner matches | FK + service owner check; no required result |
| Module Completion explanation | Snapshot has all required items with status and exact accepted evidence for complete state | Service evaluates in transaction; immutable JSONB snapshot; tests |
| Plan chain | Unique `(plan, revision_number)`; predecessor same plan and lower number; predecessor not self; no cycles | DB local checks + service chain validation |
| Formula state | Allowed ordered transitions; approval evidence gate before Active | Service transaction; immutable Approval events; choices do not alone guarantee sequence |
| One active formula | Partial unique `(calculator_definition)` where lifecycle Active | PostgreSQL partial unique constraint; activation transaction changes old/new atomically |
| Formula approval evidence | Activation record requires reviewer, timestamp, test evidence, source, version id and approval action | Service lifecycle gate; required fields/non-null by action-specific validation |
| Formula second-person approval | Formula author and approving/activating actor differ | Transactional permission check and actor FKs; reject same person |
| Calculation snapshot | Formula FK exact; result immutable; decimal values canonical strings; units and method snapshot consistent | Service validation + tests |
| Plan current pointer | Current revision belongs to plan and owner; pointer changes only to newly saved revision | Service transaction; DB FK |
| Achievement evidence | Award refs exact definition revision, completion and plan revision of same owner | Service validation; duplicate/revocation uniqueness remains future criteria policy, so no unique award rule |
| Source provenance | Snapshot references exact revision and preserves source values at review time | FK + immutable snapshot; catalog edits never cascade into snapshot |
| Editorial publish | Publication event only for approved exact revision; reviewer/publication actor authorized | Service authorization + transaction; actor/action FK |
| Financial-content separation | Approver differs from author; edit after approval requires new review/approval | Service workflow and immutable events; approval is revision-pinned |
| Search eligibility | Only current eligible published editorial revision; no user entities | Projection rebuild rules + privacy tests |
| Media references | Asset key/version immutable; block/revision refs PROTECT referenced asset | FK + service; referenced asset cannot be hard deleted |
| Note anchor | Exact LessonRevision, stable block ID and selected quote; optional offsets are hints | FK to revision + service block validation; quote/block authoritative; offsets never move the anchor after text mismatch |

### Unresolved cardinality encoded flexibly

- Plans: `UserAccount 1 → 0..N MyPlan`; do not add one-plan or one-active unique constraint until product decision.
- Requirement evidence: schema remains capable of multiple explicit associations, but initial accepted semantics are one PracticeAttempt to one ModuleRequirement. No automatic credit based on reused PracticeRevision. Future multi-requirement support requires explicit per-requirement evidence decisions.
- Practice calculations: `PracticeAttempt 0..N CalculationResult`; a standalone saved result may have no attempt.
- Achievements: no duplicate-award uniqueness until award/reattempt/revocation policy is decided.
