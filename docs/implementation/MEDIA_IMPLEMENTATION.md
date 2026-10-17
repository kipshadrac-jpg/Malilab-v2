# Media Implementation Specification

**Status:** Proposed immutable asset-version model. Storage infrastructure is not selected.

Published media follows the approved human-governed publication workflow: the approver is not the author for published financial content, and the exact revision/event retains actor and role. Media metadata and storage remain editorial-owned and are not removed by learner-account deletion.

- `MediaAsset` represents one immutable file/version, not a mutable filename whose bytes can be replaced. A changed cover or image creates a new row with a new opaque key, checksum, media kind, MIME type, byte size, attribution/rights metadata, and state.
- Editorial revision or content block references its exact `MediaAsset`; old revisions continue resolving the same bytes. No in-place overwrite at the storage key.
- Service validates allowed media kind, MIME/extension consistency, byte-size limit (limit TBD), and checksum. Do not permit executable content or user uploads absent product approval.
- Storage path/key is opaque and outside release source directories. Database stores stable key and metadata, not large binary bytes. Local persistent storage is an initial candidate only if capacity, access control, backup and restore checks pass; object storage remains an evolution option.
- Hard deletion is prohibited while referenced by any revision. Replaced/unreferenced assets enter an explicit review/retention process; account deletion does not apply to editorial assets.
- Historical rendering requires retention of bytes for all retained revisions. Rights expiration or removal policy and media storage choice remain TODO; never break old revisions silently.
