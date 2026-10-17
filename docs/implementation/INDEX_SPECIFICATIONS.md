# Index Specifications

Candidate B-tree indexes below correspond to identified product queries. Create only after query plans/representative volume validate them. PostgreSQL PK/FK indexes are assumed only where the database does not create them automatically (PostgreSQL does not automatically index referencing FK columns). Avoid indexing every state, JSON key, or private text field.

| Index | Fields | Query supported / rationale |
|---|---|---|
| Identity slug unique | normalized slug | Public Playbook/Module/Lesson/Practice resolution |
| Revision history unique | `(identity_id, revision_number)` | Ordered editor history and exact revision lookup |
| Current pointer FK | current revision ID where non-null | Resolve current published revision; verify parent/state in service |
| Editorial queue | `(state, updated_at)` on mutable identity/draft queue only | Staff review/draft listing; create if admin queue uses it |
| Publication history | `(identity_id, occurred_at DESC)` | Audit a content identity's publication events |
| Recommendation order | unique `(playbook_revision_id, position)` | Render ordered recommended Modules |
| Learning requirement order | unique `(module_revision_id, target_kind, position)` and target membership unique | Render ordered curriculum and check duplicate targets |
| Lesson block order | within-revision position if block rows; JSON array otherwise no DB order index | Render blocks from one immutable revision |
| Attempt owner history | `(owner_id, submitted_at DESC)` | Account-scoped Practice history |
| Account email identity | unique normalized `(email)` | Authentication lookup and duplicate-account prevention; verification state may be filtered for activation, not a substitute for login identity uniqueness |
| Response lookup | `(attempt_id, prompt_key)` unique | Load/validate responses for one attempt |
| Journey steps | unique `(journey_id, sequence)` | Ordered journey; plus `(owner_id, created_at)` on journey list |
| Journey target reverse lookup | unique concrete target association; index target registry FK | Find whether/where a target appears in journey |
| Requirement evidence | unique `(attempt_id, requirement_id)`; `(owner_id, module_revision_id, requirement_id, evidence_state)` | Exact evidence lookup and completion evaluation |
| Accepted evidence per attempt | partial unique `(practice_attempt_id)` where evidence is accepted/current | Enforce initial one-accepted-attempt/one-requirement semantics; if reassessment history is represented through supersession, only the current accepted decision participates |
| Module completion history | `(owner_id, module_revision_id, evaluated_at DESC)` | Explain completion per exact revision |
| Calculation result history | `(owner_id, calculated_at DESC)`; optional `(practice_attempt_id, calculated_at)` | Private result list and attempt's zero-many result retrieval |
| Formula active | partial unique `(calculator_definition_id)` where state Active | Guarantee at most one active version per definition |
| Formula approvals | `(formula_version_id, occurred_at)` | Governance trail and approval evidence |
| Staff audit actor | `(actor_id, occurred_at)` on review/publication/formula approval events | Actor history and accountability; role snapshot remains stored on event |
| Plan revisions | unique `(plan_id, revision_number)`; `(owner_id, plan_id, revision_number)` only if owner denormalization is approved/needed | Plan history and predecessor traversal |
| Notes | `(owner_id, updated_at DESC)` | User's private note list |
| Note anchor lookup | `(lesson_revision_id, block_key)` only if annotation rendering requires reverse lookup | Load notes for a viewed block; do not index quote text or expose it globally |
| User awards | `(owner_id, awarded_at DESC)` | Achievement display; no uniqueness on award key before policy |
| Source snapshots | `(content_revision_ref, source_id)` | Render provenance for exact revision |
| Content topics | `(topic_id, content_revision_ref)` and unique `(content_revision_ref, topic_id, role)` | Browse/filter topic |
| Search projection | GIN on `search_vector`; B-tree `(content_type, topic/state)` where measured | Public editorial full-text and filters only |
| Media key | unique storage key; checksum index only if duplicate detection needed | Immutable asset delivery/integrity |

Do not add GIN indexes to user assumptions, notes, plan snapshots, responses, or calculation values. They are private, rarely searched, and unnecessary indexing increases exposure surface and write cost. Composite indexes must begin with the common equality filters (usually owner or parent) followed by ordering time/position.
