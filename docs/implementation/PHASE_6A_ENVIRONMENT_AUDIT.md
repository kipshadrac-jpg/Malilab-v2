# Phase 6A Environment Audit

**Status: Current Phase 6A environment verified 2026-10-07.** This records environment/schema state only; independent Phase 6A acceptance remains required and Phase 6B is blocked.

## Verified current state

| Check | Result | Evidence |
|---|---|---|
| OS | Oracle Linux 9.8 | Host verification supplied for this execution |
| Python | 3.11.13 | Host verification supplied; `.venv/bin/python --version` returned 3.11.13 |
| Virtualenv | `/home/opc/malilab/.venv` | Valid Python 3.11 environment; pip 22.3.1 |
| PostgreSQL | 16.15 active and enabled | Host verification supplied |
| Listener | `127.0.0.1:5432` accepting connections | `pg_isready` |
| App connection | Database `malilab`, role `malilab_app` | Successful `psql` using local `~/.pgpass`; no credential output |
| Initial application schema | Empty | PostgreSQL reported zero non-system tables before implementation |
| Local auth | SCRAM-SHA-256 | Host verification supplied |
| Application role | `malilab_app`: NOSUPERUSER, NOCREATEDB, NOCREATEROLE | Directly verified |
| Isolated test role | `malilab_phase6a_test`: CREATEDB, no CONNECT on `malilab` | Directly verified; local-only credential |
| Current schema | 56 public tables, 37 total migration records, 16 MaliLab migration records; no domain seed/import data | `scripts/verify_schema.py` and read-only PostgreSQL checks |

## Implementation package set

The approved Phase 6A framework baseline is Django 5.2 LTS with its PostgreSQL adapter. The project virtualenv contains only the approved runtime dependencies: Django 5.2.18, `psycopg` 3.3.6 with its binary distribution, and `django-otp` 1.7.3 for the approved staff MFA requirement. No legacy requirements or virtualenv packages are sources for this project.

## Isolation result

The clean Phase 6A schema is applied only to the clean `malilab` database as `malilab_app`. The old PostgreSQL 13 and legacy application have been removed. No legacy database/schema or data is used. Credentials remain in the user's `~/.pgpass` and are not written to source or this audit. PostgreSQL listens on loopback. Independent acceptance remains pending.
