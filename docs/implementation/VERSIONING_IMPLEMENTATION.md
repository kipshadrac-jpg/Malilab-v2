# Versioning Implementation

| Record | Mutability / numbering | Current pointer and historical references |
|---|---|---|
| Playbook, Module, Lesson, Practice Activity identity | Stable mutable editorial identity; lifecycle active/retired | Current published revision nullable FK; exact learning records reference immutable revision |
| Playbook/Module/Lesson/Practice revision | Immutable after creation of reviewed/published snapshot; positive sequence unique per identity | New edit creates next revision; publication event switches identity pointer; historical revision PROTECT |
| Module requirements and Playbook recommendations | Child relations owned by exact immutable Module/Playbook revision | New parent revision gets a new relation set; never mutate published membership |
| Lesson blocks | Immutable payload owned by exact LessonRevision; schema version and stable block keys | Old blocks remain rendered by compatible renderer; new edits copy/rebuild into new revision, not update old JSON |
| Practice attempt/response | Draft editability only if later-approved UX supports it; submitted values immutable | Exact PracticeRevision FK; changes require another attempt or correction record, not rewriting submitted snapshot |
| Formula Version | Immutable artifact/method and assumptions once tested; version key unique | Formula Definition points to active version; lifecycle audit events append; CalculationResult pins exact version |
| Plan Revision | Immutable snapshot; monotonic revision number per Plan; predecessor exact FK | Plan current pointer advances; prior revisions are PROTECT and never recalculated |
| Source Snapshot | Immutable source values at content/formula review | References mutable Source identity but copies relevant title/URL/date/version/access context; source edits cannot change snapshot |
| Calculation Result | Immutable inputs, assumptions, outputs, formula/method/source/warning context | Formula version PROTECT; exact decimal snapshots; never recompute after formula update |
| Journey Step | Append-only, increasing sequence per journey | References target registry to exact revision or same-owner user record; subsequent state is another step |
| Requirement Evidence / Module Completion / User Achievement | Immutable evidence decision and explanation | Exact ModuleRevision, requirement, PracticeRevision/Attempt, completion evidence and definition revision references; later reevaluation creates a new record |
| MediaAsset | Proposed one immutable row per byte version | Replacing image adds a new row/key/checksum; revisions continue to reference old asset. This makes history safe without mutable blob replacement. |
| RequirementEvidence | Immutable decision for one exact PracticeAttempt and one exact ModuleRequirement | Initial accepted semantics are one attempt to one requirement. Corrections/reassessment create a superseding evidence decision; prior evidence and ModuleCompletion remain unchanged. No evidence carries to a newer ModuleRevision. |

### Revision rules

1. Draft edits may mutate draft state only under editorial authorization. Once submitted/reviewed/published, authored revision content is frozen; correction is a new revision.
2. Revision number allocation must be transactional and unique per identity.
3. A stable identity's current pointer is a convenience for new discovery only. Learner historical records never resolve through it.
4. Publication, retirement, approval, and formula state changes create append-only history events; current state can be rebuilt/audited from events and pointers.
5. Current pointers must point to a revision belonging to the identity and an allowed lifecycle state.
6. Block schema/render compatibility is versioned; do not transform an old revision in place. Retain a renderer or documented fallback for stored schema versions.
7. Exact retirement deletion/retention and Plan/Note user data deletion are constrained by outstanding policy decisions; historical references use PROTECT until the policy is decided.

## Owner-approved behavior that constrains versions

- Email/password custom account identity is stable; email verification gates full personal features. Account deletion is a controlled hybrid workflow and never a model-level account-wide cascade.
- Review and approval pin exact immutable revisions. Editing after approval requires review/approval again; financial content author and approver differ. Formula activation has second-person approval, staff use MFA, and event snapshots retain actor/role/revision/version/time.
- Each monetary value has explicit currency; initial supported currency is KES, no implicit FX. Decimal calculation precision and display precision differ; formula-specific rounding is deterministic. Formula-specific precision/ranges remain per-calculator TODO.
- Note anchors remain on the original LessonRevision and ContentBlock; quote is authoritative, offsets are only hints, and no cross-revision reanchoring occurs.
