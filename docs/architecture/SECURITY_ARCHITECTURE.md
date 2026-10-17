# Security Architecture

**Status:** Accepted security architecture direction only. This is not a legal opinion or a claim of regulatory compliance; no controls have been implemented.

## 1. Assets and trust boundaries

Protect account credentials/sessions, private Notes, Practice responses, income and contribution assumptions, scenarios/calculation results, My Plan revisions, Progress, editorial drafts/review comments, source working material, database credentials, application secrets, backups, and published content integrity.

Trust boundaries:

1. Browser/client is untrusted; all user input and calculator results are revalidated server-side.
2. Reverse proxy is the network edge; only intended HTTP(S) traffic reaches the application.
3. Web process is the application trust boundary for account authorization and domain rules.
4. PostgreSQL and media storage are private application dependencies; no direct public access.
5. Staff/admin paths are higher impact and require least privilege and auditable publication actions.
6. An optional AI provider is an external boundary; never send user-owned financial data. Only explicitly supplied editorial material may be sent under a future approved provider/data policy.

## 2. Authentication and sessions

Use the owner-approved custom Django user model with email/password, verified email for full personal functionality, email recovery and Django-managed server-side sessions. Require secure cookie settings in deployment, CSRF protection for state-changing browser requests, safe session rotation, sensible session expiration and protected recovery. Anonymous published reading is allowed; persistent personal features require authenticated and verified email. Staff MFA is required. Phone/OTP and social login are future scope. Age/eligibility remains TODO; target users may include school-going people, so do not infer an age rule.

Do not implement token-based public API authentication until an API consumer is approved.

## 3. Authorization and isolation

- Learner can read/write only their own notes, practice attempts, scenarios, plans, progress, and achievements.
- Resolve ownership server-side on every operation. Do not trust submitted account IDs, plan IDs, or permission flags.
- Separate editor, reviewer/publisher, and platform-operation capabilities. Keep the initial role set small; exact staff roster and whether one person may hold multiple capabilities are TBD.
- Draft and review content is never served by public content queries.
- Publish/retire operations require explicit permission and create an audit event.
- Support role/permission checks in application services as well as presentation guards.
- Avoid staff access to user financial records unless a separately approved support need establishes narrow, audited access.

### Defense in depth for user-owned financial information

Application-level authorization is mandatory: use cases obtain the authenticated account from the session, scope each read/write to that owner, and verify ownership of every related Note, Practice attempt, Scenario, Calculation Result, Plan Revision, Progress record, and Achievement. Never authorize from a client-supplied owner ID. Shared list, search, export, and administrative paths require the same checks.

Authorization tests are required before release and must cover cross-account detail access, list/filter/query paths, update/delete, nested related-object IDs, stale IDs, and staff routes. A denial must reveal no record contents. Testing strategy and tooling remain for a later phase.

**PostgreSQL row-level security is not required for the initial architecture.** The first system has one trusted Django application and controlled DB access paths. Application ownership checks are the primary boundary; RLS would add connection-scoped identity state and migration/admin complexity without replacing those checks. Reconsider RLS if independent services, direct database consumers, or other access paths are introduced. Keep the database private and do not give staff direct access to user data by default.

## 4. Sensitive financial data

Treat plan targets, current/desired income, savings/contributions, investment assumptions, calculations, responses, and notes as sensitive personal data. Collect only fields needed for the user's explicit Practice/My Plan action. Keep these values out of public search indexes, shared caches, email/notifications, AI prompts, error messages, and operational logs. Use private responses and owner-scoped queries. At-rest encryption, field-level encryption, export/delete, retention, backup expiration, and jurisdictional questions require deployment/privacy review; do not assert obligations without evidence.

## 5. Application and content threats

| Threat | Initial mitigation direction |
|---|---|
| Cross-account IDOR/data disclosure | Central owner-scoped services; deny by default; tests later at authorization boundary. |
| Account takeover/session theft | Framework auth, TLS, secure cookies, CSRF, verified-email recovery controls, required staff MFA, authentication abuse limits. |
| Malicious or unsafe content/AI HTML | Typed allow-listed content blocks; output escaping; safe URL/asset validation; no raw HTML execution. |
| Draft content leaked | Query current published revision only in reader/search; separate staff permission and preview route. |
| Forged or stale calculation result | Server-authoritative deterministic calculator, formula version and assumptions snapshot; validate units/ranges. |
| Excessive calculator workload | Bound payload/input sizes; validate range/complexity; apply rate limiting if abuse/load evidence supports it. |
| Sensitive data in logs/analytics | Structured redaction; never log request bodies for financial routes; no advanced analytics by default. |
| Compromised editor account | Least privilege, staff authentication protections, audit content publication, review state. |
| Dependency/runtime compromise | Supported releases at build time, patch process, dependency review/scanning decision in testing/security phase. |
| Database/media theft or loss | Private network/socket, separate credentials, protected backups, restore procedure, limited filesystem permissions. |
| Source/content tampering | Immutable published revision record, audit publication events, backups and controlled editor permission. |
| Secrets leakage | Runtime secret injection/protected files outside repository; rotate on exposure; no secret logging. |

## 6. Admin and audit

Audit material editorial state changes (submit/review/approve/publish/retire), permission changes, and security-sensitive account actions. Avoid capturing note text, financial values, or entire request payloads in audits. Define audit retention and access policy later. Audit records support accountability but are not a compliance guarantee.

Editorial capability boundaries distinguish authoring, reviewing/approving, publishing, and platform operation. Whether these capabilities require different people, and whether an author may approve their own work, is TODO/TO-BE-DEFINED. Human review and explicit publish permission are required; AI generation alone cannot authorize either transition.

## 7. Account and staff policy prerequisites

Resolve before implementing account or editorial administration behavior:

- Registration uses the custom email/password account model, verified email for full personal features, and email recovery; anonymous published reading is allowed.
- Staff MFA and the minimum editorial roles/separation are owner-approved; implementation maps them to least-privilege permissions.
- TODO/TO-BE-DEFINED: age/eligibility policy and any appropriately reviewed safeguards.
- TODO/TO-BE-DEFINED: age policy for school-going users; investigate product/legal requirements without assuming them.
- TODO/TO-BE-DEFINED: per-class deletion/export processing, audit actor minimization, and operational backup expiry under the approved hybrid lifecycle.

Do not infer legal obligations or age restrictions in architecture.

## 8. Transport, infrastructure, and backup

Deployment design should use HTTPS at the reverse proxy, restrict DB and media access to the application, run the application under a dedicated least-privilege OS account, separate runtime secrets from code, and protect backups with access control/encryption. Exact firewall, TLS, patching, backup frequency, recovery objectives, and key handling belong to the deployment phase. No nginx/systemd change is made here.

## 9. Privacy lifecycle questions

TODO/TO-BE-DEFINED: data classification/notice and consent basis; user data export and deletion; retention for accounts, notes, plans, progress and backups; staff support access; minor-user safeguards; hosting/data residency requirements; applicable Kenyan legal/regulatory obligations. Seek qualified review when needed; architecture does not invent legal requirements.
