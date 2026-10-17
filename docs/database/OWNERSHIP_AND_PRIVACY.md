# Ownership and Privacy Catalogue

Ownership is a primary data boundary, distinct from who edits or operates a record. The classification does not claim legal categories. User financial circumstances, assumptions, plans and responses are treated as sensitive by design.

## 1. Ownership classes

| Class | Meaning | Access/change rule |
|---|---|---|
| A. System-owned | Account, framework identity reference, technical state or governed formula artifact controlled by MaliLab. | Only trusted application/system processes; actor attribution for administrative changes. |
| B. Editorial-owned | Curated content, taxonomy, source catalog and media metadata owned by MaliLab editors. | Draft/review/publish staff permissions; public access only to eligible published revision through content-access policy. |
| C. User-owned | A user's private authored or financial context. | Exactly one account owner; application-level owner checks on every read/write/delete/list/nested reference. No client-supplied owner IDs trusted. |
| D. Derived | Rebuildable or evaluated state derived from canonical records/evidence. | Preserve explainable source references; owner-scope where user-specific; no independent authority over source facts. |
| E. Audit/history | Durable record of a decision/action/event. | Append-only conceptual record, limited access, actor/time, retention policy explicit; do not treat as an unrestricted generic log. |

## 2. Entity ownership assignment

| Entities | Primary class | Privacy/access boundary |
|---|---|---|
| User Account; framework authentication identity/session reference | A | Account/staff identity data; authentication policy unresolved. Credentials/session secrets remain framework-managed. |
| Playbook, Module, Lesson, Practice Activity, Tool, Calculator Definition and their authored revisions; learning requirements; recommendations; related links; topics; content-topic links; content blocks; achievement definitions/revisions; Dictionary terms/revisions (future); Media Asset metadata; Source catalog and Source snapshots | B | Drafts, unpublished revisions, editorial sources/comments are staff-only; published content can be read subject to access policy. |
| Practice Attempt/Response; Learning Journey Context/Journey Step; Calculation Result; My Plan/Plan Revision; Note | C | Private to owner by default. Numeric assumptions/answers/results receive sensitive handling; do not expose in search, analytics, logs or AI provider. |
| Lesson Completion, Requirement Evidence and Module Completion | D | User-scoped derived facts; private to that user, not public search. Evidence pins exact revision and attempt; ownership follows learner. |
| Search Projection | D | Published editorial data only; rebuildable; never user-owned data or drafts. |
| Formula Version | A | System-governed logic/version; editorial method/source may be displayed, code/config access remains restricted. |
| Formula Approval, Editorial Review, Publication Event, User Achievement | E | Actor/evidence/history; User Achievement also owner-private. Comments may contain staff-only material. Avoid duplicating financial values into audit messages. |

## 3. Authorization boundaries

1. Identity authenticates the account. Every user-data operation derives owner from trusted session/account context.
2. The application service checks ownership for parent and every nested/related private record. An unguessable ID is not authorization.
3. Cross-account references are rejected: a plan cannot attach another user's practice attempt or calculation result; a Journey Step targeting user-owned data must target the journey owner's record; Requirement Evidence, attempt, completion, and achievement evidence must belong to the same user. Editorial revision references remain editorial-owned and are not copied into user records.
4. Staff roles are separate from learner ownership. Editorial roles permit only assigned authoring/review/approval/publication capabilities. Staff do not receive broad My Plan/Note/financial-input access by default. Support-access policy remains TODO.
5. Public reader/search routes expose only approved published editorial revisions through a single access-policy boundary. Authentication requirement for reading remains unresolved; user private data never enters that projection.
6. Calculations accept validated input and execute trusted formula versions server-side. Clients cannot submit authoritative outputs or formula code.
7. AI content tools receive editorial source material only; no learner notes, responses, income, calculations or plans.

## 4. Defense in depth

Application-level owner checks are mandatory. Cross-account authorization tests are required for list, detail, nested IDs, filters, update, delete, relationship attachment, calculation save, plan revision and staff/admin routes. Test both direct IDs and guessed/foreign references; verify response errors do not reveal private values.

PostgreSQL row-level security is **not required** for the initial architecture: one trusted Django application is the controlled database access path, and owner scoping belongs in application services. RLS would add connection-scoped user context, admin/maintenance complexity, and migration risk while not replacing application checks. Revisit if independent services, direct DB consumers, multiple applications, or materially broader database access paths appear. Database credentials remain private and least-privileged.

## 5. Data minimization and unresolved policy

Collect only information needed for the approved core loop. Do not assume profile demographics, bank credentials, account balances, contact fields, or financial-product holdings are required. Define specific field collection only from approved product UX. Avoid financial values in logs/error messages and exclude them from public analytics. Registration, contact verification, age policy, export, deletion, sharing, retention, encryption details, staff support access and applicable legal review are TODO/TO-BE-DEFINED.
