# Deletion and Retention Specification

**Owner-approved direction:** use a hybrid account lifecycle. A deletion request disables access, enters controlled deletion/export processing, removes or anonymizes identifiable user data by data class, retains editorial data, retains only necessary/minimized audit history, and handles backup expiry separately. Exact processing details and operational backup schedule remain TODO/TO-BE-DEFINED; no legal period is inferred. No account-wide cascade is permitted. A dedicated service will orchestrate deletion/export rather than model-level cascading.

| Relationship class | Recommended `on_delete` | Reason / condition |
|---|---|---|
| Revision → stable editorial identity | `PROTECT` | Preserve exact identity and historical provenance; retire identity rather than delete referenced revisions. |
| Published revision → source snapshot/media/requirements/relationships | `PROTECT` | Prevent broken historical editorial rendering/context. |
| User-owned parent → purely owned response/value child | `PROTECT` by default; deletion service removes/anonymizes in an ordered transaction according to data class | No database cascade as account-wide policy; preserve referential integrity during controlled processing. |
| User owner → attempts, plans, revisions, results, journey, notes, progress/evidence/awards | `PROTECT`/restricted | Prevent silent erasure and maintain referential integrity; controlled service may remove/anonymize after dependencies are processed. |
| Plan → PlanRevision; journey → JourneyStep; attempt → response | `PROTECT` | Deletion service handles dependencies explicitly; historical records are not implicitly cascaded. |
| PracticeAttempt → CalculationResult optional relation | `SET_NULL` only if result remains independently owned and attempt can be removed under policy; otherwise `PROTECT` | Preserve calculation and avoid false attempt linkage. Must be selected with account deletion policy. |
| Governance event → actor | `PROTECT` until deletion service processes actor references; then approved actor anonymization/detachment with role snapshot | Audit treatment is separate from learner financial data; preserve minimized action history without claiming an exact retention duration. |
| Audit/history → formula/revision/result/evidence | `PROTECT` | Append-only history requires targets. |
| Optional current pointer → revision | nullable pointer may be cleared when identity retired; revision itself remains | Identity without current public revision is valid when retired/unpublished. |
| Media file → MediaAsset row | no delete while referenced; storage garbage collection only after reference/retention check | Preserve published and historical rendering. |
| SearchProjection → source revision | projection may `CASCADE`/be deleted and rebuilt when eligibility changes | Derived, not canonical; published-only. |

### Remaining implementation detail before deletion/export workflow

1. Per-class exact delete/anonymize behavior, ordering, and export contents/format.
2. Backup expiry schedule and deletion propagation; backup deletion is operational and not immediate DB deletion.
3. Detailed actor-reference anonymization and minimal audit fields.
4. Age/eligibility policy and any appropriate review; no age rule is assumed.

The lifecycle direction itself is approved; the remaining details do not block the core Django schema. The deletion/export service and production data handling must not ship until the corresponding details are resolved. Production user data requires off-host backups and validated restore under the deployment architecture.
