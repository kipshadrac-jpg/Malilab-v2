# Ownership and Authorization Implementation Specification

**Baseline:** Django application-level authorization is mandatory. PostgreSQL RLS is not required initially under the approved single-trusted-application architecture. This is a design specification, not security code.

Account identity is owner-approved: custom Django user model, email/password, email verification for full personal functionality, email recovery and Django-managed server-side sessions. Public published reading is available anonymously. All persistent personal features require an authenticated, verified account. Phone/OTP and social login are future scope. Age/eligibility policy remains unresolved and is not inferred.

## Ownership path

| User-owned model | Required owner path |
|---|---|
| PracticeAttempt, PracticeResponse | Attempt → `UserAccount`; response → attempt → owner |
| LearningJourney, JourneyStep | Journey → owner; target registry owner must match for user-owned target |
| CalculationResult | Direct owner; optional PracticeAttempt same owner |
| MyPlan, PlanRevision | Plan → owner; all private references (attempt/result/journey/note where selected) same owner |
| Note | Direct owner; optional journey same owner; editorial revision is public/editorial reference only |
| LessonCompletion, RequirementEvidence, ModuleCompletion | Direct learner owner; attempt and related evidence same owner |
| UserAchievement | Direct owner; PlanRevision/completion evidence same owner |

## Mandatory application rules

- Derive owner from authenticated server context. Ignore/reject client-supplied `owner_id`.
- Scope every list/detail/update/delete query to owner before returning objects; validate nested relationship IDs against that same owner.
- On create/attach, verify every private relation belongs to same owner in the same transaction. This includes a journey target, calculation result attached to attempt, calculation/attempt/context attached to plan revision, and evidence/award references.
- Authorization applies to HTML routes, JSON endpoints, admin actions, exports, background/maintenance commands, and error paths. Unguessable IDs are not authorization.
- Editorial draft/review/publication permissions are separate from learner ownership. Staff have no default access to notes, financial inputs, plans, responses, or calculations. Any support access workflow requires explicit policy, purpose, audit, and review before implementation.
- Only authorized staff may create/edit drafts, review, approve, activate formulas, publish, supersede, or retire content. Author and approver must differ for published financial content; formula activation requires second-person approval. No role can publish AI draft without explicit human approval.
- Staff MFA is required. Roles are Author/Editor, Reviewer, Approver/Publisher and Administrator. Published financial content requires a different author and approver; formula activation requires a second person. Administrator access to learner finances is not automatic. Role actor and exact revision/version/time are captured in events.
- Calculations run trusted server-side formula versions after validated input. Never accept authoritative output or executable formula from clients.
- Search reads only published editorial projection. Caches must not mix authenticated user data with public content.
- Redact private financial values, note bodies, credentials, tokens and secrets from logs/errors/analytics.

## Defense-in-depth tests required

For every user model test list/detail/nested lookup/update/delete/attach/export using a second user's object ID. Test filters cannot broaden ownership; foreign JourneyTarget, plan revision, attempt, result, note or evidence references are rejected. Test staff routes do not expose private data by default. Test search indexes only published content and never private payloads.

Anonymous tests must confirm that public published reading works while Notes, Practice persistence/history, My Plan, Progress, Achievements, and every other persistent personal feature require a signed-in, email-verified account. Email verification and recovery flows must not reveal whether another person's account exists.

RLS may be revisited only if direct database clients, multiple applications, independent services, or broader database access paths are introduced; it does not replace application checks.
