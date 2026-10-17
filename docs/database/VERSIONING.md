# Versioning Strategy

Versioning is used to preserve meaning, not merely to record edits. This document distinguishes stable identity from immutable snapshots and records where a reference must pin an exact revision.

## 1. Versioned objects

| Object | Stable identity | Snapshot/version | Change rule |
|---|---|---|---|
| Playbook, Module, Lesson, Practice Activity | Editorial identity | Immutable content revision with monotonic per-identity sequence | Edit creates a draft revision; approval/publication switches current pointer and appends event. Old published revisions remain referenceable. |
| Module curriculum | Module identity | Module Revision plus its exact ordered Module Learning Requirements | Any membership/order/classification/completion-condition change creates a new Module Revision. Existing Module Completion is not rewritten. |
| Playbook recommendation | Playbook identity | Recommendation set belongs to Playbook Revision and pins Module Revision | Updating recommendation creates a new Playbook Revision/link set; existing journey references remain. |
| Learning Journey | Journey identity | Ordered immutable Journey Steps pin exact editorial revisions or user-owned records | New activities or state observations append steps; existing steps never resolve to latest content. |
| Lesson body | Lesson identity | Lesson Revision with ordered blocks and block schema version | Published blocks immutable; new content changes create new Lesson Revision. Existing Note anchors remain on old revision/block. |
| Practice Activity | Activity identity | Practice Activity Revision | Attempt pins exact revision and response prompt keys; editing activity does not reinterpret prior response. |
| Formula | Calculator Definition identity | Immutable Formula Version and approval events | Formula changes create a new version. Active pointer changes only through evidence-backed approval. Results retain old version. |
| Calculation | None beyond result identity | Immutable saved Calculation Result snapshot | Never recompute/overwrite on formula update; an explicit recalculation creates a new result. |
| My Plan | Plan identity | Immutable Plan Revision chain | Every saved edit creates new revision with predecessor; no financial thinking is overwritten. |
| Achievement | Definition identity | Definition Revision | User Achievement references exact criteria/display revision awarded. Criteria edits do not reinterpret old award. |
| Source | Mutable catalog identity | Provenance Snapshot attached to reviewed content/formula version | Snapshot captures source context at review; later catalog edits cannot change it. |
| Editorial review/publication | Editorial identity/revision | Append-only action event | Correction is another event with actor/time/reason where policy requires; do not erase prior event. |
| Search | Canonical editorial identity/revision | Rebuildable projection | Rebuild or replace projection from eligible current published revisions; not a source of truth. |
| Dictionary Term | Future stable identity | Future Definition Revision | Same pattern as other editorial content, only after scope approval. |

## 2. Exact historical references

When a learner starts from a Playbook, Learning Journey Context has a Journey Step for the exact Playbook Revision and, when followed, a step/reference for the exact recommendation and target Module Revision. Later steps may reference exact Lesson and Practice revisions, a saved Calculation Result, and a Plan Revision. Each step has sequence, typed kind/target, observed state and timestamps. Steps reference underlying records without copying their bodies. If scenario assumptions materially explain the user's path, store only the relevant scenario/assumption snapshot with provenance rather than depending on a future mutable editorial value. The target kind/reference pair is allow-listed and validated; editorial targets always pin a revision. Step kinds may be added without a schema column for each type.

Notes reference exact content revision and block where applicable. Completion evidence references exact Lesson Revision, Module Learning Requirement and Module Revision. Requirement Evidence references one exact Practice Attempt, Practice Activity Revision, Module Learning Requirement and Module Revision; the requirement's target Practice revision must equal the attempt's revision. A Practice Attempt may have zero-many requirement-evidence associations and zero-many saved Calculation Result links. Each saved Calculation Result references its exact Formula Version and immutable value/method snapshots. Plan Revision and Journey Step point to these exact records rather than recalculating or copying them. Retiring an editorial item leaves those references resolvable.

## 3. Module completion across curriculum changes

Module Completion is a decision evaluated against one Module Revision and its requirement set. The record explains each required requirement and its supporting exact evidence record or missing condition. For Practice requirements, the evidence reference is Requirement Evidence, identifying the learner's exact Practice Attempt and exact Practice revision. A new Module Revision may add/remove/reorder/reclassify learning requirements but must not mutate old completion evidence. If the system evaluates the newer curriculum, it creates a separate evaluation against the new revision. Whether prior completion carries forward as recognition is a product policy still TODO; it must not be inferred by schema. Whether one accepted Practice Attempt can satisfy multiple requirements remains a curriculum/completion policy; relationship cardinality alone does not imply acceptance.

## 4. Plan and formula reproducibility

Plan Revision captures its own target, assumptions, path and references at save time. Comparing two revisions compares those snapshots, not current values. Any linked Calculation Result independently preserves exact Formula Version and calculation inputs/assumptions/outputs/time. A recalculation after six months creates a new Calculation Result and, if the user's saved thinking changes, a new Plan Revision. Never substitute the current Formula Version when rendering an old result.

Formula Version's definition, units, assumption contract, rounding/method, tests/expected results, source snapshot, reviewer and approval/activation timestamps are tied to its immutable version. A code deployment alone does not activate the formula. Retiring a formula prevents new use but preserves historical results.

## 5. Content blocks and schema evolution

Lesson Content Blocks are ordered values in one Lesson Revision. Block identity is stable within that revision, allowing an annotation to identify its origin. A new Lesson revision may have changed block IDs/content. Do not migrate an old note anchor silently to a new block. A renderer may support old block schema versions or show a stable archived representation; the fallback/rendering approach is a physical/UI decision.

## 6. Versioning items not yet selected

TODO/TO-BE-DEFINED: revision retention duration; whether every draft save creates a revision or drafts may be edited before immutable review submission; version key format; prior Module completion carry-forward behavior; whether one accepted Practice Attempt can satisfy multiple requirements; note quote/offset anchoring strategy; typed payload migration/fallback; Formula implementation artifact binding; and retention/deletion exceptions. Do not use mutable current pointers as the only historical reference.
