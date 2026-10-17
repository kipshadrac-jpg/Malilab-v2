# Django Domain Structure

**Status:** Proposed modular-monolith package boundary; no project/apps initialized.

| Django app/domain | Responsibilities and owned models | References/dependencies | Required now? |
|---|---|---|---|
| `accounts` | Custom Django user model/stable account identity; email/password initial auth; verified-email state; Django server-side session integration and account lifecycle state | Referenced as owner/actor by private and governance models; email-based recovery; no phone/OTP or social login initially | Yes; owner-approved identity policy |
| `content` | Playbook/Module/Lesson/Practice identities and revisions; requirements/recommendations/related links/topics; source/snapshots; reviews/publication events; media metadata; achievement definitions | `accounts` actors; no user-owned data | Yes |
| `practice` | PracticeAttempt and validated response snapshots | `accounts`, exact `content` PracticeRevision, optional journey target; emits evidence inputs to learning and calculation context | Yes |
| `calculations` | LabTool, CalculatorDefinition, FormulaVersion/Approval, saved CalculationResult and immutable method/input/output snapshots | `accounts`, `content` formula/catalog/source references, optional PracticeAttempt | Yes for approved initial Lab Tools |
| `planning` | MyPlan and immutable PlanRevision snapshots/references | `accounts`, `practice`, `calculations`, journey/content references; must not depend on progress | Yes |
| `learning` | LearningJourney/Step, LessonCompletion, RequirementEvidence, ModuleCompletion, Achievement award | `accounts`, exact content revisions, PracticeAttempt, CalculationResult, PlanRevision; downstream consumer of evidence | Yes |
| `discovery` | Rebuildable SearchProjection and query boundary, potentially implemented inside `content` initially | Reads only eligible published content; no writes to canonical content/user records | Required only to UX-approved search extent; can remain a service/module in `content` |
| `dictionary` | Future DictionaryTerm/DefinitionRevision | Content references only if approved | No; future |

### Boundary rules

- Use seven logical responsibilities but avoid one app per entity. `discovery` may remain a module within `content`; do not create an independent service.
- Cross-domain writes go through explicit application/domain services with one transaction boundary where required. No direct model-save chains that hide ownership or lifecycle rules.
- `learning` consumes facts from practice/planning/calculations. Practice, calculations, and planning never require a Progress query to function.
- `content` never owns learner Notes, responses, plans, results, or progress. Content revisions are referenced by exact FK.
- Anonymous readers may read public published content through the content-access policy. An authenticated, verified account is required for persistent personal features.
- Formula code/method lives behind calculation-domain services, not templates, frontend code, model methods, or arbitrary endpoints.
- No separate apps for sources, review, media, badges, or topics; they remain content-owned subdomains until independent lifecycle/scale needs are demonstrated.
- Staff roles are Author/Editor, Reviewer, Approver/Publisher, and Administrator. Staff MFA is required. Administrators manage staff/operations but do not gain learner financial-data access by default. The approver differs from the author for published financial content; formula activation requires second-person approval.

### App dependency direction

`accounts` is foundational. `content` has no dependency on learner state. `practice`, `calculations`, and `planning` reference accounts/content and each other only through specified records. `learning` consumes exact records from all of them. `discovery` reads a published-only projection. No circular dependency, event broker, worker, or microservice is required initially.
