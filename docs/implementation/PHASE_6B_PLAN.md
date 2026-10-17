# Phase 6B — User Experience Planning and Implementation Contract

**Status:** Planning artifact. All routes, screens, and implementation slices below are **PROPOSED** and require explicit owner approval before implementation. This document does not authorize code, schema, database, infrastructure, or product changes.

## 1. Purpose

Phase 6B turns the accepted Phase 6A Django/PostgreSQL domain foundation into MaliLab's first usable, server-rendered product experience. It should deliver a coherent path from public Playbook discovery through Modules and readable Lessons, then let an eligible account persist Practice and learning evidence. It is a learning library and applied-learning experience, not a finance blog, generic LMS, or promised path to a financial outcome.

## 2. Starting baseline

Phase 6A is accepted by `PHASE_6A_INDEPENDENT_ACCEPTANCE_AUDIT.md`: **PHASE 6A ACCEPTED — READY FOR PHASE 6B**. Treat the Phase 5 specifications, product documents, accepted implementation and acceptance audit as authoritative. Do not reopen or redesign them without concrete evidence of a blocking dependency.

The inspected application has seven domain apps: `accounts`, `content`, `practice`, `calculations`, `planning`, `learning`, and `discovery`. They contain models, services, migrations and tests. The only configured application URL is Django admin (`/admin/`). There are no user-facing templates, forms, or public routes yet. Settings use Django sessions and the custom email account; `UserAccount.can_use_personal_features` requires an active, verified account. Registration/recovery screens and delivery are absent.

Relevant service interfaces already present include editorial `submit_for_review`, `review_revision`, `approve_and_publish`; practice `create_attempt`, `save_response`, `submit_attempt`; learning `create_note`, `append_journey_step`, `record_requirement_evidence`, `evaluate_module_completion`; planning `create_plan`, `append_revision`; and discovery `rebuild_published_projection`. These are domain-service entry points, not view contracts. Editorial workflow UI is not part of the first release.

The content model has stable Playbook, Module, Lesson and Practice identities with revision records/current-published pointers; Module requirements and Playbook recommendations; a `LessonRevision.blocks` JSON field currently validated to paragraph blocks with UUID key, position, and text payload; source/provenance and related-content records; and immutable media metadata. It does not yet deliver media bytes. Learning has append-only journey/evidence/completion records, revision-pinned notes, and achievements. Planning has owned `MyPlan` and immutable `PlanRevision`. Discovery has a PostgreSQL `SearchProjection` with `tsvector`/GIN. Calculations has tool/formula/result structures, but no approved active formulas.

The independent audit found no Phase 6A blocker. This plan records no `PHASE_6A_DEPENDENCY_FINDING` at planning time.

## 3. Product objectives

- Make published Playbooks the primary public entry point and allow anonymous reading of published content.
- Let a learner follow Playbook → recommended Module → ordered Lessons, while keeping exploration non-linear and ungated unless an exact approved requirement states otherwise.
- Make Lessons calm, readable and mobile-first, and connect them to Practice and their Module context.
- Require an active verified account for private persistence: Practice attempts, Notes, My Plan, Progress, achievements and learning journey records.
- Preserve exact revision identity and user ownership in all persisted learning evidence.
- Present completion as explainable evidence against an exact Module Revision, with only required requirements blocking completion.
- Keep planning user-directed and calculations transparent; no formula, guarantee, or personal recommendation is invented.

## 4. First release scope

**Recommended first release boundary:** a public learning-library slice plus a minimal authenticated applied-learning slice.

The user can open the homepage, browse published Playbooks, inspect a Playbook's current published revision and its approved Module recommendations, browse a Module's current published revision, and read its ordered published Lessons. From a Lesson the user can move to adjacent Lessons in that Module, return to Module/Playbook context, and see a Practice entry when the exact current published Practice revision is connected to the Lesson/Module requirements. A public user may read all published content.

An active verified account can start and submit the connected Practice activity, with responses and attempt tied to the exact Practice revision. The product records the exact submitted attempt and any applicable accepted evidence against one exact Module requirement; it then shows a requirement checklist and completion state for that Module Revision. An account can create a revision-pinned Note from a Lesson and view its notes. My Plan can be added after core evidence/ownership workflows: the owner defines target, timeframe, assumptions and strategy path in a new immutable revision and can inspect earlier revisions. Progress can then explain journey events, evidence, completion and any achievement already supported by approved criteria.

The first approved release should prioritize the public discovery-to-reading loop and one complete private Practice/evidence loop. Notes, My Plan, Progress, search, and achievements are staged vertical slices; do not claim the whole loop complete until their own criteria pass. No content is seeded by this plan.

### User journeys

1. **Anonymous discovery:** Home → Playbooks → Playbook → recommended Module → Module → Lesson → previous/next Lesson or Practice prompt. Sign-in wall appears only when a persistent action is requested.
2. **Practice and evidence:** eligible account opens a Practice checkpoint from its source Lesson/Module → starts attempt on exact published Practice revision → saves response(s) → explicitly submits → receives submission/feedback state → eligible accepted attempt is associated with exactly one matching requirement → Module checklist reflects evidence and completion evaluation.
3. **Notes:** eligible account selects supported text in a Lesson paragraph → creates a Note pinned to the exact LessonRevision and block UUID, with selected quote and optional offsets → opens Notes list → follows source link to that same historical revision. If source content has since changed, show that the note belongs to an earlier revision and do not reanchor.
4. **My Plan:** eligible account enters My Plan from the learner navigation or a relevant learning context → creates a plan if needed → saves a new immutable snapshot of user-defined target/timeframe/assumptions/path and any approved context references → views current and prior revisions. No Progress dependency.
5. **Progress:** eligible account opens Progress → sees recorded lesson encounters/completions, attempts, requirement evidence, exact-revision Module completions and any award records, with source links. It is a read model of evidence, never the authority that creates it.
6. **Search:** visitor or eligible account submits a query → receives only published/current public editorial results grouped by Playbook, Module, Lesson and (if approved) Practice. Private user records never enter public results.

## 5. Scope exclusions

This plan excludes registration, account recovery and email delivery UI/infrastructure; editorial author/review/publish UI; upload or media byte storage/processing/CDN; financial formulas and calculator activation; payments/subscriptions; user-facing AI; voice/audio; full Dictionary; advanced recommendations/analytics/knowledge graph; public API/SPA/microservices; deployment; and any new curriculum or content block types. No new user role, external service, formula, score, pricing, promise, or infrastructure dependency is introduced.

## 6. Route architecture (all routes PROPOSED)

Convention: Django-rendered HTML first, same-origin forms for writes, CSRF protected. Slugs resolve stable editorial identities; view services select the current published revision. The route never accepts an arbitrary revision ID to reveal unpublished content. A historical revision route may be added only for an owner-authorized Note source view and must enforce publication/history policy; exact policy is **TO-BE-DEFINED**. No JSON route is required for the first release. Progressive enhancement can improve interactions but baseline navigation and forms work without JavaScript.

| Proposed route | Purpose | Access | Owning app | Domain model(s) | Required service boundary | Progressive enhancement | JSON necessary? |
|---|---|---|---|---|---|---|---|
| `GET /` | Playbook-led home and entry points | Public | `content` (shell may be project-level) | Playbook, PlaybookRevision | public current-revision query/presenter (PROPOSED; no current read service exists) | Optional | No |
| `GET /playbooks/` | Published Playbook discovery/list | Public | `content` | Playbook, PlaybookRevision, recommendations | public current-revision query/presenter (PROPOSED) | Optional filters if approved | No |
| `GET /playbooks/<slug>/` | Playbook scenario, context, recommendations | Public | `content` | Playbook, PlaybookRevision, PlaybookModuleRecommendation, ModuleRevision | exact current published resolver (PROPOSED) | Optional | No |
| `GET /modules/` | Browse published Modules | Public | `content` | Module, ModuleRevision | public current-revision query/presenter (PROPOSED) | Optional filters | No |
| `GET /modules/<slug>/` | Module overview, requirements, lesson sequence | Public | `content` | Module, ModuleRevision, ModuleLearningRequirement, LessonRevision, PracticeActivityRevision | exact current published resolver (PROPOSED) | Optional | No |
| `GET /lessons/<slug>/` | Canonical lesson reader | Public | `content` | Lesson, LessonRevision, ModuleRevision, Playbook context | exact current published resolver + ordered block presenter (PROPOSED) | Selection/note enhancement only | No |
| `GET /lessons/<slug>/revisions/<n>/` | Historical source for existing Note | Conditional private/history policy | `learning` with `content` resolver | Note, LessonRevision | owner note lookup + safe exact revision resolver (PROPOSED) | No | No |
| `GET /practice/<slug>/` | Public activity instructions and account CTA | Public content; attempt private | `content`/`practice` boundary | PracticeActivity, PracticeActivityRevision | current public revision resolver; attempt service on write | Native form; optional enhancements | No |
| `POST /practice/<slug>/attempts/` | Start exact-revision attempt | Verified account | `practice` | PracticeAttempt, PracticeActivityRevision | `create_attempt` | Optional | No |
| `POST /practice/attempts/<id>/responses/` | Save response | Verified owner | `practice` | PracticeAttempt, PracticeResponse | `save_response` | Optional | No |
| `POST /practice/attempts/<id>/submit/` | Submit attempt explicitly | Verified owner | `practice` | PracticeAttempt, PracticeResponse | `submit_attempt` | Optional | No |
| `GET /my-plan/` and `GET /my-plan/revisions/<n>/` | Current plan and revision history | Verified account | `planning` | MyPlan, PlanRevision | owner-scoped query + `create_plan`/`append_revision` | Optional | No |
| `GET /progress/` | Evidence-derived journey/completion/awards | Verified account | `learning` | LearningJourney, JourneyStep/targets, LessonCompletion, RequirementEvidence, ModuleCompletion, UserAchievement | owner-scoped projection/query; `evaluate_module_completion` only at evidence boundary | Optional | No |
| `GET /notes/` | Owner's note list | Verified account | `learning` | Note, LessonRevision | `owned_notes` | Optional | No |
| `GET /notes/<id>/` | Note detail and source link | Verified owner | `learning` | Note, LessonRevision | owner-scoped note query | Optional | No |
| `POST /lessons/<slug>/notes/` | Create anchored Note | Verified account | `learning` | Note, LessonRevision | `create_note` + anchor validation | Selection helper useful | No |
| `GET /accounts/login/`, `POST /accounts/login/`, `POST /accounts/logout/` | Existing-account session entry/exit | Public/login; logout authenticated | `accounts` | UserAccount, Django session | Django auth/session, verified gate at private feature boundary | No | No |
| `GET /search/`, `POST /search/` or `GET /search/?q=` | Search public editorial content | Public | `discovery` | SearchProjection and exact target revisions | new query service over PostgreSQL search projection (PROPOSED; none exists) | Optional filtering | No |

No separate module lesson route is needed initially; ordered lessons are linked from Module. The exact URL style and route names are **PROPOSED — REQUIRES OWNER APPROVAL**. Login route is possible using existing auth foundations; registration/recovery/email delivery is not included and remains a product-access dependency for new users.

## 7. Authentication boundary

**Public:** homepage; Playbook, Module, Lesson and published Practice reading; Playbook discovery; public search; related-content links, subject to current-publication resolution.

**Verified active account required:** Practice attempt creation/response/submission; Notes; My Plan; Progress; achievements and persistent journey/completion state. Every read, nested lookup and mutation is scoped to `request.user` via domain services/querysets. Never trust a submitted owner identifier. If unauthenticated, preserve a safe return path and invite login; after login re-resolve the same public content and exact revision. Do not queue an action with user data before authentication. Verification and eligibility for personal features follows Phase 6A. New account acquisition is not solved by login alone: registration/recovery/email delivery are explicit deferred dependencies and need separate authorization/scope before release to an audience without accounts.

Staff editorial access remains governed by existing staff groups, MFA, separate reviewer/publisher controls and exact revision services. No new roles or editorial UI are proposed here.

## 8. Content delivery architecture

The public resolver begins with stable identity, reads its `current_published_revision`, and verifies that the referenced revision is published and belongs to that identity. A missing, draft, review, rejected, superseded or mismatched revision is not returned publicly. Resolve every relationship to its exact revision, not a mutable identity's latest arbitrary revision. Apply this at each level:

```text
Playbook(slug) → current published PlaybookRevision
  → active PlaybookModuleRecommendation → exact ModuleRevision (public/current policy)
    → ModuleRevision requirements/ordered LessonRevision references
      → exact LessonRevision and validated Content Blocks
```

Only current published revisions are the source for public pages. Stable identities, revision pointers, recommendation/requirement records, related-content relationships and publication events stay under `content`. Draft/reviewed historical content must not leak through a URL, search, navigation, `404` distinction or cached response. Treat unpublished and absent content equivalently to public callers. User-facing cache behavior must not serve an old private/draft response; cache policy and invalidation details are **TO-BE-DEFINED** before caching is enabled.

Module and Lesson order comes from approved requirement/relationship `position` values and is deterministic; tie/duplicate behavior is constrained by existing model validation. Previous/next links are derived within the same published ModuleRevision's published LessonRevision set. Do not infer content relationships that are absent. Practice links appear only through an explicit exact-revision requirement or approved relationship. Related content comes only from current eligible relationships and is advisory, not a prerequisite.

Every learning action and saved note records its exact content revision. A later publication may change the canonical public page, but must not rewrite old evidence or note anchors. Showing historical context in Progress/Notes may require a historical-content rendering policy; whether old content remains publicly viewable, is shown as a minimal unavailable-source card, or requires ownership is **TO-BE-DEFINED**.

## 9. Lesson reader architecture

The reader is a focused, book-like learning surface with clear relationship to its Module and Playbook. Proposed structural hierarchy:

1. Global responsive shell and accessible primary navigation.
2. Breadcrumb/context: Playbook when relevant → Module → Lesson position/title.
3. Lesson header: title, supported summary, current Module context; no invented metadata.
4. Reading progress/context indicator based on position in the Module, not an unsupported completion claim.
5. Content block renderer iterating validated `LessonRevision.blocks` in position order. Initial supported type is **paragraph only** (`key`, `type`, `position`, `payload.text`). Escape/render plain text safely; no raw HTML, unsupported block fallbacks, invented headings/lists/callouts/media blocks, or inferred schema. Empty block array is accepted by Phase 6A; whether publication requires content is **TO-BE-DEFINED**, so reader handles an empty published body without crashing.
6. Practice checkpoint when explicit exact-revision connection exists, with required/optional/recommended classification visible where applicable.
7. Previous/next Lesson navigation within the ModuleRevision; Module overview and Playbook context links.
8. Authenticated Note/highlight action, with accessible native selection fallback and stable block UUID/quote anchor.
9. Completion state only when backed by a `LessonCompletion` record or explicit approved event behavior; mere page view is not completion.
10. Related Lesson/Module links only from supported relationships.

Typography, spacing, color, and responsive breakpoints are design work after plan approval. Prioritize readable line length, generous spacing, semantic heading structure where model supports it, keyboard access, visible focus, contrast, and no horizontal overflow. No visual system is implemented by this plan.

## 10. Practice architecture

Practice is entered from its published public instructions and from a directly connected Lesson/Module checkpoint. The page identifies the source Lesson/Module and exact requirement classification; an account is required only to persist an attempt. The activity uses the exact `PracticeActivityRevision.response_schema` and supported prompt data; its schema-to-form rendering contract and supported answer types are **TO-BE-DEFINED** and must be derived from actual approved activity schemas, not invented here.

Start uses `create_attempt(user, practice_revision)` after re-resolving the exact current published revision and verified-account status. Responses are saved through `save_response` under owner scope while the attempt is started. “Submitted” means the explicit `submit_attempt` transition has persisted; a started/draft attempt does not satisfy a requirement. Submission feedback must distinguish received/submitted from accepted/evaluated. Automatic acceptance, review, scoring, feedback rules and correction/retry UI are **TO-BE-DEFINED**; no algorithm is proposed. Only an accepted attempt can produce requirement evidence under the existing contract. Record evidence through `record_requirement_evidence` only when exact attempt revision and requirement target match, the module revision is appropriate, the owner matches, and evidence state is accepted. One accepted attempt satisfies one requirement. Preserve all evidence; reassessment appends/corrects according to existing supersession rules rather than overwriting.

The user sees saved/submitted state, any explicitly approved feedback, and the exact requirement consequence. Unaccepted or merely submitted work is shown as such and does not silently complete a requirement. Module completion evaluation uses exact ModuleRevision and requirement set. No JSON endpoint is needed for basic form submission.

## 11. Module completion architecture

Use `evaluate_module_completion(user, module_revision, journey=...)` as the domain authority; the view displays its result and does not duplicate rules. Evaluate the exact ModuleRevision and its requirement set. Every unsatisfied `required` requirement blocks completion. `optional` and `recommended` do not block. Explain each requirement with status and its evidence link (attempt/revision); show optional/recommended work separately. Display the exact module revision context (title/revision number, with a user-facing date only if supported) so historical completion is not mistaken for current curriculum completion. Reassessment or new revisions preserve existing evidence/completion history; do not silently carry evidence to a different revision or infer equivalency. Progress is not the source of truth.

Completion could be `complete`/`incomplete` based on service output; detailed UI wording and whether a later requirement change creates a new evaluation record are **TO-BE-DEFINED** from existing service semantics before view implementation.

## 12. Notes architecture

Create Notes only for a verified owner using `create_note`. For a Lesson highlight, save exact `LessonRevision`, stable paragraph block UUID, selected quote, and optional start/end offsets as hints. The anchor validator checks quote/block identity; offsets are not identity. Notes remain private and owner-scoped, can be listed at `/notes/`, and link to the exact source revision. The lesson UI may offer a plain note action without text selection; product text/anchor requirements remain **TO-BE-DEFINED**.

On source revision change, keep the note anchored to its old revision. Do not reanchor, mutate the quote, or copy it to a new revision. Render a clear earlier-revision context; if historical rendering is unavailable, display the saved quote and a safe source-unavailable state. No cross-revision migration. Editing/deleting, note search/export, offline behavior, and transfer into My Plan are **TO-BE-DEFINED**; the first slice may provide create/list/source navigation only, with no unsupported edit/delete UI.

## 13. My Plan architecture

My Plan is owner-scoped and independent of Progress. Entry may be from authenticated navigation and an explicitly relevant learning checkpoint. `create_plan` creates the owned container; every save calls `append_revision` to preserve immutable target, assumptions and strategy path snapshots, predecessor, and any valid same-owner journey/practice/calculation context. Viewing revision history is read-only. Never update a historical `PlanRevision` in place. The form exposes only fields supported by the existing planning model/service and approved user experience.

The user decides their definition of financial freedom, target, timeframe, assumptions, possible path and whether the plan fits their circumstances. MaliLab may display recorded user inputs and, only after separately approved deterministic formula contracts exist, quantify scenarios and assumptions. No financial formula, target validation, feasibility claim, recommendation, or default assumption is specified here. Formula-dependent calculations are **TO-BE-DEFINED**. Whether multiple plans/scenarios, draft autosave, notes transfer, or plan attempt thresholds are required is **TO-BE-DEFINED**.

## 14. Progress architecture

Progress is a one-way explanation/read model over source evidence. It reads `LearningJourney`/ordered append-only `JourneyStep` and typed targets, `LessonCompletion`, `RequirementEvidence`, exact `ModuleCompletion`, `UserAchievement`, plus plan history where the approved screen needs to show plan attempts. It does not create/edit practice evidence, plans, or editorial records and never determines completion itself.

Display only evidence-backed claims: lessons encountered or explicitly completed (distinguish these); attempts submitted/accepted; which requirement each accepted attempt satisfied; exact ModuleRevision completion and remaining required/optional/recommended items; recorded achievement awards; and journey milestones. Avoid streaks, points, leaderboards, deadlines or a three-month outcome promise. Achievement catalog, award criteria, and any automatic issuance are **TO-BE-DEFINED**; show only persisted awards whose issuance policy is approved. “Plan attempt” criteria are **TO-BE-DEFINED**; do not label a plan complete or successful based only on existence.

## 15. Search and discovery architecture

Search entry is a normal rendered page/form. A proposed `discovery` query service searches the PostgreSQL `SearchProjection` and returns exact target revisions, grouping result cards by Playbook, Module, Lesson, Practice. Initial result text may use existing projection title/searchable text/filter metadata; only approved filter metadata may be exposed. Public query includes only current published revisions as maintained by the projection service; revalidate each target at result presentation to prevent stale projection leakage. Private Notes, PracticeAttempts/Responses, Plans, calculations, Progress and account data are never indexed or searchable publicly.

Use PostgreSQL full-text search and existing tsvector/GIN foundation. Query parser, ranking/order, stop-word/language behavior for Kenyan terms, pagination, filters, highlighting/snippets and minimum query behavior are **TO-BE-DEFINED**. Proposed initial grouping: Playbooks first, then Modules, Lessons, Practice; exact within-group ordering by relevance and deterministic title tie-breaker, pending approval. Empty state offers Playbook browsing without inventing recommended content. No results still show only public material. JSON is unnecessary; use query string form and server-rendered results. No external search engine.

## 16. Media dependency analysis

The first release can use text-only paragraph lessons, CSS/layout, and existing cover asset references only if an actual delivery URL exists and safe delivery policy is approved. Current Phase 6A stores immutable `MediaAsset` metadata/references; it does not store or serve bytes. Do not add upload, object storage, transformations, CDN or a new external service in this phase plan. Cover imagery is not a hard dependency for functional public reading; neutral presentation may be used pending approved content. Any image/media requirement that becomes necessary must be scoped as a separate media delivery dependency (byte storage, authorization/public visibility, cache, retention, failure fallback, rights, and tests) before implementation. No audio/speaker capability.

## 17. Lab Tools and formulas

Lab Tools are not required for the first release because no approved formula contracts are present and text-based Practice/evidence can deliver a coherent initial learning slice. Existing `LabTool`, `CalculatorDefinition`, `FormulaVersion`, `FormulaApproval`, and `CalculationResult` are a structural seam only. No active formula, UI, result behavior, or formula approval workflow is claimed.

Before a later Lab Tool implementation, each formula requires approved purpose and user-facing explanation; exact inputs/outputs and units; KES/currency policy; ranges, precision, deterministic rounding; assumptions and source/date context; validation/error behavior; version and approval rules; reproducibility; safety/limitations; linkage to Practice/Plan; and test vectors. These contracts are **TO-BE-DEFINED**. Calculation services remain deterministic server-side domain services, separate from form/view presentation; UI never performs authoritative financial arithmetic. No invented assumptions or formulas.

## 18. Future subscription seam

Keep public content resolution and any future access decision behind an application-level content-access policy boundary so a later entitlement decision can wrap content without putting provider logic into views or `content` models. Initial policy is public published content is readable; user-owned persistence requires verified account. **PROPOSED** seam: a small access-policy service called by content presenters/feature entry points, defaulting to current public/verified-account policy. Do not create an entitlement model or provider integration in this planning artifact; exact policy API is **TO-BE-DEFINED** and should be introduced only when a real restricted-content requirement exists. No payment provider or subscription implementation.

## 19. AI boundary

No chatbot routes, learner prompts, AI models, or AI dependencies. Existing editorial provenance/review/publication governance remains the boundary for any future internal drafting assistance. AI-produced material requires human review and approval before publication. Future extension point is an internal content-production workflow behind editorial services, never a public answer source by default; details remain **TO-BE-DEFINED**.

## 20. Data/model impact analysis

Current model names are as inspected in the seven apps. “No database change” is the baseline; route/view/query/presenter services may be needed without schema changes. The exact coverage of fields against each approved screen must be verified during implementation planning before a slice starts.

| Capability | Existing Foundation | New Data Needed? | Migration? | Reason |
|---|---|---|---|---|
| Application shell/navigation | Django settings/session/auth middleware; no user UI | No | No | Templates, static assets and route wiring only; no model |
| Public homepage/Playbook discovery/detail | `content.Playbook`, `PlaybookRevision`, `PlaybookModuleRecommendation`, `RelatedContentRelationship` | No | No | Current published pointers and exact revision links support read-only presentation |
| Module browsing/detail | `Module`, `ModuleRevision`, `ModuleLearningRequirement` | No | No | Existing revision and positioned requirement structure supports display |
| Lesson reading/navigation | `Lesson`, `LessonRevision.blocks`, module requirements | No | No | Current block contract supports paragraph rendering; no new blocks |
| Public Practice reading | `PracticeActivity`, `PracticeActivityRevision` | No | No | Existing revision holds title/instructions/prompt/response schema |
| Practice attempts/responses/evidence | `practice.PracticeAttempt/PracticeResponse`; `learning.RequirementEvidence/ModuleCompletion`; existing services | No | No | Exact attempt/revision/requirement, ownership and immutable evidence contracts exist; UI/form parser may be new service code |
| Module completion display | requirements + evidence/completion models and `evaluate_module_completion` | No | No | Completion authority already exists and required-only blocking is accepted |
| Notes | `learning.Note`, exact LessonRevision/block anchor and `create_note` | No | No | Revision, UUID key, quote and offsets supported |
| My Plan | `planning.MyPlan/PlanRevision`, `create_plan`/`append_revision` | No | No | Immutable revision snapshots and ownership already support workflow |
| Progress/achievements | journey, typed targets, lesson completion, evidence, module completion, `UserAchievement` | No | No | Evidence-derived presentation; award criteria/service maturity may require service work, not new data by default |
| Search/discovery | `discovery.SearchProjection`, PostgreSQL tsvector/GIN and projection builder | No | No | Search query service/view can use existing index; no external infrastructure |
| Media delivery | `content.MediaAsset` metadata and revision references | **Possibly, proposed only after scope** | **Possibly** | No byte storage/delivery exists; first text-only release does not require it |
| Lab Tool/formulas | calculations structures and `save_result` | No for structural seam; formula-specific data only after approval | No now | No formula behavior is approved; future formula contracts may expose genuine gaps |
| Registration/recovery/email | custom `UserAccount`, auth/session, verification fields | No assumed now | No assumed now | Delivery/UI policy and service need separate definition; don't infer fields or provider |
| Editorial workflow UI | governance models/services | No | No | Staff UI can be layered over exact services; not first release |
| Subscription/access policy | no entitlement model | No now | No | Proposed application policy seam; add data only with approved restricted content |
| User-facing AI/audio/payments | excluded | No | No | Explicitly out of scope |

No new model, field, constraint, index, migration or database change is proposed as necessary for the first release. Any implementation discovery that changes this must be documented as **PROPOSED — REQUIRES OWNER APPROVAL**, with a specific gap in accepted 6A and a separate authorization; do not modify schema under this plan.

## 21. Testing strategy and capability traceability

Every slice adds acceptance tests at view/service integration boundaries; preserve all Phase 6A tests and add no weakening/skips. Use isolated test settings and PostgreSQL integration coverage for database-specific constraints/search. Test rendered HTML and forms without requiring JavaScript, plus progressive enhancement where included. Responsive behavior is tested at representative narrow and wide viewport sizes with keyboard and automated browser checks where tooling is approved. Never point tests at live `malilab`.

| Product requirement → capability | Route/UI boundary | Domain service/model | Test requirement | Acceptance criterion |
|---|---|---|---|---|
| Discover Kenyan learning from Playbooks → public library | `/`, `/playbooks/`, detail | current-public resolver; Playbook revisions/recommendations | anonymous access; current published exact revision; draft/review/superseded absent; safe missing behavior | Public reader sees only allowed published/current Playbook and exact linked Modules |
| Learn structured content → Module/Lesson reader | module and lesson routes | content resolver; ModuleRevision, LessonRevision, requirements | navigation ordering, ownership irrelevance for public reads, publication protection, paragraph escaping, empty body | Playbook → Module → Lesson works without authentication and no unsupported blocks render |
| Apply learning → Practice attempt | Practice page/forms | practice create/save/submit; PracticeAttempt/Response | login/verified boundary; owner isolation; exact revision; submit transition; retries/invalid response behavior | submitted state is explicit; only accepted exact attempt may create one requirement evidence |
| Explain completion → requirement checklist | Module/progress UI | `evaluate_module_completion`; evidence/completion models | required blocks, optional/recommended don't; exact ModuleRevision; evidence mapping; reassessment history | Learner sees satisfied and remaining requirements plus exact evidence and revision |
| Capture insight → Notes | lesson action/list/detail | `create_note`, `owned_notes`; Note/LessonRevision | owner isolation; quote/block/offset validation; revision change no reanchor; source navigation | Note stays private and anchored to exact revision/key/quote |
| Define personal direction → My Plan | plan UI | `create_plan`, `append_revision`; MyPlan/PlanRevision | ownership, each edit new immutable revision, predecessor/context same owner, historical reads | Previous snapshots remain unchanged and Progress is not required |
| Understand journey → Progress/achievements | `/progress/` | owner-scoped read model; learning evidence models | data reflects source evidence; no false completion; ownership/private leakage; achievements only persisted | Progress explains evidence and never becomes its source of truth |
| Find relevant public learning → search | `/search/` | proposed query service; SearchProjection | public-only, exact target, current revalidation, private exclusion, query/empty/order/filter | Only allowed current published content appears; deterministic grouping/order per approved policy |
| Account persistence boundary → login/private actions | auth and gated forms | Django auth, `UserAccount.can_use_personal_features` | anonymous, unverified, disabled, wrong-owner, CSRF, safe redirect/session checks | Public reading stays open; private operations require eligible owner |
| Mobile-readable learning → responsive presentation | all public/private pages | no domain model | narrow viewport, keyboard, zoom/reflow, text sizing, no overflow, semantic headings/labels | Core browse/read/submit flows work on mobile without essential JS |

Security regression coverage must include object-ID tampering, nested owner scoping, CSRF on writes, open redirects, session/login behavior, unpublished content side channels, XSS from content/response/notes, and private data in search/cache/log surfaces. Phase 6A regression suite remains green after every implementation slice and at gate.

## 22. Dependency-aware implementation order

1. **6B.1 Route/presenter contract and application shell.** Define URL names, shared navigation, error states, and public/private response policy. No domain feature assumes templates exist.
2. **6B.2 Public exact-revision content delivery.** Add tested resolver/query services for current published identities, exact linked revisions, publication denial, ordered navigation. This is prerequisite for every public page and action.
3. **6B.3 Playbook → Module → Lesson vertical reader.** Home/discovery, Playbook and Module pages, paragraph Lesson reader, previous/next, empty/error states. This delivers the first actual public user experience.
4. **6B.4 Existing-account login boundary.** Session login/logout and safe sign-in prompt for private actions; verify active email eligibility. Registration/recovery/email remains a separate release dependency.
5. **6B.5 Practice submission vertical slice.** Schema-driven form contract based on approved current response schemas, owner-scoped attempt/response/submit services, explicit submitted state. Resolve accepted/feedback semantics before surfacing accepted status.
6. **6B.6 Requirement evidence and Module completion UI.** Map only eligible accepted attempts to exact matching requirement; display required vs optional/recommended and exact revision. Depends on 6B.5.
7. **6B.7 Notes create/list/source return.** Revision-pinned paragraph quote interaction, private list and safe historical source policy. Depends on public reader and auth.
8. **6B.8 My Plan revisions.** Form limited to approved model/service fields, create/edit-as-new-revision/history; no calculation. Depends on auth and planning form contract, not Progress.
9. **6B.9 Progress and achievements.** Read-only explanation of journey/evidence/completion and existing persisted awards. Depends on evidence and plan attempt policy where displayed; award criteria must be approved before awards are issued.
10. **6B.10 Search/discovery.** PostgreSQL query service, grouped cards and filters after public route/query policy is stable; projections must be maintained on publication and revalidated.
11. **6B.11 Responsive/accessibility/security acceptance and release hardening.** Validate integrated flows, performance requirements once defined, and Phase 6A regression suite.

Optional ordering: search may ship with 6B.3 if query behavior is approved and publication projection updates are reliable; otherwise defer it without blocking the reader. Notes and My Plan can ship independently after auth. Lab Tools are not a dependency of first release. Do not imply this sequence authorizes each slice.

## 23. Acceptance criteria and Phase 6B gate

Phase 6B can be declared complete only when all approved in-scope slices have acceptance tests and:

- All Phase 6A tests still pass on the supported test layers; all Phase 6B tests pass.
- No unauthorized schema, migration, PostgreSQL, settings, dependency, external-service or deployment changes occurred.
- Public pages resolve exact current published revisions and expose no draft/reviewed/unpublished/private data, including through direct URLs, search, errors, caching or related links.
- Playbook → Module → Lesson navigation follows explicit relationships and deterministic order.
- Private routes/actions enforce active verified account and owner scope for list, detail, nested references and writes.
- Practice submission preserves exact Practice revision and submitted-attempt semantics; evidence is immutable, owner-correct, exact-requirement-linked, and one accepted attempt satisfies at most one requirement.
- Completion is evaluated against exact ModuleRevision; required items block, optional/recommended do not; evidence and remaining work are explained.
- Notes retain exact LessonRevision, stable block key and selected quote; offsets remain hints; no cross-revision reanchor occurs.
- Every My Plan edit appends an immutable PlanRevision with valid same-owner context; historical revisions remain readable and unchanged.
- Progress is evidence-derived and does not authoritatively change practice, plan or editorial state.
- Public search exposes only allowed published/current exact target revisions and excludes all private user records.
- Functional browse/read/forms work responsively and accessibly on mobile; no core path requires JavaScript.
- No Lab Tool/formula, payment/subscription, user-facing AI, audio, media pipeline, editorial UI, or registration/recovery functionality is falsely claimed complete.
- Documentation and traceability map each shipped capability to tests and acceptance evidence.

## 24. Risks

- **No new-account onboarding:** login-only UI cannot serve users without pre-provisioned accounts. Registration, verification delivery and recovery require a separately authorized contract before broad public launch.
- **No published seed content:** the live foundation has no domain content rows per acceptance audit; useful live discovery requires independently approved editorial content and publication through governance.
- **Public resolver absent:** models/services enforce lifecycle rules, but no read presenter/view currently applies them. Resolver correctness is a release-critical new service boundary.
- **Practice response schema:** model has a schema field but no user-facing renderer contract. An implementation must first inspect and approve allowed schemas and validation/feedback behavior.
- **Media delivery gap:** referenced metadata does not imply available bytes. First release should not rely on media without a separately accepted delivery path.
- **Completion semantics:** service exists, but user-facing accepted-attempt/feedback wording and plan-attempt/achievement thresholds remain open.
- **Historical rendering:** Notes and evidence reference immutable revisions while public content points to current. Historical access/privacy policy needs a decision.
- **Empty lesson revisions:** accepted model permits empty blocks; content quality/publish checklist policy remains open.
- **Search projection freshness/query semantics:** rebuild service exists but no route/query service or operational refresh contract exists.
- **Accessibility/performance thresholds:** the desired experience is documented, but measurable requirements remain **TO-BE-DEFINED**.

No Phase 6A defect or missing foundation dependency is presently evidenced. If implementation shows otherwise, record `PHASE_6A_DEPENDENCY_FINDING` with evidence; do not fix it under this planning artifact.

## 25. TO-BE-DEFINED items

- Exact home/discovery composition, route naming, content catalogue and editorial release set.
- Historical revision visibility for Notes, Progress and evidence; unavailable-source behavior.
- Public cache policy and publication invalidation.
- Practice response schema allow-list/form rendering, validation, feedback, acceptance/review, retry/correction semantics.
- Whether lesson encounter and completion are distinct events and what action records each.
- Plan form fields, cardinality/scenario model, edit workflow, plan-attempt threshold and note transfer.
- Achievement catalog/criteria/issuance and relationship to plan attempt.
- Search ranking, language/tokenization, filters, snippets, pagination and event freshness.
- Media byte storage/delivery if required; cover fallback and rights process.
- Formula contracts and Lab Tool release scope.
- Registration/recovery/email delivery and account acquisition dependency.
- Access-policy seam API and any future restricted content/entitlement model.
- Measurable accessibility, browser compatibility, response/performance and privacy/retention criteria.
- Editorial publication checklist for non-empty lessons and content quality.

## 26. Explicit Phase 6C+ candidates

Subject to future product and owner approval: registration/recovery/email delivery; editorial author/review/publish interface; complete media storage/delivery; approved deterministic financial formulas and Lab Tools; richer My Plan scenarios and calculator links; advanced search/recommendations; full Dictionary; sophisticated analytics; subscriptions/entitlements/payments; internal AI content-production tooling; user-facing AI assistant only if separately approved; voice/audio only if product direction changes explicitly; production deployment and operational hardening. Listing a candidate is not approval or a schedule commitment.

## 27. Implementation authorization boundary

This plan was originally approved for planning only. GOV-002 now records the owner’s explicit authorization to execute the planned Phase 6B application slices. That authorization does not approve model or migration changes, live data/schema operations, settings/dependency/deployment changes, content seeding, payments, AI, formulas, or audio; those boundaries remain governed by the applicable project decisions. The recommended first implementation slice is **6B.1–6B.3: tested public exact-revision content delivery and the Playbook → Module → Lesson reader**, with login/persistent actions following as a separate dependency slice.
