# Field and PostgreSQL Type Specifications

This is a mapping contract, not SQL or Django syntax. `Required` means non-null unless a lifecycle state explicitly permits an absent value. All PKs are proposed `bigint`; all times are timezone-aware `timestamptz`. Text length limits are validation rules to be approved with representative content, not guessed here.

| Logical field group / models | PostgreSQL type proposal | Null/default | Constraints/index | Privacy / mutability |
|---|---|---|---|---|
| IDs for all persisted models | `bigint` identity primary key | generated | PK; never treated as authorization | System; stable |
| Editorial slugs | `varchar` normalized slug | required | unique per identity type; indexed lookup | Public metadata; mutable only through controlled redirect-safe edit |
| Revision number | `integer` positive | required | unique `(identity_id, revision_number)`, check > 0 | Editorial; immutable |
| Owner/actor/revision FK | `bigint` FK | required except optional actor/initial pointer | btree; PROTECT/RESTRICT as specified | Owner-sensitive or staff-private; immutable on evidence |
| State, action, kind, classification, step type | `varchar` bounded controlled key | required; explicit initial state | CHECK/choices; indexed only for queues/current state | Depends on model; transition controlled |
| Position/sequence | `integer` positive/nonnegative | required | unique within parent; btree for ordered retrieval | Editorial/user history; immutable after publish/append |
| Timestamps: created, updated, occurred, recorded, submitted, reviewed, calculated, published | `timestamptz` | required where event exists | composite owner/time or revision/time where queried | Audit/history; immutable event time |
| Long editorial prose | `text` | required or optional by content contract | no broad index; public projection only | Editorial revision; immutable after publication |
| Lesson content blocks | `jsonb` array of typed block objects, or normalized child rows only if query needs justify it | required, defaults to empty only if valid lesson | schema version, block key/order validation in service; JSONB GIN only if proven query needs | Editorial revision; immutable |
| Block identity/type/order | JSONB `key`, `type`, `position`; stable block key represented UUID string; order integer | required | unique key and order in revision checked on write | Editorial; immutable for published version |
| Practice response schema/response values | `jsonb` typed snapshots; exact decimal answer values represented as canonical decimal strings plus unit | schema required; responses optional until answered | size/depth/key allow-list validation; no client-supplied executable content | User-private; submitted values immutable |
| Plan targets/assumptions/path/context | `jsonb` versioned structures; exact decimal values strings and explicit unit/currency | target and assumptions required conceptually; empty set allowed only where product definition permits | schema validation and max-size bounds; no indexing individual keys by default | User financial sensitive; immutable per revision |
| Calculation inputs/assumptions/outputs | `jsonb` versioned; Decimal values canonical strings | required snapshot, including empty assumptions array where appropriate | checksum/reproduction metadata; bounded | User financial sensitive; immutable |
| Financial scalar amounts (if later normalized) | PostgreSQL `numeric(p,s)` / Django DecimalField | required per specific calculator contract | range/nonnegative/check only where formula defines it | Sensitive; precision must be approved |
| Financial scalar amount precision | Formula-specific | exact `numeric(p,s)`/DecimalField where normalized; no universal precision/scale | Per-calculator maximum range, working precision and overflow behavior documented before calculator implementation | KES initial; currency explicit; financial private |
| Currency/unit code | `varchar` controlled code, not unconstrained label | required only for monetary or dimensional values; no implicit KES default | validator against approved code/unit registry; index only where queried | Part of private snapshots; immutable |
| Currency support set and conversions | `varchar` currency code | KES at initial launch; field extensible | No implicit conversion; another currency requires approved calculator specification; FX future | Per-value explicit currency |
| Formula checksum/version key | `varchar` identifier/digest | required before Test/approval | unique `(definition, version_key)`; format validation | System governance; immutable |
| Formula test/source/warning/method snapshots | `jsonb` schema-versioned objects, text where human prose | required at applicable lifecycle gate | validate fields and source snapshot links | System/editorial; immutable |
| Source URL/reference | `text` or bounded `varchar` | nullable if no URL; preserve non-URL citation refs | URL syntax validation, not a claim of source validity | Editorial; mutable catalog, immutable snapshot copy |
| Source dates | `date` publication date; `timestamptz` retrieved/reviewed | nullable when genuinely unknown | chronology checks where applicable | Editorial provenance; immutable snapshot |
| Note body | `text` | nullable only for highlight-only note | owner/time btree; no public text index | User-private; mutable until deleted per policy |
| Note anchor | `jsonb` with `anchor_schema_version`, exact block key, selected quote, optional character offsets | optional for ordinary Note; required for highlight selection | Validate against exact LessonRevision and block; quote/block authoritative; offsets are hints only | User-private and exact revision-bound |
| Note anchor selection representation | Versioned `jsonb`: exact LessonRevision FK, stable block ID, selected quote, optional character offsets | Revision/block/quote required for highlight; offsets optional | Block ID and quote are authoritative; offsets are hints and cannot move anchor if text differs; no cross-revision remap | User-private, revision-local |
| Search text | `text` plus PostgreSQL `tsvector` maintained by projection update/rebuild strategy | required for searchable revision | GIN only on projection; published-only content | Public editorial only; derived |
| Search metadata | `jsonb` bounded category/topic/type filters | optional | ordinary indexes for approved frequent filters | Public editorial only |
| Media byte size | `bigint` | required when known | nonnegative check | Editorial metadata |
| Media checksum/key/MIME | `varchar`/text | required for stored bytes | unique storage key + checksum check/verification | Editorial; immutable per asset version |
| User/account state | controlled `varchar`; custom Django user identity with normalized email and framework-managed password/session primitives | verified email required before full personal features | unique normalized email; email recovery; server-side sessions; no phone/social identity initially | Identity private; credentials framework-managed |
| Boolean flags | `boolean` | explicit, no nullable tri-state unless domain needs unknown | CHECK unnecessary | State per lifecycle; immutable in revisions |

## Null/default policy

Do not use empty strings to mean unknown. Null is reserved for genuinely optional/not-yet-known fields. Do not add defaults for product assumptions, currency, formula values, content access, account policy, or completion criteria. Initial states such as `Draft` may be defaults only where the lifecycle document explicitly requires them.

## Per-model logical field mapping

The following inventory maps the logical fields from `docs/database/FIELDS.md` to their proposed PostgreSQL type families. Parentheses after a field identify a foreign key. Common `id bigint PK` applies to every persisted row. `created_at timestamptz` is included for persisted entities/events; `updated_at timestamptz` applies only to mutable identity/catalog records and mutable user notes. Immutable revisions/events do not receive a misleading update timestamp. Nullability, defaults and uniqueness follow the constraints above; optional references are nullable. Sensitive snapshots inherit owner privacy.

| Model | Fields → type mapping |
|---|---|
| UserAccount | Custom Django user identity: normalized unique `email varchar`, framework-managed password credential, `email_verified boolean`, optional `email_verified_at timestamptz`, controlled `status varchar`, `created_at/updated_at/closed_at timestamptz`, deletion workflow state/time as approved. No phone/social fields initially; age policy remains undecided. |
| Playbook | `slug varchar`, `status varchar`, `current_published_revision_id bigint FK nullable`, `created_at/updated_at timestamptz`. |
| PlaybookRevision | `playbook_id bigint FK`, `revision_number integer`, `status varchar`, `title/summary/scenario/audience_context/financial_situation/desired_outcome text or bounded JSONB`, `assumptions/discovery_metadata JSONB`, optional `cover_asset_id bigint FK`, `created_at timestamptz`, optional `submitted_at/published_at timestamptz`. |
| Module | `slug varchar`, `status varchar`, `current_published_revision_id bigint FK nullable`, timestamps. |
| ModuleRevision | `module_id bigint FK`, `revision_number integer`, `status varchar`, `title varchar`, `description text`, optional `estimated_effort JSONB` (unit/value TBD), `prerequisite_refs JSONB` only if approved; `metadata JSONB`, timestamps. |
| Lesson | `slug varchar`, `status varchar`, `current_published_revision_id bigint FK nullable`, timestamps. |
| LessonRevision | `lesson_id bigint FK`, `revision_number integer`, `status varchar`, `title varchar`, `summary text nullable`, `content_schema_version integer`, `blocks JSONB`, `metadata JSONB`, timestamps. |
| LessonContentBlock (embedded) | `block_key UUID string`, `block_type varchar`, `position integer`, `payload JSONB`, `schema_version integer`; fields validated within LessonRevision; not separate table by default. |
| ModuleLearningRequirement | `module_revision_id bigint FK`, `target_kind varchar`, nullable `lesson_revision_id/practice_revision_id bigint FK` with exactly one set, `classification varchar`, `position integer`, `completion_condition_key varchar nullable`, `active boolean`, `created_at timestamptz`. |
| PlaybookModuleRecommendation | `playbook_revision_id/module_revision_id bigint FK`, `position integer`, `rationale text nullable`, `active boolean`, `created_at timestamptz`. |
| RelatedContentRelationship | `source_revision_ref/target_revision_ref bigint FK via typed reference`, `relationship_kind varchar`, `position integer nullable`, `rationale text nullable`, timestamps. Exact typed-reference physical pattern is proposed and must avoid GFK integrity loss. |
| Topic | `name varchar`, `slug varchar`, `description text nullable`, `status varchar`, timestamps. |
| ContentTopicAssignment | `content_revision_ref bigint FK typed`, `topic_id bigint FK`, `role varchar`, `position integer nullable`, `created_at timestamptz`. |
| PracticeActivity | `slug varchar`, `status varchar`, `current_published_revision_id bigint FK nullable`, timestamps. |
| PracticeActivityRevision | `activity_id bigint FK`, `revision_number integer`, `status varchar`, `title/instructions/prompt text`, `response_schema JSONB`, `tool_refs JSONB`, `safety_text text nullable`, `content_schema_version integer`, timestamps. |
| PracticeAttempt | `owner_id bigint FK`, `practice_revision_id bigint FK`, `journey_id bigint FK nullable`, `status varchar`, `started_at/submitted_at timestamptz`, `response_summary JSONB nullable`, timestamps. |
| PracticeResponse | `attempt_id bigint FK`, `prompt_key varchar`, `value JSONB` (decimal string for exact amounts), `unit varchar nullable`, `answered_at timestamptz`; unique attempt/prompt. |
| LearningJourney | `owner_id bigint FK`, `starting_context JSONB nullable`, `created_at timestamptz`. |
| JourneyStep | `journey_id/target_ref_id bigint FK`, `sequence integer`, `step_type/step_state varchar`, `occurred_at/recorded_at timestamptz`, `context_metadata JSONB nullable`. |
| JourneyTargetRef | `target_kind varchar`, `owner_id bigint FK nullable` (null for editorial target), `created_at timestamptz`; target subtype is one-to-one row with concrete FK. |
| JourneyTarget subtype | `target_ref_id bigint OneToOne FK`, one exact concrete revision/user record FK, `created_at timestamptz`; one subtype per target. |
| LabTool | `slug/title varchar`, `description text`, `status varchar`, timestamps. |
| CalculatorDefinition | `lab_tool_id bigint FK`, `key/title varchar`, `contract_schema_version integer`, `input_contract/output_contract JSONB`, `current_formula_version_id bigint FK nullable`, `status varchar`, timestamps. |
| FormulaVersion | `definition_id bigint FK`, `version_identifier varchar`, `lifecycle_state varchar`, `formula_artifact_ref varchar`, `artifact_checksum varchar`, `assumptions_specification/test_evidence/source/methodology/warnings JSONB`, `rounding_method varchar nullable`, `created_at timestamptz`. |
| FormulaApproval | `formula_version_id/actor_id bigint FK`, `action varchar`, `role_snapshot varchar`, `evidence_refs JSONB`, `note text nullable`, `occurred_at timestamptz`. |
| CalculationResult | `owner_id/formula_version_id bigint FK`, `practice_attempt_id bigint FK nullable`, `inputs/assumptions/outputs/source_snapshot/warnings_snapshot JSONB`, `unit/currency varchar nullable`, `precision_policy/rounding_method/methodology_version varchar`, `calculated_at timestamptz`, `saved_label varchar nullable`. |
| MyPlan | `owner_id bigint FK`, `status varchar`, `current_revision_id bigint FK nullable`, timestamps. |
| PlanRevision | `plan_id bigint FK`, `revision_number integer`, `predecessor_id bigint self-FK nullable`, `target/assumptions/strategy_path JSONB`, optional `journey_id bigint FK`, exact private refs as FK association(s), exact editorial context refs, `created_at timestamptz`. |
| Note | `owner_id bigint FK`, `kind varchar`, `body text nullable`, `lesson_revision_id bigint FK nullable`, `block_key varchar nullable`, `anchor_schema_version integer nullable`, `anchor_data JSONB nullable`, `journey_id bigint FK nullable`, `created_at/updated_at/deleted_at timestamptz`. |
| LessonCompletion | `owner_id/lesson_revision_id bigint FK`, optional exact `requirement_id/journey_step_id bigint FK`, `evidence_kind varchar`, `completed_at/recorded_at timestamptz`, `evidence_context JSONB nullable`. |
| RequirementEvidence | `owner_id/module_revision_id/requirement_id/practice_revision_id/attempt_id bigint FK`, `evidence_state varchar`, `recorded_at/evaluated_at timestamptz`, optional predecessor/supersession ref for correction, `evaluation_context JSONB nullable`. One accepted attempt→one requirement initially. |
| ModuleCompletion | `owner_id/module_revision_id bigint FK`, `outcome varchar`, `evaluated_at timestamptz`, `requirement_evidence_snapshot JSONB`, `journey_id bigint FK nullable`, timestamps. |
| AchievementDefinition | `slug varchar`, `status varchar`, `current_revision_id bigint FK nullable`, timestamps. |
| AchievementDefinitionRevision | `definition_id bigint FK`, `revision_number integer`, `name varchar`, `description text`, `criteria_key varchar`, `criteria_config JSONB`, `status varchar`, timestamps. |
| UserAchievement | `owner_id/definition_revision_id/module_completion_id/plan_revision_id bigint FK`, `awarded_at timestamptz`, `evidence_refs JSONB`; optional evidence refs only where criteria allow. |
| Source | `source_key/title varchar`, `url_or_reference text nullable`, `publication_date date nullable`, `version_reference varchar nullable`, `current_metadata JSONB nullable`, timestamps. |
| SourceSnapshot | `source_id bigint FK`, exact typed `content_revision_ref` (or formula version where applicable), `source_identity/title/url_reference/version_reference varchar/text`, `publication_date date nullable`, `retrieved_at/reviewed_at timestamptz nullable`, `reviewer_id bigint FK nullable`, `relationship_to_content varchar/text`, `snapshot_schema_version integer`. |
| EditorialReview | exact typed revision FK, `reviewer_id bigint FK`, `action varchar`, `comment text nullable`, `occurred_at timestamptz`, `review_context JSONB nullable`. |
| PublicationEvent | identity/revision typed FK, `actor_id bigint FK nullable only if actor-retention policy requires`, `action varchar`, `occurred_at timestamptz`, `event_context JSONB nullable`. |
| SearchProjection | exact revision FK, `content_kind varchar`, `title/searchable_text text`, `search_vector tsvector`, `filter_metadata JSONB`, `schema_version integer`, `indexed_at timestamptz`. |
| MediaAsset | `asset_key varchar`, `media_kind/mime_type varchar`, `byte_size bigint`, `checksum varchar`, `attribution/rights_metadata JSONB`, `status varchar`, `created_at timestamptz`; immutable file-version row. |
| DictionaryTerm (future) | `slug/display_term varchar`, `status varchar`, timestamps. |
| DictionaryDefinitionRevision (future) | `term_id bigint FK`, `revision_number integer`, `definition_blocks JSONB`, `source_refs JSONB`, `status varchar`, timestamps. |

Any typed relation omitted from direct scalar mapping is implemented by explicit association/FK models, never an unvalidated integer ID. `SourceSnapshot` and cross-content relationship target registries require the concrete target-type set to be finalized before migrations.
