# Product-to-Physical Traceability Matrix

| Product requirement / owner decision | Architecture | Logical model | Physical mapping / implementation constraint | Required tests |
|---|---|---|---|---|
| Anonymous public reading | Content access-policy boundary; public published content only | Published editorial revisions; SearchProjection | Published-only projection service exists; public UI/routes remain deferred | Projection excludes drafts, retired and private records; public route acceptance remains deferred |
| Accounts for persistent personal features | Session-based same-origin web; verified account boundary | User Account owns private records | Custom Django user model; persistent features require authenticated and email-verified account | Anonymous/unverified personal create/read denied; verified account succeeds |
| Email/password and recovery | Django-managed sessions/auth primitives | User Account stable identity | Unique normalized email; framework-managed password; email verification state; no phone/OTP or social initially; complete delivery and registration/recovery UI deferred | Unique identity and verification boundary tested; email delivery/UI remains deferred |
| User-owned Notes, Practice history, Plan, Progress, achievements and financial values | Application-level owner checks; RLS not initially required | Notes, Attempts, Results, Plan, Journey, evidence/completion/awards | Explicit owner FK/path; no caller-supplied owner; same-owner links; no public indexing | Cross-account list/detail/nested/attach/update/delete/export tests |
| Hybrid account deletion/retention | Account lifecycle service; no account-wide cascade | User-owned, derived, editorial and audit ownership classes | Disable access; process export/deletion; remove/anonymize user data by class; editorial remains; minimize audit; PROTECT/restricted links; backup expiry separate | Deletion preserves referential integrity; editorial untouched; audit actor treatment; backup expiry/restore later |
| Human editorial governance | Draft→review→approval→publication; AI is draft only | EditorialRevision, Review, PublicationEvent, SourceSnapshot | Roles Author/Editor, Reviewer, Approver/Publisher, Administrator; exact revision/actor/role/time; author != approver for financial content; edits invalidate approval | Same author/approver rejected for covered content; edited revision requires renewed review; unauthorized publish denied |
| Staff MFA and least privilege | Staff authentication is separate from learner access | Staff actor references on audit/governance | MFA required; administrator has no implicit financial-data access | MFA required for staff; staff role matrix and private data denial |
| Formula governance (deferred) | No activation governance implemented in Phase 6A | CalculatorDefinition, FormulaVersion, FormulaApproval, CalculationResult structures only | Formula activation governance, seeded formulas and real financial formulas are deferred; no formula is active | No activation-governance acceptance claim |
| KES-first financial calculations (deferred) | Calculator contracts and deterministic arithmetic await approved formula work | Formula/Result structures only | No financial formulas are seeded or activated; formula-specific currency/precision behavior is deferred | Formula calculation acceptance remains deferred |
| Practice and calculator exploration | Calculation logic outside UI/models; server-side validated service | PracticeAttempt/Response, CalculationResult | Attempt may have zero-many saved results; result pins exact formula/context; inputs/outputs exact decimal snapshots | No-calculation attempt valid; 0/1/N results; deterministic replay; owner match |
| My Plan immutable history | Planning independent of Progress | MyPlan, PlanRevision | Revision snapshot/predecessor; no plan cardinality uniqueness invented; protected historical refs | Edits create new revision; old results/assumptions unchanged; same-owner refs |
| Revision-local notes/highlights | Notes stay with historical content; no cross-revision auto-migration | Note → exact LessonRevision → ContentBlock | Required anchor is revision + stable block ID + quote; optional offsets hints only; changed text cannot move anchor | Reorder/edit/removal, quote mismatch, offsets mismatch, historical rendering; no cross-version reanchor |
| One accepted Practice Attempt satisfies one Module Requirement | Evidence-based progress, downstream of source facts | RequirementEvidence and exact ModuleCompletion | Explicit accepted evidence; one accepted Attempt→one Requirement initially; no inferred multi-credit; reevaluation/reassessment appends preserved history | Same attempt cannot satisfy second requirement; exact revision membership; correction preserves old completion |
| Learning journey | Ordered append-only historical context | Journey Context, Journey Steps, exact revision/user targets | Typed target reference with FKs; sequence unique; private target same owner | Ordered append; exact target type/revision; same owner; new step type does not add JourneyStep column |
| Search | PostgreSQL/application projection; canonical editorial records remain source | SearchProjection | Published editorial fields only, rebuildable, no private notes/plans/results | Public query and rebuild equivalence; privacy exclusion and representative Kenyan queries |
| Media history | Exact revision asset reference; no user media assumed | MediaAsset | Immutable metadata row/key per asset version; replacement uses a new row; PROTECT referenced asset; storage and byte retention are deferred | Metadata mutation rejected; referenced asset deletion protected; delivery/storage pipeline deferred |
| Internal AI production | Human-reviewed internal content only | Draft revision/provenance/review/publication | No AI auto-publish; source/provenance attached to draft; no learner data sent | AI-generated draft cannot publish without human approval; no private data in provider payload |
| Future capabilities | Modular monolith, bounded extension points | Dictionary/future entitlement/analytics concepts remain out of initial model | No initial models for payment, FX, phone login, social login, advanced notes, full dictionary or analytics | Ensure core model does not introduce these implicitly |

## Owner-approved decision trace

- Anonymous reading → published-content policy; account-required persistence → owner-scoped private models.
- Email/password → custom stable account identity, verified email, email recovery, server-side sessions.
- Staff approval → immutable revision governance with role/actor/time events and second-person constraints.
- KES-first → explicit currency, exact decimal arithmetic, formula-specific precision and rounding in FormulaVersion/CalculationResult context.
- Revision-local notes → exact LessonRevision and ContentBlock anchor with quote and optional hint offsets.
- One accepted attempt per requirement → explicit RequirementEvidence and exact ModuleCompletion snapshot; no automatic carry-forward.

## Phase 6A implementation verification (2026-10-07)

`python scripts/verify_traceability.py` verifies every one of the 46 MaliLab domain models in `accounts`, `content`, `practice`, `calculations`, `planning`, `learning`, and `discovery` is mapped to an approved requirement group and test module. `scripts/inspect_migrations.py` gates project migrations to additive schema operations before apply. PostgreSQL schema verification checks the custom-user, exact-revision, evidence cardinality, plan version, and public-search index invariants. It does not claim formula activation governance.

| Requirement group | Implemented records/services | Automated coverage |
|---|---|---|
| Accounts/authentication | `accounts.UserAccount`, normalized email backend, verified-account gate, Django sessions, TOTP device support | `accounts/tests.py`; OTP admin-site MFA policy |
| Editorial/versioning/provenance/media | Stable Playbook/Module/Lesson/Practice identities and revisions, requirements/recommendations, topics, source snapshots, review/publication events, media metadata | `content/tests.py`; revision and typed-reference database constraints |
| Ownership/practice | Owner-scoped attempts/responses and verified-account persistence service | `practice/tests.py` |
| Calculation foundation (activation deferred) | Tool/definition/version/approval/result schema only; no formulas seeded or activated | `calculations/tests.py`; formula governance deferred |
| Planning | Plans and immutable ordered revisions with same-owner evidence attachment | `planning/tests.py` |
| Journey/notes/progress/achievements | Typed target associations, ordered steps, exact-revision notes, evidence/completion snapshots and awards | `learning/tests.py`; target and evidence constraints |
| Search | PostgreSQL `tsvector` projection with GIN index and published-current-only projection service | `discovery/tests.py`; PostgreSQL schema verifier |
