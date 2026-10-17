# Entity Catalogue

This catalogue defines the logical persistent concepts and distinguishes required initial scope from future or conditional concepts. The count is **41 logical entity types**, including two future Dictionary types. Journey Step and Requirement Evidence are independently addressable relationship/history records. Embedded value collections and framework-owned authentication internals are not counted as entities. See [FIELDS.md](FIELDS.md) for per-field specification.

| # | Entity | Domain / ownership | Persist? / lifecycle and purpose | Relationships and versioning |
|---:|---|---|---|---|
| 1 | User Account | Identity / System-owned | Yes; active, suspended, deletion-pending, closed states are conceptual only pending policy. Establishes authenticated ownership. | Owns user records; framework authentication reference. Stable identity, not content-versioned. |
| 2 | Playbook | Editorial-owned | Yes; stable editorial identity, current published revision pointer, active/retired. | Has revisions; revisions recommend Module revisions. |
| 3 | Playbook Revision | Editorial-owned | Yes; immutable authored snapshot, draft through published/superseded/retired lifecycle. | Belongs to Playbook; has recommendations, topics, sources, assets and related-content links. Independently referenceable. |
| 4 | Module | Editorial-owned | Yes; stable identity and current published revision pointer. | Has revisions; can be related to Playbooks and other Modules. |
| 5 | Module Revision | Editorial-owned | Yes; immutable curriculum/metadata snapshot. | Belongs to Module; owns learning requirements, topics, source/media and related links. |
| 6 | Lesson | Editorial-owned | Yes; stable reusable identity; current published revision pointer. | Has revisions; Module revisions include its revisions by requirement links. |
| 7 | Lesson Revision | Editorial-owned | Yes; immutable title/metadata/body/block snapshot and lifecycle. | Belongs to Lesson; may be referenced by Module requirement, Practice, journeys, notes and progress. |
| 8 | Lesson Content Block | Editorial-owned | Yes as a child value within Lesson Revision; ordered typed educational content. | Revision-owned, stable block identity within revision, schema-versioned payload. Not independently mutable after revision publication. |
| 9 | Module Learning Requirement | Editorial-owned | Yes; defines order, required/optional/recommended classification, exact target revision and completion condition within one Module Revision. | Belongs to Module Revision; targets Lesson Revision or Practice Activity Revision. |
| 10 | Playbook–Module Recommendation | Editorial-owned | Yes; recommendation order/rationale/status within one Playbook Revision. | From Playbook Revision to exact Module Revision. |
| 11 | Related Content Relationship | Editorial-owned | Yes where approved relations are useful; typed, directional or explicitly symmetric relation between exact revisions. | Source revision to target revision; relation kinds restricted to approved vocabulary. |
| 12 | Topic | Editorial-owned | Yes if basic discovery taxonomy is needed; stable curated topic. | Connected to revisions through Content–Topic Assignment. Taxonomy depth remains open. |
| 13 | Content–Topic Assignment | Editorial-owned | Yes; links a content revision to a Topic with optional local ordering/role. | Exact revision and topic; unique pair/role. |
| 14 | Practice Activity | Editorial-owned | Yes; stable activity identity and current published revision. | Has revisions; linked through Module requirements and Lesson blocks/relationships. |
| 15 | Practice Activity Revision | Editorial-owned | Yes; immutable prompt, response specification, instructions, tool references and safety text. | Belongs to activity; attempts pin exact revision. |
| 16 | Practice Attempt | User-owned | Yes for explicitly submitted/saved attempts; in-progress draft persistence is TODO. Records an exploratory attempt, not necessarily a scored answer. | Owned by User; pins exact Practice revision and optional journey; has responses, zero-many Requirement Evidence links, and zero-many saved Calculation Result links. |
| 17 | Practice Response | User-owned | Persist when the activity's response must survive; response data belongs to one attempt. | Child of attempt; values can contain sensitive financial information. |
| 18 | Learning Journey Context | User-owned | Persist when a journey begins from editorial discovery; stable journey identity/header and relevant starting context. | Has ordered Journey Steps; referenced by attempts, plans and progress. Journey is distinct from the underlying records it references. |
| 19 | Journey Step | User-owned | Yes; append-only ordered historical step within one journey. Identifies an observed learner-path milestone/state without copying its target record. | Belongs to one Journey Context; carries extensible step kind and exact typed target reference; target user data must share journey owner. |
| 20 | Lab Tool | Editorial-owned | Yes for each published tool identity; descriptive/user-facing tool concept. | Maps to Calculator Definition where calculator behavior applies; may be referenced by content. |
| 21 | Calculator Definition | Editorial-owned | Yes; stable calculation capability metadata, input/output contract and current Formula Version pointer. | Belongs to or is exposed by Lab Tool; has Formula Versions. |
| 22 | Formula Version | System-owned | Yes; immutable executable/method specification version with lifecycle/evidence. | Belongs to Calculator Definition; referenced by approvals and results. |
| 23 | Formula Approval | Audit/history | Yes; durable review/approval/activation/retirement action and evidence metadata. | References Formula Version, actor, action and timestamp. Append-only conceptual history. |
| 24 | Calculation Result | User-owned | Persist only when explicitly saved or attached to Practice/Plan; immutable reproducibility snapshot. | Owned by User; pins Formula Version, complete inputs/assumptions/outputs, units/currency/precision methodology where relevant and source/warning snapshots; has zero-many Practice Attempt and Plan Revision links. |
| 25 | My Plan | User-owned | Yes; stable plan container with current revision pointer and lifecycle state. Count per user unresolved. | Has ordered Plan Revisions; owner cannot be inferred from revision input. |
| 26 | Plan Revision | User-owned | Yes; immutable snapshot of a user's target, assumptions, path and evidence context. | Belongs to Plan; predecessor and relevant Practice/Calculation/Journey/content revision refs. |
| 27 | Note | User-owned | Yes; private authored note, insight, highlight or annotation with optional exact content anchor. | Belongs to User; optional exact revision/block anchor and journey context. |
| 28 | Lesson Completion | Derived | Yes as explainable user-scoped learning fact or rebuildable equivalent; records learner evidence against exact Lesson Revision. | User + Lesson Revision + optional exact Module Learning Requirement/Journey Step context. Not a universal completion percentage. |
| 29 | Requirement Evidence | Derived | Yes; addressable evidence association linking one exact Practice Attempt to one exact Module Learning Requirement within one Module Revision. | Same learner/owner; exact Practice Revision must match requirement target. One attempt may link to multiple requirement-evidence records; acceptance policy per requirement remains explicit and unresolved. |
| 30 | Module Completion | Derived | Yes as explainable decision/history; records outcome against one Module Revision and its required items. | User + Module Revision + immutable requirement/evidence snapshot citing exact evidence records; re-evaluation creates another decision. |
| 31 | Achievement Definition | Editorial-owned | Yes for minimal achievements; stable identity and current definition revision. | Has definition revisions; criteria version pinned by User Achievement. |
| 32 | Achievement Definition Revision | Editorial-owned | Yes; immutable name/description/criteria identifier and state. | Belongs to definition; exact rule content/criteria remain TODO. |
| 33 | User Achievement | Audit/history | Yes; durable award record and evidence references. | User + Definition Revision + qualifying Module Completion and Plan Revision/evidence. Duplicate-award policy TBD. |
| 34 | Source | Editorial-owned | Yes; editor-maintained source identity/current metadata. Mutable catalog record is not historical evidence by itself. | Has snapshots attached to content revisions. |
| 35 | Source Provenance Snapshot | Editorial-owned | Yes when cited/relevant; immutable historical source details as reviewed for a content revision. | References Source and exact content revision; reviewer/time retained as applicable. |
| 36 | Editorial Review | Audit/history | Yes; review request/action, decision, reviewer, timestamp and comments/access scope. | References exact editorial revision; author/approver separation policy unresolved. |
| 37 | Publication Event | Audit/history | Yes; publish/supersede/retire event with actor/time and selected revision. | References editorial identity/revision. |
| 38 | Search Projection | Derived | Yes as a rebuildable index/projection if search is implemented. | Derived from currently eligible published revisions; canonical source remains editorial records. |
| 39 | Media Asset | Editorial-owned | Yes for referenced asset metadata; file bytes live in a future storage implementation. | Revisions/content refer by stable identity; replacement creates new asset revision/reference or new identity according to implementation policy. |
| 40 | Dictionary Term | Editorial-owned, Future | Future only; stable term identity. | Has Definition Revisions and links to content if approved. |
| 41 | Dictionary Definition Revision | Editorial-owned, Future | Future only; immutable definition and provenance. | Belongs to term; same editorial/source lifecycle. |

The count is 39 current/conditional types and 2 future Dictionary types. No entity count includes embedded values or framework-owned authentication internals.

## Entities intentionally not promoted

- Profile: optional and not justified yet; account settings can remain on User Account until product needs emerge.
- Authentication identities, credential hashes, sessions, recovery tokens: selected framework owns these; policy unresolved.
- Separate target, assumption, strategy, input, output, calculation source, highlight, note anchor, or plan evidence records: values embedded in their owning immutable snapshot/attempt by default. Requirement Evidence and Journey Step are exceptions because bidirectional lookup, ordering, state and historical association require addressable records.
- Generic audit log, analytics event, graph edge, entitlement/payment, AI job, and notification entities: excluded from initial scope.
