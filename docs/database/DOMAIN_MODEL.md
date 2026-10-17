# MaliLab Domain Model

**Status:** Phase 4 domain specification. This is the conceptual authority for the later logical model; it defines no SQL, Django models, migrations, or physical storage choices. Field details are in [FIELDS.md](FIELDS.md).

## 1. Three modeling levels

1. **Domain model:** named concepts, ownership, lifecycle, and rules in this document.
2. **Logical data model:** records, fields, relationships, constraints, and indexes in the companion database documents. These are implementation-neutral commitments unless marked Proposed or TODO.
3. **Future physical implementation:** Django/PostgreSQL types, table decomposition, JSON representation, deletion mechanics, indexes, migrations, and transactional details. These belong to a later implementation phase.

## 2. Domain inventory and ownership

Ownership labels are defined in [OWNERSHIP_AND_PRIVACY.md](OWNERSHIP_AND_PRIVACY.md). Common revision/status fields are not separate entities.

| Domain | Persistent concepts and primary ownership | Persistence decision |
|---|---|---|
| Identity | User Account (System-owned); optional Profile (Deferred); authentication identity/session records (System-owned, framework-managed) | Persist account identity/status and lifecycle timestamps. Do not design custom credential records. Profile is not required absent a product need. |
| Editorial content | Playbook, Module, Lesson and Practice Activity identities and revisions; Module Learning Requirement; Playbook–Module Recommendation; Related Content Relationship; Topic and Content–Topic Assignment (Editorial-owned) | Persist stable identities, immutable content revisions, revision-pinned relationships and editorial metadata. |
| Practice | Practice Attempt and Practice Response (User-owned); Requirement Evidence (Derived, user-scoped); Learning Journey Context and Journey Step (User-owned references/context) | Persist submitted/explicitly saved work sufficient for the core loop and historical explanation. Requirement Evidence links an exact attempt to an exact requirement. |
| Calculations | Lab Tool and Calculator Definition (Editorial-owned); Formula Version and Formula Approval (System-owned governance/history); Calculation Result (User-owned when explicitly saved) | Persist governed formula versions/approval evidence and saved result snapshots. Unsaved transient calculations need not persist. |
| Planning | My Plan and immutable Plan Revision (User-owned) | Persist plan identity and each saved snapshot. Target, assumptions, path and linked evidence are revision snapshot values, not independently mutable child records by default. |
| Notes | Note, including a note or highlight/annotation form (User-owned) | Persist owner-authored text/selection and an exact content-revision anchor where applicable. |
| Progress | Lesson Completion and Module Completion (Derived, user-scoped) | Persist explainable learning facts/decisions or rebuildable summaries; completion pins exact content/module revisions and evidence. Do not require Progress for other domains to work. |
| Achievements | Achievement Definition and its Definition Revision (Editorial-owned); User Achievement (Audit/history, user-scoped) | Persist issued awards and evidence references; criteria remain TODO where unspecified. |
| Source/editorial governance | Source catalog record and Source Provenance Snapshot (Editorial-owned); Editorial Review and Publication Event (Audit/history) | Snapshot source details per reviewed content revision; preserve review and publication history. |
| Search/discovery | Search Projection (Derived) | Rebuild from eligible published revisions; never canonical and never includes user-owned data. |
| Media | Media Asset (Editorial-owned) | Persist identity and editorial metadata/reference; physical bytes and storage location are future physical decisions. |
| Dictionary | Dictionary Term and Definition Revision (Editorial-owned, Future) | Conceptual future structure only. Do not build full Dictionary tables in initial scope unless approved core content requires a term. |

## 3. Core concepts and rules

### Editorial identities and revisions

Playbook, Module, Lesson, Practice Activity, Calculator Definition, Achievement Definition, and (future) Dictionary Term have stable editorial identities and separately addressable immutable revisions. A revision contains the authored snapshot, its state and revision sequence. Publication points to one approved revision; a later edit creates another revision. Retiring or superseding an identity does not erase revisions referenced by learners.

### Module learning structure

A Module Revision owns its ordered Lesson/Practice requirement set. Each requirement targets a specific published or publishable content revision, carries its revision-local order and classification, and preserves its completion-condition reference. Both Lesson and Practice requirements can be classified Required, Optional, or Recommended in the logical model. Recommended Practice is a supported relationship label, not a requirement that any specific activity use it. Completion is assessed against the exact Module Revision; only Required items can block completion. Exact item-level completion conditions and editorial use of Recommended Practice are TODO/TO-BE-DEFINED; no percent or global Lesson flag determines completion.

### Playbook recommendation

A Playbook–Module Recommendation belongs to a **Playbook Revision** and points to an exact **Module Revision**. It has revision-local order, active/inactive state within that revision, and optional rationale/context. This makes the recommendation a historical editorial fact and allows the same Module identity/revision to serve multiple Playbooks without duplication. A new Playbook revision may change its recommendations without rewriting journeys already started.

### Lesson reuse

The product concept says a Lesson belongs to a Module. The logical model keeps stable Lesson identity separate from Module membership so the same Lesson Revision can be linked from more than one Module Revision if editorially approved. This is a reuse capability, not a requirement to reuse content. Module-specific ordering and completion meaning live on Module Learning Requirement. The Lesson revision itself does not own a single Module parent. Revisit only if editorial practice confirms that Lessons must be strictly exclusive to one Module.

### Practice and journey context

Practice Activity Revision is editorial definition; Practice Attempt/Response is learner-owned evidence and pins the definition revision attempted. Requirement Evidence records which exact Module Learning Requirement, within which exact Module Revision, an attempt is being used to satisfy. It also pins the exact Practice Activity Revision and attempt, learner, evidence state, and relevant times. One attempt may be associated with zero or more requirement evidence records; whether one attempt is sufficient for multiple requirements is an explicit completion-policy decision, not inferred from relationship cardinality.

Learning Journey Context is the learner-owned journey identity and header context. Its ordered, append-only Journey Steps record milestones against underlying editorial revisions or user-owned records. A step stores a typed step kind, a typed reference to the exact referenced identity/revision/result, sequence, observed state (such as entered, completed, skipped, or other relevant state), occurrence time, and optional context/metadata. A journey can contain any subset and sequence of step kinds; adding a step kind does not require a new column. Steps reference rather than copy Playbook, Module, Lesson, Practice, Calculation Result, or Plan Revision records. The journey owner is authoritative; all user-owned references must have the same owner. A step represents an observed milestone; later state changes append a further step rather than silently rewriting historical state.

### Calculation and plan snapshots

Formula Version is immutable and governed through Draft → Tested → Reviewed → Approved → Active → Retired. Active status requires recorded evidence and an explicit approval/activation action. A saved Calculation Result pins Formula Version and captures normalized inputs, assumptions, outputs, units, rounding/methodology metadata, calculation time, and relevant source/warning snapshot. It is not recomputed when a formula changes.

My Plan is a user-owned stable identity. Every save that changes the plan creates an immutable Plan Revision with predecessor reference where applicable and a snapshot of the user's thinking. Plan values, target, assumptions, strategy/path, and relevant references are captured in that revision. One-versus-multiple plans per user remains unresolved. Revision comparison uses stored snapshots; it does not recalculate the past.

### Explainable Progress and achievement

Lesson Completion records a user action/evidence against an exact Lesson Revision. Practice Attempt and Plan Revision are first-class evidence sources; Requirement Evidence links a Practice Attempt to the exact requirement it supports. Module Completion pins an exact Module Revision and records the required items satisfied, the evidence references for each, and any outstanding required items at the time of evaluation. Its snapshot cites Requirement Evidence and/or Lesson Completion as applicable. Progress consumes these facts; neither Practice nor My Plan depends on Progress. Re-evaluation under a newer Module Revision creates a distinct completion decision; it does not rewrite history. A User Achievement pins its definition revision and references its qualifying Module Completion and Plan Revision/evidence. Detailed eligibility rules remain TODO.

### Source provenance and editorial history

A mutable Source catalog helps editors maintain identity/current metadata. Each relevant reviewed content revision also stores a Source Provenance Snapshot: source identity, title, URL/reference, publication date, access/retrieval date, source version/reference, relationship to content, reviewer and review timestamp where applicable. Editorial Review and Publication Event preserve durable decisions and actor/time; current state alone is insufficient history.

## 4. Deliberately not separate entities by default

- Profile: not justified by an approved user-facing requirement yet.
- Authentication credentials, recovery tokens, sessions: delegated to selected framework/account policy in a later phase; do not create custom conceptual credential tables here.
- Lesson Content Block: logical child value owned by an immutable Lesson Revision; whether physically normalized or stored as validated structured payload is a future implementation choice.
- Practice response sets, calculator inputs/assumptions/outputs, plan target/assumptions/path, Module Completion evidence explanation, provenance snapshots, and note anchors: revision/attempt-owned value collections, not independently mutable identities by default. Requirement Evidence is a separate relationship record because it must be addressable from either the exact requirement or the exact attempt.
- Generic audit log, universal graph edge, analytics event warehouse, recommendation engine, payment/entitlement tables, or AI provider tables: not justified in initial data scope.

## 5. Boundary and unresolved decisions

See [RELATIONSHIPS.md](RELATIONSHIPS.md), [CONSTRAINTS_AND_INDEXES.md](CONSTRAINTS_AND_INDEXES.md), and [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md). Open choices include account/authentication policies; one or multiple plans; exact persistence of unsaved Practice/calculation work; completion and achievement criteria; content-reuse editorial policy; retention/deletion/export; source citation standards; Dictionary timing; and physical representation of typed content/snapshots.
