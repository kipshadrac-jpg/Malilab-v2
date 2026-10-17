# MaliLab Data Model Audit

> **Phase 4B status:** This document records the initial audit findings. The two HIGH findings have been reconciled across the logical-model documents; see [DATA_MODEL_RECONCILIATION.md](DATA_MODEL_RECONCILIATION.md) for the focused re-audit and current Phase 5 readiness. Statements below describing missing links are the original audit record and are superseded by the reconciliation.

## 1. Executive Verdict

The Phase 4 specification represents the approved product loop and gets the major ownership and revision boundaries right. It has a strong foundation for version-pinned editorial content, immutable plan revisions, calculation governance, explainable Module completion, and private user data.

The initial audit found two high-severity gaps: Learning Journey Context had only single later-activity references, and Practice Attempt lacked explicit links to Calculation Results and requirement evidence. Phase 4B adds ordered Journey Steps, Requirement Evidence, and an optional zero-to-many Attempt-to-Calculation Result relationship. Whether one attempt may satisfy multiple requirements remains a policy decision; the logical model now represents and can explain each association without assuming its acceptance.

Other issues need explicit decisions before the affected features are implemented: precise note-anchor behavior, currency/precision capture, media immutability, the scenario snapshot boundary, and account deletion/retention. These do not require schema implementation now. Existing `PROJECT.md`, `DECISIONS.md`, `ROADMAP.md`, product documents, architecture documents, and database documents were reviewed. No existing database document was changed as part of this audit.

Severity definitions: **CRITICAL** means core integrity or privacy cannot be protected; **HIGH** means a required historical/product behavior is not represented reliably; **MEDIUM** means the design is plausible but underspecified and needs resolution before the affected implementation; **LOW** means a contained detail can safely remain deferred.

## 2. Product Traceability

| Product concept | Logical representation and ownership | Dependencies / workflow | Audit |
|---|---|---|---|
| Playbooks and revisions | `Playbook` and `Playbook Revision`; editorial-owned | Revision carries scenario, assumptions, intended outcome, discovery metadata, media and source provenance | Represented; exact revision is referenceable. |
| Modules and revisions | `Module` and `Module Revision`; editorial-owned | Revision owns ordered learning requirements and content relationships | Represented; completion is revision-specific. |
| Module recommendations | Playbook-revision-owned `Playbook–Module Recommendation` targeting exact Module Revision | Followed recommendation is referenced from `Learning Journey Context` | Represented; many-to-many without duplicating Modules. |
| Lessons and revisions | `Lesson` and `Lesson Revision`; editorial-owned | Module requirements target exact Lesson Revision; blocks belong to that revision | Represented; reuse is possible, subject to evidence-context clarification in §6. |
| Practice and revisions | `Practice Activity`, `Practice Activity Revision`; editorial-owned | Module requirements target exact Practice Activity Revision; attempts snapshot response context | Represented; evidence relationship is revision-specific. |
| Practice attempts | `Practice Attempt` and `Practice Response`; user-owned | Exact Practice Activity Revision, learner, responses, timestamps, state, journey context | Explicit Requirement Evidence and optional calculation links added in Phase 4B. |
| Lab Tools and calculators | `Lab Tool` and `Calculator Definition`; editorial/system-owned | Formula versions define behavior; calculation service executes it | Represented as a conceptual separation. |
| Formula versions and approvals | Immutable `Formula Version`, append-only `Formula Approval`; system/audit-owned | Test evidence, sources, reviewer, approval and activation lifecycle | Strongly represented; currency/precision details need tightening (§8). |
| Calculation runs/results | Immutable `Calculation Result`; user-owned result referencing exact Formula Version | Calculation service validates inputs and assumptions, persists only on save/attach | Optional zero-to-many result relationship to a Practice Attempt added in Phase 4B. |
| My Plan and revisions | User-owned `My Plan` plus immutable predecessor-linked `Plan Revision` | May reference target, assumptions, path, attempts, results and learning context | Represented. One-vs-many plan policy remains open and need not block a one-to-many model. |
| Notes and highlights/anchors | User-owned `Note`, exact Lesson Revision and optional block/selection anchor | Reader creates note against the revision viewed | Represented in concept; anchor selection and degradation behavior remain underspecified (**MEDIUM**, §10). |
| Learning Journey Context | User-owned journey identity with ordered Journey Steps | Connects discovery to learning and plans without copying underlying records | Multi-step exact-revision history represented by Phase 4B Journey Step. |
| Progress and evidence | User-scoped Lesson/Module completion and evidence records; derived/current state consumes facts | Exact revisions and requirement evidence explain completion | Core model represented; Lesson Completion idempotency remains an implementation detail (§4). |
| Achievements | Editorial `Achievement Definition`/revision and user-owned award with evidence refs | Award follows approved criteria and qualifying completion/plan evidence | Represented; award criteria and deduplication remain product decisions. |
| Sources/provenance | Editorial `Source` plus immutable per-revision `Source Snapshot` | Review and publication retain relevant citations and review metadata | Represented, including source context at review/publication. |
| Editorial review/publication | `Editorial Review`, `Publication Event`, revision lifecycle | Human review gates AI-assisted draft; publication changes current pointer | Represented; author/approver policy remains open. |
| Media | Editorial `Media Asset` referenced by revisions | Covers, diagrams and lesson media | Concept represented. Byte-level immutability/version policy is unclear (**MEDIUM**, §10/§15). |
| Search projection | Derived projection of eligible published revisions | Rebuildable from canonical editorial content; private user data excluded | Represented and appropriately separated. |

No additional core product capability is wholly absent. The initial supporting inconsistencies—standalone versus embedded scenario snapshots, multi-step journey context, and Practice-to-calculation handoff—are addressed in this document's findings and Phase 4B status notes; see the reconciliation for current status.

## 3. Versioning Audit

| Change scenario | Record preserving history / exact reference | Old state interpretable? | Risk of current content rewriting history? |
|---|---|---|---|
| Playbook revised after follow | Journey Steps reference exact Playbook Revision and followed recommendation | Yes; later steps retain exact target references and order | No, if revisions, recommendation and steps remain immutable. |
| Module revised after completion | `Module Completion` pins Module Revision and requirement/evidence snapshot | Yes; a later revision gets a distinct completion evaluation | No; carry-forward recognition is explicitly unresolved rather than silently recalculated. |
| Lesson revised after note | Note/anchor and Lesson Completion reference exact Lesson Revision and optional block identity | Yes if old revision/block are retained; text-range selection behavior still needs a rule | No silent retargeting is specified. Exact anchor robustness remains **MEDIUM**. |
| Practice definition changes | `Practice Attempt` pins Practice Activity Revision and response keys/data; Requirement Evidence pins target requirement | Yes; response context and evidence remain tied to exact revisions | No, if prompt keys, attempt and evidence references remain immutable. |
| Formula retired | Calculation Result pins Formula Version and input/assumption/output/method snapshot; approvals are append-only | Yes, subject to durable availability of the formula artifact and numeric policy | No automatic recalculation is specified. Currency/precision ambiguity is **MEDIUM**. |
| Module requirements change | New Module Revision owns a new requirement set; completion pins old revision and evidence | Yes; new curriculum is evaluated separately | No. Carry-forward rules remain open and do not mutate the old completion. |
| Playbook recommendation changes | Recommendation belongs to Playbook Revision and targets exact Module Revision; Journey Step references it | Yes, including ordered later journey steps | No. New journey history appends steps; old steps remain unchanged. |
| Plan edited repeatedly | Each immutable Plan Revision references its predecessor and snapshots the thinking at that time | Yes; revisions can be compared and calculations remain separately pinned | No, if edits always append and current pointer alone changes. |

Overall, the revision strategy is sound. The initial journey and calculation-association gaps are resolved in Phase 4B with ordered Journey Steps and explicit optional Attempt-to-Calculation Result links. These preserve references without copying large editorial documents into user records.

## 4. Learning and Evidence Audit

The conceptual chain is present: a Module Revision defines requirements; requirements target exact Lesson or Practice revisions; evidence and completion records are revision-specific; Progress consumes those facts; achievements cite qualifying evidence. The one-way boundary is consistent with architecture: My Plan can write and operate without reading Progress.

The model can explain a completion in principle by retaining the Module Revision, its requirement set, and which required items have evidence. Optional and recommended items do not block completion. A new Module Revision does not silently change the basis of an old completion.

The initial audit identified evidence attribution and idempotency details; Phase 4B resolves attribution as follows:

- **RESOLVED in Phase 4B — Practice evidence attribution:** Requirement Evidence pins exact Module Revision, requirement, Practice Revision, Practice Attempt, learner, evidence state and times. Module Completion cites selected evidence. Whether one attempt may be accepted for multiple requirements remains explicitly open.
- **MEDIUM — Evidence idempotency:** the specification leaves duplicate Lesson Completion and evidence handling open. Define the logical identity of a completion/evidence fact and whether repeated study creates a new attempt or reuses existing completion before implementation. This prevents duplicate evidence from being mistaken for distinct requirements satisfied.

The current model should preserve requirement satisfaction as explainable evidence, not a percentage. There is no Progress → My Plan dependency in the documented boundary; that boundary should remain unchanged.

## 5. Playbook Journey Audit

The intended path is correctly revision-aware at entry: Playbook Revision → recommendation on that revision → exact Module Revision → user-owned Learning Journey Context. Small scenario/assumption snapshots can preserve the learner’s contextual assumptions without copying the full Playbook body. Plan Revision can then reference the journey and exact learning revisions.

- **RESOLVED in Phase 4B — Multi-step path representation:** Journey Step now stores ordered, append-only observations with a step type, typed exact target, state, timestamps and optional metadata. It supports multiple steps without copying target records or adding a column for each step type.
- **MEDIUM — Scenario boundary mismatch:** the architecture names Scenario/Assumption as a domain with minimal saved scenario persistence; the database model embeds scenario snapshots in attempts, journey contexts, results and plan revisions, without a standalone Scenario entity. This is a reasonable simplification if scenarios have no independent lifecycle, but the boundary is not explicitly reconciled. State whether the snapshots are the approved persistence model or whether reusable user scenarios are needed. This matters to prevent implementers from creating incompatible duplicate scenario stores.

No large editorial content needs to be duplicated in journey or plan records. Journey references should identify exact revisions and recommendation identity; compact user assumptions may be snapshotted where their meaning depends on time.

## 6. Lesson and Practice Reuse Audit

**Lesson reuse:** The model can support one Lesson identity/revision used by multiple Module Revisions because membership and ordering live in revision-specific Module Learning Requirements. Requirement identity can disambiguate why the same Lesson counts in a particular Module. This is technically safe if completion evidence cites the requirement or an equivalent Module-specific evidence edge. Reuse is not an approved product requirement, so it should remain an editorial capability, not a requirement to reuse content.

**Practice reuse:** One Practice Activity identity/revision can be targeted by multiple Module requirements. Requirement Evidence now identifies which exact Module Revision/requirement a specific attempt supports, so evidence attribution is representable. Whether one attempt may be accepted for more than one requirement remains a product/completion-policy decision; until that rule is settled, reuse is structurally possible but should not imply automatic multi-requirement satisfaction.

**MEDIUM — Revision semantics under reuse:** exact revision pinning is good, but a Module revision must continue to target a particular Practice/Lesson revision even if the identity receives a new revision. The current design says this; preserve it as a constraint and never resolve a requirement dynamically to “latest.”

## 7. Practice Attempt Audit

| Information | Present? | Audit finding |
|---|---|---|
| Exact Practice Activity Revision | Yes | Correct historical pin. |
| Learner/owner | Yes | Owner-scoped and same-owner references are required. |
| Inputs and responses | Yes | Response keys/data are associated with the attempt and revision prompt schema. |
| Result and completion state | Yes conceptually | Attempt state and result are included; exact domain semantics remain activity-specific, not quiz-only. |
| Timestamp | Yes | Started/submitted timestamps are described. |
| Learning context | Yes, optional journey context | Ordered Journey Steps preserve multiple historical activities and exact targets. |
| Calculation/formula context | Resolved in Phase 4B | Practice Attempt has an optional zero-to-many relationship to saved Calculation Results; each result stays formula-pinned. |
| Plan handoff | Yes | Plan Revision may reference exact same-owner Practice Attempts and Calculation Results; a reverse Attempt→Plan link is not required by the product model. |
| Module requirement attribution | Resolved in Phase 4B | Requirement Evidence pins exact Module Revision, requirement, Practice Revision and Attempt; acceptance policy for reuse remains open. |

**RESOLVED in Phase 4B — Calculation association:** the logical model now defines an optional zero-to-many same-owner Practice Attempt → Calculation Result relationship. Each result preserves its exact Formula Version and snapshots; no attempt requires a calculation.

Practice is correctly broader than quizzes. The model accommodates reflection, numeric inputs, assumptions, scenarios and calculator interaction without requiring correctness scoring.

## 8. Calculator and Formula Audit

The model separates Lab Tool identity, Calculator Definition, immutable Formula Version, approval history, and user-owned Calculation Result. The formula lifecycle is explicitly Draft → Tested → Reviewed → Approved → Active → Retired; activation requires formula definition, assumptions, test cases and expected results, source/reference, reviewer, approval timestamp and version identifier. Invalid/unapproved activation is prohibited by the documented lifecycle and constraints. Results retain the exact formula version and snapshots, and retirement does not rewrite prior outputs.

| Reproducibility requirement | Status |
|---|---|
| Formula version and method/definition | Present, including immutable definition artifact reference. |
| Inputs and assumptions | Present as result snapshots. |
| Output and calculation timestamp | Present. |
| Units | Present conceptually. |
| Currency | Not explicit as a required currency identifier per currency-valued value (**MEDIUM**). A generic unit could be insufficient to distinguish currency semantics. |
| Precision and rounding | Rounding/methodology are captured conceptually; numeric precision/encoding and exact policy snapshot are not pinned (**MEDIUM**). |
| Source and approval context | Formula version points to sources and append-only approval actions; approval-at-run can be derived if event ordering is durable. Clarify whether result must snapshot the approval state/time used at calculation. |
| Warnings/disclaimers | Present as methodology/warning snapshot. |
| Deterministic execution/testing | Domain service boundary and formula test evidence are present; tests must cover boundary, rounding and representative inputs before activation. |

**MEDIUM — Currency/precision contract:** require each monetary input/output to carry an explicit currency/unit and capture the exact precision/rounding policy with the result or immutable formula artifact. This matters for reproducibility and comparison; “unit” alone may not adequately distinguish currency, scale and rounding. This is a conceptual specification correction, not physical SQL design.

There is no evidence that calculation logic is embedded in templates, client code, or arbitrary persistence entities. The calculation service boundary should remain authoritative, deterministic and independently testable.

## 9. My Plan Audit

`My Plan` is a user-owned identity whose edits create immutable `Plan Revision` snapshots linked to a predecessor. Revisions can reference targets, timeframe, assumptions, path/strategy, relevant practice attempts, calculation results and formula versions, learning context, and exact Playbook/Module/Lesson revisions. This supports comparison of the learner’s thinking over time without copying large editorial records. It does not require Progress to function.

The one-vs-multiple-plan policy is a product/UX decision, not a blocking logical-model decision: the documented one-to-many model can be implemented without enforcing “one active plan.” Before enforcing a uniqueness rule or finalizing plan-selection UX, the owner should decide whether users may have multiple plans and how active/archive state behaves. Do not add an arbitrary unique-active constraint while unresolved.

**MEDIUM — Concurrent revision writes:** the chain permits a simple predecessor relationship but does not specify conflict behavior if two edits start from the same current revision. For the single-user initial product this can be resolved as an implementation rule (reject stale predecessor or create an explicit branch); it should not permit silent overwrite. This is not a Phase 5 blocker.

Historical interpretation is adequate if every referenced result, attempt and editorial revision is retained or handled under an explicit account-deletion policy.

## 10. Notes and Anchoring Audit

Notes reference the exact Lesson Revision and may identify a content block plus selection data. Stable block identity within an immutable Lesson Revision means reordering or removing a block in a later revision does not silently retarget an old note. If the old revision and its blocks remain available, the original context is still interpretable.

**MEDIUM — Anchor precision and degradation:** the specification leaves the exact selection-anchor strategy open. It does not say whether the anchor stores selected text, offsets, quote/context, or a fallback when the block is changed or unavailable. A block reference alone locates a block but may not locate the user’s highlighted passage within it. Define the anchor and display fallback before note implementation. This protects the user’s annotation from appearing against unrelated text.

If a block is removed from a new Lesson Revision, an old note remains attached to the old revision; it may be shown as historical/original context, but must not be auto-migrated. User edit/delete and retention follow account policy.

## 11. Ownership and Privacy Audit

The ownership catalogue distinguishes system-owned, editorial-owned, user-owned, derived, and audit/history information. User accounts own plans/revisions, attempts/responses, calculations, notes, journey contexts, completion/evidence and awards. Editorial revisions, formulas and source records do not inherit user ownership. Search projections include published editorial material only and are rebuildable; they exclude notes, plans, calculations, practice responses and other private financial data.

Application-level authorization is the accepted initial defense; PostgreSQL row-level security is not required in the architecture for the initial application. Every read and write of user-owned records must scope by authenticated owner, and all cross-record references must validate same-owner constraints where applicable. Staff roles must not imply access to private financial records. Administrative access and exceptional support access require explicit separation and audit policy.

No documented relationship inherently exposes one user’s records to another, but the model needs same-owner enforcement for Attempt ↔ Result, Plan Revision ↔ Attempt/Result/Note, journey context and achievement evidence. Add authorization and negative cross-user tests before implementation; they should prove that guessed identifiers and mixed-owner references cannot read or mutate another user’s data. This is a required defense-in-depth test, not a demand for RLS.

**HIGH — Account deletion/retention is unresolved:** deletion must account for immutable plans, attempts, calculations, awards and audit references. The current model correctly avoids silent cascades but leaves hard deletion, anonymization, retention duration and backup expiry undecided. This is not a blocker to Phase 5 design, but it is a blocker before collecting production user data. Decide per record class and ensure references cannot leave identifiable user data unintentionally.

## 12. Source and Editorial Governance Audit

The model links content revisions to source provenance snapshots and editorial review/publication history. Snapshots preserve source identity, title, URL/reference, publication date, retrieval/access date, source version/reference, reviewer and review timestamp where available. This prevents mutable Source catalogue edits from changing what supported a historical content revision. Formula versions also require source context and approval evidence. AI-generated drafts pass through human review and approval; generation alone does not publish.

No major provenance relationship is missing at the conceptual level. Before implementation, ensure each published revision can identify all applicable snapshots (not merely a single mutable Source row), and that reviewer/time are retained on the review/publication event. Preserve source snapshots when a source is retired. No legal/regulatory policy is inferred here.

## 13. Constraints and Index Audit

The logical constraints cover identity/revision numbering, one current active revision, ordered membership/recommendations, exact revision targets, immutable published revisions, formula lifecycle and a single active formula, ownership, same-owner references, requirement uniqueness, and append-only history. Indexes are aimed at owner-scoped records, current published content, ordered revision membership, formula lookups, and search projections. The strategy is appropriate at logical stage and does not over-specify physical indexes.

| Issue | Severity | Why it matters / correction |
|---|---|---|
| Practice Attempt ↔ Calculation Result relationship | Resolved in Phase 4B | Optional zero-to-many relationship and same-owner/exact Practice revision constraints are now documented. |
| Journey multi-step references | Resolved in Phase 4B | Journey Step has sequence uniqueness, typed-target validation, owner matching and immutable reference constraints. |
| Duplicate Lesson Completion/evidence identity left open | MEDIUM | Repeated events can produce duplicate or contradictory completion facts. Define idempotency/evidence key before implementation. |
| Achievement award uniqueness explicitly unresolved | LOW | Duplicate awards may occur if criteria are evaluated repeatedly. Do not decide badge criteria now; define uniqueness/idempotency when award rules are approved. |
| Plan active uniqueness unresolved | LOW | Correctly avoids an unsupported one-plan assumption. Add constraint only after product cardinality is approved. |
| Practice requirement attribution | Resolved in Phase 4B | Requirement Evidence identifies the exact attempt/requirement pair with uniqueness and exact target checks. |

No separate SQL or database-engine requirements are proposed by this audit.

## 14. Data Flow Audit

| Flow | Input → entities touched | Historical context / derived records | Authorization boundary and resulting state |
|---|---|---|---|
| 1. Discover Playbook | Published search projection → Playbook Revision | Projection points to canonical revision; no user record required until tracking starts | Publicly eligible published content only; projection is derived/rebuildable. |
| 2. Follow recommendation | Selected recommendation → Learning Journey Context | Stores exact Playbook Revision, recommendation and Module Revision; scenario snapshot as needed | Authenticated owner/consent policy applies; journey is private and immutable in its references. |
| 3. Complete Lesson | Viewed Lesson Revision → Lesson Completion/evidence | Exact Lesson Revision and Module requirement context should be recorded | Owner-scoped write; state explains the revision completed. |
| 4. Complete Practice | Practice Activity Revision, responses → Attempt/Responses/Requirement Evidence | Exact Practice Revision, journey step, exact requirement and evidence state | Owner-scoped; validate same learner and exact target revision. |
| 5. Run/save calculator | Inputs/assumptions → Formula Version → Calculation Result | Formula/output snapshot persists only if saved; optional Attempt link supports zero/one/many results | Server calculation service; owner-scoped result; no cross-user read/write. |
| 6. Create Plan | Learning context, user target/assumptions → My Plan + first Plan Revision | Exact context/results/revisions referenced; immutable snapshot | Authenticated owner; write succeeds without Progress. |
| 7. Edit Plan | Current Plan Revision + edits → new Plan Revision | Predecessor, prior state, new assumptions/results retained | Owner check and stale-revision handling; current pointer advances, old revision remains. |
| 8. Create Note | Lesson Revision/block/selection + text → Note | Original revision and anchor remain fixed | Private owner-only access; excluded from search. |
| 9. Revise Lesson | Editorial draft/review → new Lesson Revision, reviews, publication event, projection | Old revisions/blocks remain for notes/progress; new projection targets new revision | Editorial role/publication authorization; human approval required. |
| 10. Retire Formula | Formula approval/action → Formula Version lifecycle and active pointer | Old results retain old version; new runs cannot resolve retired formula as active | Authorized formula reviewer/approver action, audited; no rewriting saved results. |
| 11. Revise Module requirements | New Module Revision and requirement set → review/publication/completion evaluation | Old completion stays against old revision; new evaluation is separate | Editorial publication gate; no silent progress rewrite. |
| 12. Award Achievement | Eligible completion/plan evidence → User Achievement | Exact definition revision and qualifying evidence references retained | System award under approved rule; user-scoped; duplicate policy is unresolved. |
| 13. Delete account | Authenticated request → account status and affected user-owned records | Policy must resolve anonymize/delete/retain and backup expiry; editorial records remain | Verify request/authority; apply per-entity policy without leaking identity or orphaning private evidence. |

The flows are generally consistent with the domain boundaries. Flows 2, 4, 5 and 7 rely on the corrections/decisions identified above for complete path, requirement, calculation and concurrency history.

## 15. Premature Complexity Review

| Structure | Classification | Reasoning |
|---|---|---|
| Stable Playbook/Module/Lesson identities and immutable published revisions | REQUIRED NOW | Editorial updates must not alter learner history. |
| Revision-specific Playbook recommendations and Module learning requirements | REQUIRED NOW | They define the core discovery and completion loop. |
| Practice Activity revisions, attempts and responses | REQUIRED NOW | Practice and persistence are core; attempts must preserve the activity seen. |
| Formula version governance and immutable saved results | REQUIRED FOUNDATION | Calculators are core, and financial outputs must be explainable/reproducible. Specific calculator inventory is still product-defined. |
| Immutable My Plan revisions and owner boundaries | REQUIRED NOW | Plan history is a confirmed product/architecture decision. |
| Notes anchored to exact revision; explainable completion evidence | REQUIRED NOW | Required learning support and historical context. |
| Human editorial review, source snapshots and publication history | REQUIRED FOUNDATION | Protects content quality and changing financial information. |
| Search projection of published content | REQUIRED NOW only to the extent approved UX requires basic discovery | A derived/rebuildable projection is sufficient; dedicated search infrastructure is not justified initially. |
| Learning Journey Context | REQUIRED FOUNDATION | Needed to preserve Playbook-origin and learning context; implement the minimal corrected representation. |
| Topic/category vocabulary and typed related-content links | FUTURE BUT SAFE TO MODEL | Useful for discovery ecosystem, but do not build a large taxonomy/graph before content needs it. |
| Dictionary Term/Definition revisions | FUTURE BUT SAFE TO MODEL | Explicitly future scope; lesson references may need lightweight terminology links before a full Dictionary. |
| Standalone reusable Scenario aggregate | PREMATURE / SHOULD DEFER pending boundary decision | Embedded snapshots meet current history needs unless scenarios have independent reuse/edit lifecycle. |
| Full generalized event ledger or generic audit table | PREMATURE / SHOULD DEFER | Durable publication, formula approval, plan revisions and awards are already specific histories; no need for an indiscriminate event store. |
| Enterprise CMS role matrix, custom authentication record graph | PREMATURE / SHOULD DEFER | Staff/account policy remains open; begin with minimum justified boundaries and adopt the chosen auth provider/model later. |
| Advanced analytics, knowledge graph, recommendation engine, subscription/payment, user-facing AI | FUTURE / OUT OF INITIAL SCOPE | Explicitly deferred product capabilities; must not drive initial model complexity. |
| Reusable Lesson/Practice authoring as a mandatory convention | FUTURE BUT SAFE TO MODEL | Structural capability exists, but reuse is not an approved requirement and Practice evidence semantics need clarification. |

The catalogue’s logical entity count is not a recommendation to create one physical table per conceptual term. The implementation should keep separately persisted records only where identity, lifecycle, ownership, query behavior or immutable history justify them.

## 16. Blocking Decisions

“Blocking” below means blocking a coherent Phase 5 handoff or the specific later implementation that needs the decision. Phase 5 is UI/UX design in the current roadmap; it does not authorize physical database implementation.

### Original blockers resolved in Phase 4B

- Journey Step now represents multiple ordered references and states.
- Requirement Evidence and Attempt-to-Calculation Result relationships now trace Practice → Lab Tool → completion evidence; whether one attempt may satisfy multiple requirements remains a policy decision.

### Blocking before affected implementation / production data

- **HIGH — Account deletion and retention:** define deletion/anonymization/retention by user-owned record class and backup expiry before production user data is collected. This is needed to prevent private financial history being retained or deleted inconsistently.
- **MEDIUM — Note anchor behavior:** define exact selection anchoring and fallback before notes/highlights are implemented, so annotations do not detach from their meaning.
- **MEDIUM — Calculation currency/precision:** define explicit currency/unit and precision/rounding snapshots before financial calculators are implemented.
- **MEDIUM — Scenario persistence boundary:** reconcile the architecture’s Scenario/Assumption domain with the database’s embedded snapshots before implementation to avoid two competing models.

### Non-blocking

- One versus multiple plans: the logical one-to-many model is valid without enforcing one active plan. Decide before final plan-selection UX or an active-plan uniqueness constraint.
- Achievement thresholds, award deduplication and revocation: unresolved product mechanics can remain placeholders; decide before enabling award issuance.
- Carry-forward rules when new Module revisions change requirements: old completion remains valid for its old revision; policy is needed only before presenting cross-revision equivalence.
- Whether one accepted Practice Attempt may satisfy multiple requirements remains a completion-policy decision; the evidence model can represent each exact association.
- Staff role separation, author/approver separation, account registration/authentication and age policy: retain their existing TODO status; resolve for the relevant account/editorial implementation, without inventing product/legal rules.

### Future product decisions

- Full Dictionary lifecycle and terminology governance.
- Whether saved user scenarios need their own independently editable/reusable identity.
- Advanced content relationship graph, recommendations, analytics, payments/subscriptions, or user-facing AI.

## 17. Recommended Corrections

Recommendations R1 and R2 were reconciled in Phase 4B; remaining recommendations are outside that targeted correction and remain open as stated.

| ID | Severity | Recommendation | Why it is needed |
|---|---|---|---|
| R1 | RESOLVED | Added ordered Journey Step with typed exact targets, state/time and owner context. | Preserves multiple historical activities without copying targets or adding a field per step type. |
| R2 | RESOLVED (policy open) | Added optional zero-to-many Attempt→Calculation Result links and Requirement Evidence linking exact attempt to exact requirement and Module Revision. | Traces Practice→Lab Tool→Plan and explains completion without inventing the multiple-requirement acceptance rule. |
| R3 | MEDIUM | Define result-level currency/unit plus the immutable precision/rounding/method policy needed to reproduce monetary outputs; state whether approval state/time is snapshotted or deterministically reconstructed from approval history. | Identical inputs must remain interpretable under the exact formula and monetary conventions used. |
| R4 | MEDIUM | Specify Note anchor data (block identity plus quote/range/context strategy) and behavior when selection text cannot be found. Keep the anchor pinned to the original Lesson Revision. | A block-only reference may not identify the highlighted passage, and silent retargeting would damage user annotations. |
| R5 | MEDIUM | Reconcile standalone Scenario/Assumption domain wording with embedded immutable snapshots in Practice, journey, calculation and plan records. Record whether no independent Scenario entity is intended for the initial model. | Avoids contradictory ownership and lifecycle assumptions without creating an unnecessary aggregate. |
| R6 | MEDIUM | Define whether Media Asset references pin immutable asset versions/bytes or whether replacing media may change historical rendering; prefer immutable references for content where the image is part of the historical meaning. | A stable editorial revision can otherwise display a different cover/diagram after its asset is replaced. |
| R7 | HIGH (production gate) | Approve account deletion, anonymization, retention and backup-expiry behavior per user-owned record class before production data collection. | Plans and calculations can contain sensitive financial context, while achievements/audit references can outlive their owner unless governed deliberately. |
| R8 | MEDIUM | Define completion/evidence idempotency and stale Plan Revision write behavior before implementation. | Prevents duplicate evidence and silent concurrent edits from corrupting explainability/history. |

## 18. Phase 5 Readiness

The original audit verdict applied before Phase 4B. Its two HIGH findings are documented as resolved and reconciled across the logical model. The current focused readiness verdict is in [DATA_MODEL_RECONCILIATION.md](DATA_MODEL_RECONCILIATION.md). No physical implementation is authorized.
