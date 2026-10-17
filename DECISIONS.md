# MaliLab Decisions

This file records material product, architectural, technical, security, and operational decisions. Product entries capture owner-approved direction. Phase 3 architecture decisions marked Accepted incorporate the owner's approval and required refinements; they do not authorize application implementation or infrastructure changes. Proposed ideas and unresolved questions are not accepted decisions.

## Decision record format

- **ID and title:** Stable identifier and concise subject.
- **Status:** Proposed, Accepted, Superseded, or Rejected.
- **Date:** Date recorded or decided.
- **Context:** Requirements and constraints.
- **Decision:** The selected direction.
- **Rationale:** Why it fits the known requirements.
- **Consequences:** Benefits, costs, risks, and follow-up work.
- **References:** Related product or decision documents.

Preserve superseded records and link them to replacements. Record options and owner approval for future material decisions.

## Accepted product direction

### PROD-001 — Kenyan financial research-and-learning environment

- **Status:** Accepted product direction; Phase 3 architecture subsequently approved with refinements.
- **Date:** 2026-10-07
- **Context:** Master specification defines MaliLab's meaning, mission, and Kenyan context.
- **Decision:** MaliLab is a Kenyan financial research-and-learning environment helping people study how money works in Kenya, experiment with their circumstances, understand what the ecosystem can support, and develop a practical financial-freedom direction.
- **Rationale:** This captures the owner's stated product concept and distinguishes it from a finance blog or generic course platform.
- **Consequences:** Content and examples must be grounded in Kenyan context. Specific validated user problems remain to be researched.
- **References:** `docs/product/VISION.md`, `docs/product/USERS.md`

### PROD-002 — Playbook-led, exploratory learning model and initial scope

- **Status:** Accepted product direction; detailed behaviors remain open.
- **Date:** 2026-10-07
- **Context:** The master specifies Playbooks, Modules, Lessons, Practice, My Plan, and supporting learning systems.
- **Decision:** The initial core loop is Playbook → Module → Lesson → Practice → Lab Tool → My Plan → Progress. Initial scope also includes minimum necessary Notes, user account/persistence, learning achievement support, and basic discovery/search where required by approved UX. The full Dictionary, advanced analytics, sophisticated recommendations, large-scale knowledge graph, advanced AI user assistant, subscriptions/payments, and voice/audio are future or out of scope. Discovery is Playbook-led and exploration is not restricted to one rigid path.
- **Rationale:** Connects relevant situations to structured learning and personal application.
- **Consequences:** Relationships and scope boundaries are documented in `docs/product/PRODUCT_MODEL.md`; detailed interactions and account implementation remain for later definition.
- **References:** `docs/product/PRODUCT_MODEL.md`, and the related concept specifications under `docs/product/`

### PROD-003 — Educational, exploratory financial content

- **Status:** Accepted product direction.
- **Date:** 2026-10-07
- **Context:** The master requires distinction between education, hypothetical scenarios, calculations, assumptions, and personal decisions.
- **Decision:** MaliLab must not guarantee financial outcomes. Tools and content expose assumptions and limitations where relevant; current regulatory, tax, rate, availability, and institutional content should support source attribution and review.
- **Rationale:** Keeps exploratory learning distinct from promised outcomes and supports responsible treatment of changing information.
- **Consequences:** Detailed editorial review, sourcing, and legal/regulatory requirements remain TODO/TO-BE-DEFINED; no Kenyan regulatory requirements are inferred here.
- **References:** `docs/product/PRACTICE.md`, `docs/product/LAB_TOOLS.md`, `docs/product/CONTENT_SYSTEM.md`

### PROD-004 — Internal content-production AI; human review

- **Status:** Accepted product direction.
- **Date:** 2026-10-07
- **Context:** The master identifies AI as internal research and content-production assistance, not the product identity.
- **Decision:** AI may assist with supplied research and scenario-based drafts; AI-generated content requires human review before publication. A general user-facing chatbot is not required. Voice/speaker interaction is out of scope.
- **Rationale:** Preserves owner-directed use of AI while retaining human publication review.
- **Consequences:** Tools, data-handling rules, and authoring workflow remain undecided.
- **References:** `docs/product/CONTENT_SYSTEM.md`

### PROD-005 — Free initial phase; subscription later

- **Status:** Accepted product direction; timing and terms unresolved.
- **Date:** 2026-10-07
- **Context:** The master states a future monthly subscription intention, excludes payment implementation from the initial build, and says the first phase should be free for observation.
- **Decision:** Do not implement subscription or payments in the initial build. Preserve future subscription/entitlement readiness as a product consideration without selecting architecture.
- **Rationale:** Supports initial observation before monetization while retaining the stated future intention.
- **Consequences:** Meaning of “first phase,” free-scope boundaries, pricing, and future terms require owner definition.
- **References:** `docs/product/MONETIZATION.md`

### PROD-006 — Reading and interactive learning only; no audio functionality

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** The library-like experience description was ambiguous alongside the explicit voice/speaker exclusion.
- **Decision:** MaliLab is an editorial reading and interactive learning platform. It has no speaker button, voice conversation, text-to-speech, podcast/audio lesson requirement, voice learning mode, or audio-first lesson format. “Reading/listening-library feel” refers only to an organized, curated book/story/library experience and does not imply audio functionality.
- **Rationale:** Applies the owner's explicit clarification and resolves the earlier ambiguity.
- **Consequences:** Product and UI language must not imply audio capability.
- **References:** `docs/product/LESSONS.md`, `docs/product/CONTENT_SYSTEM.md`, `PROJECT.md`

### PROD-007 — Three-month horizon is not a deadline or promise

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** The master specified an approximate three-month outcome; the owner refined its interpretation.
- **Decision:** Approximately three months is an intended learning horizon for a sufficiently engaged user to reach the point of constructing and investigating a personal financial-freedom direction. It is not a required completion period, deadline, or promise of achieving financial freedom.
- **Rationale:** Preserves the intended horizon without guaranteeing a financial result.
- **Consequences:** The product outcome is the user's ability to define a target, timeframe, assumptions, and possible path based on their circumstances. “Meaningful engagement” evaluation remains open.
- **References:** `docs/product/VISION.md`, `docs/product/PRODUCT_MODEL.md`

### PROD-008 — User-defined financial freedom

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** Users have different circumstances and goals; the product must not impose a universal definition.
- **Decision:** Each user defines what financial freedom means for them. MaliLab supports quantifying and investigating that target using relevant assumptions such as current and desired income, savings/contributions, timeframe, investment assumptions, inflation, and income changes. Examples are illustrative, not an exhaustive or prescriptive taxonomy.
- **Rationale:** Makes personal context central to My Plan and Lab Tool exploration.
- **Consequences:** Outputs remain educational and exploratory, not guaranteed financial advice or outcomes.
- **References:** `docs/product/VISION.md`, `docs/product/PRACTICE.md`, `docs/product/MY_PLAN.md`, `docs/product/LAB_TOOLS.md`

### PROD-009 — Conceptual learning achievement and evidence

- **Status:** Accepted at conceptual level; detailed rules unresolved.
- **Date:** 2026-10-07
- **Context:** The owner retained Module completion plus a practical plan attempt as meaningful learning achievement while deferring badge mechanics.
- **Decision:** Module completion conceptually means completing the intended learning for a Module. A practical plan attempt means constructing and investigating a personal target, timeframe, assumptions, and possible path. The product should preserve evidence of completed intended learning and the user's plan attempt, with relevant Lesson/Practice/Tool context where applicable.
- **Rationale:** Preserves evidence of study and personal application rather than treating clicks alone as learning.
- **Consequences:** Initial scope includes a minimal persistent Progress/achievement record. Detailed thresholds, evidence representation, and Badge award mechanics remain TODO/TO-BE-DEFINED.
- **References:** `docs/product/PROGRESS.md`, `docs/product/MODULES.md`, `docs/product/MY_PLAN.md`

## Unresolved product decisions

These are open questions, not accepted decisions:

- TODO/TO-BE-DEFINED: Define validated priority users/problems and how “meaningful engagement” and the intended learning outcome will be evaluated; the three-month horizon is not a deadline.
- TODO/TO-BE-DEFINED: Define the minimum Playbook, Module, Lesson, Practice, and My Plan behaviors and their relationships, optionality, and sequencing.
- TODO/TO-BE-DEFINED: Define detailed completion/attempt thresholds, Progress representation, and Badge mechanics; retain the conceptual definitions and evidence requirements in `PROGRESS.md`.
- TODO/TO-BE-DEFINED: Define detailed age/eligibility policy and per-feature privacy/user-control behavior for persisted Notes, Practice, Lab Tool scenarios, My Plan, and achievements. Core authentication and hybrid account deletion direction are approved under DB-019.
- TODO/TO-BE-DEFINED: Define initial Lab Tool catalogue, formulas, assumptions, sources, and review responsibilities.
- TODO/TO-BE-DEFINED: Define exactly where basic search is needed in the approved UX.
- TODO/TO-BE-DEFINED: Define any required supporting Dictionary references for the core loop; the full Dictionary remains future scope.
- TODO/TO-BE-DEFINED: Define content sourcing, editorial approval, review cadence, and treatment of changing financial information.
- TODO/TO-BE-DEFINED: Define whether and how product measurement is approved; advanced analytics remain future scope, with consent and privacy requirements unresolved.
- TODO/TO-BE-DEFINED: Define the duration of the initial free phase and future subscription terms.
- TODO/TO-BE-DEFINED: Confirm priority languages, accessibility needs, and supported user contexts.

Phase 2 Product Definition and Phase 3 architecture (with required refinements) were approved by the owner. Phase 3 approval does not authorize implementation or deployment.

## Phase 3 architecture decisions and status

### ARC-001 — Modular monolith

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** The initial product has related editorial, learning, calculator, plan, and progress workflows without evidence for independent service scaling or teams.
- **Decision:** Use one modular application with explicit domain boundaries and one deployment initially. Do not create microservices or a distributed event bus.
- **Rationale:** Keeps transactions and operations simple while preserving domain ownership and future evolution.
- **Consequences:** Requires disciplined internal boundaries; extraction remains possible only when demonstrated need justifies cost.
- **Alternatives:** Service-oriented/microservices and event-driven architecture are deferred due to operational and transactional complexity without an initial use case.
- **References:** `docs/architecture/SYSTEM_ARCHITECTURE.md`, `docs/architecture/DOMAIN_ARCHITECTURE.md`

### ARC-002 — Django server-rendered web application

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** Content-heavy mobile-first reading, account forms, internal editorial administration, and no approved native/external client.
- **Decision:** Use Django for a server-rendered application with progressive enhancement and internal application services; no SPA or public API-first architecture initially.
- **Rationale:** Provides integrated web/auth/admin/ORM/form capabilities suited to editorial workflows and limits client-side operational complexity.
- **Consequences:** Views/templates must remain presentation adapters; domain services prevent framework coupling. Supported language/framework versions are selected at implementation time.
- **Alternatives:** FastAPI/Flask require more assembly for editorial/admin flows; SPA/API adds another application layer without approved need.
- **References:** `docs/architecture/TECHNOLOGY_DECISIONS.md`, `docs/architecture/FRONTEND_ARCHITECTURE.md`, `docs/architecture/API_ARCHITECTURE.md`

### ARC-003 — PostgreSQL relational source of truth

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** Content relationships, immutable revisions, user ownership, plan/scenario snapshots, and transactions are central.
- **Decision:** Use PostgreSQL as the initial authoritative database; keep relationships relational and use validated structured block payloads where appropriate.
- **Rationale:** Strong relational integrity and transaction support, useful full-text search, and JSON support without requiring a document/graph database.
- **Consequences:** Requires database operations/backups; physical models, fields, indexes, and migrations remain later work.
- **Alternatives:** SQLite is not the production-parity target; MySQL is viable but offers no decisive requirement advantage; a document store weakens relational linking.
- **References:** `docs/architecture/DATA_ARCHITECTURE.md`, `docs/architecture/TECHNOLOGY_DECISIONS.md`

### ARC-004 — Versioned structured editorial content

- **Status:** Accepted with revision-scoped learning requirements and source snapshots.
- **Date:** 2026-10-07
- **Context:** Lessons need flexible block structure and edits must not destroy historical user learning context.
- **Decision:** Give each authored item a stable identity and immutable revision snapshots; publish an approved revision pointer; store lesson content as validated typed blocks rendered by allow-listed components. Preserve source provenance snapshots and review actor/time with each reviewed revision. Module revisions pin their ordered learning relationships and requirement classifications.
- **Rationale:** Supports flexible editorial composition, safe rendering, sources, and historical Notes/Progress references.
- **Consequences:** Requires content revision lifecycle, schema evolution, migration/fallback policy, and preview/version-aware UI.
- **Alternatives:** Mutable single-document content can erase history; arbitrary HTML is unsafe; one record per paragraph is overly rigid/fragmented.
- **References:** `docs/architecture/CONTENT_ARCHITECTURE.md`, `docs/architecture/DATA_ARCHITECTURE.md`

### ARC-005 — Deterministic versioned calculation service

- **Status:** Accepted with formula activation evidence gate.
- **Date:** 2026-10-07
- **Context:** Calculators must expose inputs, assumptions, formulas/methodology, outputs, limitations, and calculation date; results must be deterministic and testable.
- **Decision:** Keep formula logic in a dedicated in-process calculation domain/service; use the lifecycle Draft → Tested → Reviewed → Approved → Active → Retired; only activate a version after retaining its definition, assumptions, test cases and expected results, source/reference, reviewer, approval timestamp, and version identifier. Validate explicit inputs and preserve reproducible input/assumption/result snapshots and calculation timestamp.
- **Rationale:** Makes results explainable and independent of UI; prevents silent formula changes and client-side trust.
- **Consequences:** Exact formulas/catalogue and test implementation remain for later phases; code existence alone never activates a formula. Historical results remain tied to their formula version and assumptions.
- **Alternatives:** UI-embedded/client-only formula logic risks duplication and tampering; user-supplied formula execution is rejected.
- **References:** `docs/architecture/DOMAIN_ARCHITECTURE.md`, `docs/architecture/DATA_ARCHITECTURE.md`, `docs/architecture/TECHNOLOGY_DECISIONS.md`

### ARC-006 — Preserve plan revisions and learning evidence

- **Status:** Accepted: immutable plan revision snapshots and one-way Progress consumption.
- **Date:** 2026-10-07
- **Context:** My Plan and achievement evidence must preserve the user's assumptions and relevant learning context over change.
- **Decision:** Every saved My Plan edit creates an immutable Plan Revision snapshot with a predecessor reference and, where applicable, references to target/assumptions, Practice attempt, calculation result/formula version, learning context, and Playbook/Module/Lesson revisions. Learning and planning domains produce facts/evidence; Progress consumes them one way and is not required for My Plan to function.
- **Rationale:** Prevents updates from erasing prior thinking and makes learning status explainable.
- **Consequences:** Preserves historical comparability without recalculating old results; exact fields, comparison UI, plan cardinality, deletion, and evidence thresholds remain unresolved.
- **Alternatives:** Overwrite-in-place without history is insufficient for the approved evidence requirement.
- **References:** `docs/architecture/DATA_ARCHITECTURE.md`, `docs/architecture/DOMAIN_ARCHITECTURE.md`

### ARC-007 — No initial shared cache or background queue

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** No initial product workflow requires delayed processing, scheduled work, or demonstrated high read load.
- **Decision:** Start without Redis/cache broker or worker; use synchronous domain calls and database transactions.
- **Rationale:** Avoids operational components without an evidenced workload.
- **Consequences:** Slow/retryable workflows must be kept out of request path if later added; add worker only with idempotency/monitoring design.
- **Alternatives:** Celery/RQ/Redis or cloud queues are deferred until a real workload exists.
- **References:** `docs/architecture/SYSTEM_ARCHITECTURE.md`, `docs/architecture/TECHNOLOGY_DECISIONS.md`

### ARC-008 — PostgreSQL search initially

- **Status:** Proposed candidate; validation required before implementation acceptance.
- **Date:** 2026-10-07
- **Context:** Initial discovery needs search only where UX requires it; no scale or multilingual evidence justifies a search cluster.
- **Decision:** Keep PostgreSQL full-text search/filters as the initial candidate over a rebuildable projection of currently published content. Validate representative English, Kenyan financial terms, spelling variants, abbreviations, and natural user phrasing before accepting it. Exclude private user data and drafts.
- **Rationale:** Low operations burden and canonical content remains the source of truth.
- **Consequences:** Dedicated search is deferred unless tuned PostgreSQL search cannot meet approved relevance/language goals or measured latency/index load exceeds approved targets; retain an adapter/projection boundary for replacement.
- **Alternatives:** OpenSearch/Elasticsearch/hosted search deferred until measurable limitations.
- **References:** `docs/architecture/CONTENT_ARCHITECTURE.md`, `docs/architecture/TECHNOLOGY_DECISIONS.md`

### ARC-009 — Same-origin capability interfaces, no public API-first surface

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** Approved product has no native app, partner, or external API consumer.
- **Decision:** Render browser routes server-side and expose narrow same-origin JSON operations only for interactions that need them; domain calls use internal service interfaces. Reader routes call a content-access policy boundary; initial access is free without subscription/payment entitlement checks, and future entitlement rules can be added behind that boundary.
- **Rationale:** Avoids freezing a public contract and avoids one endpoint per entity.
- **Consequences:** A future external/mobile client will require a separately designed/versioned API adapter.
- **Alternatives:** REST/GraphQL API-first is deferred absent a consumer.
- **References:** `docs/architecture/API_ARCHITECTURE.md`

### ARC-010 — Initial asset storage via adapter; no media pipeline

- **Status:** Proposed; local storage conditional on capacity and backup validation.
- **Date:** 2026-10-07
- **Context:** Editorial covers and illustrations may be needed, but no audio, user uploads, or advanced media transformations are specified.
- **Decision:** Keep asset identity separate from storage location and initially use persistent local media storage if capacity/backup checks permit. Keep an adapter path to object storage.
- **Rationale:** Simple for a small single-host deployment while allowing migration.
- **Consequences:** Requires separate backup/capacity checks; multi-node/availability needs may require object storage/CDN.
- **Alternatives:** DB blobs and a complex media pipeline are not justified; object storage remains viable if hosting requirements favor it.
- **References:** `docs/architecture/CONTENT_ARCHITECTURE.md`, `docs/architecture/DEPLOYMENT_ARCHITECTURE.md`

### ARC-011 — Minimal session authentication and owner-scoped authorization

- **Status:** Accepted; authentication and staff-policy refinements recorded in DB-019.
- **Date:** 2026-10-07
- **Context:** User accounts and persistence are in approved initial scope; private financial plans/notes require isolation.
- **Decision:** Use framework-supported same-origin session authentication and enforce per-account ownership in application services on every private-data path. Require cross-account authorization tests before release. PostgreSQL RLS is not required initially because the trusted Django application is the sole controlled DB access path; reconsider if independent services/direct DB consumers are introduced. Do not add an external identity provider or API token system initially.
- **Rationale:** Aligns with a server-rendered web application and minimizes custom credential/security code.
- **Consequences:** Email/password, verified email, recovery, custom user identity, staff MFA/roles, approval separation, and hybrid account lifecycle are specified in DB-019. Age/eligibility remains TODO. User data remains owner-scoped and subject to controlled deletion/export.
- **Alternatives:** Managed identity provider deferred pending verified need; custom authentication rejected.
- **References:** `docs/architecture/SECURITY_ARCHITECTURE.md`, `docs/architecture/API_ARCHITECTURE.md`

### ARC-012 — Isolated conventional Linux deployment design

- **Status:** Accepted isolation principle; physical host topology Deferred to deployment phase.
- **Date:** 2026-10-07
- **Context:** Target environment is Oracle Linux 9 x86_64; legacy deployment must remain untouched.
- **Decision:** Design a separate Django process behind a reverse proxy, private PostgreSQL, and persistent media on a dedicated application configuration/data path; use a host-native process supervisor if the later deployment review confirms suitability.
- **Rationale:** Fits the environment without orchestration complexity and establishes strong separation from the legacy application.
- **Consequences:** CPU, memory, disk, DB, media, backup, and restore capacity must be validated. Establish off-host backups and validate database+media restoration before production data is considered safe. Host placement, proxy reuse, DB placement, staging, and rollback remain deferred; no service or proxy configuration is authorized now.
- **Alternatives:** Containers/orchestration or managed DB may be reconsidered if operations/availability needs justify cost.
- **References:** `docs/architecture/DEPLOYMENT_ARCHITECTURE.md`, `docs/architecture/SCALABILITY.md`

### ARC-013 — Human-reviewed internal AI draft workflow only

- **Status:** Accepted human-review workflow; provider integration Deferred.
- **Date:** 2026-10-07
- **Context:** AI is internal content-production assistance and human review before publication is required.
- **Decision:** AI output, if generated, enters the normal marked-draft → human review → revision → approval → publication workflow. Preserve supplied source/provenance and generation context with the draft where available. No auto-publish, user-facing advisor, or learner data transfer. Provider integration is optional and may remain manual initially.
- **Rationale:** Keeps editorial provenance and accountability; avoids an unnecessary external data dependency.
- **Consequences:** Provider/data terms and provenance fields need approval before integration.
- **Alternatives:** Autonomous pipeline and user-facing chatbot are excluded from initial architecture.
- **References:** `docs/architecture/AI_CONTENT_PRODUCTION.md`, `docs/architecture/CONTENT_ARCHITECTURE.md`

### ARC-014 — Versioned Module learning requirements

- **Status:** Accepted at conceptual level; item completion semantics TODO/TO-BE-DEFINED.
- **Date:** 2026-10-07
- **Context:** Progress must explain completion against the Module revision the learner studied.
- **Decision:** Each Module revision carries a learning-requirement set classifying Lessons and Practice activities as required, optional, or recommended. Recommended Practice is a supported relationship label; no particular activity is required to use it. Completion is evaluated against that exact revision: all required items meet their approved item-level condition; optional/recommended items do not block completion. Progress identifies satisfied and outstanding requirements.
- **Rationale:** Preserves meaning when curriculum/order changes and explains why a Module is considered complete without arbitrary percentages.
- **Consequences:** Final completion conditions and physical representation remain later decisions; changed requirements create a new Module revision.
- **References:** `docs/architecture/CONTENT_ARCHITECTURE.md`, `docs/architecture/DATA_ARCHITECTURE.md`, `docs/architecture/DOMAIN_ARCHITECTURE.md`

### ARC-015 — Historical learning journey context

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** A learner may enter through a specific Playbook and follow a revision-specific Module recommendation.
- **Decision:** Preserve a Learning Journey Context referencing the exact Playbook revision, the Playbook→Module recommendation followed, relevant scenario/assumption context, and relevant Module/Lesson revisions. Practice attempts, Plan Revisions, and Progress evidence may reference it. Do not copy Playbook content into user-owned records.
- **Rationale:** Keeps the origin and meaning of historical learning/planning interpretable after editorial updates.
- **Consequences:** Logical identity is specified in Phase 4; physical representation and retention remain implementation/data-lifecycle decisions. Editorial source content remains independently versioned.
- **References:** `docs/architecture/CONTENT_ARCHITECTURE.md`, `docs/architecture/DATA_ARCHITECTURE.md`

### ARC-016 — Immutable My Plan revisions and one-way Progress

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** Users must preserve historical financial thinking and Progress must explain learning without coupling plan operations to a status service.
- **Decision:** Every saved plan edit creates an immutable snapshot linked to its predecessor. Snapshots may reference relevant Practice, Calculation Result and Formula Version, learning context, and Playbook/Module/Lesson revisions. Learning/Practice/My Plan produce facts/evidence; Progress consumes them one way. My Plan does not depend on Progress.
- **Rationale:** Enables comparison across previous/current assumptions and avoids circular domain dependencies.
- **Consequences:** Exact fields, cardinality, comparison UX, and deletion behavior remain unresolved; historical results are not silently recalculated.
- **References:** `docs/architecture/DATA_ARCHITECTURE.md`, `docs/architecture/DOMAIN_ARCHITECTURE.md`

### ARC-017 — Formula activation requires reviewable evidence

- **Status:** Accepted architecture gate; formula catalogue and calculation methods TODO/TO-BE-DEFINED.
- **Date:** 2026-10-07
- **Context:** Deterministic calculation alone does not establish correctness or safe release.
- **Decision:** Formula versions follow Draft → Tested → Reviewed → Approved → Active → Retired. Activation requires a version identifier, formula definition, assumptions, test cases and expected results, source/reference, reviewer, and approval timestamp. Results preserve formula version, assumptions/input snapshot, outputs, and calculation timestamp for reproducibility.
- **Rationale:** Prevents code presence or silent edits from changing calculations used by learners.
- **Consequences:** Test execution and approval workflow are later-phase work; each formula change creates a new version.
- **References:** `docs/architecture/DATA_ARCHITECTURE.md`, `docs/architecture/DOMAIN_ARCHITECTURE.md`, `docs/architecture/TECHNOLOGY_DECISIONS.md`

### ARC-018 — Revision-scoped source provenance snapshots

- **Status:** Accepted.
- **Date:** 2026-10-07
- **Context:** A mutable source catalog alone cannot prove which source details informed an older financial content revision.
- **Decision:** Each reviewed/published content revision preserves relevant source identity, URL/reference, title, publication date, retrieval/access date, source version/reference, and association to content, where applicable; it also preserves reviewer and review timestamp.
- **Rationale:** Historical content remains interpretable when source metadata or source documents change.
- **Consequences:** Exact representation and citation policy are specified conceptually in Phase 4 and remain editorial/implementation details; no regulatory requirement is inferred.
- **References:** `docs/architecture/CONTENT_ARCHITECTURE.md`, `docs/architecture/DATA_ARCHITECTURE.md`

### ARC-019 — Application-level owner checks; no initial PostgreSQL RLS

- **Status:** Accepted for initial architecture.
- **Date:** 2026-10-07
- **Context:** Sensitive user financial data is accessed through one trusted Django application in the initial modular monolith.
- **Decision:** Enforce owner-scoped authorization in application services on every user-data operation and require cross-account authorization tests before release. PostgreSQL row-level security is not required initially; reconsider if independent services or direct DB consumers are introduced.
- **Rationale:** Central application checks are mandatory; initial DB access is controlled, while RLS adds connection-context and administration complexity and does not replace application authorization.
- **Consequences:** Database remains private; tests cover cross-account detail/list/nested/update/delete and staff paths. RLS can be revisited if the access topology changes.
- **References:** `docs/architecture/SECURITY_ARCHITECTURE.md`, `docs/architecture/DATA_ARCHITECTURE.md`

### ARC-020 — Content-access policy boundary

- **Status:** Accepted; subscription/payment remains Deferred.
- **Date:** 2026-10-07
- **Context:** The current product is free, while future subscription is intended. Owner-approved reading policy permits anonymous published-content reading and requires an account for persistent personal features.
- **Decision:** Reader routes call one content-access policy boundary. Initial access is free and public published content is readable anonymously; persistence and personal features require an authenticated, email-verified account. No payment/subscription entitlement check is present; future entitlement rules can be added behind the boundary.
- **Rationale:** Preserves future access-policy evolution without implementing monetization now.
- **Consequences:** Private feature authorization remains owner-scoped; no billing or entitlement subsystem is created.
- **References:** `docs/architecture/DOMAIN_ARCHITECTURE.md`, `docs/architecture/API_ARCHITECTURE.md`

### ARC-021 — Search validation before accepting PostgreSQL candidate

- **Status:** Proposed candidate; validation TODO/TO-BE-DEFINED.
- **Date:** 2026-10-07
- **Context:** Basic discovery is in scope but exact search expectations and languages are not approved.
- **Decision:** Keep PostgreSQL full-text search/filters as the initial candidate and validate representative English, Kenyan terminology, spelling variants, abbreviations, and natural user phrasing. Consider dedicated search only if approved requirements or measured latency/index load remain unmet after tuning.
- **Rationale:** Avoids premature search operations while requiring product-relevant evidence before launch.
- **Consequences:** No search engine is selected, installed, or configured. Queries and acceptance thresholds remain open.
- **References:** `docs/architecture/DOMAIN_ARCHITECTURE.md`, `docs/architecture/TECHNOLOGY_DECISIONS.md`

### ARC-022 — Production data safety capacity and restore gate

- **Status:** Accepted requirement; host topology Deferred to deployment phase.
- **Date:** 2026-10-07
- **Context:** Initial environment is a single Oracle Cloud server with an existing legacy deployment; capacity and failure-domain details are unverified.
- **Decision:** Validate CPU, memory, disk, database, media, backup, and restore capacity before production. Establish off-host backups and validate restoration of database and media before production data is considered safe. Do not assume co-location on the existing host.
- **Rationale:** A single-host failure or untested backup could make user plans, editorial content, or media unrecoverable and could affect the legacy workload.
- **Consequences:** Physical host placement and recovery objectives remain deployment-phase decisions. No server changes occur in this refinement.
- **References:** `docs/architecture/DEPLOYMENT_ARCHITECTURE.md`, `docs/architecture/ARCHITECTURE_RISKS.md`

## Explicit prerequisites still TODO/TO-BE-DEFINED

Core account/auth, hybrid account deletion, staff roles/MFA/approval separation, KES-first numeric policy, revision-local note anchor rules, and initial one-attempt/one-requirement semantics are approved in DB-019. Remaining items are:

- **TODO/TO-BE-DEFINED:** Age/eligibility policy; obtain appropriate review without inventing legal obligations.
- **TODO/TO-BE-DEFINED:** Per-class deletion/export processing details and exact backup expiry schedule.
- **TODO/TO-BE-DEFINED:** Search validation queries, supported languages, and relevance acceptance criteria.
- **TODO/TO-BE-DEFINED:** Exact initial calculator catalogue, formula methods, numeric ranges/precision/rounding, and unit conventions per calculator.
- **TODO/TO-BE-DEFINED:** Detailed completion conditions/achievement award thresholds beyond the approved initial evidence rule.

## Architecture review state

Phase 2, Phase 3 and Phase 4 domain/logical data specification (including Phase 4B audit reconciliation) are approved. Phase 5 physical specifications are reconciled with owner decisions in DB-019; the updated physical audit is READY FOR PHASE 6. This is a readiness assessment only; explicit Phase 6 approval is still required before implementation.

## Phase 4 domain and logical data decisions

Statuses here describe the conceptual/logical specification, not physical implementation. Accepted means the domain rule is specified; Proposed means an option is documented but requires owner resolution; Deferred means later scope; TODO/TO-BE-DEFINED means no decision is made.

### DB-001 — Stable editorial identity and immutable revisions

- **Status:** Accepted for logical model.
- **Date:** 2026-10-07
- **Context:** Learner progress, notes, practice, and plans must retain historical content context.
- **Decision:** Playbook, Module, Lesson, and Practice Activity have stable editorial identities and immutable, independently referenceable revisions. Published updates create new revisions; publication/review history is durable.
- **Rationale:** Preserves the exact learning material that informed notes, attempts, plans and progress.
- **Consequences:** Physical revision storage, renderer compatibility, and retention remain later implementation decisions.
- **Alternatives:** Mutable current-only content was rejected because it loses historical meaning.
- **References:** `docs/database/VERSIONING.md`, `docs/database/ENTITY_CATALOG.md`

### DB-002 — Revision-scoped curriculum and recommendation links

- **Status:** Accepted for logical model.
- **Date:** 2026-10-07
- **Context:** Playbook recommendations and Module completion requirements must remain identifiable after editorial changes.
- **Decision:** Playbook–Module Recommendation belongs to a Playbook Revision and targets an exact Module Revision. Module Learning Requirement belongs to one Module Revision and targets an exact Lesson or Practice Activity Revision. Requirements are typed, ordered, and support required, optional, or recommended classifications for both target kinds; only required items block completion.
- **Rationale:** Lets editors revise discovery and curriculum without changing a learner's historic path or completion basis.
- **Consequences:** One Module can serve several Playbooks without copies. Old journey/completion records retain exact links. Detailed completion conditions remain TODO.
- **Alternatives:** Duplicating Modules per Playbook or storing requirements globally on a Lesson would create inconsistency or erase revision-specific meaning.
- **References:** `docs/database/DOMAIN_MODEL.md`, `docs/database/RELATIONSHIPS.md`

### DB-003 — Lesson identity reusable, reuse policy not required

- **Status:** Proposed logical capability; editorial reuse policy TODO.
- **Date:** 2026-10-07
- **Context:** Product says Lessons belong to Modules; architecture allows future reuse.
- **Decision:** Model Lesson identity independently from Module membership so a Lesson Revision can be referenced by multiple Module Revisions if approved. Do not duplicate a Lesson per Playbook/Module by default.
- **Rationale:** Retains the product's Lesson-in-Module experience while leaving a controlled reuse path.
- **Consequences:** Ordering and completion meaning remain Module-revision-owned. If strict one-Module ownership is later required, revise before physical implementation.
- **Alternatives:** Strict single-parent ownership is possible but would make later reuse require content duplication or redesign.
- **References:** `docs/database/DOMAIN_MODEL.md`, `docs/database/RELATIONSHIPS.md`

### DB-004 — Immutable Plan Revision snapshots

- **Status:** Accepted for logical model.
- **Date:** 2026-10-07
- **Context:** Historical financial thinking must remain comparable and reproducible.
- **Decision:** Every saved plan edit creates an immutable Plan Revision with predecessor reference where applicable and snapshots of target, assumptions, path, and exact Practice, Calculation, Formula, Learning Journey, Playbook, Module, and Lesson references where relevant.
- **Rationale:** Preserves changing financial thinking and allows historical comparison without recomputation.
- **Consequences:** One versus multiple plans, status semantics, fields, retention and deletion remain unresolved. No previous result is silently recalculated.
- **Alternatives:** Updating one mutable plan record was rejected because it erases prior assumptions.
- **References:** `docs/database/VERSIONING.md`, `docs/database/FIELDS.md`

### DB-005 — Evidence-based Progress records

- **Status:** Accepted conceptually; detailed evidence/criteria TODO/TO-BE-DEFINED.
- **Date:** 2026-10-07
- **Context:** Completion must be explainable and Progress consumes evidence without becoming an upstream dependency.
- **Decision:** Lesson Completion pins Lesson Revision; Module Completion pins Module Revision and preserves a per-required-item evidence/satisfied/missing explanation. Requirement Evidence links an exact submitted Practice Attempt and Practice Activity Revision to an exact Module Learning Requirement within an exact Module Revision. Progress consumes these records; My Plan does not depend on Progress.
- **Rationale:** Answers why completion is recorded and keeps Progress downstream of learning/planning facts.
- **Consequences:** Completion conditions, reevaluation/carry-forward, visibility and achievement thresholds are unresolved. No percentage is authoritative.
- **Alternatives:** A single mutable percentage or a Progress service required by plan writes was rejected as opaque and cyclic.
- **References:** `docs/database/DOMAIN_MODEL.md`, `docs/database/RELATIONSHIPS.md`, `docs/database/DATA_FLOWS.md`

### DB-006 — Formula and calculation snapshot governance

- **Status:** Accepted for logical model.
- **Date:** 2026-10-07
- **Context:** Calculation results must be deterministic and reproducible after formula changes.
- **Decision:** Formula Version has governed lifecycle and durable evidence-backed Formula Approval actions. Saved Calculation Result is immutable and pins formula version, inputs, assumptions, outputs, units, rounding/method, applicable source/warnings, and calculation timestamp.
- **Rationale:** A later formula release must not change or obscure a previously shown result.
- **Consequences:** Exact numeric representation, formula artifact binding and catalog remain TODO for implementation/product definition. Unsaved runs need not persist.
- **Alternatives:** Recomputing old results with the current formula was rejected.
- **References:** `docs/database/FIELDS.md`, `docs/database/VERSIONING.md`

### DB-007 — Revision-scoped source provenance and editorial history

- **Status:** Accepted for logical model.
- **Date:** 2026-10-07
- **Context:** A mutable source catalog is not sufficient to explain historical content.
- **Decision:** Preserve applicable source identity/title/URL/publication date/access date/version reference as a snapshot on reviewed revisions, with reviewer/time where applicable. Editorial review and publication actions are durable history.
- **Rationale:** Mutable catalog metadata alone cannot show which source version was reviewed at publication time.
- **Consequences:** Citation standards, review policy, and retention remain open; no legal obligation is inferred.
- **Alternatives:** Reference to the current Source record alone was rejected as insufficient provenance.
- **References:** `docs/database/VERSIONING.md`, `docs/database/DATA_LIFECYCLE.md`

### DB-008 — User ownership and no initial RLS

- **Status:** Accepted for initial logical architecture.
- **Date:** 2026-10-07
- **Context:** User financial information requires separation across accounts.
- **Decision:** User-owned entities carry one authoritative owner; every private relationship is same-owner validated. Application-level authorization is mandatory and PostgreSQL RLS is not required initially for the single trusted application access path.
- **Rationale:** Explicit ownership keeps user data isolated while avoiding database security complexity without multiple access paths.
- **Consequences:** Required cross-account tests and the hybrid account deletion/export lifecycle in DB-019 apply. Staff support access remains separately controlled. Revisit RLS if access topology changes.
- **Alternatives:** RLS remains a revisit option if direct or independent data access is introduced; it does not replace application checks.
- **References:** `docs/database/OWNERSHIP_AND_PRIVACY.md`, `docs/database/CONSTRAINTS_AND_INDEXES.md`

### DB-009 — Plan cardinality remains unresolved

- **Status:** TODO/TO-BE-DEFINED.
- **Date:** 2026-10-07
- **Context:** Product documents defer one-versus-multiple plans; account deletion/retention direction is now approved separately in DB-019.
- **Decision:** One-versus-multiple plan policy remains open. The logical and physical model permits zero or more plans per user and adds no one-plan or one-active uniqueness constraint.
- **Rationale:** Product documents defer plan cardinality; choosing now would invent product behavior.
- **Consequences:** Do not invent plan cardinality. Account deletion/retention is superseded by DB-019.
- **Alternatives:** One-plan and multiple-plan policies remain open for owner decision. Account deletion is governed by DB-019.
- **References:** `docs/database/DATA_LIFECYCLE.md`, `docs/database/CONSTRAINTS_AND_INDEXES.md`

### DB-010 — Search and Dictionary data remain bounded

- **Status:** Proposed search projection; Dictionary Deferred.
- **Date:** 2026-10-07
- **Context:** Initial discovery is required where approved UX needs it; full Dictionary is future scope.
- **Decision:** Search is a derived, rebuildable projection of approved published editorial revisions only. No personal financial data enters it. Dictionary Term/Definition Revision are future conceptual entities only.
- **Rationale:** Keeps canonical content authoritative and excludes speculative user/knowledge graph systems.
- **Consequences:** Search engine/configuration and validation remain open; do not instantiate Dictionary domain absent approval.
- **Alternatives:** Search as canonical content or as a user-data index was rejected; dedicated search remains conditional on evidence.
- **References:** `docs/database/DOMAIN_MODEL.md`, `docs/database/OWNERSHIP_AND_PRIVACY.md`

### DB-011 — Physical schema decisions deferred

- **Status:** Deferred to implementation phase.
- **Date:** 2026-10-07
- **Context:** Phase 4 is data design only.
- **Decision:** Do not specify SQL/Django field syntax, physical tables, database configuration, migrations, or persistence technology beyond approved PostgreSQL architecture.
- **Rationale:** Phase 4 authorizes domain and logical specification only.
- **Consequences:** Implementation must resolve physical questions in `docs/database/IMPLEMENTATION_NOTES.md` without changing accepted domain rules silently.
- **Alternatives:** Premature DDL/model design is excluded by the phase boundary.

### DB-012 — Learning Journey uses ordered historical steps

- **Status:** Accepted for logical model; physical target-reference representation deferred.
- **Date:** 2026-10-07
- **Context:** The Phase 4 audit found that a scalar Learning Journey Context could not preserve multiple later learning, calculation, and planning activities.
- **Decision:** Learning Journey Context is a learner-owned journey identity with zero or more ordered, append-only Journey Steps. Each step records an allow-listed type, typed reference to an exact editorial revision or same-owner user record, observed state, timestamps, and optional bounded context. Steps reference underlying records without copying them; new step types do not require a new column per type.
- **Rationale:** Preserves an ordered historical path from Playbook discovery through learning and plans while keeping data ownership in the referenced domains.
- **Consequences:** Exact type-target validation and owner checks are logical requirements. Physical referential-integrity strategy is deferred; account deletion must resolve private target references.
- **Alternatives:** Scalar context fields cannot represent repeated/branching steps; copied content duplicates editorial/user-owned data; an unrestricted event ledger is not required.
- **References:** `docs/database/DOMAIN_MODEL.md`, `docs/database/FIELDS.md`, `docs/database/RELATIONSHIPS.md`, `docs/database/VERSIONING.md`

### DB-013 — Practice evidence and optional calculation links are explicit

- **Status:** Accepted for logical model; initial one-attempt/one-requirement policy approved in DB-019.
- **Date:** 2026-10-07
- **Context:** The Phase 4 audit found no explicit relationship from Practice Attempt to saved Calculation Result or to the exact Module requirement it may satisfy.
- **Decision:** Requirement Evidence links one exact submitted Practice Attempt and its Practice Activity Revision to one exact Module Learning Requirement within one exact Module Revision, with learner, state and timestamps. Module Completion snapshots the evidence selected for each requirement. A Practice Attempt may have zero or more Requirement Evidence associations and zero or more saved Calculation Results. A Calculation Result optionally links to one same-owner Practice Attempt and remains immutable/formula-pinned.
- **Rationale:** Makes evidence lookup bidirectional and completion explainable, while supporting calculator-free practice and multiple saved calculations without recomputing prior results.
- **Consequences:** Only accepted evidence can satisfy a required item. Initially, one accepted attempt satisfies one requirement; no inferred multi-credit. The relation remains extensible for future explicit per-requirement evidence. Progress remains downstream; My Plan remains independent.
- **Alternatives:** Inferring links from timestamps/inputs or current content is ambiguous and unsafe; requiring every attempt to have a result would invent behavior.
- **References:** `docs/database/DOMAIN_MODEL.md`, `docs/database/RELATIONSHIPS.md`, `docs/database/CONSTRAINTS_AND_INDEXES.md`, `docs/database/DATA_MODEL_RECONCILIATION.md`

## Phase 4 approval and Phase 5 physical specification

### DB-014 — Phase 4 logical data model approved

- **Status:** Accepted by owner.
- **Date:** 2026-10-07
- **Context:** Owner explicitly stated that Phase 4 is formally approved and authorized Phase 5 physical implementation specification.
- **Decision:** Treat the domain/logical model, its audit, and reconciliation as approved authority for physical mapping. This supersedes stale roadmap text that said Phase 4 awaited review. It does not authorize Phase 6 implementation.
- **Rationale:** Phase gates must reflect the owner's latest explicit approval.
- **Consequences:** Phase 5 may document Django/PostgreSQL proposals only. Phase 6 still requires separate explicit approval and closure of blocking decisions.
- **References:** `docs/database/`, `docs/implementation/PHASE_5_AUDIT.md`

### DB-015 — Physical primary keys and persistence representation

- **Status:** Proposed; not owner-approved.
- **Date:** 2026-10-07
- **Context:** Phase 5 requires concrete Django/PostgreSQL mapping while Phase 4 left key and JSON/relational representation open.
- **Decision:** Propose PostgreSQL `bigint` internal primary keys, explicit relational foreign keys, `timestamptz`, and bounded schema-versioned JSONB for structured snapshots. Financial decimals in snapshots are canonical strings; standalone exact amounts use `numeric` only after precision/scale is defined. IDs do not grant access.
- **Rationale:** Fits a single PostgreSQL modular monolith, keeps ordinary references relational, and avoids floating-point financial drift.
- **Consequences:** Revisit UUIDs if external/cross-system identifiers become a requirement. JSONB needs strict versioned validation and size limits. Monetary precision and units remain blocking for calculator implementation.
- **References:** `docs/implementation/PHYSICAL_DATA_MODEL.md`, `FIELD_SPECIFICATIONS.md`

### DB-016 — Typed Learning Journey target adapter

- **Status:** Proposed; validate complexity before implementation.
- **Date:** 2026-10-07
- **Context:** Journey Steps must reference heterogeneous historical objects, remain FK-integrity protected, and avoid a new column on JourneyStep for every step kind.
- **Decision:** Propose JourneyStep → JourneyTargetRef and per-target one-to-one association records with concrete foreign keys. Do not use unrestricted Django GenericForeignKey. New target kinds add an association type, not a JourneyStep column.
- **Rationale:** Preserves exact target references and one stable step schema while avoiding unreferential generic IDs.
- **Consequences:** Typed subtype completeness and same-owner validation need transactional service rules/tests; relational join count and association complexity require review. A simpler alternative must preserve FK integrity.
- **References:** `docs/implementation/MODEL_SPECIFICATIONS.md`, `PHYSICAL_DATA_MODEL.md`

### DB-017 — Immutable physical media versions

- **Status:** Proposed.
- **Date:** 2026-10-07
- **Context:** Logical media replacement policy did not settle byte mutability; historical content must render against the asset reviewed/published with it.
- **Decision:** Treat each physical MediaAsset row/storage key as an immutable file version. Replacement creates a new asset row/key; referenced bytes cannot be overwritten/deleted.
- **Rationale:** Prevents a stable asset reference from silently serving changed bytes to old revisions.
- **Consequences:** Requires storage cleanup/rights policy and additional rows for replacements; backend and byte limits remain deferred.
- **References:** `docs/implementation/MEDIA_IMPLEMENTATION.md`, `VERSIONING_IMPLEMENTATION.md`

### DB-018 — Phase 6 implementation blockers remain open

- **Status:** Superseded by DB-019 (Phase 5C owner decisions).
- **Date:** 2026-10-07
- **Context:** The initial Phase 5 audit found unresolved account/auth, retention, staff governance, calculator numeric, note-anchor and completion-evidence policies.
- **Decision:** Historical record of the initial Phase 5 gate: those choices were left open pending owner review. This decision is superseded by DB-019.
- **Rationale:** These decisions determine security boundary, data destruction, financial correctness, annotation integrity, and learning completion meaning.
- **Consequences:** The initial NOT READY verdict was appropriate at that time. DB-019 resolves those six owner decisions and the reconciled Phase 5 audit supersedes that verdict. No code is authorized by this record.
- **References:** `docs/implementation/PHASE_5_AUDIT.md`

### DB-019 — Phase 5C implementation policies approved

- **Status:** Accepted by product owner.
- **Date:** 2026-10-07
- **Context:** The owner explicitly resolved all six blockers identified by the initial Phase 5 audit and authorized documentation reconciliation only.
- **Decision:** (1) Use a custom Django user/stable account identity with email/password, verified email required for full personal functionality, email recovery and Django server-side sessions; anonymous public reading is allowed and personal persistence requires a verified account; phone/OTP and social login are future, age/eligibility remains open. (2) Use a hybrid deletion lifecycle: disable access, controlled deletion/export, remove or anonymize identifiable user data by class, retain editorial data and only necessary/minimized audit history, handle backup expiry separately; no account-wide CASCADE; use protected/restricted relations and a dedicated service. (3) Staff roles are Author/Editor, Reviewer, Approver/Publisher, Administrator; staff MFA required; Administrator has no default financial-data access; author and approver differ for published financial content; formula activation requires second-person approval; edits after approval require new review/approval; preserve actor/role/exact revision/version/time. (4) KES-first extensible currency, explicit currency on every monetary value, initial KES support unless a calculator spec adds more, no implicit FX, decimal-safe arithmetic, distinct calculation/display precision and deterministic formula-specific rounding; rates/dates/durations/units explicit per formula; no universal precision/scale. (5) Notes use exact LessonRevision + stable ContentBlock ID + selected text quote + optional offset hints; offsets cannot move an anchor after text differs; no cross-revision auto-reanchor. (6) One accepted Practice Attempt satisfies one Module Requirement initially; each accepted evidence association is explicit, no inferred multi-credit, completion is against exact ModuleRevision, evidence does not carry forward, reassessment preserves history; physical model stays extensible for future explicit multi-requirement evidence.
- **Rationale:** These decisions establish secure identity/ownership, preserve deletion integrity and editorial audit, require accountable human publication/formula governance, and make personal calculations and learning evidence reproducible without inventing formula details.
- **Consequences:** The Phase 5 audit is updated to READY FOR PHASE 6. Readiness does not authorize implementation; separate Phase 6 approval is required. Age/eligibility, backup expiry, calculator catalog/ranges/precision/units and detailed note rendering remain scoped TODOs rather than blockers to the schema foundation.
- **References:** `docs/implementation/PHASE_5B_DECISION_BRIEF.md`, `docs/implementation/PHYSICAL_DATA_MODEL.md`, `docs/implementation/PHASE_5_AUDIT.md`, `docs/implementation/TRACEABILITY_MATRIX.md`

### GOV-001 — Phase 6A independent acceptance satisfies its acceptance gate

- **Status:** Accepted by owner; status-document maintenance remains incomplete where `PROJECT.md` conflicts.
- **Date:** 2026-10-13
- **Context:** The Phase 6A independent acceptance audit records acceptance, while `PROJECT.md` and roadmaps retained stale wording that fresh acceptance was still required. The owner explicitly ruled: “The existing Phase 6A independent acceptance audit satisfies the Phase 6A acceptance gate; reconcile the stale governing status documents using the authorized project process, but do not treat this decision alone as Phase 6B.5 implementation authorization.”
- **Decision:** Treat the existing independent audit as satisfying Phase 6A acceptance. Reconcile roadmap and phase-status records to that fact through this decision record, while preserving the separate requirement for explicit Phase 6B.5 implementation authorization. This decision alone is not that authorization.
- **Rationale:** Records the owner's explicit governance ruling and avoids repeating an already completed acceptance audit.
- **Consequences:** Roadmaps may acknowledge Phase 6A acceptance and Phase 6B planning, but `PROJECT.md` remains unchanged by task constraint and therefore retains contradictory current-status wording. Full governing-document status consistency is not claimed. The exact outstanding action is to update `PROJECT.md` §§1, 8, 17, and 18 through a separately authorized constitution-maintenance action. No Phase 6B.5 implementation is authorized.
- **References:** `PROJECT.md`; `ROADMAP.md`; `docs/implementation/ROADMAP.md`; `docs/implementation/PHASE_6A_INDEPENDENT_ACCEPTANCE_AUDIT.md`; `docs/implementation/PHASE_6B_PLAN.md`; `docs/implementation/PHASE_6B_5B_GOVERNANCE_GATE_RECONCILIATION.md`.

### GOV-002 — Phase 6B execution authorization

- **Status:** Accepted owner authorization.
- **Date:** 2026-10-13
- **Context:** Earlier Phase 6B planning and readiness records said implementation was not authorized. The owner has now issued the `MALILAB — PHASE 6B EXECUTION RECOVERY AND COMPLETION DIRECTIVE`, requiring implementation and verification through the existing Phase 6B plan, while preserving Phase 6A acceptance and existing architecture/schema boundaries.
- **Decision:** The directive explicitly authorizes application implementation and testing for the remaining planned Phase 6B slices. GOV-001 remains unchanged and Phase 6A acceptance is not reopened. Preserve existing models and migrations; any necessary schema or live-database change remains subject to the existing separate authorization rules. The directive does not authorize unrelated scope, production data changes, deployment changes, or weakening PostgreSQL configuration. Pending PRS recommendations are not reclassified as separately approved product policy unless the directive itself specifies the behavior.
- **Rationale:** Carry out the current owner instruction while retaining the project’s migration, security, and scope controls.
- **Consequences:** Historical readiness reports remain evidence of the earlier state. Current execution status must be assessed against actual code and tests; PostgreSQL verification and any consequential unresolved decisions remain explicit completion gates.
- **References:** `docs/implementation/PHASE_6B_PLAN.md`; `docs/implementation/PHASE_6B_5A_OWNER_DECISION_ADDENDUM.md`; current Phase 6B execution directive.
