# MaliLab Project Constitution

MaliLab is a new project. This constitution records the approved product direction and Phase 3 architecture with required refinements. Items that remain undecided are marked TODO/TO-BE-DEFINED. Phase 6A acceptance is satisfied by the existing independent acceptance audit, as recognized by GOV-001 in `DECISIONS.md`. Phase 6B execution is authorized by GOV-002 under the current owner directive. Preserve existing schema and migration authorization rules; unresolved consequential decisions and PostgreSQL compatibility remain implementation/acceptance gates. This does not authorize production infrastructure or later-phase work.

## 1. Project Vision

Be a place where people in Kenya can research their way toward better financial decisions in the Kenyan ecosystem. See [product/VISION.md](docs/product/VISION.md).

## 2. Product Mission

Help people study how money works in Kenya, experiment with their own financial circumstances, understand what the Kenyan financial ecosystem can support, and turn what they learn into a practical financial-freedom direction. MaliLab is a research-and-learning environment, not simply a finance blog or generic course platform.

## 3. Target Users

Working and aspiring working Kenyans across income levels and occupations, including young people, students, employed adults, informal workers, traders, freelancers, professionals, entrepreneurs, business owners, executives, and people preparing for retirement. Do not assume a formal salary, bank account, investment experience, high disposable income, or advanced financial knowledge.

## 4. Problems We Are Solving

MaliLab is intended to help users understand financial concepts in a Kenyan context, investigate situations relevant to them, and connect learning to practical personal planning. TODO/TO-BE-DEFINED: validate and prioritize specific user problems and evidence.

## 5. Product Principles

- Kenyan financial ecosystem is the central context; do not default to generic US-centric assumptions.
- Discovery begins with relatable financial situations and questions through Playbooks.
- Learning connects structured knowledge to practical exploration and personal planning.
- Encourage exploration rather than require one rigid course path.
- Make assumptions and limitations visible; never promise financial outcomes.
- TODO/TO-BE-DEFINED: further product principles and prioritization.

## 6. Functional Requirements

The confirmed product concepts and their relationships are specified in `docs/product/`. Initial core scope is Playbook → Module → Lesson → Practice → Lab Tool → My Plan → Progress, with minimum necessary Notes, user account/persistence, and learning achievement support, plus basic discovery/search where required by approved UX. The full Dictionary, advanced analytics, sophisticated recommendations, large-scale knowledge graph, advanced AI user assistant, subscriptions/payments, and voice/audio are future or out of scope. Content production AI is internal and human-reviewed; it is not a required general user-facing chatbot. Exact behaviors not stated in product documents remain TODO/TO-BE-DEFINED.

## 7. Non-Functional Requirements

The intended experience is mobile-first, highly readable, calm, approachable, editorial, and visually structured. MaliLab is an editorial reading and interactive learning platform with an organized, curated book/story/library feel; that reference does not imply audio functionality. TODO/TO-BE-DEFINED: measurable performance, accessibility, compatibility, availability, privacy, and other quality requirements.

## 8. Architecture Principles

- Derive architecture from approved product requirements; do not select it by familiarity alone.
- Preserve the possibility of future subscription entitlements without implementing payments in the initial build.
- Do not use the retired application as the architectural foundation.
- Phase 3 architecture and its required refinements are documented under `docs/architecture/` and approved. The Phase 5 physical specification is approved. Phase 6A acceptance is satisfied by the existing independent acceptance audit under GOV-001 in `DECISIONS.md`. Phase 6B application implementation is authorized by GOV-002. GOV-001 remains limited to Phase 6A acceptance. Schema changes, live database changes, and production operations remain governed by their existing separate authorization rules.
- Record material decisions in `DECISIONS.md`; do not cross later phase gates without explicit owner approval.

## 9. Technology Strategy

The approved Phase 3 direction is a Django modular monolith, PostgreSQL, server-rendered frontend, and a single relational source of truth. See `docs/architecture/TECHNOLOGY_DECISIONS.md`. Phase 6A currently uses the dependency versions recorded in `requirements.txt`; this does not authorize later-phase dependencies.

## 10. Database Principles

Derive data from approved product and architecture requirements. Phase 3 accepts PostgreSQL as the database technology. Phase 4 specifies the domain and logical data model under `docs/database/`; the approved Phase 5 physical specification maps it to Django/PostgreSQL. The clean PostgreSQL 16 development database is the current authority. Remaining retention and formula-specific decisions stay TODO/TO-BE-DEFINED.

## 11. API Principles

The approved Phase 3 direction is server-rendered routes and internal application-service interfaces, with narrow same-origin JSON operations only where interaction requires them; no public API-first surface is included initially. See `docs/architecture/API_ARCHITECTURE.md`. Specific future public API needs and contracts remain TODO/TO-BE-DEFINED.

## 12. UI/UX Principles

Favor Playbook-led discovery and a curated digital library or book-like editorial reading and interactive learning experience over a generic LMS dashboard. The direction is original to MaliLab, mobile-first, organized, calm, premium, approachable, and readable. There is no speaker button, voice conversation, text-to-speech, podcast/audio lesson requirement, voice learning mode, or audio-first lesson format. Reference screenshots, if supplied, are inspiration only. Exact navigation and screen designs remain TODO/TO-BE-DEFINED.

## 13. Security Principles

Phase 3 and Phase 4 specify the security architecture and logical ownership/privacy boundaries. Phase 5C decisions specify custom-user email/password authentication, verified-email personal access, session handling, anonymous public reading, staff roles/MFA, and the hybrid account deletion direction; see `DECISIONS.md` DB-019. TODO/TO-BE-DEFINED: age/eligibility, per-class deletion/export details, backup expiry, and any applicable regulatory requirements. Financial content should distinguish educational information, hypothetical scenarios, calculations, assumptions, and personal decisions; support source attribution and review when current rates, products, or institutional details are presented.

## 14. AI/Automation Principles

AI is an internal research and content-production assistant for structuring research, drafting and organizing content, and preparing drafts from supplied material or scenarios. Human review is required before publication. A general user-facing chatbot is not required by this specification; an advanced AI user assistant is future scope. Voice and audio functionality are out of scope. Further AI workflow and data-handling requirements remain TODO/TO-BE-DEFINED.

## 15. Testing Strategy

TODO/TO-BE-DEFINED during architecture and implementation planning. Product acceptance criteria are not yet fully defined.

## 16. Deployment Strategy

Deployment architecture is documented for later review in `docs/architecture/DEPLOYMENT_ARCHITECTURE.md`. No production deployment, nginx, or systemd configuration is authorized by Phase 4.

## 17. Development Workflow

- Work through phase gates in order and stop at each required approval gate.
- Keep product requirements under `docs/product/`, architecture under `docs/architecture/`, and material decisions in `DECISIONS.md`.
- Do not invent unresolved requirements; record TODO/TO-BE-DEFINED.
- Do not implement application code before the applicable specifications and phase authorization are approved. Phase 6A acceptance is satisfied by the existing independent acceptance audit under GOV-001. Phase 6B implementation is authorized by GOV-002. Complete only behavior specified by the owner directive and approved records; retain unresolved consequential decisions and PostgreSQL compatibility as explicit acceptance gates.

## 18. Definition of Done

For Product Definition, the required product documents are populated, consistent with the master specification, and explicit about unresolved matters; the owner has approved Phase 2. For Architecture, domain and technical decisions are documented with alternatives, consequences, and unresolved decisions; Phase 3 has owner approval with required refinements incorporated. Phase 4 delivers the approved conceptual and logical data specification; Phase 5 provides the approved physical specification. Phase 6A acceptance is satisfied by the existing independent acceptance audit, as recognized by GOV-001 in `DECISIONS.md`. Phase 6B application implementation is authorized by GOV-002. PostgreSQL compatibility and unresolved consequential product decisions remain acceptance gates; GOV-002 does not authorize schema or production changes.

## 19. Architecture Change Rules

Material architecture choices must be documented with context, options, rationale, consequences, and status, and must not silently alter approved product requirements. Phase 3 decisions are recorded in `DECISIONS.md`; deferred product and deployment policy questions remain open.

## 20. Technical Debt Rules

TODO/TO-BE-DEFINED: prioritization and review cadence. Record future shortcuts and deferred work visibly with impact and follow-up when known.

## 21. Codex Working Rules

- Treat this as a new independent project; do not copy or inherit the legacy application's models, database design, views, URLs, templates, APIs, frontend, architecture, or deployment structure without explicit direction.
- Do not invent product features, business rules, financial claims, regulatory requirements, or investment promises.
- Keep unresolved requirements as TODO/TO-BE-DEFINED and separate confirmed intent from proposals.
- Do not cross a phase gate without explicit owner approval. GOV-002 is the explicit owner authorization for Phase 6B application implementation; it does not authorize schema or production changes.
- Do not install dependencies, initialize a framework, create database tables or migrations, or modify nginx/systemd outside their authorized phases. Phase 6A remediation may apply reviewed Django migrations to the clean MaliLab development database only.
- Do not modify `/home/opc/malilab_legacy` or unrelated files/services.
