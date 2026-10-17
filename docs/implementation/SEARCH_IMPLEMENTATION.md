# Search Implementation Specification

**Status:** PostgreSQL/application-level search is the accepted initial candidate; search remains a derived projection, not canonical content. No search engine or index is configured.

Public reading is allowed anonymously, but projection eligibility remains limited to approved published editorial revisions. Anonymous access never includes persisted private/personal features; those require authenticated, email-verified accounts. This distinction is enforced by the content access policy, not by adding user data to search.

## Projection

Candidate projection fields: exact published revision reference, content kind, title, summary/short excerpt, selected published lesson text/block text, topic/category labels, Playbook scenario/discovery terms, slug, publication eligibility, projection schema/index timestamp. Only allow-listed editorial values enter it. Exclude drafts, private source comments, notes, attempts, plans, calculations, financial assumptions, and private response data.

Use PostgreSQL full-text (`tsvector` + GIN) and ordinary filters initially. Weight title/slug above summary and body; final weighting/config is subject to validation. Search route is a query service with pagination and access-policy filtering, not per-entity unrestricted endpoints. Search projection can be regenerated from canonical current published revisions; publish/revise/retire triggers transactional/outbox-free synchronous projection maintenance initially, with periodic/rebuild command if needed. No worker is justified yet.

## Validation before adoption

Use representative Kenyan searches including English, Kenyan terminology (e.g. SACCO, T-bill/Treasury Bill, MMF/Money Market Fund, CRB), spelling/spacing variants, abbreviations, and natural questions. Add Kiswahili or other language query sets only when supported languages are approved. Review relevant-result quality, ordering, synonyms, publication/retirement updates, privacy exclusion, and latency on representative content. Search thresholds and supported languages remain TODO.

Introduce a dedicated search service only when approved quality/language needs, measured latency/index load, or corpus scale continue to fail after PostgreSQL tuning and query improvements. Preserve the projection adapter and canonical content boundary for migration.
