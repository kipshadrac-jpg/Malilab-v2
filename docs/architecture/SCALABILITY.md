# Scalability and Evolution

**Status:** Accepted growth principles. No traffic figures or performance targets are assumed.

## 1. Starting point: small initial user base

One modular Django application and one PostgreSQL database are sufficient architectural starting points. Serve pages synchronously, keep user workflows transactional, use DB-backed search, local persistent assets if capacity/backup permit, and omit distributed cache, worker, search cluster, and microservices. Separate logical domains and user/editorial data even on one deployment.

This minimizes operational work while preserving transaction correctness for content publication, plan revisions, scenario snapshots, and Progress evidence.

## 2. Growth to thousands of users

First measure actual behavior rather than assume scale. Likely pressure points are:

- Database connection/query volume from content and user progress.
- Expensive or poorly indexed search/filter queries.
- Calculator request volume/latency.
- Media bandwidth and disk usage.
- Single-host CPU, memory, disk I/O, and failure domain.
- Content revision and search-projection maintenance.

Evolution steps, in order of evidence:

1. Profile queries and app requests; add appropriate indexes and pagination.
2. Optimize rendered content and static/media delivery; use browser/proxy caching only for safely public immutable content.
3. Increase application capacity or move app and DB to suitable separate hosts while retaining the same modular boundaries.
4. Move editorial media to object storage/CDN if disk, delivery, or availability requires it.
5. Add a bounded worker/queue for a confirmed slow/retryable workflow, with idempotency and monitoring.
6. Add a dedicated search service only when PostgreSQL quality/scale or language needs demonstrably fail product requirements.
7. Add read replicas or horizontal app replicas only when database/app metrics justify them and session/media behavior is designed for it.

## 3. Larger public platform

The modular monolith can scale vertically and by multiple stateless web workers before service extraction. Externalize shared state (database, media, sessions if needed), use managed/replicated PostgreSQL and object storage/CDN when availability/scale warrants it, and build explicit asynchronous boundaries only around demonstrated workloads. Extract a service only when it has independent scaling, release, data ownership, or security needs strong enough to outweigh distributed-system costs.

Future subscriptions, advanced analytics, recommendation, a full dictionary/knowledge graph, and user-facing AI remain product scope decisions; growth does not automatically justify implementing them.

## 4. Revisit triggers

No numeric thresholds are set without expected load and service objectives. Revisit when measured DB saturation, tail latency, search relevance, storage growth, deployment downtime, or operational toil crosses an owner-approved target; when multiple teams need independent release; or when a new approved capability imposes an asynchronous/scale requirement. Record measurements and trade-offs in a decision update before adding infrastructure.

## 5. Bottleneck and complexity watchlist

Avoid one giant query/render path, unbounded lesson block payloads, no pagination, repeated calculation calls without limits, synchronous media transformations, and search over private data. Avoid premature Redis, a job queue, OpenSearch, a graph database, Kubernetes, or service splitting. These choices create new backup, monitoring, security, and deployment requirements.
