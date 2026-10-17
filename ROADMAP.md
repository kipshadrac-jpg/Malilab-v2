# MaliLab Roadmap

This roadmap tracks owner-approved phase gates. Product/architecture/data documents remain authoritative for scope. No implementation phase begins without explicit owner authorization. Under owner decision GOV-001, the existing independent Phase 6A acceptance audit satisfies the Phase 6A acceptance gate. `PROJECT.md` status is reconciled with the later execution authorization in GOV-002. GOV-002 records the later explicit owner authorization to execute the planned Phase 6B application slices; existing schema and production-operation gates remain in force.

## Phase 1 — Project foundation

**Status:** Complete.

Established the documentation workspace, project constitution, decision process and roadmap.

## Phase 2 — Product Definition

**Status:** Approved by owner.

Product vision, target users, core loop, initial scope, financial-freedom framing, editorial direction, safety boundaries, internal AI role and future monetization boundary are documented. Remaining product decisions stay marked TODO/TO-BE-DEFINED.

## Phase 3 — Architecture

**Status:** Approved with required refinements incorporated.

Modular-monolith architecture, domain boundaries, security, calculation governance, source provenance, search candidate and conditional deployment principles are documented.

## Phase 4 — Domain Model and Database Specification

**Status:** Formally approved by owner; audit findings reconciled.

The conceptual/logical data model and its audit/reconciliation under `docs/database/` are authoritative. It includes ordered append-only Learning Journey Steps, exact revision references, same-owner private references, Requirement Evidence, optional calculation links, immutable Plan Revisions, and exact Module Completion evidence.

## Phase 5 — Physical Implementation Specification

**Status:** Reconciled with owner-approved Phase 5C decisions; approved for implementation. The Phase 6A foundation is implemented and accepted by the existing independent audit (GOV-001). This does not itself authorize Phase 6B.5 implementation.

The Django/PostgreSQL model mapping, fields, constraints, indexes, versioning, ownership, deletion, search, media, migration and testing requirements are under `docs/implementation/`. The six original implementation blockers are resolved in DB-019 and the Phase 5B brief. Remaining age/eligibility, backup expiry, calculator-specific, and detailed rendering items remain at their later feature or operational gates. See `docs/implementation/PHASE_5_AUDIT.md` and the Phase 6A implementation report.

## Phase 6 — Django/PostgreSQL Implementation

**Status:** Phase 6A foundation and remediation round 3 complete under explicit owner authorization; independent acceptance is satisfied by the existing audit (GOV-001). Phase 6B application implementation proceeds under GOV-002, with separate schema and production-operation gates retained. `PROJECT.md` reflects the authorization while preserving separate schema and production-operation gates.

The Phase 6A Django/PostgreSQL foundation and remediation rounds are documented in the [round 3 report](docs/implementation/PHASE_6A_REMEDIATION_ROUND3_REPORT.md) and prior remediation reports. The implementation preserves approved account/authentication, hybrid deletion, staff/MFA, revision-local note-anchor and one-attempt/one-requirement policies. Formula activation governance, real financial formulas, full media pipeline, production deployment, full email delivery, and registration/recovery UI remain deferred. The existing independent acceptance audit satisfies the Phase 6A gate under GOV-001. `PROJECT.md` now records the GOV-002 authorization. PostgreSQL compatibility and unresolved consequential choices remain Phase 6B completion gates.

## Phase 7 — Testing and hardening

**Status:** Not started. Phase 6A automated acceptance and PostgreSQL schema verification are recorded in its implementation report; further system-wide hardening remains future work.

Define and execute the approved automated, security, privacy and operational test plan after implementation exists.

## Phase 8 — Deployment

**Status:** Not started; separate authorization required.

Capacity validation, off-host backup, restore validation, recovery and deployment planning must precede production data. The retired legacy application remains isolated and untouched.
