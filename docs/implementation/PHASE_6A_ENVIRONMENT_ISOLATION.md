# Phase 6A Environment Isolation

**Status: Current environment verified 2026-10-07; independent acceptance pending.** The old PostgreSQL 13 installation and old MaliLab system have been removed; the current development target is the clean `malilab` database accessed as `malilab_app` on loopback. No legacy schema or data is used. Phase 6B remains blocked.

## Current verified environment

| Item | Current result |
|---|---|
| OS | Oracle Linux 9.8 (host verification supplied for this resumed execution) |
| System Python | 3.11.13 (host verification supplied) |
| Project virtualenv | `/home/opc/malilab/.venv`, Python 3.11.13 (directly verified) |
| PostgreSQL | 16.15, active and enabled (host verification supplied) |
| Listener | `127.0.0.1:5432` accepts connections (directly verified) |
| Database / role | `malilab` / `malilab_app` (directly verified through local `~/.pgpass`; credential not displayed) |
| Application tables before Phase 6A | 0 (directly verified in `malilab`) |
| Authentication | Local SCRAM-SHA-256; password source is the user's local `~/.pgpass` |
| Application role privileges | `malilab_app` remains NOSUPERUSER, NOCREATEDB, NOCREATEROLE |
| PostgreSQL test role | `malilab_phase6a_test`, no CONNECT privilege on `malilab`; credential is local only |
| Test database lifecycle | `test_malilab_phase6a` created/dropped by Django; absent after test run |

The read-only command used was equivalent to `psql -h 127.0.0.1 -U malilab_app -d malilab` and queried only current database, current role, and non-system table count. No password was requested, read into output, or recorded here.

## Isolation and scope

Phase 6A created its clean Django migration history only in the verified empty `malilab` database. Remediation round 2 is implemented. SQLite ran 56 tests with four PostgreSQL-only tests skipped; PostgreSQL ran all 56 tests. Do not import legacy data, reuse a retired schema, or create compatibility models. Keep credentials outside Git and application source. PostgreSQL remains loopback-only. Independent acceptance remains required; Phase 6B and production deployment are not authorized.
