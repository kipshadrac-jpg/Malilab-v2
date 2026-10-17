# MaliLab — Codex Master Build Instructions
## Product Definition → Architecture → Implementation → Deployment

**Project:** MaliLab  
**Working directory:** `/home/opc/malilab`  
**Legacy project:** `/home/opc/malilab_legacy`  
**Status:** New project from scratch  
**Owner:** Project owner  
**Codex role:** Engineering agent / implementation partner  
**Primary audience:** Kenyan users across working and aspiring working classes

---

# 0. How Codex Must Use This Document

This document is the master execution plan for building the new MaliLab.

Codex MUST work through the phases in order.

Do not skip phases because a later task appears obvious.

Do not implement application code until the relevant product and architecture documents have been approved by the project owner.

When a phase says **STOP**, Codex must stop and wait for the next instruction.

When requirements are missing, Codex must write `TODO/TO-BE-DEFINED` rather than inventing product decisions.

The project owner and ChatGPT define product intent. Codex translates approved intent into documentation, architecture, code, tests, and deployment.

---

# 1. Non-Negotiable Project Rules

## 1.1 New project

The new MaliLab is independent of the retired application.

The legacy application exists at:

`/home/opc/malilab_legacy`

Treat it as historical reference only.

Do not copy or inherit its:

- models
- database design
- views
- URLs
- templates
- APIs
- frontend
- architecture
- deployment structure

unless the owner explicitly requests a specific reference.

## 1.2 Scope control

Codex must not:

- invent product features
- invent business rules
- invent financial claims
- invent Kenyan regulatory requirements
- make unsupported investment promises
- silently introduce major architecture decisions
- install dependencies before the relevant architecture phase
- modify nginx before deployment phase
- create systemd services before deployment phase
- modify `/home/opc/malilab_legacy`
- delete unrelated server files
- modify unrelated system services

## 1.3 Documentation before implementation

Important decisions must be documented before implementation.

Material decisions must be recorded in:

`DECISIONS.md`

Product requirements belong under:

`docs/product/`

Architecture decisions belong under:

`docs/architecture/`

Database decisions belong under:

`docs/database/`

API decisions belong under:

`docs/api/`

UI/UX decisions belong under:

`docs/ui/`

Security decisions belong under:

`docs/security/`

Testing decisions belong under:

`docs/testing/`

Deployment decisions belong under:

`docs/deployment/`

## 1.4 Verification

Every implementation phase must include:

1. what changed
2. files changed
3. tests run
4. test results
5. remaining known issues
6. whether the phase is complete

---

# 2. Product Definition

## 2.1 What MaliLab means

MaliLab combines:

- **Mali** — Swahili for wealth
- **Lab** — a place dedicated to intensive research, experimentation, investigation, and discovery

MaliLab is therefore designed as:

> A Kenyan financial research-and-learning environment where people study how money works in Kenya, experiment with their own financial circumstances, understand what the Kenyan financial ecosystem can support, and turn what they learn into a practical financial-freedom plan.

MaliLab is not simply a finance blog.

MaliLab is not a generic online course platform.

MaliLab is not intended to copy US-centric personal-finance education.

Its central context is the Kenyan financial ecosystem.

---

# 3. Target Users

MaliLab should serve working and aspiring working Kenyans across different income levels and occupations.

Examples include:

- school-going young people who want to understand money
- university/college students
- employed young adults
- informal workers
- boda boda riders
- mama mboga and small traders
- freelancers
- professionals
- entrepreneurs
- business owners
- corporate executives
- people preparing for retirement

The product should not assume that every user has:

- a formal salary
- a bank account
- investment experience
- high disposable income
- advanced financial knowledge

The system should be capable of adapting explanations and practical scenarios to different financial realities.

---

# 4. Three-Month Outcome

A major product goal is that after approximately three months of meaningful use, a user should be able to define:

> A realistic financial-freedom direction and timeframe based on their own income, circumstances, assumptions, and chosen strategy.

The platform should help the user understand:

- what financial freedom means for them
- how much income they may want/need
- what resources they currently have
- how much they can potentially allocate
- how long different scenarios may take
- what assumptions drive the result
- which Kenyan financial instruments or structures may be relevant
- what they still need to learn

MaliLab must not guarantee financial outcomes.

---

# 5. Core Product Model

The core learning architecture is:

`PLAYBOOK → MODULE → LESSON → PRACTICE → MY PLAN`

with supporting systems:

`NOTES`
`LAB TOOLS`
`DICTIONARY`
`PROGRESS`
`BADGES`

---

# 6. Playbooks

## 6.1 Definition

A Playbook is the primary discovery and marketing entry point into MaliLab.

A Playbook begins with a realistic financial situation, question, ambition, or problem.

It should allow a person to recognize themselves in a scenario.

Example:

> A 20-year-old boda boda rider earns approximately KES 800 per working day and wants to stop depending on boda boda work by age 32.

The Playbook does not simply provide a financial answer.

It explores the situation and identifies the knowledge, decisions, experiments, and tools that can help the person investigate the path.

## 6.2 Playbook goals

A Playbook should:

1. attract discovery/search traffic
2. describe a relatable Kenyan financial situation
3. create curiosity
4. explain what needs to be understood
5. connect the user to relevant Modules
6. introduce practical experiments
7. lead toward personal planning
8. recommend related Playbooks naturally

## 6.3 Playbook structure

A Playbook may contain:

- long-form cover
- title
- short description
- scenario
- starting assumptions
- financial context
- questions to investigate
- relevant Modules
- practical experiments
- Lab Tools
- related Playbooks
- possible next steps

Do not assume every Playbook has exactly the same number of sections. Define reusable content structures while allowing editorial flexibility.

---

# 7. Modules

## 7.1 Definition

A Module is a structured domain of financial knowledge.

Examples may include:

- Treasury Bills and Bonds
- SACCOs
- Money Market Funds
- Insurance
- Emergency Funds
- Retirement
- Credit
- Tax
- Banking
- Business finance
- Other Kenyan financial ecosystem domains

These are examples, not a final list.

## 7.2 Module structure

A Module may contain:

- cover
- title
- description
- introduction
- ordered Lessons
- practical activities
- Lab Tool references
- related concepts
- Dictionary references
- related Playbooks
- completion criteria
- badge/achievement metadata

Example concept:

`Treasury Bills & Bonds`

could contain lessons progressing from:

1. What it is
2. Important terminology
3. Understanding how terminology applies
4. Practical account/setup concepts
5. How the instrument works
6. Applying the knowledge to a personal scenario

The exact curriculum must be defined later.

---

# 8. Lessons

Lessons are the primary learning units.

The lesson experience should prioritize:

- skimmability
- short paragraphs
- strong hierarchy
- meaningful spacing
- frequent subheadings
- bold key insights
- lists where appropriate
- clear examples
- Kenyan context
- practical explanation
- visual organization
- connections to other concepts

MaliLab should feel like a carefully designed reading/listening-library experience even though voice is NOT part of this project.

The design should feel closer to:

- a curated digital library
- a book/story collection
- a premium editorial learning environment

than a conventional LMS dashboard.

Reference screenshots supplied by the owner are visual inspiration only.

Do not copy them.

---

# 9. Practice

Practice is where MaliLab becomes a "Lab".

Practice should connect knowledge to the user's own situation.

A practice activity can ask questions such as:

- What income would make you comfortable?
- What financial target are you trying to reach?
- What resources do you currently have?
- What can you realistically allocate?
- How long might a target take?
- What assumptions affect the outcome?
- Which Kenyan financial instruments could potentially support the strategy?

Practice should use Lab Tools such as calculators where appropriate.

Practice is exploratory, not a guarantee.

---

# 10. Lab Tools

Calculators are part of the practical research environment.

Potential tool categories include:

- savings projections
- compound growth
- contribution scenarios
- target-date calculations
- income replacement scenarios
- inflation scenarios
- investment-return sensitivity
- debt/repayment scenarios
- emergency-fund scenarios

The final calculator catalogue must be defined later.

Tools must clearly show:

- inputs
- assumptions
- formulas or methodology where appropriate
- outputs
- sensitivity/scenario changes
- limitations
- educational context

Do not present hypothetical calculations as guaranteed financial outcomes.

---

# 11. My Plan

My Plan is the user's personal planning workspace.

It should grow naturally from learning.

Concept:

`LESSON → INSIGHT → NOTE → MY PLAN → LAB TOOL → PERSONAL SCENARIO`

The user should be able to take what they learn and attempt to construct a personal financial direction.

My Plan should eventually be capable of holding:

- financial goals
- target dates
- current assumptions
- income information
- savings/investment assumptions
- scenarios
- notes
- decisions
- selected tools
- learning references

The exact data model must be designed during the architecture phase.

---

# 12. Notes

Notes are context-aware learning notes.

The user should be able to:

- highlight useful information
- save an insight
- write a note
- connect a note to a Lesson
- potentially send an insight into My Plan

Notes should not become a generic disconnected note-taking app.

The purpose is to connect:

`WHAT I LEARNED → WHAT I THINK → WHAT I PLAN`

---

# 13. Learning Completion

MaliLab should not define learning solely as reading/click completion.

A meaningful learning achievement should combine:

`MODULE COMPLETION + PRACTICAL PLAN ATTEMPT`

This means a person:

1. studied a structured financial topic
2. attempted to apply the knowledge to a personal situation

Badges can represent successful advancement.

The exact badge system is to be defined during product design.

---

# 14. Progression

Progress is primarily driven by Playbooks and applied learning.

Example:

`Playbook discovered`
→ `Relevant Module selected`
→ `Lessons studied`
→ `Practice experiment`
→ `Module completed`
→ `Plan attempted`
→ `Badge`
→ `Related Playbooks discovered`
→ `Further Modules`

The platform should allow exploration rather than forcing a rigid single-course path.

---

# 15. Knowledge Network

MaliLab should eventually become a knowledge environment for the Kenyan financial ecosystem.

Important entities may include:

- financial instruments
- financial institutions
- terminology
- concepts
- laws/regulations where appropriate
- financial strategies
- scenarios
- lessons
- modules
- playbooks

These should eventually be cross-linked.

---

# 16. MaliLab Dictionary

The Dictionary is a future core knowledge feature.

It should explain Kenyan financial terminology in accessible language.

Examples might include:

- CDS account
- Treasury Bill
- Treasury Bond
- Yield
- Coupon
- SACCO
- MMF
- CRB
- other relevant terms

Dictionary entries should be linkable from Lessons and Playbooks.

The final taxonomy is TODO/TO-BE-DEFINED.

---

# 17. Homepage Philosophy

The homepage should prioritize discovery through Playbooks.

It should NOT feel like a generic LMS dashboard.

The user should be able to discover financial journeys based on questions such as:

- What am I trying to solve?
- What am I trying to understand?
- What financial goal am I trying to reach?
- What situation describes me?

The homepage should feature carefully designed Playbook covers and summaries.

Modules can be discovered as part of the broader library.

The exact navigation architecture is still to be designed.

Avoid assuming conventional bottom navigation or generic dashboard patterns without design justification.

---

# 18. Visual Direction

The supplied reference screenshots establish a direction, not a template.

The intended feeling is:

- organized
- editorial
- calm
- premium
- approachable
- book/library-like
- discovery-oriented
- highly readable
- mobile-first
- visually structured

Module covers can visually resemble books or collections.

Playbooks should have longer, richer covers and strong summary descriptions.

The design must be original to MaliLab.

Do not reproduce another platform's exact layout, typography, icons, colors, or interaction patterns.

---

# 19. Content Production AI

AI is primarily MaliLab's internal research and content-production assistant.

It should help the owner:

- structure research
- organize lessons
- draft lessons
- transform supplied research into structured content
- create Playbook drafts from supplied scenarios
- keep content in the prescribed editorial format
- speed up content production

AI must follow explicit editorial instructions.

AI is not the central user-facing product identity.

The user-facing product does NOT require a general AI chatbot as part of this specification.

Voice/speaker interaction is explicitly OUT OF SCOPE for the MaliLab project.

---

# 20. Editorial Rules

Content should favor:

- short 2–4 line paragraphs
- frequent subheadings
- bold key insights
- lists over walls of text
- intentional whitespace
- clear progression
- examples
- practical application
- accessible explanations
- Kenyan context

Content should avoid:

- unnecessary jargon
- giant text walls
- generic US assumptions
- unsupported claims
- false certainty
- guaranteed financial outcomes
- excessive marketing language

---

# 21. Monetization

MaliLab is intended to become a monthly subscription service in the future.

However:

**Subscription/payment implementation is NOT part of the initial build plan.**

The first phase should be free so the owner can observe:

- how people use MaliLab
- what content attracts users
- what people value
- where people stop
- which Playbooks perform well
- which Modules create meaningful engagement

Architecture should avoid making future subscription/entitlement impossible, but payment processing should not be implemented now.

---

# 22. Product Measurement

Potential product signals include:

- Playbook discovery
- Playbook engagement
- Module starts
- Lesson completion
- Practice attempts
- Lab Tool usage
- My Plan creation
- Module completion
- Plan attempts
- badges earned
- related Playbook exploration
- return usage
- content usefulness

Do not define final KPIs until product analytics requirements are explicitly approved.

---

# 23. Safety and Financial Content

MaliLab is educational.

It must distinguish:

- educational information
- hypothetical scenarios
- calculations
- assumptions
- personal financial decisions

Financial calculations must expose assumptions and limitations where relevant.

The system must not turn illustrative scenarios into promises.

When regulatory, tax, rates, product availability, or institutional details are included, the content system should support source attribution and content review.

Exact source/review architecture must be defined later.

---

# 24. Initial Product Documents to Create

During the Product Definition phase, Codex should create:

`docs/product/VISION.md`

`docs/product/PRODUCT_MODEL.md`

`docs/product/USERS.md`

`docs/product/PLAYBOOKS.md`

`docs/product/MODULES.md`

`docs/product/LESSONS.md`

`docs/product/PRACTICE.md`

`docs/product/MY_PLAN.md`

`docs/product/NOTES.md`

`docs/product/PROGRESS.md`

`docs/product/DICTIONARY.md`

`docs/product/LAB_TOOLS.md`

`docs/product/CONTENT_SYSTEM.md`

`docs/product/MONETIZATION.md`

Also update:

`PROJECT.md`

`ROADMAP.md`

`DECISIONS.md`

Do not implement application code during this phase.

---

# 25. Product Definition Phase Prompt

Use this prompt in Codex:

---

We are beginning MaliLab Phase 2: Product Definition.

Read `/home/opc/malilab/PROJECT.md` and this master specification first.

Convert the approved product direction into a coherent product specification.

Create and populate:

- docs/product/VISION.md
- docs/product/PRODUCT_MODEL.md
- docs/product/USERS.md
- docs/product/PLAYBOOKS.md
- docs/product/MODULES.md
- docs/product/LESSONS.md
- docs/product/PRACTICE.md
- docs/product/MY_PLAN.md
- docs/product/NOTES.md
- docs/product/PROGRESS.md
- docs/product/DICTIONARY.md
- docs/product/LAB_TOOLS.md
- docs/product/CONTENT_SYSTEM.md
- docs/product/MONETIZATION.md

Update:

- PROJECT.md
- ROADMAP.md
- DECISIONS.md

Rules:

1. Translate the owner's defined product intent accurately.
2. Do not invent missing requirements.
3. Mark unresolved questions TODO/TO-BE-DEFINED.
4. Separate confirmed requirements from proposed ideas.
5. Do not select the technology stack.
6. Do not write application code.
7. Do not initialize frameworks.
8. Do not create database schemas.
9. Do not create migrations.
10. Do not install dependencies.
11. Do not modify nginx.
12. Do not modify systemd.
13. Do not touch `/home/opc/malilab_legacy`.

The product specification must clearly distinguish:

- Playbooks
- Modules
- Lessons
- Practice
- Lab Tools
- My Plan
- Notes
- Progress
- Badges
- Dictionary
- Content production AI

Explain how these concepts connect.

Pay special attention to the product loop:

Playbook → Module → Lesson → Practice → My Plan → Progress

The final documentation should be detailed enough that a later architecture phase can translate it into a domain model without guessing.

At the end:

1. show the created/updated files
2. summarize confirmed requirements
3. list unresolved product decisions
4. identify contradictions, if any
5. propose questions that require owner approval
6. STOP

Do not implement anything.

---

# 26. Product Review Gate

After Codex completes Phase 2, the owner must review the documentation.

Do NOT proceed to architecture until:

- product model is coherent
- Playbook model is clear
- Module/Lesson relationship is clear
- Practice model is clear
- My Plan purpose is clear
- learning completion definition is clear
- homepage philosophy is clear
- AI role is clear
- monetization scope is clear
- unresolved questions are visible

---

# 27. Architecture Phase

Only after Product Definition approval, begin architecture.

Codex must evaluate:

- frontend architecture
- backend architecture
- API architecture
- database architecture
- content architecture
- search architecture
- media architecture
- authentication
- authorization
- analytics
- AI/content tooling
- caching
- deployment
- observability
- testing
- security
- future subscription readiness

Do not choose technology based on familiarity alone.

Evaluate options against:

- mobile-first UX
- content-heavy reading
- interactive calculators
- structured content
- search/discovery
- future scale
- maintainability
- server resources
- development speed
- security
- cost
- Kenyan operational realities

Create architecture documents before implementation.

Suggested outputs:

`docs/architecture/SYSTEM_ARCHITECTURE.md`

`docs/architecture/DOMAIN_MODEL.md`

`docs/architecture/FRONTEND.md`

`docs/architecture/BACKEND.md`

`docs/architecture/CONTENT_ARCHITECTURE.md`

`docs/architecture/AI_ARCHITECTURE.md`

`docs/architecture/SEARCH.md`

`docs/architecture/MEDIA.md`

`docs/architecture/ANALYTICS.md`

`docs/architecture/SECURITY.md`

`docs/architecture/SCALABILITY.md`

`docs/deployment/ENVIRONMENTS.md`

`docs/deployment/SERVER.md`

`docs/testing/TEST_STRATEGY.md`

No application implementation until the architecture gate is approved.

---

# 28. Database Phase

After architecture approval:

Define the domain model before creating migrations.

Likely conceptual domains include:

- users
- profiles
- Playbooks
- Modules
- Lessons
- Lesson content
- content blocks
- practice activities
- Lab Tools
- calculator scenarios
- plans
- notes
- progress
- badges
- Dictionary entries
- concepts
- relationships
- content sources
- editorial/review states
- analytics events

These are conceptual examples only.

Codex must derive the actual schema from approved requirements.

For every entity define:

- fields
- types
- relationships
- ownership
- constraints
- indexes
- lifecycle
- audit needs
- deletion behavior
- privacy classification

Then STOP for review before migrations.

---

# 29. UI/UX Phase

Design the mobile-first experience before implementation.

Core surfaces should include:

- Home/discovery
- Playbook detail
- Module detail
- Lesson reader
- Practice
- Lab Tools
- My Plan
- Notes
- Progress
- Dictionary
- Profile/account

Design goals:

- book/library feeling
- highly readable lessons
- strong discovery
- minimal cognitive overload
- clear progression
- meaningful visual hierarchy
- original MaliLab visual identity

Do not blindly reproduce reference screenshots.

Create:

`docs/ui/UX_PRINCIPLES.md`

`docs/ui/INFORMATION_ARCHITECTURE.md`

`docs/ui/DESIGN_SYSTEM.md`

`docs/ui/SCREEN_SPECIFICATIONS.md`

`docs/ui/LESSON_READER.md`

`docs/ui/PLAYBOOK_EXPERIENCE.md`

`docs/ui/MY_PLAN.md`

---

# 30. Implementation Phase

Only after Product + Architecture + Database + UI specifications are approved.

Implementation rules:

1. Work in small verifiable phases.
2. Do not implement the entire product in one uncontrolled operation.
3. Write tests alongside meaningful functionality.
4. Keep documentation synchronized.
5. Use migrations deliberately.
6. Never silently change approved architecture.
7. Record material changes in DECISIONS.md.
8. Verify each phase before moving on.

Suggested implementation sequence:

1. project foundation
2. authentication/user foundation
3. content/domain foundation
4. Module/Lesson system
5. Playbook system
6. lesson reader
7. practice framework
8. Lab Tools
9. My Plan
10. Notes
11. progress/badges
12. Dictionary
13. search/discovery
14. analytics
15. admin/content production
16. security hardening
17. testing
18. deployment

The exact sequence may change after architecture.

---

# 31. Content Management / AI Authoring

A later internal authoring system should allow the owner to:

1. define research instructions
2. provide source material
3. ask AI to structure content
4. review the draft
5. edit
6. approve
7. publish
8. associate content with Modules/Playbooks
9. attach sources
10. update content later

AI-generated content must remain subject to human review before publication unless a future explicit policy says otherwise.

---

# 32. Deployment Phase

Only after the application is tested locally/in the target environment.

Deployment must:

- preserve SSH access
- avoid unnecessary server changes
- use controlled environment configuration
- avoid exposing secrets
- configure nginx deliberately
- configure systemd deliberately
- provide health checks
- provide logs
- provide rollback/recovery procedures
- document deployment

The existing healthy nginx installation may be reused.

Do not remove or modify unrelated server configuration.

---

# 33. Server Rules

Current environment:

- Oracle Linux 9.8
- x86_64
- Codex CLI 0.160.1
- nginx active
- `/home/opc/malilab` is the new project
- `/home/opc/malilab_legacy` is the retired project

Codex must not modify:

`/home/opc/malilab_legacy`

unless explicitly instructed.

The current project should remain inside:

`/home/opc/malilab`

---

# 34. Phase Gates

## Gate 1
Project foundation complete.

## Gate 2
Product Definition approved.

## Gate 3
Architecture approved.

## Gate 4
Domain/database design approved.

## Gate 5
UI/UX approved.

## Gate 6
Implementation begins.

## Gate 7
Testing and hardening.

## Gate 8
Production deployment.

Codex must not cross a gate without explicit owner approval.

---

# 35. Definition of a Successful MaliLab

The project should ultimately enable a Kenyan user to:

1. discover a financial situation or goal that feels relevant
2. enter through a Playbook
3. understand why certain knowledge matters
4. study relevant Modules
5. read well-designed Lessons
6. perform practical experiments
7. use Lab Tools with their own assumptions
8. capture useful Notes
9. build a personal My Plan
10. complete meaningful learning
11. receive evidence of progress
12. discover related financial knowledge
13. continue researching their financial path

The final product should feel like:

> **A place to research your way toward better financial decisions in the Kenyan ecosystem.**

Not merely:

> A website containing finance courses.

---

# 36. Final Codex Instruction

Until a phase is explicitly approved:

- do not implement the next phase
- do not invent requirements
- do not make silent architecture decisions
- do not modify unrelated infrastructure
- do not touch the legacy application

When uncertain:

**STOP and ask.**

When requirements are missing:

**DOCUMENT THE GAP.**

When a major decision is needed:

**PROPOSE OPTIONS AND RECORD THE DECISION.**

When implementation is approved:

**BUILD SMALL, TEST, VERIFY, DOCUMENT, THEN CONTINUE.**
