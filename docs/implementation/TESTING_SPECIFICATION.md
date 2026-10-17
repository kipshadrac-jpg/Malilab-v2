# Testing Specification

These are required future tests; none are created or run in Phase 5.

| Test group | Required assertions |
|---|---|
| Model constraints | Identity slug/revision uniqueness; positive revision/order; target-kind consistency; unique requirement/recommendation membership; active formula uniqueness; plan revision chain; nullable pointers valid. |
| Account/authentication | Custom user identity, normalized unique email, password/session behavior, verification gate for full personal features, email recovery, anonymous public reading, no personal persistence for anonymous/unverified users. |
| Ownership isolation | Two-account tests for every user-owned model: list, detail, nested IDs, filters, attach, update, delete, export and error messages. Foreign owner references fail closed. |
| Revision integrity | Published revisions, source snapshots, submitted attempts, saved calculations, plan revisions, journey steps, completions and awards cannot be silently edited/deleted; current pointers do not retarget historical refs. |
| Content lifecycle | Draft/review/approved/published/superseded/retired transitions; publication requires authorized human approval; AI-created draft cannot publish directly. |
| Structured blocks | Every allow-listed block validates; malformed/unknown schema is rejected or safely rendered; HTML/script payload is not executed; old schema versions retain compatible rendering. |
| Journey | Ordered unique append-only sequence; every target resolves to exact typed object; private target owner matches journey owner; adding step kinds requires association mapping, not JourneyStep schema mutation. |
| Requirement evidence | Exact ModuleRevision/Requirement/PracticeRevision/Attempt match; owner match; attempt submitted; duplicate pair blocked; one accepted attempt satisfies one requirement; no inferred credit for another requirement; reassessment creates preserved history. |
| Module completion | Explanation includes each exact required requirement, status and supporting evidence; incomplete requirement prevents Complete; new revision evaluation does not rewrite old completion. |
| Calculation reproducibility | Fixed formula artifact + canonical decimal inputs/assumptions reproduce stored result; no float drift; units/currency/precision/rounding/method/warnings/source snapshots preserved. |
| Formula governance | Illegal transitions fail; no activation without test cases, expected outputs, source, reviewer, approval timestamp and explicit action; second-person approval (author differs from activator); one active formula per definition; retired version remains available to old results. |
| Plan revisions | Every edit creates next immutable revision; predecessor belongs to same plan and is earlier; private evidence refs same owner; old plan comparisons never recalculate. |
| Notes/anchors | Note pins exact LessonRevision and block identity plus selected quote; offsets are hints only; changed text never silently moves selection; no cross-revision reanchor; test Unicode/render normalization and stale historical display. |
| Deletion behavior | Hybrid account lifecycle; access disabled before processing; data-class removal/anonymization preserves references; no account-wide cascade; editorial remains; minimized audit actor handling is separate; backup expiry is operational and separately tested. |
| Search privacy | Only eligible published revisions appear; drafts/retired and all user data excluded; projection rebuild matches canonical state; representative Kenyan query suite. |
| Media | Asset key/checksum immutable; new asset replacement preserves old revision; referenced asset cannot be removed; access does not expose private storage paths. |
| Authorization/editorial | Test approved role grants, required staff MFA, different author/approver for published financial content, second-person formula activation, renewed review after edits, and no staff default access to user finances. |
| Migration | Fresh install, upgrade from prior schema, idempotent data migrations, backup/restore rehearsal, rollback/forward-repair behavior. |
