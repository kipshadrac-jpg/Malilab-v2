# Field Catalogue

This is a logical field specification, not Django or PostgreSQL syntax. Type names are conceptual. Required/optional status describes domain validity; final nullability and encoding are physical choices. Privacy: E = editorial/public after publish, W = staff working, P = personal, F = sensitive financial, S = operational/system. Index shorthand is detailed in CONSTRAINTS_AND_INDEXES.md.

## Common conventions

Every independently identified record has a stable opaque ID (required, unique identity, immutable; privacy follows record). Mutable records have created/updated timestamps; immutable revisions/events have creation/action time and are corrected by new history, not mutation. User records have one authoritative owner reference, never accepted from client input as proof. Editorial revisions have parent identity, positive revision sequence unique per parent, controlled state, author/time and schema version. Published revisions are immutable. References use stable identities and exact revision IDs where historical meaning matters. Indexes are limited to documented query paths.

## User Account — System-owned

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| id | Stable account identifier | Req | Unique identity | P | Immutable |
| auth_subject | Framework identity reference | Req once auth is selected | Unique within selected auth system; never client owner input | P | Framework-managed |
| contact_identifier | Email/phone or other login reference | Optional pending auth policy | Normalize/unique only if chosen; never public-search indexed | P | Mutable; verification policy TBD |
| status | Account state | Req; initial state TBD | Controlled transitions; staff lifecycle query index only if needed | P/S | Mutable with history as required |
| staff_access_ref | Framework-managed permission reference | Opt | Validate via staff authorization system; no client input | P/W | Changes follow unresolved staff policy |
| created_at / updated_at | Timestamps | Req | No standalone index | S | Created immutable; updated mutable |
| deletion_state_at | Deletion/lifecycle timestamp or state ref | Opt | No standalone index | P/S | Meaning and workflow TBD |

No Profile or custom credential fields are approved. A privacy/consent state is not modeled until a product/data-handling basis is defined. Registration, login identifier, recovery, staff login/MFA, role grants, author/approver separation, age policy and account deletion remain TODO/TO-BE-DEFINED.

## Editorial identities

Applies separately to Playbook, Module, Lesson, Practice Activity, Lab Tool, Calculator Definition, Achievement Definition, Dictionary Term (future).

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| id | Stable identifier | Req | Unique identity | E/W | Immutable |
| slug | Normalized editorial key | Req to publish | Unique among active same-type identities; indexed | E | Controlled change; redirects/aliases unresolved |
| current_published_revision_id | Revision reference | Opt before first publish | One per identity; lookup index | E/W | Mutable pointer; Publication Event preserves history |
| lifecycle_state | Controlled state | Req; draft conceptually | Valid transitions; editorial queue index | E/W | Mutable with events |
| internal_owner | Staff reference | Opt | Staff identity validation | W | Mutable; role policy open |
| created_at / updated_at | Timestamps | Req | No standalone index | S | Created immutable; updated mutable |

## Editorial revisions

Applies to Playbook Revision, Module Revision, Lesson Revision, Practice Activity Revision, Achievement Definition Revision, Dictionary Definition Revision (future).

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| id | Stable revision identifier | Req | Unique; historical reference | E/W | Immutable |
| parent_identity_id | Typed identity reference | Req | Indexed; correct entity kind | E/W | Immutable |
| revision_number | Positive sequence | Req | Unique per parent; composite lookup index | E/W | Immutable |
| state | Editorial state | Req; Draft | Controlled lifecycle; editorial queue index | E/W | Transitions audited; payload immutable after publish |
| title | Text | Req for publication | Nonblank/bounded; search source | E after publication | Immutable after publication |
| summary / description | Text | Optional by type | Bounded/plain or typed content | E after publication | Immutable after publication |
| authored_payload | Structured values | Req by type | Allow-listed keys/types, size bounds, safe renderer | E/W | Immutable after publication |
| cover_asset_ref | Media reference | Opt | Must resolve to allowed Media Asset | E/W | Immutable in revision |
| authored_by / authored_at | Staff reference and time | Req for editorial history | Both present for authored revision | W/E | Immutable |
| published_at | Timestamp | Opt until publication | Consistent with state/event | E | Immutable historical time |
| schema_version | Content format key | Req | Supported renderer version | S/E | Immutable |

Type payloads: Playbook Revision has scenario, context, assumptions, intended outcome and discovery metadata; Module Revision has introduction, estimated effort and curriculum metadata; Lesson Revision owns content blocks; Practice Activity Revision owns prompt/instructions and response specification; Achievement Definition Revision owns display text and criteria reference; Dictionary Definition Revision owns structured definition and terminology metadata. Final required fields follow an editorial publish checklist still to be defined.

## Lesson Content Block

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| lesson_revision_id | Lesson Revision reference | Req | Indexed; correct type | E/W | Immutable after publication |
| block_id | Stable within-revision key | Req | Unique within revision; annotation anchor | E | Immutable after publication |
| position | Nonnegative ordinal | Req | Unique within revision; ordered retrieval | E | Immutable after publication |
| block_type | Allow-listed key | Req | Type-specific validator | E | Immutable after publication |
| payload | Typed structured value | Req | Schema and size validation; no arbitrary executable HTML/code | E/W | Immutable after publication |
| schema_version | Version key | Req | Renderer-supported | S/E | Immutable |

Possible types include heading, paragraph, list, callout, insight, example, table, image, reference, calculator, practice prompt and related concept. This is extensible, not a mandatory final list. Typed blocks permit safe rendering, targeted validation and schema evolution without one opaque HTML field.

## Module Learning Requirement

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| module_revision_id | Module Revision reference | Req | Indexed | E | Immutable after publication |
| target_revision_id | Lesson or Practice revision | Req | Must match target kind; indexed | E | Immutable after publication |
| target_kind | Controlled enum | Req | Lesson or Practice only | E | Immutable |
| classification | Enum | Req | Lesson and Practice: Required/Optional/Recommended; only Required blocks Module completion | E | Immutable |
| position | Nonnegative ordinal | Req | Unique within target-kind list of Module Revision | E | Immutable |
| completion_condition_ref | Versioned declarative rule key | TBD by item | Allow-list only, no arbitrary code | E/S | Pinned to Module Revision |
| active | Boolean | Req; true in final authored set | No inactive published requirement unless explicit policy | E | Immutable after publication |

## Playbook–Module Recommendation

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| playbook_revision_id | Playbook Revision reference | Req | Indexed | E | Immutable after publication |
| module_revision_id | Module Revision reference | Req | Indexed; exact target version | E | Immutable after publication |
| position | Nonnegative ordinal | Req | Unique in Playbook Revision list | E | Immutable |
| rationale | Bounded structured text | Opt | Safe text rendering | E | Immutable |
| active | Boolean | Req | Inactive links excluded from user display | E | Immutable |

## Related Content Relationship, Topic, Content–Topic Assignment

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| source_revision_id | Exact editorial revision | Req for relationship | Indexed | E | Immutable after publication |
| target_revision_id or topic_id | Exact revision or Topic | Req | Correct target type; indexed | E | Immutable after publication |
| relationship_kind / topic_role | Controlled vocabulary | Req | Only approved relation kinds | E | Immutable |
| position | Nonnegative ordinal | Opt | Unique per ordered source/role if present | E | Immutable |
| rationale | Bounded text | Opt | Safe text | E | Immutable |
| Topic.name / slug | Text/key | Req | Normalized unique label/key; discovery index | E | Editorially mutable; old revision display label may snapshot |
| Topic.description / state | Text/state | Opt/Req | Bounded; Active/Retired conceptually | E/W | Mutable with history if needed |

## Practice Attempt and Practice Response

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| attempt.id / owner_user_id | ID / User Account ref | Req | Owner indexed; owner never client-authoritative | P | Owner immutable |
| activity_revision_id | Exact Practice Activity Revision | Req | Indexed; revision must have been available | E reference | Immutable |
| journey_context_id | Same-owner Journey Context | Opt | Owner match | P/F | Immutable link |
| status | Controlled attempt state | Req; save/submit semantics TBD | Valid state transitions | P/F | Draft may edit by policy; submitted evidence immutable |
| started_at / submitted_at | Timestamps | Start req; submit opt | Chronology validation | P | Start immutable; submit set once |
| response_summary | Typed structured values | Opt | Bounded, validated against pinned prompt schema | P/F | Snapshot with attempt |
| response.attempt_id / prompt_key | Attempt ref / pinned prompt key | Req | Unique per attempt/prompt; indexed parent | P/F | Parent/prompt immutable |
| response.value | Typed answer | Req when answered | Validate type, units and range against pinned revision | P/F | Editable only while attempt policy permits |
| response.answered_at | Timestamp | Req when answered | No standalone index | P | Immutable per response version |

Each submitted Practice Attempt may have zero or more Requirement Evidence records. An attempt can be associated with multiple exact requirements in the logical model; whether each association is accepted for completion is determined by the evidence state and unresolved completion policy, not by relationship cardinality.

## Requirement Evidence

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| id | Unique record identifier | Req | Unique | P | Immutable |
| owner_user_id | User Account reference | Req | Same owner as Practice Attempt; indexed | P | Immutable |
| module_revision_id | Exact Module Revision | Req | Must be parent of requirement; indexed | E reference | Immutable |
| requirement_id | Exact Module Learning Requirement | Req | Must belong to module_revision_id and target Practice revision | E reference | Immutable |
| practice_revision_id | Exact Practice Activity Revision | Req | Must equal requirement target; indexed | E reference | Immutable |
| practice_attempt_id | Exact Practice Attempt | Req | Attempt must pin practice_revision_id and share owner; indexed | P reference | Immutable |
| evidence_state | Controlled decision state | Req | Accepted or Not Accepted; only Accepted satisfies a required item | P | Immutable decision tied to exact pair |
| recorded_at / evaluated_at | Timestamps | Req | Chronology; owner/revision query | P | Immutable |
| evaluation_context | Bounded structured explanation/reference | Opt | Must not copy unnecessary financial values; validation tied to requirement revision | P/F | Immutable with evaluation |

There may be multiple attempts and thus multiple evidence records for one requirement. There is at most one evidence decision for a given Practice Attempt + requirement pair. Module Completion records which accepted evidence it cites for each required item. A correction/reassessment workflow is TODO/TO-BE-DEFINED; it must preserve any prior Module Completion snapshot.

## Learning Journey Context

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| id | Unique record identifier | Req | Unique | P | Immutable |
| owner_user_id | User Account ref | Req | Indexed; owner boundary | P | Immutable |
| created_at | Timestamp | Req | Owner journey history query | S/P | Immutable |
| journey_context_snapshot | Relevant initial scenario/assumption values | Opt | Store only context needed, not editorial body | P/F | Immutable snapshot |

## Journey Step

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| id | Unique record identifier | Req | Unique | P | Immutable |
| journey_context_id / owner_user_id | Journey and User Account references | Req | Owner indexed; owner must match journey; never client-authoritative | P | Immutable |
| sequence | Positive ordinal | Req | Unique within journey; ordered-history index | P | Immutable |
| step_type | Extensible controlled key | Req | Allow-listed and compatible with target kind; adding a step type must not require a new field | P/E | Immutable |
| target_kind / target_reference | Typed reference to exact editorial revision or underlying user-owned record | Req | Target kind allow-listed; editorial target pins revision; user target shares owner; target must exist | P or E reference | Immutable reference; does not copy target body |
| step_state | Controlled observed state | Req | Examples: entered, completed, skipped, saved/relevant; meaningful for step_type | P | Immutable observation; later state change appends another step |
| occurred_at / recorded_at | Timestamps | Req | Chronology validation; journey sequence/history query | P | Immutable |
| context_metadata | Bounded structured values | Opt | Schema/type/size validation; no unnecessary financial or editorial body duplication | P/F | Immutable snapshot |

## Calculator Definition, Formula Version and Formula Approval

| Entity.field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| CalculatorDefinition.lab_tool_id | Lab Tool ref | Req when tool implements calculator | Indexed | E | Immutable identity link |
| CalculatorDefinition.input_output_contract | Typed contract | Req | Units/ranges/default rules explicit | E/S | Version with formula definition |
| CalculatorDefinition.current_formula_version_id | Formula Version ref | Opt until activated | At most one active pointer | S | Controlled pointer; approval history retained |
| FormulaVersion.calculator_definition_id | Definition ref | Req | Indexed | S/E | Immutable |
| FormulaVersion.version_identifier | Version key | Req | Unique per definition | S/E | Immutable |
| FormulaVersion.lifecycle_state | Controlled state | Req; Draft | Draft→Tested→Reviewed→Approved→Active→Retired only | S | Transition history append-only |
| FormulaVersion.formula_definition_ref | Versioned method/artifact reference | Req before Tested | Exact reviewed implementation identifier/checksum; no user code | S | Immutable |
| FormulaVersion.assumptions_specification | Typed explanation | Req before Tested | Explicit units and defaults | E/S | Immutable |
| FormulaVersion.test_evidence_ref | Cases and expected results | Req before approval | Identifiable reproducible test set | S | Immutable evidence |
| FormulaVersion.source_snapshot | Source provenance values | Req before approval where formula depends on sources | Source/reference preserved | E/S | Immutable |
| FormulaVersion.rounding_method / methodology / warnings | Structured values | Req where relevant; warnings opt | Deterministic units/rounding; bounded text | E/S | Immutable |
| FormulaApproval.formula_version_id / actor_id | References | Req | Indexed by version and actor | S | Immutable |
| FormulaApproval.action / occurred_at | Controlled action / timestamp | Req | Lifecycle validation; time indexed | S | Immutable |
| FormulaApproval.role_snapshot / evidence_refs / note | Role, refs, bounded text | Evidence and role req for approval actions; note opt | Activation gate checks complete evidence | W/S | Immutable |

## Calculation Result

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| owner_user_id | User Account ref | Req for saved results | Indexed | P | Immutable |
| formula_version_id / calculator_definition_id | Exact references | Req | Must match; formula was Active at calculation time | S reference | Immutable |
| input_snapshot | Typed values with units | Req | Validate against pinned contract; bounds | F | Immutable |
| assumption_snapshot | Typed values and origin (user/default/source) | Req, may be empty set | Distinguish user-set/default/source | F | Immutable |
| output_snapshot | Typed values and units | Req | Produced by trusted calculation service | F | Immutable |
| methodology_snapshot / rounding | Method and numeric policy | Req | Reproducible identifier | E/F | Immutable |
| source_snapshot / warnings_snapshot | Source and limitations at calculation time | Required where relevant; warnings opt | Snapshot, not mutable current row only | E/F | Immutable |
| calculated_at | Timestamp | Req | Indexed with owner for history | P/F | Immutable |
| practice_attempt_id | Same-owner Practice Attempt reference | Opt | An attempt may link to zero or many saved results; the attempt's exact Practice Revision and owner must match | P reference | Immutable once linked |
| saved_label | Text | Opt | Bounded | P | Mutable annotation only; result is immutable |

Unsaved calculations need not persist. Saved results are user-owned and cannot be presented as guaranteed advice/outcome.

## My Plan and Plan Revision

| Field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| MyPlan.owner_user_id | User Account ref | Req | Indexed; ownership check | P | Immutable |
| MyPlan.status | Draft/Active/Completed/Archived concept | Req; initial meaning TBD | Valid transitions | P | Mutable with state history if needed |
| MyPlan.current_revision_id | Plan Revision ref | Opt until first save | Must belong to plan; one pointer | P | Mutable pointer; history remains |
| MyPlan.created_at / updated_at | Timestamps | Req | No standalone index | S | Created immutable; updated mutable |
| PlanRevision.plan_id | My Plan ref | Req | Indexed; same owner | P | Immutable |
| PlanRevision.revision_number | Positive sequence | Req | Unique per plan; indexed | P | Immutable |
| PlanRevision.predecessor_id | Prior revision ref | Opt on first revision | Same plan, lower sequence, no cycle | P | Immutable |
| PlanRevision.target_snapshot | User-defined target values | Req conceptually | Preserve user's units/timeframe and definition; no universal goal taxonomy | F | Immutable |
| PlanRevision.assumptions_snapshot | Typed values/provenance | Req conceptually; may be empty | Explicit units and user/default/source origin | F | Immutable |
| PlanRevision.strategy_path_snapshot | Structured text/steps | Opt | Bounded; no system promise | F | Immutable |
| PlanRevision.practice_attempt_ref | Practice Attempt ref | Opt | Same owner | F reference | Immutable |
| PlanRevision.calculation_result_refs | Calculation Result refs | Opt | Same owner; formulas pinned by result | F reference | Immutable |
| PlanRevision.note_refs | Note references | Opt; transfer behavior unresolved | Same owner; only explicit association/copy behavior after UX decision | P/F reference | Immutable references in this revision |
| PlanRevision.learning_context_ref / content_context_refs | Journey and exact Playbook/Module/Lesson revisions | Opt | Same owner for journey; correct revision types | P/F and E refs | Immutable |
| PlanRevision.created_at | Timestamp | Req | Owner-plan history query | S | Immutable |

Targets, assumptions, strategy and path are revision-owned snapshots, not independently mutable entities by default.

## Note, Lesson Completion and Module Completion

| Entity.field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| Note.owner_user_id | User Account ref | Req | Indexed | P | Immutable |
| Note.kind / body | Controlled kind / text | Kind req; body optional for highlight-only | Bounded; private notes excluded from public search | P | User editable; history policy TBD |
| Note.anchor | Exact revision/block and selection data | Opt | Validate block/selection against pinned revision | P/E ref | Never silently retarget |
| Note.journey_context_id | Same-owner Journey Context | Opt | Owner match | P | Mutable association only explicitly |
| Note.created_at / updated_at / deleted_at | Timestamps | Created/updated req, deleted opt | Owner listing/deletion query | S/P | Policy TBD |
| LessonCompletion.owner_user_id / lesson_revision_id | User + exact Lesson revision refs | Req | Indexed | P/E ref | Immutable evidence scope |
| LessonCompletion.requirement_ref / journey_context_id | Exact requirement/context refs | Opt | Must match module revision/owner | P/E ref | Immutable |
| LessonCompletion.evidence_kind / completed_at | Controlled evidence key / time | Req; semantics TBD | Valid evidence method | P/S | Append/correct, never silently change |
| ModuleCompletion.owner_user_id / module_revision_id | User + exact Module Revision | Req | Indexed | P/E ref | Immutable scope |
| ModuleCompletion.evaluated_at / outcome | Time / Complete or Incomplete | Req | Indexed by owner/time; only all required conditions satisfied permits Complete | P | Immutable decision |
| ModuleCompletion.requirement_evidence_snapshot | Structured requirement/evidence list | Req | Every required item accounted for; satisfaction supported by exact evidence refs | P/E refs | Immutable explanation |
| ModuleCompletion.journey_context_id | Journey ref | Opt | Same owner | P | Immutable |

## Achievement, source provenance, editorial events

| Entity.field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| AchievementDefinition.slug / current_revision_id | Key / revision ref | Slug req; pointer opt | Unique key; one current pointer | E | Pointer mutable; event history |
| AchievementDefinitionRevision.name / description / criteria_ref / state | Text/key/state | Display fields req; criteria TODO | Criteria is versioned allow-listed rule, not arbitrary code | E/W | Immutable after publication |
| UserAchievement.owner_user_id / definition_revision_id | User + exact definition revision | Req | Indexed by owner; uniqueness policy open | P/E ref | Immutable |
| UserAchievement.awarded_at / evidence_refs | Time / qualifying Module Completion + Plan Revision refs | Req | Evidence same owner and matches approved criteria | P/F ref | Immutable |
| Source.identity / title / URL / publication_date / version_ref | Key/text/ref/date | Identity/title required as known; others opt | URL/reference validated where applicable | E/W | Mutable current catalog only |
| SourceSnapshot.source_id / content_revision_id | Source and exact revision refs | Req | Indexed by content revision | E | Immutable |
| SourceSnapshot.title / URL / publication_date / accessed_at / version_ref | Snapshot values | Preserve applicable known values; unknown explicit | No current-row lookup may substitute for snapshot | E | Immutable |
| SourceSnapshot.reviewer_id / reviewed_at | Staff ref / time | Req when review applies | Pair required for reviewed claim | W/E | Immutable |
| EditorialReview.revision_id / reviewer_id / action / occurred_at | Exact revision, actor, action, timestamp | Req | Indexed revision/time; authorized staff | W | Append-only |
| EditorialReview.comment | Staff text | Opt | Bounded, staff-only, retention TBD | W | Immutable event |
| PublicationEvent.identity_id / revision_id / action / actor_id / occurred_at | References, controlled action, actor/time | Req | Correct identity/revision; indexed identity/time | E/W | Append-only |

## Search, media and future Dictionary

| Entity.field | Type | Req/default | Unique / validation / index | Privacy | Mutability/version |
|---|---|---|---|---|---|
| SearchProjection.content_revision_id | Eligible published revision | Req | Unique per projection purpose; indexed | E | Rebuildable |
| SearchProjection.searchable_text / filter_metadata | Derived text/typed values | Req | Public approved fields only; no user data/drafts | E | Rebuildable |
| SearchProjection.indexed_at / schema_version | Time/version | Req | N | S | Rebuildable |
| MediaAsset.asset_key / media_kind | Stable key / allow-listed kind | Req | Unique key; MIME/size validation | E/W | Stable identity |
| MediaAsset.metadata / source_rights / state | Typed metadata, attribution, state | Metadata/state req as applicable; rights policy TBD | Safe and editorially checked | E/W | Replace file by new version/reference; preserve old refs |
| DictionaryTerm.slug / display_term / state | Key/text/state | Future only | Unique normalized key; term lookup index | E | Controlled editorial lifecycle |
| DictionaryDefinitionRevision.term_id / revision_number / definition / source_refs / state | Ref, sequence, structured text, refs, state | Future only | Unique sequence; validated blocks/provenance | E/W | Immutable revision |

## Embedded values

Practice responses, input/assumption/output sets, plan target/timeframe/path, requirement evidence list, scenario details, note anchors and source snapshots inherit the parent owner/privacy/retention/version semantics. A separate entity is justified only if an approved requirement needs independent identity, query, edit, sharing or lifecycle.
