# Logical Constraints and Indexes

No SQL or physical index syntax is specified here. Indexes listed are logical query requirements and should be validated against measured usage before implementation.

## 1. Integrity constraints

| ID | Constraint | Why it matters |
|---|---|---|
| C1 | Every stable identity and immutable revision has a unique ID; revision sequence is positive and unique within its identity/type. | Supports durable references across edits. |
| C2 | At most one current published revision pointer per editorial identity; it points to an approved/published revision of that identity. | Prevents ambiguous current content. |
| C3 | Published content/formula/plan/evidence snapshots are immutable; correction creates a new revision/event. | Protects historical meaning and calculations. |
| C4 | Each Playbook–Module Recommendation belongs to one Playbook Revision and targets one exact Module Revision; ordering is unique within that Playbook Revision. | Preserves recommendation followed and avoids duplication. |
| C5 | Each Module Learning Requirement belongs to one Module Revision, targets exactly one Lesson or Practice revision, and uses an allowed classification for the target kind. | Makes completion interpretable and revision-scoped. |
| C6 | Requirement order and target membership are unique within the appropriate Module Revision target list. | Avoids duplicate or ambiguous learning requirements. |
| C7 | Required-item completion can be recorded only when all required requirements in that exact Module Revision have satisfying evidence; evidence identifies the exact target revision and condition. | Prevents arbitrary completion percentages. |
| C8 | Lesson block keys and ordering are unique within a Lesson Revision; block payload validates against type and schema version. | Allows safe rendering and stable note anchors. |
| C9 | User-owned record has exactly one owner; owner references are immutable, not caller-selected, and private references between records must have matching owners. | Prevents cross-account data access. |
| C10 | Plan Revision belongs to one plan, has a unique increasing revision number, predecessor from same plan with lower number, and no cycle. | Preserves plan history. |
| C11 | Plan Revision, Calculation Result, Practice Attempt submission and User Achievement evidence references cannot be retargeted after creation. | Maintains historical comparison and explainability. |
| C12 | A Formula Version may become Active only after required evidence exists and a distinct explicit activation action is recorded; at most one active version per Calculator Definition at a time. | Prevents code presence from implying approved financial logic. |
| C13 | Formula lifecycle transitions follow Draft → Tested → Reviewed → Approved → Active → Retired; invalid or skipped transitions are rejected unless a separately approved exceptional process is defined. | Makes governance auditable. |
| C14 | Every saved Calculation Result references the exact Formula Version active at execution and stores inputs, assumptions, outputs, unit/rounding/methodology and calculation time. | Permits later reproduction without current formula lookup. |
| C15 | Source snapshots attach to exact content/formula revision; catalog edits never rewrite source snapshot. | Preserves provenance. |
| C16 | Editorial publication requires an approved revision and an authorized publication event; AI draft alone cannot publish. | Preserves human review gate. |
| C17 | Search projection contains only eligible published editorial revisions and no user-owned data, drafts or private sources. | Avoids privacy leaks. |
| C18 | A Note anchor refers to exact revision and optional block; update/retirement never retargets it implicitly. | Keeps annotations meaningful. |
| C19 | A User Achievement references the definition revision and qualifying evidence; award uniqueness/reattempt policy remains TODO. | Makes awards explainable without inventing mechanics. |
| C20 | Media replacement preserves references needed by published revisions; asset hard deletion is blocked while referenced. | Prevents broken historical content. |
| C21 | Every Journey Step belongs to exactly one owner-matched journey, has a unique positive sequence within it, one allow-listed step type and target kind, and a resolvable typed target; editorial targets pin exact revisions and private targets share the journey owner. | Preserves an ordered, interpretable journey without a column per step type or copied target records. |
| C22 | Journey Steps are immutable observations. A changed state is represented by a later step; sequence and occurrence time preserve ordering/history. | Prevents later journey state from silently rewriting what was observed. |
| C23 | Each Requirement Evidence references exactly one Module Revision, a requirement belonging to it, its exact Practice Revision target, and a submitted Practice Attempt pinned to that Practice Revision; all user-owned references share one owner. | Proves which attempt was offered for which exact curriculum requirement. |
| C24 | At most one Requirement Evidence association exists per Practice Attempt + requirement. A requirement may have evidence from multiple attempts and an attempt may be associated with multiple requirements. Only evidence in an accepted state may satisfy a required item; whether one attempt is acceptable for multiple requirements remains a curriculum/completion policy, not a structural assumption. | Prevents duplicate associations while preserving explicit evidence and leaving the product rule open. |
| C25 | Module Completion evaluates exactly one Module Revision and snapshots every required item's state plus the exact accepted evidence selected for satisfaction; evidence must match the requirement target and learner. | Makes completion explainable and stable after later edits. |
| C26 | A Practice Attempt may link to zero or many saved Calculation Results. Each linked result is same-owner and retains its exact Formula Version and calculation snapshots; no Practice Attempt requires a result. | Supports zero/one/many calculations without recalculating history or requiring calculator use. |
| C27 | If a journey records a Playbook-origin step, it is unique for that journey and precedes the recommendation-followed and Module-entry steps; a followed recommendation belongs to that exact Playbook Revision and points to the exact Module Revision recorded by the corresponding step. | Preserves the order and identity of the route from discovery into learning. |

## 2. Candidate logical indexes

| Index | Fields / key | Expected query | Unique? / rationale |
|---|---|---|---|
| I1 | Editorial identity type + normalized slug | Resolve public content URL | Unique among active same-type identities. |
| I2 | Revision parent identity + revision number | Revision history/current lookup | Unique composite. |
| I3 | Editorial revision state + updated/authored time | Staff draft/review queue | Nonunique; add only for measured queue query. |
| I4 | Publication identity + event time | Current/history publication | Nonunique; latest event lookup. |
| I5 | Playbook Revision + recommendation position | Render ordered recommended Modules | Unique order per revision; optionally target uniqueness. |
| I6 | Module Revision + target kind + position | Render ordered learning requirements | Unique order; target membership unique as C6. |
| I7 | Lesson Revision + block position | Render lesson content | Unique order. |
| I8 | Content Revision + Source Snapshot | Show historical citations | Nonunique lookup. |
| I9 | User owner + created/submitted time | Account-scoped history lists | Nonunique; includes attempts, notes, results and plans. |
| I10 | User owner + plan + revision number | Show plan history/current predecessor | Unique per plan revision number. |
| I11 | User owner + exact Module Revision + evaluation time | Explain module progress | Nonunique history query; completion uniqueness policy TBD. |
| I12 | Formula Definition + lifecycle state | Resolve active formula | Conditional unique active version per definition. |
| I13 | Formula Version + approval action/time | Governance audit and evidence | Nonunique. |
| I14 | User owner + achievement definition revision | Show user's awards/check duplicates | Unique award policy TBD; do not enforce until criteria resolved. |
| I15 | Note owner + updated time | Private note list | Nonunique; no global text search. |
| I16 | Search projection text + content type/topic/state | Public discovery | Search engine-specific later; projection only. |
| I17 | Content Topic Assignment topic + exact revision | Topic browse/filter | Nonunique; composite uniqueness on revision/topic/role. |
| I18 | Related relationship source revision + kind + position | Render related content | Unique ordering per relation group. |
| I19 | Journey Context + sequence | Render one user's ordered learning path | Unique sequence per journey; user-scoped journey traversal. |
| I20 | Journey Step target kind + exact target reference | Find journeys/steps referring to a target where needed | Nonunique; add only for supported history queries; never index private target values. |
| I21 | Owner + Module Revision + requirement + evidence state/time | Explain requirement satisfaction and review evidence | Nonunique; owner-scoped evidence history. |
| I22 | Practice Attempt + requirement | Prevent duplicate attempt/requirement evidence association and find evidence from either side | Unique composite. |
| I23 | Owner + Practice Attempt + Calculation Result | Show saved calculations used in an attempt | Nonunique; same-owner link; result lookup remains owner-scoped. |

Do not index every field. Sensitive financial input values, note body, source snapshots, and arbitrary structured payloads are not indexed by default. Physical index choice and query plans are later work.

## 3. Constraints requiring product/implementation resolution

TODO/TO-BE-DEFINED: one vs multiple plans; what counts as a distinct Lesson completion; whether completion is per user+revision or per enrollment/journey; multiple journeys for the same origin; achievement deduplication/revocation; relation symmetry vocabulary; account uniqueness/auth contact policy; soft-delete semantics; source review requirements; whether search supports private note search (currently excluded); whether requirements can be deactivated after a Module revision is published (default: no); and the curriculum rule for whether one accepted Practice Attempt may satisfy more than one requirement.
