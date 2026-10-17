# Phase 5B — Implementation Blocker Decision Brief

**Purpose:** Record the six owner decisions approved in Phase 5C and retain their rationale/options for implementation. This brief does not authorize Phase 6. Owner-approved choices are distinguished from recommended technical defaults and remaining future/TODO policy.

**Current status note:** The statement above records this brief's status when approved. Phase 6A implementation is now complete and Phase 6A remediation is underway in the clean PostgreSQL 16.15 `malilab` development database. Phase 6B remains blocked until the remediation has passed a separate acceptance audit.

## Context from the approved product and architecture

MaliLab is a Kenyan, editorial reading and interactive learning platform. Its first product loop connects Playbooks, Modules, Lessons, Practice, Lab Tools, My Plan and Progress. It stores user-owned financial assumptions, practice responses, calculations, plans, notes and learning history. Those records are private by default and must be owner-scoped. Financial content and calculations are exploratory, not guaranteed outcomes. The application is planned as a Django/PostgreSQL modular monolith with server-rendered pages, server-side deterministic calculations, immutable historical revisions, and human approval before publication. The initial product is free; subscriptions and payments are future scope.

The Phase 4 logical model is approved. The six items covered below were unresolved in the original Phase 5 audit and are now **OWNER-APPROVED** by explicit Phase 5C instruction. Their terms below are authoritative. Recommendations and future items remain non-binding unless stated as owner-approved.

## 1. Account and authentication

### What the architecture needs

- A stable account identity to own private records and to scope every read/write operation.
- A same-origin web session suitable for server-rendered Django pages. The architecture does not require public API tokens or a mobile client in the initial product.
- Separate learner access from staff/editorial privileges.
- A recovery process that does not expose another person's account or financial data.
- A Django user model choice before the first migration. Changing the user model after schema work begins is costly.
- Registration/authentication/recovery and staff MFA have been owner-approved as specified below. Age/eligibility and any age-related review remain open; no age or regulatory rule is inferred here.

“Django built-in authentication” is a framework foundation, not one specific login method. It supplies account/password/session primitives and permission hooks; the owner still chooses whether an account is registered by email, phone, social identity or another method.

| Option | User experience and Kenyan context | Complexity/security/recovery | Future and Django model impact |
|---|---|---|---|
| Django built-in auth with username/password | Familiar account-and-password flow, but a username alone may be hard to remember. Contact information is not inherently required. | Lowest initial dependency footprint; password reset needs a verified recovery channel if enabled. Protect with framework password/session protections, rate limits and secure reset tokens. | Fits same-origin sessions and staff permissions. A custom user model or explicit identity table should be selected before migrations; adding verified contact later is possible but account matching/migration needs care. |
| Email + password | Widely understood account flow; depends on users having reliable private email access, which should be validated with target users rather than assumed. | Needs mail delivery, address verification and secure reset flow; email account compromise/reuse affects recovery. Operational email delivery becomes a dependency. | Straightforward with Django; unique normalized email identity can be chosen, but changing the login identifier later requires a migration and account-linking policy. |
| Phone number + password or OTP | May be convenient for users who rely on a phone number more than email; number changes, shared devices and delivery reliability must be tested in the intended audience. | SMS/OTP adds provider cost, delivery failure, number recycling and SIM-swap/account-recovery risks. Phone is personal data. Phone-only recovery can lock out users whose number changes. | Requires normalized phone identity and a number-change/reverification process. External provider integration and abuse controls add work. OTP/passwordless behavior must be explicitly chosen. |
| Email + phone | Offers an alternative contact/recovery path if both are verified and the user maintains them. | Highest contact-data and verification burden among these options; two channels expand support and attack surface. Avoid collecting both without a clear need. | More account fields and identity-linking/change rules. Could support recovery flexibility, but no approved requirement currently needs both. |
| Social login | Can reduce password friction for users who already use a supported identity provider. | Adds external provider dependency, account-linking and provider-outage/recovery complexity; excludes users without that provider and shares identity metadata. | Can be added through an identity boundary later, but requires explicit providers, data handling, and account-linking policy. Future capability, not initial requirement. |

### Owner-approved decision

**OWNER-APPROVED:** Use a custom Django user model/stable account identity, email + password, required email verification for full account functionality, email password recovery, and Django-managed server-side sessions. Anonymous/public reading is allowed. Persistent personal features require an account. Phone/OTP and social login are future scope. Age/eligibility remains TODO and no age policy is inferred.

## 2. Account deletion and retention

The product stores sensitive user-authored and financial context. Deleting an account may affect learning continuity, historical calculation reproducibility, staff/audit accountability and references between private records. Editorial content must not be deleted merely because one learner leaves. This is a product/data policy issue; this brief makes no claim about legal obligations.

| Data class | Examples | Technical handling question |
|---|---|---|
| User-owned data | Notes/highlights, Practice responses/attempts, scenarios/calculation inputs and results, Plans/revisions, journey steps | Delete, anonymize, export, or retain at user's request? How should a plan revision's linked result be treated? |
| User-scoped derived data | Lesson/Module completion, Requirement Evidence, progress, achievements | Delete with source records, preserve anonymized aggregates, or retain a non-identifying award? Derived records must not remain identifiable through references if their source is erased. |
| Editorial data | Playbooks, Modules, Lessons, published revisions, media, formula definitions, source snapshots | Retain independent of user account. User deletion must not cascade into editorial records or other learners' history. |
| Audit data | Editorial reviews/publication events, formula approvals, security/admin actions | Preserve necessary decision history while deciding whether actor IDs can be anonymized, detached, or retained. Avoid copying learner financial values into audit messages. |
| Anonymized/derived data | Aggregate counts or non-identifying usage measures, if later approved | Must be demonstrably detached from accounts and private payloads. Analytics is not part of initial scope; do not create an analytics store by implication. |
| Operational copies | Backups and media copies | Define expiry and restore/deletion propagation. Deleting a live row does not immediately remove an older backup. Off-host backups and restore validation remain deployment prerequisites. |

### Strategies

- **A. Hard deletion:** permanently remove account and associated personal records. It most directly removes live user data, but can break evidence/result references and audit attribution; backup copies need an explicit expiry process. Editorial data remains separate. May require snapshotting/anonymizing references before deletion.
- **B. Soft deletion:** disable login and mark the account closed/deletion-pending while retaining associated data. This preserves history and simplifies restoration, but is not the same as removing personal data; it needs an access restriction and retention rationale.
- **C. Anonymization:** remove or replace direct identity links while retaining selected learning/calculation records. This may preserve system statistics/history, but snapshots can still identify a person through free text, dates, or combinations of values. Anonymization requires data inventory and verification, not just nulling a user FK.
- **D. Hybrid:** immediately disable account access; allow a controlled request/review interval if the owner chooses; delete or anonymize user-owned records according to a per-class policy; preserve independent editorial records; retain only necessary, minimized audit evidence; propagate expiry to backups according to an approved schedule. This offers a manageable path but is more involved and must be explicitly specified.

### What MaliLab needs technically

1. Account deletion must not cascade into editorial content or another user's records.
2. User-owned rows need a known owner path and a controlled deletion/anonymization workflow.
3. Historical plan/calculation/progress links need an explicit outcome if a referenced private record is removed.
4. Audit records need actor handling distinct from user-authored financial data.
5. Backup expiry and deletion timing must be coherent with production operations.

### Owner-approved direction; operational details remain open

**OWNER-APPROVED:** Use a hybrid lifecycle: disable access at request, perform controlled deletion/export, remove or anonymize identifiable user data by class, retain editorial data and only necessary/minimized audit history, and handle backup expiry separately. No account-wide CASCADE. Use protected/restricted references and a dedicated service to maintain referential integrity. Exact per-class processing details and backup expiry remain TODO; no legal retention period is inferred.

## 3. Staff roles and editorial approval

AI-assisted material is internal draft input only. The approved architecture requires human review before publication and evidence-backed human approval/activation for formula versions. Source snapshots and review/publication events preserve who acted and when.

| Conceptual role | Minimum responsibility | Boundaries |
|---|---|---|
| Author/editor | Create and revise Playbooks, Modules, Lessons, Practice definitions and sources; prepare formula proposals where authorized | Draft/edit only; cannot publish just because content or AI output exists. |
| Reviewer | Inspect exact revision, source provenance, assumptions, readability and safety; record review outcome | Review applies to a pinned revision; changes after review require review again. |
| Approver/publisher | Approve and publish an exact reviewed content revision; record an event | Permission to approve/publish is distinct from edit permission. For published financial content, approver differs from author; formula activation requires second-person approval. |
| Administrator | Manage staff accounts/access and operational configuration | Should not automatically receive access to learner financial records or authority to approve content/formulas. Separate operational access from editorial authority. |

### Workflow implications

- **Editorial revision:** every review/approval references an immutable revision; edits after approval create/reopen a revision and invalidate approval for changed content.
- **Formula activation:** formula authoring, formula review and activation are privileged actions. Activation requires the formula version, test cases/expected results, assumptions, source/reference, reviewer, approval time and explicit activation record. A database state field alone is not approval.
- **Source review:** the reviewer is associated with the source snapshot/content revision reviewed; mutable source catalog updates do not alter the old snapshot.
- **Publication:** only authorized approval/publication action advances the published pointer. AI generation cannot bypass a human action.
- **Audit:** preserve actor, role at the time, action, exact target revision/version and timestamp. Staff removal must not silently erase the historical action.

### Owner-approved role and separation policy

**OWNER-APPROVED:** Roles are Author/Editor, Reviewer, Approver/Publisher, and Administrator. Author/editor drafts; Reviewer evaluates an exact immutable revision; Approver/Publisher authorizes publication; Administrator manages staff/operations without automatic access to learner financial data. Author and approver must differ for published financial content. Formula activation requires second-person approval. Staff MFA is required. Events preserve actor, role, exact revision/version and time. Editing after approval requires renewed review/approval.

## 4. Calculator numeric policy

The approved architecture requires deterministic server-side decimal-safe calculations with versioned formulas, explicit units/assumptions, tests and immutable results. It does not define supported currencies, precision, formula catalog, rounding mode, or whether conversions are in scope. Do not invent formulas or store money as binary floating-point values.

### Currency direction

| Candidate | Benefits | Costs / unanswered questions |
|---|---|---|
| KES-only | Clear Kenyan context; fewer unit conversions and simpler initial UI/validation | May not fit users whose income, savings, goals or assumptions are denominated in another currency. Requires an explicit decision about rejecting or manually converting such inputs. |
| Multi-currency from day one | Models the user's context more flexibly; makes currency explicit throughout | Requires supported currency set, conversion policy/source/date, cross-currency arithmetic rules, display and testing. Multi-currency without FX still requires same-currency validation and may broaden initial scope. |
| KES-first, extensible currency field | Prioritizes Kenyan examples while retaining a currency code with each monetary value; can reject mixed-currency calculations until a formula defines conversion | Needs explicit initial supported-code policy and no implicit conversion. More disciplined than assuming every user's circumstances are KES-only. |

**OWNER-APPROVED:** MaliLab is KES-first; every monetary value carries an explicit currency; KES is the initial supported currency unless an approved calculator specification adds another. Representation is extensible. No implicit FX conversion; FX is future scope. The remaining formula-specific numeric details below are not universal policy decisions.

### Numeric decisions required per calculator

| Dimension | Policy question / safe distinction |
|---|---|
| Monetary values | Define allowed input range, whether negative values are allowed for a given field, and whether storage uses fixed `numeric(p,s)` or canonical decimal strings inside immutable JSON snapshots. Never use float/double for exact financial values. |
| Calculation precision | Decide working precision and intermediate precision separately from what is displayed. Preserve exact inputs and formula/version so a result can be reproduced. Do not round each intermediate operation merely to match the UI. |
| Display precision | Define per output whether to show whole KES, cents, or another scale; do not infer display scale from stored scale. |
| Percentages/rates | Define whether user-facing values are typed as e.g. percent while internal representation is a decimal ratio; specify allowed precision/range and whether a rate is nominal/effective, annual/monthly, and compounding basis. Do not invent formula semantics. |
| Rounding | Select a named deterministic rounding rule at the output boundary and per formula where required. Record it in FormulaVersion and CalculationResult. Define tie behavior and negative-value behavior if relevant. |
| Dates | Store instants with timezone for events, but model financial dates as calendar dates where time-of-day is not meaningful. Specify start/end inclusion, leap-year and month-end behavior per calculator. |
| Durations | Use explicit period unit (day/month/year) and convention; do not store an ambiguous bare duration number. Define fractional-period handling per formula. |
| Units | Every non-scalar quantity has an explicit unit and conversion rule. Reject incompatible units rather than silently converting. |
| Inflation/income change | Define whether assumptions are annual/monthly, nominal/real, applied at period boundaries, and how they interact with currency and rounding per formula. |

The owner needs to approve an initial formula/catalog contract before calculator results are used with real user values. A single universal precision cannot be chosen responsibly before representative formulas and ranges are known. Decimal type families and canonical string snapshots in Phase 5 remain proposals pending that contract.

## 5. Note highlight and content anchor

Every note should preserve its exact `LessonRevision`; where a selection is attached, it also needs a stable block identity. Revisions are immutable, so the historical anchor should continue pointing at the text the learner saw. New lesson revisions must never silently retarget a note.

| Strategy | Strengths | Weaknesses |
|---|---|---|
| A. Block ID only | Small and stable through block reordering; straightforward on web/mobile | Identifies the whole block, not the selected passage. Insufficient for a highlight selection. |
| B. Character offsets within block | Precise while the exact text is unchanged; compact | Offsets become invalid after text edits, rendering normalization, Unicode/grapheme differences or selection changes. Revision pinning limits this to the original revision but rendering/mobile differences remain. |
| C. Selected text + block ID | Human-readable and survives some rendering changes; can relocate a quote within the same block | Repeated text can be ambiguous; exact quote fails after punctuation/text changes. Needs size/privacy limits and a stale/ambiguous result. |
| D. Block ID + text quote + offsets | Quote helps identify text; offsets give a fast exact match when unchanged; exact revision preserves historical source | More data and validation; offsets are only a hint and must not override a quote mismatch. Requires a defined normalization/selection format. |
| E. Rich annotation protocol (DOM paths, prefix/suffix, range serialization, cross-version matching) | May improve reattachment across content edits and complex renderers | More fragile implementation and migration surface; can appear to promise automatic re-anchoring that is not approved. Premature for initial reading product. |

### Owner-approved anchor semantics

**OWNER-APPROVED:** Use exact LessonRevision + stable ContentBlock ID + selected text quote + optional character offsets as hints. The revision, block ID and quote are authoritative; offsets never silently move a note when underlying text differs. Notes stay on the historical revision; newer content may indicate that context. No automatic cross-revision reanchoring. Normalization/rendering details may be refined during UI work without violating these guarantees. Advanced reanchoring remains future scope.

## 6. Practice Attempt → Module Requirement

The approved model separates a Practice definition/revision from a learner's submitted Attempt. Requirement Evidence links one exact Attempt and PracticeRevision to one exact Requirement within one exact ModuleRevision. Module Completion cites accepted evidence for each required requirement. The relationship can store multiple evidence associations, but it does not itself say that every association counts.

| Policy | Learning meaning | Benefits | Risks / model behavior |
|---|---|---|---|
| A. One accepted attempt satisfies exactly one requirement | Each evidence decision has one clear curriculum purpose | Simple explanation and no accidental duplicate completion; straightforward progress display | A deliberately broad Practice activity reused for multiple learning requirements may require separate submissions or duplicate attempts. |
| B. One accepted attempt may satisfy multiple requirements | A single integrated activity can demonstrate multiple outcomes | Avoids repetition where one complex Practice genuinely covers several requirements | Each requirement still needs a separate explicit evidence link and rationale; careless reuse can inflate completion or make achievements hard to explain. New Module revisions must not inherit old acceptance implicitly. |

### Owner-approved initial semantics

**OWNER-APPROVED:** One accepted Practice Attempt satisfies one Module Requirement initially. Keep the physical evidence structure capable of multiple explicit associations for future use, but do not infer multi-credit from reused Practice revisions or other similarities. Each accepted RequirementEvidence is explicit. ModuleCompletion evaluates the exact requirement set for the exact ModuleRevision. Evidence does not carry forward to a new ModuleRevision. Corrections/reassessment preserve prior history. Future multi-requirement activities require explicit per-requirement evidence decisions.

Clarify correction/reassessment separately: a new or corrected evidence decision must preserve the prior decision and any ModuleCompletion snapshot. A new ModuleRevision always has its own requirement set; evidence does not migrate to it automatically.

## 7. Cross-decision dependencies

| Dependency | Why decisions interact |
|---|---|
| Authentication → ownership → deletion | Account identity is the root of every private owner FK. Recovery and contact changes affect identity matching. Deletion policy decides whether those FKs cascade, remain protected, or are anonymized, and how Journey Steps/awards reference private records. |
| Account and staff identity → editorial/audit history | Staff authentication and role lifecycle determine who may review/publish/activate. If a staff account is disabled/deleted, durable review/publication events need actor retention or anonymization rules. |
| Staff roles → human review → formula activation | Formula activation needs a reviewer/approver and explicit approval evidence. Same-person policy and role grants determine whether workflow provides independent review or only recorded self-review. |
| Numeric policy → Practice → CalculationResult → PlanRevision | Practice input schemas define units and ranges; formula contracts define arithmetic/rounding; saved results preserve exact method and outputs; plans snapshot assumptions and reference results. A numeric policy change must create new formula/result versions and must not rewrite prior plans. |
| Note anchors → content block schema/versioning | Anchor data depends on stable block IDs and text normalization. Renderer/schema changes must preserve original revision and determine whether quote/offset matching remains possible. |
| Attempt-to-requirement policy → evidence → ModuleCompletion → achievements | The approved one-accepted-attempt/one-requirement rule constrains completion; future multi-requirement practice requires explicit evidence per requirement. Exact evidence snapshots preserve explainability for awards. |
| Deletion → audit → backups | A live-row deletion policy is incomplete unless actor events and backup copies have defined handling. Do not infer that database cascade is an account-deletion strategy. |

## 8. Phase 6 gate

The six owner decisions in this brief are **resolved**. Their implementation rules are recorded in Phase 5C reconciliations. Remaining calculator-specific and operational TODOs are listed below and are not blanket blockers for the schema foundation.

| Decision | Current status | Owner decision required? | Blocks Phase 6? | Affected models | Affected tests |
|---|---|---:|---|---|---|
| Account/authentication | **OWNER-APPROVED** | No | No; implement approved model/policy | UserAccount and all owner FKs | Email identity, verification, recovery, session, anonymous/personal route checks |
| Deletion/retention | Hybrid direction **OWNER-APPROVED**; per-class processing and backup expiry TODO | No for schema; details before deletion/export service and production data policy | Not a blocker for safe core schema; deletion workflow/production retention remains gated | Account and user-owned/derived records, audit references, backups | Access disable, class disposition, referential integrity, editorial retention, backup expiry/restore |
| Staff roles/MFA/separation | **OWNER-APPROVED** | No | No; implement approved permission policy | Staff identity, reviews, publication, formula approval | MFA, role grants, second-person constraints, audit attribution |
| Currency/numeric policy | KES-first/extensible and decimal-safe policy **OWNER-APPROVED**; per-calculator precision/range TODO | No for generic schema; calculator-specific spec before each calculator | Not a blocker for generic Django/Postgres schema; blocks calculations lacking a defined formula contract | FormulaVersion, CalculationResult, Practice/Plan snapshots | Exact decimal, explicit currency/unit, rounding, date/duration and reproducibility per formula |
| Note anchor semantics | Revision/block/quote with optional hint offsets **OWNER-APPROVED**; normalization/render specifics TODO | No | Not a blocker; retain versioned anchor payload and exact revision relation | Note, LessonRevision, ContentBlock | Reorder/edit/removal, quote mismatch, offsets do not move anchor, historical pin |
| Attempt-to-requirement semantics | One accepted attempt satisfies one requirement **OWNER-APPROVED** | No | No; direct implementation constraint | PracticeAttempt, RequirementEvidence, ModuleCompletion, UserAchievement | No inferred second credit, exact revisions, reassessment history |

Phase 6 still requires explicit owner authorization. UI/UX specifications remain a prerequisite for implementing user-facing flows. Exact calculator catalog/precision and age eligibility remain product decisions for their respective features; backup expiry is operational. These do not block the schema foundation if kept explicit. Future social login, FX conversion, advanced cross-revision note reanchoring, and payment entitlements remain out of initial scope.

## 9. Recommended decision set

### Recommended Default Implementation Practices

- Use Django-managed session/authentication security primitives for the same-origin web product; do not write custom password/session handling.
- Keep owner checks application-level on every path, do not trust client-supplied owner IDs, and use the approved hybrid deletion service with no account-wide cascade.
- Keep staff permissions separate from learner data; preserve reviewer/approver actor and exact revision/version in durable events. Require a human approval action before publication/formula activation.
- Use decimal-safe server-side arithmetic, explicit units, formula-pinned immutable results, and separate calculation precision from display rounding. Never use binary floating point for exact financial values.
- Follow the owner-approved KES-first policy with explicit currency, decimal arithmetic and no implicit FX; keep precision/ranges formula-specific.
- Follow owner-approved revision-local Note anchor semantics; never move notes across revisions automatically.
- Follow owner-approved one-accepted-attempt/one-requirement rule with explicit evidence and preserved reassessment history.
- Follow the approved hybrid deletion lifecycle and protected references; no model-level cascade.

These implementation practices apply already approved product decisions. They do not fill in remaining formula-specific, operational or UI behavior.

### OWNER-APPROVED

1. Custom Django user; email/password; verified email for full personal features; email recovery; server-side sessions; anonymous public reading; account required for personal persistence.
2. Hybrid account deletion lifecycle; no account-wide cascade; editorial retained; necessary/minimized audit only; backup expiry separate.
3. Four staff roles; staff MFA; distinct author and approver for published financial content; second-person formula activation; revision-pinned actor/role/time events; reapproval after edits.
4. KES-first extensible; explicit currency on each monetary value; no implicit FX; decimal-safe arithmetic; separate calculation/display precision; deterministic formula-specific rounding.
5. Revision-local note anchor: exact revision + stable block ID + quote + optional hint offsets; no cross-revision automatic reanchor.
6. One accepted Practice Attempt satisfies one Module Requirement initially; explicit evidence; no automatic carry-forward; reassessment preserves history.

### Future Decisions

- Social login/provider and account linking.
- Multi-currency conversion/FX rates and provenance.
- Advanced reanchoring across new lesson revisions.
- More detailed support-access workflow, analytics/aggregation and retention schedule after product scope is approved.
- Entitlements/payments, mobile-client identity/API, and expanded staff workflow tooling.

### Future / TODO (not owner blockers for the schema foundation)

- Age/eligibility policy and appropriate review.
- Exact backup expiry schedule and operational deletion propagation.
- Calculator catalog and per-calculator precision/ranges/rounding/date/duration/unit conventions; exact extended unit catalog.
- Note text normalization/rendering and stale-quote presentation details, within approved anchor guarantees.

## Phase boundary

This briefing records decision options and the owner-approved outcomes; detailed reconciliations are in the Phase 5 specifications and audit. No models, migrations, database, dependencies, infrastructure, nginx/systemd, or deployment changes are made. `/home/opc/malilab_legacy` remains outside scope.
