# Future Implementation Notes

This document is a translation guide only. Phase 4 creates no application code, models, migrations, SQL, database, or dependencies.

## 1. Authority and boundary

The logical contract is in DOMAIN_MODEL.md, ENTITY_CATALOG.md, RELATIONSHIPS.md, FIELDS.md, CONSTRAINTS_AND_INDEXES.md, VERSIONING.md, DATA_LIFECYCLE.md and OWNERSHIP_AND_PRIVACY.md. If a specification is marked Proposed or TODO/TO-BE-DEFINED, implementation must not silently choose it as a product rule. Resolve it with the owner or record an explicit decision first.

## 2. Translation guidance for Django/PostgreSQL phase

- Use domain-owned application services for cross-domain writes; a shared relational database does not permit bypassing ownership or lifecycle rules.
- Stable editorial identity and immutable revision snapshots should remain distinct. Use database constraints where practical for identity/revision uniqueness and relationships; enforce richer state transitions in domain services and verify them transactionally.
- Pin every learner reference to exact editorial revision IDs. Do not resolve historical user data through only a mutable current-publication pointer.
- Represent Learning Journey as an owner-scoped identity plus ordered, append-only Journey Steps. Use an allow-listed typed target kind/reference; validate exact revision targets and same-owner private targets. Do not add one physical column for each step type, and do not copy the referenced record's content into the step.
- Represent Practice requirement satisfaction as Requirement Evidence identifying the exact Module Revision, requirement, Practice Revision, submitted Attempt, owner, state and timestamps. Module Completion must cite the selected evidence for each requirement; it must not infer evidence from matching timestamps or current content.
- A Practice Attempt can have zero or many same-owner saved Calculation Results. Each result remains immutable and formula-pinned; no calculation is mandatory, and an old result is never regenerated from the current Formula Version.
- Treat lesson blocks and input/assumption/output/target snapshots as typed, versioned values. Validate against an allow-listed schema; do not execute arbitrary HTML, code or user formulas.
- Keep saved Plan Revisions, Calculation Results, Formula Versions, approval actions, source snapshots and publication/review events immutable/append-only at the domain boundary.
- Make owner-scoped queries explicit in every use case; never take owner identity from submitted fields. Add database constraints for same-owner relations where feasible, and authorization tests across direct/nested/query paths.
- Search is a rebuildable projection of public published content. It is not canonical and does not include learner data.
- Respect future content-block and formula version compatibility. A code migration must not alter historical formula outputs or silently migrate note anchors.

## 3. Physical questions reserved for later phase

TODO/TO-BE-DEFINED: concrete Django apps and model boundaries; UUID/integer key choice; exact native/JSON representation; data precision and currency/unit encoding; physical representation/integrity strategy for Journey Step typed targets; foreign-key delete behavior; same-owner relation enforcement strategy; partial/conditional unique constraints; database transaction boundaries; formula artifact binding; content revision rendering fallback; full-text search configuration; media persistence; account credential records; soft/hard deletion; retention; export; backup implications; schema migration rollout and rollback. The curriculum rule for one attempt satisfying multiple requirements remains a product/completion-policy decision.

## 4. Verification work belongs to implementation/testing phases

Future work should verify revision immutability, state transitions, ordered journey references and typed-target integrity, exact Practice Requirement Evidence, zero/one/multiple calculation-result links, one-active-formula invariant, deterministic calculations from snapshots, module completion explanation, cross-account isolation, safe content payload validation, provenance preservation, and all DATA_FLOWS.md scenarios. This list defines design risks to cover later; no tests are created or run in Phase 4B.
