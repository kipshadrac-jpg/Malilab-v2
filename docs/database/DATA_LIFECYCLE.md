# Data Lifecycle, Deletion and Retention

This is a conceptual lifecycle policy, not a legal retention schedule. No legal requirement or time period is inferred. Account deletion, export, retention and backup expiry require explicit product/security/legal investigation before real user data is accepted.

## 1. User-owned and user-scoped records

| Record | Edit | Delete/retire behavior | Retention/cascade rule |
|---|---|---|---|
| User Account | Profile/contact/status limited by unresolved policy | Account may be closed/deletion-requested; exact process TODO | Do not physically cascade before user-data policy is approved. Separate auth identity deletion from retained/anonymized history only under approved rules. |
| Practice Attempt/Response | Draft attempts may be editable; submitted evidence semantics TBD | User deletion control required by future policy; record may need deletion/anonymization | Child responses follow attempt; plan/achievement/progress references must be resolved transactionally, not left broken. |
| Learning Journey Context / Journey Step | Journey header is stable; steps are ordered immutable observations appended as activities occur | User lifecycle policy applies to the journey and all its steps | Steps reference but do not own editorial/user records. Same-owner private references; preserve or remove personal scenario snapshot per approved retention. Do not cascade into referenced editorial content or independently owned result/plan. |
| Requirement Evidence | Evidence association pins exact requirement, Module Revision, Practice Revision, attempt and learner; evidence state is retained | User deletion/privacy policy applies; evidence cannot be silently reassigned | Module Completion cites exact evidence; account deletion must resolve both evidence and completion snapshots consistently. Retain referenced editorial revisions independently. |
| Calculation Result | Result immutable; optional label/annotation may change; optional same-owner Practice Attempt link is immutable once attached | User deletion control required | If referenced by Practice Attempt or Plan Revision, deletion must use an explicit policy: retain, detach, anonymize, or delete linked context; unresolved. Never mutate formula/source evidence. |
| My Plan / Plan Revision | New revision only; archived state can change with history | User deletion control required; immutable revisions are not individually overwritten | Plan deletion/anonymization behavior and effects on awards/progress unresolved. A cascade must preserve referential integrity and owner privacy. |
| Note | User may edit; exact note history policy TBD | User deletion expected but exact soft/hard behavior unresolved | Anchor removal must not delete editorial content; note stays tied to exact revision until removed. |
| Lesson Completion / Module Completion | No direct user edit; correction by reevaluation/new evidence | Derived state can be rebuilt, but history/retention policy TBD | Owner deletion/privacy lifecycle; references exact content revisions. |
| User Achievement | No user mutation of evidence/award | Revocation/correction policy TBD; account deletion relation unresolved | Preserve evidence only per approved retention; never leave orphaned private plan references. |

No choice between hard deletion, soft deletion, anonymization, or retained tombstones is approved for user data. Record the choice by entity and dependent references before implementation.

## 2. Editorial content

| Record | Lifecycle | Delete/retire behavior |
|---|---|---|
| Editorial identity | Draft/unpublished/active/retired | Retire or supersede instead of destructive deletion once referenced/published. Slug reuse/redirect policy TBD. |
| Editorial revision | Draft → In Review → Approved → Published → Superseded/Retired (states may be skipped only by explicit workflow) | Published revision remains addressable for historical notes, progress, practice, plans and provenance. Unpublished abandoned drafts may be removable under an editorial policy. |
| Module requirements/recommendations/related links | Draft within parent revision; frozen at publish | Revise through new parent revision, never update a published set in place. |
| Source catalog | Mutable current metadata | May be updated/retired, but not used to rewrite snapshots. Deletion of source identity must preserve snapshots. |
| Source Provenance Snapshot | Immutable with reviewed revision | Retain with revision; preserve reviewer/source fields as recorded. |
| Review and Publication Events | Append-only | No routine deletion; access/retention policy for comments still TBD. |
| Formula Version/Approval | Versioned lifecycle and append-only actions | Retire, do not delete versions used by results; preserve approval/test/source evidence. |
| Media Asset | Active/replaced/retired | Do not remove a file while referenced by published content/history. Replacement creates a new reference/version; rights and orphan cleanup policy TBD. |
| Search Projection | Rebuildable | Remove projection when content is no longer eligible; canonical revisions remain. |
| Dictionary entries | Future | Same versioned editorial lifecycle if approved. |

## 3. Account deletion dependency review

Account deletion must identify user-owned records, derived Progress, achievement records, journey steps, requirement evidence, calculation/attempt links, references embedded in other users' content (none should exist), audit/security records, backups, and external provider data (none is approved in initial scope). A deletion operation must not expose another user's data or transfer ownership implicitly. Whether to hard-delete, anonymize, retain minimal audit evidence, or delay backup expiry is TODO/TO-BE-DEFINED, including the treatment of Plan Revision evidence referenced by awards and Journey Steps that point to deleted user records.

## 4. Physical deletion and backup boundary

The implementation phase must define transaction/cascade behavior and referential constraints, but it must not make database cascades the only expression of policy. Off-host backup expiry and restoration are operational policy, not row deletion; deleting a live record does not immediately erase prior backup copies. Define backup retention and deletion propagation before production data is considered safe.
