# Physical Data Model Specification

**Specification status:** Phase 5 specification reconciled with owner-approved Phase 5C decisions. This document remains the approved physical contract; it is not itself Django code or SQL. **Current implementation status:** Phase 6A remediation round 3 is implemented and verified in the PostgreSQL 16.15 `malilab` development database. A fresh independent acceptance audit remains required; Phase 6B remains blocked until it passes. Calculator-specific values and future policies remain open.

## Authority and modeling levels

The approved product and Phase 3 architecture define behavior. `docs/database/` is the authoritative domain/logical contract, including its audit and reconciliation. This document proposes a Django/PostgreSQL mapping. Where a physical choice would settle an unresolved product rule, it is explicitly left open and implementation is gated for that feature.

| Level | Meaning | Phase 5 result |
|---|---|---|
| Domain | Product concepts, ownership and rules | Approved in Phase 4 |
| Logical | Entities, relationships, lifecycle, constraints and evidence | Approved in Phase 4B |
| Physical | Django model/table/type/index/constraint mapping | Proposed here; no schema created |

## Recommended physical baseline

- Django modular monolith; PostgreSQL is the sole relational authority.
- Use `BigAutoField`/PostgreSQL `bigint` primary keys for internal rows. IDs are never authorization tokens; public identifiers should use slugs or opaque route identifiers where needed. Revisit UUIDs before external integrations or cross-system identity requirements.
- Use explicit `ForeignKey` relationships for ordinary associations, immutable revision references, and all user-owned records. Avoid implicit many-to-many tables where relationship order, revision, state or rationale matters.
- Store all timestamps as timezone-aware instants (`timestamptz`); distinguish occurrence time from server-recorded time where the logical model requires both.
- Use PostgreSQL `JSONB` only for bounded, versioned block/response/assumption/result/anchor snapshots. Validate with allow-listed schemas in domain services. Exact decimal values inside JSON snapshots are canonical decimal **strings**, never binary floats.
- Monetary amounts carry explicit currency. Initial supported currency is KES; representation is extensible and FX conversion is excluded. Exact values use PostgreSQL `numeric`/Django `DecimalField` where appropriate; formula-specific precision/scale, ranges and rounding are defined per calculator. Never use float/double for exact financial values.
- Stable editorial identities are mutable only for controlled metadata/current pointers; published revisions and saved learner evidence are immutable through application services.
- Foreign keys to historical revisions/results/evidence use `PROTECT` (or PostgreSQL `RESTRICT`) unless a child is a purely owned value with no historical meaning. Account deletion is not a DB cascade.

## Physical app boundaries

See `DJANGO_DOMAIN_STRUCTURE.md`. Initial physical app proposal is `accounts`, `content`, `practice`, `calculations`, `planning`, `learning`, and `discovery`. Content owns source/editorial governance, media metadata and authored revisions; `learning` owns explainable progress/evidence and achievements. No app is created in this phase. Dictionary is future-only.

## Resolved implementation policy

- Use a custom Django user model/stable account identity, email + password initially, verified email for full account functionality, email-based recovery, and Django-managed server-side sessions. Anonymous users may read public content; an account is required for persistence and private features. Phone/OTP and social login are future. Age/eligibility remains TODO and must not be inferred.
- Hybrid account lifecycle: disable access first; process export/deletion; remove or anonymize identifiable user data by class; retain editorial records and only necessary/minimized audit history; handle backups by separate expiry policy. No account-wide cascade.
- Staff roles are Author/Editor, Reviewer, Approver/Publisher, Administrator. Author and approver must be different people for published financial content. Formula activation requires second-person approval; staff MFA is required. Audit events preserve actor, role, exact revision/version and timestamp.
- KES-first, explicit currency per monetary value, no implicit FX. Calculation precision differs from display precision; rounding is deterministic and formula-specific. Formula-specific bounds, precision and conventions are set per calculator.
- Notes pin LessonRevision + stable block ID + selected quote; optional character offsets are hints only. No cross-revision automatic reanchor.
- One accepted Practice Attempt satisfies one Module Requirement in initial completion semantics. Physical associations remain flexible, but every accepted association is explicit; no inferred multi-credit. Reassessment preserves prior evidence.

## Remaining scope and blockers

The complete model/table inventory is in `MODEL_SPECIFICATIONS.md`; field mapping is in `FIELD_SPECIFICATIONS.md`. The six Phase 5 owner decisions are resolved. Remaining TODOs include age/eligibility, backup expiry schedule, calculator catalog and formula-specific ranges/precision/rounding/unit conventions, exact launch unit catalog, and note text normalization/rendering details. These do not block a safe schema foundation when represented explicitly, but their feature behavior must not be invented. Plan cardinality remains zero-to-many without an invented uniqueness rule.

Journey steps use a controlled typed-reference registry and per-target association records rather than an unrestricted generic foreign key. This retains one stable JourneyStep target FK, exact target FKs, and permits new target kinds by adding a target association type rather than a column to JourneyStep. See `MODEL_SPECIFICATIONS.md`; if this integrity-preserving adapter proves too costly, revisit before implementation rather than dropping FK integrity silently.

## Physical safeguards

Application services enforce owner scope, editorial state transitions, immutable snapshots, formula activation evidence, same-owner references, and append-only ordering. DB unique/check/FK constraints backstop invariants that PostgreSQL can express. Cross-row and cross-table invariants require transactional service validation and tests; do not pretend a normal CHECK constraint can enforce them.
