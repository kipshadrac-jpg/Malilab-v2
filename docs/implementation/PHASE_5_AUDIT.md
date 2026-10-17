# Phase 5 Physical Specification Audit

**Audit status:** Re-audited after owner-approved Phase 5C decisions. Documentation only; no implementation work was performed.

## 1. Executive Verdict

The Phase 5 physical specification is sufficiently precise to begin Django/PostgreSQL implementation without inventing product policy. The six former owner blockers are now resolved and reconciled into the physical model, field/constraint mapping, ownership/deletion rules, traceability and tests. Remaining items are scoped to later feature definition or operations and do not prevent establishing the approved schema/domain foundation.

## 2. Authentication/account identity — LOW

**Verified:** custom Django user model/stable account identity; email/password; verified email required for full account functionality; email recovery; Django-managed server-side sessions. Phone/OTP and social login are future. Age/eligibility remains expressly unresolved and no age policy is assumed. The identity choice is settled before the first migration.

**Physical coverage:** normalized unique email, framework-managed password/session primitives, verification state, and controlled account state in `UserAccount`.

## 3. Anonymous reading vs personal features — LOW

**Verified:** anonymous users may read public published editorial content. Persistent Notes, Practice history, My Plan, Progress, Achievements and all other user-owned records require an authenticated, email-verified account.

**Physical coverage:** content-access policy plus explicit owner FKs; no personal data in SearchProjection. This needs route/service tests, not an account requirement on public reads.

## 4. Ownership isolation — LOW

**Verified:** every private record has an account ownership path. Application-level owner scoping and same-owner checks are mandatory; no client-provided owner ID; PostgreSQL RLS remains unnecessary initially. Staff do not receive learner financial-data access by default.

**Physical coverage:** owner relations, protected references, cross-account tests in `OWNERSHIP_IMPLEMENTATION.md` and `TESTING_SPECIFICATION.md`.

## 5. Account deletion safety — LOW

**Verified:** hybrid lifecycle is approved: disable access, controlled deletion/export, remove or anonymize identifiable user data by class, retain editorial records, retain only necessary/minimized audit history, and manage backup expiry separately. No account-wide CASCADE. A dedicated service handles referential integrity.

**Remaining operational detail:** per-class processing sequence, export format, actor anonymization and backup expiry schedule remain TODO. These do not prevent schema implementation because references are protected and no cascade is assumed; deletion/export workflows and production retention must honor the approved lifecycle.

## 6. Staff role separation and MFA — LOW

**Verified:** Author/Editor, Reviewer, Approver/Publisher, Administrator roles; staff MFA required; Administrator has no automatic learner financial-data access; financial-content author and approver must differ; editing after approval requires renewed review/approval.

**Physical coverage:** actor/role snapshots and exact revision references on governance events; permission checks specified for application services.

## 7. Formula approval workflow — LOW

**Verified:** FormulaVersion lifecycle remains Draft → Tested → Reviewed → Approved → Active → Retired. Activation is an explicit action with a second-person approver and preserved version, test cases/expected results, assumptions, source/reference, reviewer and timestamp. AI content cannot bypass human review; formula code alone never activates a version.

**Physical coverage:** FormulaApproval event, active-version uniqueness, transactional lifecycle gate and same-actor rejection test.

## 8. KES-first numeric policy — MEDIUM

**Verified:** KES-first, extensible currency representation; every monetary value carries explicit currency; launch support is KES unless a later approved calculator specification adds a currency; no implicit FX; FX conversion is future scope.

**Remaining TODO:** exact calculator catalog, currency-code registry beyond KES, units, field ranges, rates, duration/date conventions, and formula-specific precision/rounding. These are intentionally not universalized. They do not block model/domain implementation: generic snapshots preserve exact decimal strings and explicit units/currency; a specific calculator cannot be enabled until its own contract defines these values.

## 9. Decimal-safe calculations — MEDIUM

**Verified:** exact financial arithmetic uses Decimal/numeric semantics, never binary floating point. Calculation precision is separate from display precision; rounding is deterministic and formula-specific. CalculationResult preserves FormulaVersion, inputs, assumptions, output, units/currency, precision/rounding/method/source/warnings and time.

**Remaining TODO:** do not choose a universal `numeric(p,s)`. Each calculator specification defines range, intermediate precision, output scale and rounding. This is a per-calculator implementation gate, not a blocker to implementing the generic schema and formula governance.

## 10. Note revision anchoring — LOW

**Verified:** Note pins exact LessonRevision and stable ContentBlock ID; selected quote is preserved; optional character offsets are hints only. Revision/block/quote remain authoritative. Changed text cannot silently move the selection, notes never auto-move to new revisions, and UI may identify historical-version context.

**Remaining TODO:** text normalization/rendering details may be refined in UI work but cannot weaken the owner-approved semantics. The versioned JSON anchor and exact revision relation are implementable now. Advanced cross-revision reanchoring is future scope.

## 11. One-attempt/one-requirement semantics — LOW

**Verified:** one accepted PracticeAttempt satisfies exactly one ModuleLearningRequirement initially. Physical links remain extensible, but accepted evidence is explicit and no second requirement is credited because PracticeRevision is reused. ModuleCompletion evaluates the exact ModuleRevision requirement set. Evidence does not carry to a new ModuleRevision. Correction/reassessment preserves prior evidence.

**Physical coverage:** exact Attempt, PracticeRevision, ModuleRevision and Requirement links; pair uniqueness; one accepted requirement per attempt; immutable supersession/reassessment history; ModuleCompletion snapshot.

## 12. Historical/version integrity — LOW

**Verified:** Playbook/Module/Lesson/Practice revisions, formula versions, source snapshots, CalculationResults, PlanRevisions, JourneySteps, RequirementEvidence and ModuleCompletion remain exact and immutable at the domain boundary. Current pointers are for new discovery only. Old content or formulas cannot rewrite historical notes, attempts, plans, results or completion.

## 13. Constraints and indexes — LOW

**Verified:** revision sequence, ordered membership, owner paths, formula active uniqueness, attempt/evidence cardinality, exact target matches, immutable history, public-search exclusion and source/media protection have DB constraints where local and service transaction rules where cross-row. Indexes align with account-scoped history, revision lookup, ordered journeys/requirements, formulas and public search. Avoid private JSON/text indexes.

## 14. Migration strategy — LOW

**Verified:** initial custom user identity is selected before first migration; schema is additive and historical snapshots are never rewritten; formula seed records start Draft; account deletion is a service, not migration cascade; production backups/restore remain a deployment gate. Email delivery provider is not selected, but does not change the data model.

## 15. Test coverage — LOW

**Verified:** specifications require tests for authentication/verification, public anonymous reading, owner isolation, hybrid deletion, staff MFA/roles, author/approver separation, formula lifecycle/second approval, decimal reproducibility, revision-local notes, one-attempt/one-requirement, exact completion evidence, historical references, search privacy and protected deletion behavior.

## 16. Remaining decisions and blocking assessment

| Remaining item | Severity | Blocks Django/PostgreSQL foundation? | Scope gate |
|---|---|---:|---|
| Age/eligibility policy | MEDIUM | No | Must be resolved before setting eligibility/signup behavior; no age field/rule is assumed. |
| Backup expiry schedule | MEDIUM | No | Required before production data safety/deletion claims; operational deployment policy. |
| Per-calculator catalog, ranges, precision, rate/date/duration/unit conventions | MEDIUM | No | Required before implementing/enabling each calculator; generic calculation data structures remain implementable. |
| Exact extended unit/currency catalogue | LOW | No | KES is initial; additions require approved calculator specification. No FX. |
| Note text normalization/rendering details | LOW | No | Refine during UI implementation without changing exact revision/block/quote guarantees. |
| Phone/OTP, social login, FX, advanced annotation, payments, dictionary and analytics | LOW | No | Future scope; excluded from initial implementation. |
| Account deletion/export processing details and backup propagation | MEDIUM | No for schema; yes for deletion/export workflow and production retention | Follow hybrid lifecycle; protected FKs; no account-wide cascade. |
| Detailed role-to-permission matrix | LOW | No | Implement only approved minimum role responsibilities; refine grants before staff UI. MFA and separation constraints are fixed. |

**Blocking issues:** None identified for beginning the Django/PostgreSQL implementation phase. Do not mistake this for approval to start Phase 6; separate explicit owner authorization is still required.

## 17. Phase 5 completion assessment

The physical specification now reflects all six owner decisions. The remaining TODOs do not require choosing product policy to establish the schema and domain services safely; they are gated at the relevant feature or production-operational boundary. No blocking product or physical-schema ambiguity remains.

## Final verdict

READY FOR PHASE 6
