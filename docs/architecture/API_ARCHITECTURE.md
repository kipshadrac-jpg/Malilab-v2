# API and Application Interface Architecture

**Status:** Accepted architecture direction. No routes, APIs, or application source code have been created.

## 1. API posture

MaliLab has no approved external API consumer or native application requirement. The initial system should therefore be capability-oriented and server-rendered, not API-first:

- Browser navigations use authenticated or public (policy TBD) server-rendered routes.
- Forms submit commands to application services and return rendered pages/redirects.
- Narrow same-origin JSON operations may support calculator/scenario interactions where UX requires immediate updates.
- Internal domains communicate through application service interfaces, not HTTP calls to themselves and not direct cross-domain record mutation.
- No public REST, GraphQL, webhook, partner, or mobile API is part of initial scope.

This approach avoids an endpoint for every record and leaves a versioned API as a future adapter if an approved consumer appears.

## 2. Capability boundaries

| Capability | Initial interface | Data returned/changed | Authorization boundary |
|---|---|---|---|
| Discover and read Playbooks/Modules/Lessons | Rendered pages and query-string filters | Current published content only | Anonymous public reading is allowed through the content-access policy; drafts never exposed. Persistent personal features require an authenticated, email-verified account. |
| Search published content | Rendered search results; optional JSON only if UX requires it | Search projection references and public snippets | Published content only; exclude private user data; access policy is checked before rendering content. |
| Submit Practice | Same-origin form; optional JSON for interactive input only | Owner's attempt and references to activity version | Authenticated user; verify activity published and all target objects owner-scoped. |
| Explore calculator | Same-origin JSON request/response or form submission | Validated inputs, assumption explanation, versioned result | Server validates all values; no trust in client outputs. Persistence requires explicit save action and account ownership. |
| Save/update My Plan/Note | Same-origin forms and redirects; JSON only where UX requires | User-owned revision/note | Authenticated owner; CSRF protection and per-object authorization. |
| Editorial create/revise/review/publish | Staff-only rendered admin/editor routes | Draft revisions, review actions, publication event | Staff capability checks; only authorized publication action makes content public. |
| Account/session | Framework-provided same-origin forms/session | Account status and session | Secure cookie/session boundary; account methods TBD. |

Exact route shapes depend on the later UI specification; this document intentionally does not freeze URLs.

## 3. Internal application-service contracts

The eventual application layer should expose use-case operations such as:

- resolve current published Playbook/Module/Lesson revision and relationships;
- publish an approved revision and update its search projection transactionally;
- validate and execute a named calculator formula version;
- save a Practice attempt and its optional scenario context;
- create a plan revision with a validated owner and calculation references;
- attach a Note to a specific content revision/block;
- record explainable Progress facts and evaluate only owner-approved achievement criteria.

These are capability descriptions, not final function signatures. Services enforce authorization and transaction boundaries. They should return domain results/errors that presentation adapters render consistently.

## 4. Security and request rules

- Same-origin session authentication for browser interactions; protect state-changing browser requests against CSRF.
- Authenticate before reading/writing private records; authorize by record owner, not only by an ID supplied in a URL or payload.
- Staff authorization is separate from learner ownership. Only explicit editorial permission can review/publish.
- Published content reads go through one content-access policy boundary. Initial policy does not require payment/subscription entitlement; a future policy can add entitlement checks without duplicating them in each route.
- Validate server-side types, ranges, units, content version state, relationship validity, and ownership.
- Escape rendered text and render only allow-listed structured content blocks; never execute user or AI HTML.
- Do not accept client-calculated results as authoritative. Calculation outputs come from the server-side engine.
- Do not expose drafts, reviewer comments, unpublished sources, secrets, or private financial inputs through response errors.

## 5. Errors, validation, and response behavior

Use consistent internal error categories: invalid input, unauthenticated, unauthorized/not-owned, not found/not published, state conflict (e.g., stale revision), and unexpected service failure. Browser routes render accessible actionable errors. JSON errors use stable machine-readable codes plus safe user-facing messages and field-level validation details where useful. Do not return stack traces, database details, or sensitive input values.

Exact response envelope and status mapping are implementation decisions. If an external API is later approved, define and version a formal public error contract separately.

## 6. Pagination and versioning

Paginate lists that can grow (search results, admin content lists, user notes/progress) using stable ordering and bounded page size. Exact page size is TBD from UX. A public API does not exist, so no API version prefix is required initially. Content revision identifiers are not API versions. Any future external API should version its contract independently and define deprecation policy.

## 7. Idempotency and duplicate actions

Browser forms should defend against accidental repeated submission through redirects/state checks and stable operation semantics. For actions that may be retried after uncertain network response (e.g., creating a plan revision via JSON), an idempotency token/key may be needed. Exact operations are not selected; do not add a general idempotency subsystem before a retryable use case is defined.

## 8. Rate limiting

Some controls are justified for authentication abuse and high-cost calculation requests, but thresholds and enforcement are TODO/TO-BE-DEFINED after UX and hosting are known. Start with bounded calculation input sizes and normal request validation; introduce a proxy/application limit where a threat or measured load warrants it. Do not implement a distributed rate-limit service without need.

## 9. Asynchronous APIs

No asynchronous job API or callback is required initially. If future AI generation/media processing is long-running, introduce a job resource/status flow only alongside an approved worker/queue design. Do not make calculator results asynchronous absent measured latency needs.
