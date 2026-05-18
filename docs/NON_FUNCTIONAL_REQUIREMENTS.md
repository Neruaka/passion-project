# NON-FUNCTIONAL REQUIREMENTS — Personal AI Operating System

> Quality attributes & system-wide constraints for the PASSION project.
>
> **Version:** 1.0 — All NFR locked
> **Date:** May 2026
> **Owner:** Frederick
> **Status:** ✅ Locked, ready for Architecture phase

---

## TABLE OF CONTENTS

1. [Overview & Methodology](#1-overview--methodology)
2. [Performance](#2-performance)
3. [Reliability](#3-reliability)
4. [Security](#4-security)
5. [Observability](#5-observability)
6. [Scalability](#6-scalability)
7. [Cost](#7-cost)
8. [Maintainability](#8-maintainability)
9. [Testability](#9-testability)
10. [Usability & Accessibility](#10-usability--accessibility)
11. [Compatibility](#11-compatibility)
12. [Privacy & Data Sovereignty](#12-privacy--data-sovereignty)
13. [Summary Matrix](#13-summary-matrix)

---

## 1. OVERVIEW & METHODOLOGY

### What are NFRs?

While the [Functional Requirements](./SPECIFICATIONS.md) describe **what** the system does, Non-Functional Requirements describe **how well** the system does it. They define the system's quality attributes and constraints.

### Key concepts used throughout

**SLI (Service Level Indicator)** — A measurable metric (e.g., "p95 latency").
**SLO (Service Level Objective)** — A target for the SLI (e.g., "p95 latency < 200ms").
**SLA (Service Level Agreement)** — A formal contract (not applicable here — single-user system).

**RTO (Recovery Time Objective)** — Max acceptable time to restore service after failure.
**RPO (Recovery Point Objective)** — Max acceptable data loss in a failure.

**p50 / p95 / p99** — Latency percentiles (NOT averages). p95 = 95% of requests are under this latency.

### MoSCoW priority

NFRs use the same MoSCoW priority system as user stories:
- 🔴 **MUST** — Non-negotiable requirements
- 🟡 **SHOULD** — Important but not blocking MVP
- 🟢 **COULD** — Nice-to-have
- ❌ **WON'T** — Out of scope (this iteration)

---

## 2. PERFORMANCE

### NFR-PERF-001 — Backend API latency 🔴 MUST

| Endpoint type | Target p95 | Target p99 | Notes |
|---|---|---|---|
| GET endpoints (simple reads) | < 200ms | < 500ms | dashboard, training log, stats |
| POST endpoints (writes) | < 400ms | < 1s | manual logs, config updates |
| Endpoints with heavy aggregation | < 1s | < 2s | weekly/monthly stats non-cached |
| LLM endpoints (workout suggestion) | < 5s | < 10s | depends on Claude API |
| `/api/v1/health/ingest` (Tasker) | < 800ms | < 2s | background, lower priority |
| WebSocket round-trip | < 100ms | < 300ms | chat must feel instant |

### NFR-PERF-002 — Sync job performance 🟡 SHOULD

| Job | Target avg duration | Target max |
|---|---|---|
| Hevy sync (30 min interval, delta) | < 3s | < 15s |
| Cronometer sync (1h interval) | < 5s | < 30s |
| Health Connect ingest (1h interval) | < 2s | < 10s |
| Nightly analysis job (PR, plateaus, stats) | < 60s | < 5 min |

### NFR-PERF-003 — Frontend performance 🔴 MUST

Aligned with Google Core Web Vitals 2026:

| Metric | Target | Notes |
|---|---|---|
| **First Contentful Paint (FCP)** | < 1.5s | first visual content |
| **Largest Contentful Paint (LCP)** | < 2.5s | main element loaded |
| **Time to Interactive (TTI)** | < 3s | page is usable |
| **Cumulative Layout Shift (CLS)** | < 0.1 | no visual "jumps" |
| Time to first dashboard render | < 1s on i5 LAN | local network advantage |

### NFR-PERF-004 — Expected data volumes (5-year projection) 🟡 SHOULD

| Table | 1 year | 5 years | Notes |
|---|---|---|---|
| workouts | ~365 | ~1 800 | ~1 workout/day max |
| workout_exercises | ~2 500 | ~12 600 | ~7 exos/workout |
| workout_sets | ~12 500 | ~63 000 | ~5 sets/exo |
| personal_records | ~100 | ~500 | 4 PR types × exercises |
| exercise_analysis | ~600 | ~3 000 | plateaus/regressions/behind_schedule |
| weekly_stats | 52 | 260 | 1 row/week |
| monthly_stats | 12 | 60 | 1 row/month |
| **health_metrics** | ~500K | **~2.5M** | high-volume time-series |
| **agent_actions** | ~200K | **~1M** | agent action logs |
| messages (chat) | ~10K | ~50K | conversations |
| agent_memory (vectorial) | ~50K | ~250K | RAG snippets |

**Estimated total DB size at 5 years: ~14 GB** (well within i5 32GB capacity).

### NFR-PERF-005 — Table partitioning strategy 🟡 SHOULD

To handle time-series tables at scale:

- **health_metrics**: PARTITION BY RANGE (recorded_at), quarterly partitions
- **agent_actions**: PARTITION BY RANGE (created_at), quarterly partitions
- **workouts**: no partitioning (volume manageable)
- **workout_sets**: no partitioning (volume manageable)

Quarterly chosen over monthly: 3× fewer partitions to manage, equivalent performance for the expected volume.

### NFR-PERF-006 — Archival strategy 🟢 COULD

- agent_actions logs > 90 days: compressed JSONB or moved to archive table
- For MVP: ignore archival, address when > 500K rows
- Trigger: nightly job checks current partition size, sends ntfy alert if threshold exceeded

### NFR-PERF-007 — Critical indexes 🔴 MUST

Indexes to create on bootstrap:

```sql
-- workouts
CREATE INDEX idx_workouts_start_time ON workouts(start_time DESC);
CREATE UNIQUE INDEX idx_workouts_hevy_id ON workouts(hevy_id);

-- workout_sets
CREATE INDEX idx_workout_sets_exercise ON workout_sets(workout_exercise_id, order_index);

-- personal_records
CREATE INDEX idx_prs_exercise_time ON personal_records(exercise_template_id, achieved_at DESC);

-- health_metrics (CRITICAL — high volume)
CREATE INDEX idx_health_metrics_type_time ON health_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_health_metrics_recorded_brin ON health_metrics USING BRIN (recorded_at);

-- agent_memory (vector search)
CREATE INDEX idx_agent_memory_embedding ON agent_memory USING hnsw (embedding vector_cosine_ops);

-- agent_actions
CREATE INDEX idx_agent_actions_created_name ON agent_actions(created_at DESC, agent_name);
```

**Note on BRIN indexes**: Block Range Index — ultra-lightweight indexes (~1000× smaller than B-tree) optimized for naturally-ordered columns like timestamps. Perfect for time-series data.

### NFR-PERF-008 — Materialized views refresh 🟡 SHOULD

| View | Refresh frequency | Method |
|---|---|---|
| daily_health_summary | nightly at 04:30 | CONCURRENTLY (no blocking) |
| weekly_stats | every Sunday at 23:30 | CONCURRENTLY |
| monthly_stats | 1st of month at 23:30 | CONCURRENTLY |

---

## 3. RELIABILITY

### NFR-REL-001 — Uptime SLO 🔴 MUST

| Component | SLO target | Monthly downtime tolerance |
|---|---|---|
| **Frontend dashboard** | 99% | ~7h/month (acceptable) |
| **Backend API** | 99% | ~7h/month |
| **Brain orchestrator** | 99.5% | ~3.6h/month |
| **PostgreSQL database** | 99.9% | ~43 min/month (critical) |
| **Background jobs (Celery)** | 99% | ~7h/month |
| **External sync (Hevy/Cronometer)** | 95% | wider tolerance (third-party APIs) |

**Rationale for 99% (not higher)**: Self-hosted on a residential French internet connection (FAI outages, electricity glitches, system reboots for updates). Higher SLOs would require redundancy infrastructure disproportionate to a personal project.

### NFR-REL-002 — Retry & backoff strategy 🔴 MUST

| Action | Retry strategy |
|---|---|
| External API calls (Hevy, Cronometer, Resend, ntfy) | 3 retries with exponential backoff (1min, 5min, 15min) |
| LLM API calls (Anthropic, Gemini) | 3 retries with backoff (2s, 10s, 30s) |
| Failed DB writes | 5 fast retries (50ms, 200ms, 1s, 5s, 30s) |
| Health Connect ingestion | retry at next hourly window |

### NFR-REL-003 — Backup strategy (3-2-1 rule) 🔴 MUST

**The 3-2-1 backup rule:**
- **3** copies of data
- **2** different storage media
- **1** off-site copy

**Implementation:**

```
Copy 1 (production)  → PostgreSQL on i5 internal SSD
Copy 2 (local)       → pg_dump daily to external USB drive (~50€ for 2TB)
Copy 3 (off-site)    → Weekly sync to Backblaze B2 encrypted
```

**Constraints:**
- All backups encrypted with `age` (or `gpg`) before upload (zero-knowledge)
- Local backups: 7 days rolling + 1 monthly backup retained
- Off-site backups: 12 months rolling
- RPO ≤ 24h (max acceptable data loss)
- RTO ≤ 30 min (max recovery time)
- Restore tested once at project bootstrap (Phase 1)

**Estimated Backblaze B2 cost**: ~$0.005/GB/month × 14 GB → ~$0.07/month (negligible).

### NFR-REL-004 — Graceful degradation 🔴 MUST

When components fail, the system degrades instead of crashing entirely:

| Failing component | Degradation behavior |
|---|---|
| Hevy API down | Continue displaying already-synced history |
| Anthropic API down | Fallback to pre-defined templates for suggestions |
| Redis down | Temporarily disable WebSockets / background jobs, API still accessible |
| Health Connect ingestion down | Flag data as stale, no blocking error displayed |
| Cronometer MCP broken | Display last-known nutrition state, manual entry fallback |

### NFR-REL-005 — Idempotence 🔴 MUST

All critical operations must be idempotent (executable multiple times without duplicate effects):

| Operation | Idempotency mechanism |
|---|---|
| Workout sync | UPSERT by `hevy_id` UNIQUE constraint |
| Nutrition sync | UPSERT by `cronometer_id` |
| Health ingestion | UPSERT by `source_record_id` |
| Notifications | Dedup token to prevent spam on retry |
| Briefing generation | Daily idempotency key |

---

## 4. SECURITY

### NFR-SEC-001 — Authentication & sessions 🔴 MUST

```
- Main password: bcrypt with cost ≥ 12
- Password hash storage: .env on backend (never committed, never plaintext)
- Sessions: JWT signed HS256, 7-day expiration, auto-refresh on activity
- Cookies: httpOnly + Secure + SameSite=Strict
- System password (admin LLM zone): DIFFERENT from main password
- Login rate limit: 5 attempts / 15 min / IP, then 30 min lockout
- No "password reset" flow for MVP (single-user, you know your password)
- TOTP 2FA: Phase 4+ (not MVP)
```

### NFR-SEC-002 — Secrets management 🔴 MUST

```
- ALL secrets in .env file (never hardcoded):
  - DATABASE_URL
  - JWT_SECRET (32-byte random min)
  - HEVY_API_KEY
  - CRONOMETER_USERNAME / PASSWORD
  - ANTHROPIC_API_KEY
  - GEMINI_API_KEY
  - RESEND_API_KEY
  - NTFY_TOPIC
  - HEALTH_INGEST_TOKEN (for Tasker)
  - ADMIN_PASSWORD_HASH
  - SYSTEM_PASSWORD_HASH

- .env added to .gitignore (critical)
- .env.example committed with placeholder values
- Secrets rotation: annual minimum, sooner on suspected compromise
- No secrets logged (automatic filtering of sensitive field names)
```

### NFR-SEC-003 — Network exposure 🔴 MUST

**Decision: Tailscale only** (see ADR-004).

```
- No public exposure of API or dashboard
- Access ONLY via Tailscale (private mesh VPN)
- Caddy reverse proxy local on i5, listens on Tailscale IP only
- Mandatory HTTPS (Let's Encrypt via Tailscale Funnel or internal ACME)
- No port forwarding on internet router for MVP
- WebSocket traffic also via Tailscale
```

### NFR-SEC-004 — Data at rest 🔴 MUST

```
- PostgreSQL: no LUKS disk encryption (would cause reboot friction → violates uptime SLO)
- Backups encrypted with age (modern, simple)
- Application-level encryption for ultra-sensitive data (Phase 4+):
  - Blood panels
  - Personal journal entries
- Passwords: bcrypt mandatory, NEVER MD5/SHA1
- API tokens: hashed in DB if reusable, plaintext in .env if one-time use
```

### NFR-SEC-005 — Data in transit 🔴 MUST

```
- TLS 1.3 everywhere, TLS 1.2 minimum
- HSTS header: Strict-Transport-Security max-age=31536000; includeSubDomains
- Internal services (DB, Redis): no TLS (Docker internal network)
- External API calls (Anthropic, Hevy, etc.): their HTTPS
```

### NFR-SEC-006 — Input validation & sanitization 🔴 MUST

```
- ALL API inputs validated with Pydantic strict types
- Payload size limits:
  - JSON requests: 5 MB max
  - PDF uploads (blood panels): 10 MB max
  - Chat messages: 10 000 chars max
- SQL injection prevention: SQLAlchemy ORM (no raw SQL with user input)
- XSS prevention: React auto-escaping + Content-Security-Policy header
- CSRF: tokens on non-API forms (low risk for API-only architecture)
- General rate limit: 100 req/min/IP on API
```

### NFR-SEC-007 — LLM-specific security 🟡 SHOULD

Based on OWASP Top 10 for LLM Applications (2024):

| Risk | Mitigation |
|---|---|
| **Prompt injection** | Structured prompts, system/user separation, JSON output enforcement, post-LLM guardrails |
| **Sensitive data leak** | No unnecessary PII in prompts, output filtering |
| **Excessive agency** | Strict tool whitelisting, human approval for critical actions |
| **Insecure plugin design** | Read-only MCPs when possible, minimal scopes |
| **Model DoS** | max_tokens cap, daily budget enforcement |

---

## 5. OBSERVABILITY

### NFR-OBS-001 — Stack choice 🔴 MUST

**Decision: Full Grafana stack** (max observability):

```
- Prometheus    → metrics (time-series DB)
- Loki          → logs aggregation (label-based, like Prometheus for logs)
- Tempo         → distributed tracing
- Grafana       → unified visualization layer
- AlertManager  → alert routing
```

All self-hosted on i5 via Docker Compose, accessible only via Tailscale.

### NFR-OBS-002 — Structured logging 🔴 MUST

```
- ALL logs in structured JSON (no verbose print statements)
- Python library: structlog
- Mandatory fields:
  - timestamp (ISO 8601)
  - level (DEBUG / INFO / WARNING / ERROR / CRITICAL)
  - service (api, brain, scheduler, etc.)
  - logger_name
  - message
  - trace_id (correlation)
  - context (dict of business fields: agent_name, user_action, etc.)
- Sensitive fields AUTO-MASKED (passwords, API keys, tokens) via structlog filter
- Rotation: 30 days hot on disk, 90 days cold (Loki), then deleted
```

### NFR-OBS-003 — Metrics 🔴 MUST

```
- Library: prometheus_client (Python)
- Endpoint /metrics exposed internally for scraping
- Standard auto-instrumented metrics:
  - HTTP: request_count, request_duration (histogram), error_count
  - DB: connection_pool_size, query_duration
  - Celery: job_count, job_duration, queue_size, failure_rate

- Custom business metrics:
  - llm_tokens_used_total (counter, by model + agent)
  - llm_cost_eur_total (counter, by model + agent)
  - sync_success_total / sync_failure_total (by service)
  - agent_actions_total (by type + status)
  - workouts_synced_total
  - prs_detected_total

- Metric storage: Prometheus local, 30 days retention
```

### NFR-OBS-004 — Distributed tracing 🟡 SHOULD

```
- Library: OpenTelemetry (otel)
- Auto-instrumentation: FastAPI + SQLAlchemy + Celery + HTTPX
- Tracing backend: Tempo (local)
- Sampling: 100% for MVP (low volume), adjustable later
- Trace ID propagated via X-Trace-Id header
- LLM operation spans tagged with: model, agent, tokens_in, tokens_out, latency
```

### NFR-OBS-005 — Alerting 🔴 MUST

```
- Source: Prometheus AlertManager
- Channels: ntfy.sh (push) + Resend email
- Alert rules (non-exhaustive):
  - CRITICAL : DB down > 30s
  - CRITICAL : brain crashed > 5 min
  - CRITICAL : daily LLM budget exceeded
  - CRITICAL : error rate > 5% over 5 min
  - WARNING  : sync failure 3 times consecutive
  - WARNING  : disk usage > 80%
  - WARNING  : no health_metrics received in > 3h
  - INFO     : service restart
- Anti-spam: grouping + 1h cooldown on same alert
```

### NFR-OBS-006 — Dashboards 🟡 SHOULD

```
- Stack: Grafana local, accessible via Tailscale
- Main dashboards:
  - System Overview (uptime, latency, errors, rates)
  - LLM Usage (tokens, costs, by agent, by model)
  - Sync Status (Hevy, Cronometer, Health Connect)
  - Brain Activity (cycles, plans, executions, reflections)
  - DB Health (connections, slow queries, table sizes)
```

---

## 6. SCALABILITY

### NFR-SCA-001 — Concurrent users 🔴 MUST

```
- Target concurrency: 1 active user (Frederick) + ~5 WebSocket connections
- Background agent can run 1-5 parallel tasks (Celery workers)
- No load balancer needed
- No horizontal replication needed
```

### NFR-SCA-002 — Tolerated limits 🟡 SHOULD

```
- DB size: up to 50 GB before concerns
- LLM calls: up to 1 000/day (well above expected ~50-100 usage)
- Celery workers: up to 10 simultaneous (initial config: 4)
- DB connections: max pool 20 (initial config: 10)
- WebSocket connections: up to 50 per instance (sufficient for 1 user multi-tabs)
```

### NFR-SCA-003 — Growth strategy 🟢 COULD

```
- Single-machine first: stay single-host while i5 holds up
- Vertical scaling before horizontal: upgrade RAM/CPU before splitting
- Phase 4++++ migration if needed:
  - Offload LLM routing to local Ollama (cost savings)
  - Externalize PostgreSQL to Hetzner Cloud (~5€/month) if truly needed
- DO NOT over-engineer for MVP
```

---

## 7. COST

### NFR-COST-001 — Monthly budget target 🔴 MUST

**Hard cap: 45€/month LLM spending** (= 1.5€/day max).

```
Anthropic API (Claude routing)      : 15-25€/month (estimated)
Gemini Flash (free tier fallback)   : 0€
Cronometer Gold (annual)            : ~5€/month
Backblaze B2                        : ~$0.07/month (negligible)
Resend (free tier 3000 emails/month): 0€
ntfy.sh                             : 0€
Tailscale (personal free tier)      : 0€
i5 electricity 24/7                 : ~5-10€/month
Optional domain name                : ~1€/month
─────────────────────────────────────────────
TOTAL                              : 26-41€/month (under cap)
```

### NFR-COST-002 — Hard-coded cost controls 🔴 MUST

```
- Every LLM call records estimated cost in DB
- Pre-LLM-call check verifies:
  - daily_cost_today + estimated_cost <= daily_cost_budget_eur (1.5€)
  - daily_calls_today < daily_call_budget
  
- When limit reached:
  - ERROR returned to caller (clear message)
  - CRITICAL ntfy alert
  - Automatic fallback to Gemini Flash free tier (if Gemini quota available)

- Counters reset at midnight (cron job)
```

### NFR-COST-003 — Cost monitoring 🟡 SHOULD

```
- Dedicated Grafana dashboard: "LLM Cost Tracking"
- Daily metrics:
  - tokens by model (input/output separated)
  - cost by agent (career, fitness, etc.)
  - cost by action type (workout suggestion, chat, brain cycle, etc.)
- Weekly cumulative cost email
- ntfy alert when >80% monthly budget reached
```

### NFR-COST-004 — LLM Routing (3-tier strategy) 🟡 SHOULD

**Locked decision** (see ADR-002):

```
🟢 LEVEL 1 — Simple frequent tasks (~60% volume)
   └─ Gemini 2.5 Flash (free tier 1500 req/day)
   └─ Examples: classification, tag extraction, short summarization, JSON parsing
   └─ COST: 0€

🟡 LEVEL 2 — Medium tasks (~30% volume)
   └─ Claude Haiku 4.5
   └─ Examples: workout suggestions, nutrition plan, plateau analysis
   └─ COST: ~$1/M input + $5/M output

🔴 LEVEL 3 — Complex tasks (~10% volume)
   └─ Claude Sonnet 4.5
   └─ Examples: detailed contextual coaching, agent debugging, complex reasoning
   └─ COST: $3/M input + $15/M output
```

**Implementation strategy**: routing config in `config/llm_routing.yaml`, modifiable without redeploy.

---

## 8. MAINTAINABILITY

### NFR-MAINT-001 — Code quality tooling 🔴 MUST

```
- Python linter: ruff (replaces flake8 + isort + black + pylint)
- Python formatter: ruff format
- Python type checker: mypy (strict mode)
- TypeScript linter: ESLint (config: next/typescript)
- TypeScript formatter: Prettier
- Pre-commit hook (lefthook): runs lint/format/typecheck before commit
- CI blocks merge if lint/types/tests fail
```

### NFR-MAINT-002 — Project structure 🔴 MUST

```
passion-project/
├── backend/                    # FastAPI + Python agents
│   ├── src/
│   │   ├── api/                # REST + WebSocket endpoints
│   │   ├── agents/             # LangGraph agents
│   │   ├── brain/              # orchestrator + scheduler
│   │   ├── integrations/       # Hevy, Cronometer, ntfy clients
│   │   ├── llm/                # router + prompts + guardrails
│   │   ├── models/             # SQLAlchemy + Pydantic
│   │   ├── repositories/       # DB access (repository pattern)
│   │   ├── services/           # business logic
│   │   └── utils/              # helpers
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                   # Next.js
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── messages/               # i18n: fr.json, en.json
│   ├── package.json
│   └── Dockerfile
├── infra/                      # Docker compose, Caddy config, etc.
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── caddy/
│   ├── grafana/
│   └── prometheus/
├── scripts/                    # backup, migrations, seed, etc.
├── docs/
│   ├── SPECIFICATIONS.md
│   ├── NON_FUNCTIONAL_REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── decisions/              # ADRs
│       ├── ADR-001-backend-language.md
│       ├── ADR-002-llm-integration-strategy.md
│       ├── ADR-003-hosting-strategy.md
│       └── ADR-004-network-exposure.md
└── README.md
```

### NFR-MAINT-003 — Documentation 🟡 SHOULD

```
- README.md          : introduction + local setup
- SPECIFICATIONS.md  : functional requirements (already written)
- NON_FUNCTIONAL_REQUIREMENTS.md : this document
- ARCHITECTURE.md    : C4 diagrams, API contracts
- ROADMAP.md         : phases + sprints
- CONTRIBUTING.md    : commit conventions, branch strategy, PR rules
- CHANGELOG.md       : auto-generated from conventional commits
- docs/decisions/    : Architecture Decision Records
- API docs           : auto-generated by FastAPI (Swagger UI at /docs)
- Docstrings         : on all public functions (Google style)
```

### NFR-MAINT-004 — Conventional Commits 🔴 MUST

Mandatory commit message format:

```
feat(fitness): add Hevy webhook handler
fix(brain): prevent infinite loop in retry logic
docs(readme): update setup instructions
test(integrations): add Cronometer mock fixtures
chore(deps): bump fastapi to 0.110
refactor(llm): extract guardrails to dedicated module
perf(api): add caching on /dashboard endpoint
```

**Benefits**: auto-generated CHANGELOG, clear change type indication, semver automation (Phase 4+).

### NFR-MAINT-005 — Database migrations 🔴 MUST

```
- Alembic (Python standard for PostgreSQL migrations)
- Migrations versioned in Git (never alter schema manually)
- Auto-generated migrations reviewed manually before commit
- Rollback tested for every significant migration
- Migration file naming: YYYYMMDD_HHmm_description.py
```

### NFR-MAINT-006 — Source control & CI/CD 🔴 MUST

**Decision: GitHub + GitHub Actions** (see considerations below).

```
- Code hosting: GitHub (public repo recommended for portfolio value)
- CI/CD: GitHub Actions (free unlimited for public repos)
- Secrets: GitHub Secrets (never committed)
- Dependency scanning: Dependabot (auto-enabled)
- Security scanning: CodeQL (free for public repos)
```

CI pipeline (every PR + main push):
1. Lint (ruff, ESLint)
2. Type-check (mypy, tsc)
3. Unit tests (pytest, vitest)
4. Integration tests (testcontainers)
5. Build Docker images
6. (Phase 4+) Auto-deploy to i5 via Tailscale SSH

---

## 9. TESTABILITY

### NFR-TEST-001 — TDD strategy (hybrid pragmatic) 🔴 MUST

**Locked decision: TDD strict with pragmatic differentiation by module type.**

```
🔴 STRICT TDD (Red → Green → Refactor) mandatory for:
   - Brain orchestrator (system core)
   - LLM router & guardrails (critical logic)
   - Specialized agents (fitness, etc.)
   - Calculation services (PR detection, plateau analysis, stats)
   - Repositories (DB access)
   
🟡 Tests-first (before code) but without strict Red-Green-Refactor:
   - API endpoints (often thin wrappers)
   - Background Celery jobs
   - Alembic migrations
   
🟢 Tests-after (post-hoc) acceptable for:
   - Frontend components (highly changeable)
   - One-off scripts
   - Simple Next.js hooks
```

### NFR-TEST-002 — Coverage targets 🔴 MUST

```
- Backend critical modules     : 85%+ coverage
  - src/services/             : 90%+
  - src/agents/, src/brain/, src/llm/ : 85%+
  - src/api/                  : 70%+
- Frontend                    : 60%+ coverage
  - hooks                     : 80%+
  - shared components         : 70%+
- Global backend target       : 80%+
- No 100% obsession (counterproductive at 10-20h/week)
```

### NFR-TEST-003 — Test types 🔴 MUST

```
1. Unit tests (pytest)
   └─ isolated business logic (services, utils, parsers)
   └─ fast, no DB or network
   
2. Integration tests
   └─ with Postgres test DB (testcontainers)
   └─ with mocks for LLM, external APIs
   
3. BDD tests (pytest-bdd) ⭐ KEY DIFFERENTIATOR
   └─ Gherkin scenarios from SPECIFICATIONS.md become executable tests
   └─ Each User Story has a corresponding .feature file
   └─ Tests directly verify acceptance criteria

4. E2E tests (Phase 4+, not MVP)
   └─ Playwright on frontend
   └─ Complete user journeys
```

### NFR-TEST-004 — Test fixtures 🟡 SHOULD

```
- Pydantic factories (polyfactory)
- Database fixtures via testcontainers (disposable Postgres in Docker)
- Mocked LLM responses (snapshots of real responses)
- Hevy/Cronometer mocks in tests/fixtures/
```

### NFR-TEST-005 — CI Pipeline 🔴 MUST

```
- GitHub Actions on every PR + main push
- Pipeline stages:
  1. lint (ruff)
  2. type-check (mypy)
  3. unit tests
  4. integration tests
  5. build Docker images
  6. (Phase 4+) auto-deploy to i5

- Tests blocking: no merge if tests fail
- Performance benchmarks: track p95 latency on critical endpoints (Phase 4+)
```

---

## 10. USABILITY & ACCESSIBILITY

### NFR-UX-001 — Design system 🔴 MUST

```
- shadcn/ui as foundation
- Centralized design tokens (Tailwind CSS variables)
- Mobile-responsive (no native app, but dashboard must work on phone)
- Dark mode by default (cyberpunk PASSION/PACT vibes)
- Storybook for component docs (Phase 4+ optional)
```

### NFR-UX-002 — Accessibility (a11y) 🟡 SHOULD

```
- Target level: WCAG 2.2 AA (decent minimum)
- Contrast ratio: 4.5:1 minimum for normal text
- Keyboard navigation: logical tab order on all pages
- ARIA labels on all interactive elements
- No images without alt
- Visible focus indicator (outline ring)
```

### NFR-UX-003 — Perceived performance 🟡 SHOULD

```
- Skeleton loaders during data loads
- Optimistic UI updates (action appears before server confirmation)
- Toast notifications for important actions
- Clear actionable error states (no generic "Something went wrong")
- Loading states < 1s are skippable (no spinner for fast loads)
```

### NFR-UX-004 — Internationalization (i18n) 🟡 SHOULD

**Locked decision: Interface FR, code/docs/commits EN.**

```
- UI in French (next-intl library)
  - All visible labels: "Tableau de bord", "Mes entraînements", etc.
  - Dates in French format (DD/MM/YYYY, HH:mm)
  - Structure prepared to switch to English (but not enabled in MVP)

- Code, commits, docs in English:
  - Variable, function, class names in English
  - Code comments in English
  - Commit messages in English (conventional commits)
  - Technical documentation in English
  - JSDoc / docstrings in English

- Mixed cases:
  - LLM prompts for chat coach → French (user interacts in French)
  - But prompt names in code → English ("coach_chat_prompt")
  - User-visible text via centralized i18n file, never hardcoded
```

---

## 11. COMPATIBILITY

### NFR-COMPAT-001 — Browsers 🔴 MUST

```
- Chrome / Edge: 2 latest versions
- Firefox: 2 latest versions
- Safari: 2 latest versions (desktop only, no iOS-specific testing)
- No IE support (obvious)
- No fallback for older browsers (single user, you control your tools)
```

### NFR-COMPAT-002 — Devices 🟡 SHOULD

```
- Desktop: 1280px+ (main target, your dev screen)
- Tablet: 768-1279px (responsive)
- Mobile: 320-767px (responsive, basic features)
- No extensive cross-device testing (you are your own QA)
```

### NFR-COMPAT-003 — OS 🔴 MUST

```
- Server: Linux (Ubuntu 22.04+ or Debian 12+)
- Client: any modern browser
- Tasker: Android (Xiaomi Smart Band 9 Pro confirmed compatible)
- No Mac/Windows-specific dependencies
```

---

## 12. PRIVACY & DATA SOVEREIGNTY

This section is **critical** for a personal self-hosted assistant.

### NFR-PRIV-001 — Data ownership 🔴 MUST

```
- ALL data stored on Frederick's infrastructure (i5 + USB + Backblaze)
- No telemetry leaves the system without explicit authorization
- No third-party analytics tracking (PostHog, Mixpanel, etc.) — even for MVP
- No SaaS error reporting (Sentry, Bugsnag) — errors handled locally
```

### NFR-PRIV-002 — Data shared with LLMs 🔴 MUST

Critical because each API call sends data to providers.

```
Provider policies (May 2026):

- Anthropic API:
  - No training on API inputs (standard policy)
  - 30-day log retention by default (Zero Data Retention available on Enterprise)
  
- Google Gemini API:
  - Paid tier: NO training on inputs
  - Free tier: YES, can use for improvement (DON'T USE FOR SENSITIVE DATA)

Consequence: avoid Gemini Flash free tier for SENSITIVE data:
- SENSITIVE = blood panels, personal journal (Phase 4+), CGM data (Phase 4+)
- NON-SENSITIVE = public workouts, fitness stats, training schedule

Mitigation: @sensitive decorator forces routing to Anthropic only
```

### NFR-PRIV-003 — Right to erasure 🟡 SHOULD

```
- User can permanently delete their data (you)
- Endpoint /api/v1/admin/wipe-data (System password protected)
- Cascade deletion across related tables
- Also deletes from backups (purge script)
- Audit logs preserved (who did what when), append-only
```

### NFR-PRIV-004 — Log anonymization 🔴 MUST

```
- PII automatically filtered from logs (emails, names, specific health values)
- structlog filter with regex + forbidden keys list
- Grafana/Loki logs apply the same filtering
- Stack traces: OK for debug, but no values of sensitive variables
```

---

## 13. SUMMARY MATRIX

### MoSCoW priority distribution

```
🔴 MUST       : 28 NFRs (non-negotiable foundations)
🟡 SHOULD     : 20 NFRs (important quality attributes)
🟢 COULD      : 4 NFRs (nice-to-have)
TOTAL         : 52 NFRs
```

### Quick reference table

| NFR ID | Category | Title | Priority |
|---|---|---|---|
| NFR-PERF-001 | Performance | Backend API latency | 🔴 MUST |
| NFR-PERF-002 | Performance | Sync job performance | 🟡 SHOULD |
| NFR-PERF-003 | Performance | Frontend Core Web Vitals | 🔴 MUST |
| NFR-PERF-004 | Performance | Data volume projection | 🟡 SHOULD |
| NFR-PERF-005 | Performance | Table partitioning | 🟡 SHOULD |
| NFR-PERF-006 | Performance | Archival strategy | 🟢 COULD |
| NFR-PERF-007 | Performance | Critical indexes | 🔴 MUST |
| NFR-PERF-008 | Performance | Materialized views | 🟡 SHOULD |
| NFR-REL-001 | Reliability | Uptime SLO | 🔴 MUST |
| NFR-REL-002 | Reliability | Retry & backoff | 🔴 MUST |
| NFR-REL-003 | Reliability | Backup 3-2-1 | 🔴 MUST |
| NFR-REL-004 | Reliability | Graceful degradation | 🔴 MUST |
| NFR-REL-005 | Reliability | Idempotence | 🔴 MUST |
| NFR-SEC-001 | Security | Auth & sessions | 🔴 MUST |
| NFR-SEC-002 | Security | Secrets management | 🔴 MUST |
| NFR-SEC-003 | Security | Network exposure (Tailscale) | 🔴 MUST |
| NFR-SEC-004 | Security | Data at rest | 🔴 MUST |
| NFR-SEC-005 | Security | Data in transit | 🔴 MUST |
| NFR-SEC-006 | Security | Input validation | 🔴 MUST |
| NFR-SEC-007 | Security | LLM security | 🟡 SHOULD |
| NFR-OBS-001 | Observability | Stack choice (Grafana) | 🔴 MUST |
| NFR-OBS-002 | Observability | Structured logging | 🔴 MUST |
| NFR-OBS-003 | Observability | Metrics | 🔴 MUST |
| NFR-OBS-004 | Observability | Distributed tracing | 🟡 SHOULD |
| NFR-OBS-005 | Observability | Alerting | 🔴 MUST |
| NFR-OBS-006 | Observability | Dashboards | 🟡 SHOULD |
| NFR-SCA-001 | Scalability | Concurrent users | 🔴 MUST |
| NFR-SCA-002 | Scalability | Tolerated limits | 🟡 SHOULD |
| NFR-SCA-003 | Scalability | Growth strategy | 🟢 COULD |
| NFR-COST-001 | Cost | Monthly budget | 🔴 MUST |
| NFR-COST-002 | Cost | Cost controls | 🔴 MUST |
| NFR-COST-003 | Cost | Cost monitoring | 🟡 SHOULD |
| NFR-COST-004 | Cost | LLM routing 3-tier | 🟡 SHOULD |
| NFR-MAINT-001 | Maintainability | Code quality tooling | 🔴 MUST |
| NFR-MAINT-002 | Maintainability | Project structure | 🔴 MUST |
| NFR-MAINT-003 | Maintainability | Documentation | 🟡 SHOULD |
| NFR-MAINT-004 | Maintainability | Conventional commits | 🔴 MUST |
| NFR-MAINT-005 | Maintainability | DB migrations | 🔴 MUST |
| NFR-MAINT-006 | Maintainability | Source & CI/CD | 🔴 MUST |
| NFR-TEST-001 | Testability | TDD strategy | 🔴 MUST |
| NFR-TEST-002 | Testability | Coverage targets | 🔴 MUST |
| NFR-TEST-003 | Testability | Test types | 🔴 MUST |
| NFR-TEST-004 | Testability | Test fixtures | 🟡 SHOULD |
| NFR-TEST-005 | Testability | CI Pipeline | 🔴 MUST |
| NFR-UX-001 | Usability | Design system | 🔴 MUST |
| NFR-UX-002 | Usability | Accessibility | 🟡 SHOULD |
| NFR-UX-003 | Usability | Perceived performance | 🟡 SHOULD |
| NFR-UX-004 | Usability | i18n FR/EN | 🟡 SHOULD |
| NFR-COMPAT-001 | Compatibility | Browsers | 🔴 MUST |
| NFR-COMPAT-002 | Compatibility | Devices | 🟡 SHOULD |
| NFR-COMPAT-003 | Compatibility | OS | 🔴 MUST |
| NFR-PRIV-001 | Privacy | Data ownership | 🔴 MUST |
| NFR-PRIV-002 | Privacy | LLM data sharing | 🔴 MUST |
| NFR-PRIV-003 | Privacy | Right to erasure | 🟡 SHOULD |
| NFR-PRIV-004 | Privacy | Log anonymization | 🔴 MUST |

---

## NEXT STEPS

With Functional Requirements (SPECIFICATIONS.md) and Non-Functional Requirements (this document) locked, the next phase is the **detailed Architecture design** (ARCHITECTURE.md):

1. **C4 model diagrams** (Context, Container, Component)
2. **Data flows** between system components
3. **API contracts** with Pydantic schemas
4. **Database schemas finalized** with migrations
5. **Folder structure** complete
6. **Technology stack** with precise versions

---

*Document generated on 17 May 2026 — Frederick × Claude*
*Version: 1.0 (All NFR locked, Architecture phase next)*
