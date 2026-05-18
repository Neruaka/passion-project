# ADR-003 — Hosting: Self-hosted on existing i5 32GB Linux server

## Status

**Accepted** — 2026-05-15

## Context

PASSION must run 24/7 to fulfill its core promise as an "always-on personal assistant". The project requires:

- Backend API server (FastAPI + Celery workers)
- PostgreSQL database with pgvector
- Redis (cache + queues)
- Node.js MCP servers (hevy-mcp, cronometer-mcp)
- Full observability stack (Prometheus, Loki, Tempo, Grafana)
- Reverse proxy (Caddy)
- Background scheduling for sync jobs

Available resources for Frederick:
- Existing i5 32GB Linux server (already in homelab)
- Tight budget (target: < 50€/month total recurring)
- Time budget: 10-20h/week

Self-hosting must be balanced against the friction of running production infrastructure at home.

## Decision

**Self-host on the existing i5 32GB Linux server.**

- Operating system: Ubuntu 22.04 LTS or Debian 12
- Container orchestration: Docker + docker-compose
- Reverse proxy: Caddy (automatic HTTPS via internal ACME)
- All services on a single host for MVP
- No cloud VPS for MVP
- No Mac Mini purchase for MVP

## Rationale

### 1. Zero acquisition cost

The i5 32GB exists already. Zero additional hardware spend means more budget room for API costs and Hevy Pro lifetime.

### 2. Sufficient resources

DB size at 5 years estimated at ~14 GB, well within available disk. RAM (32GB) is plenty for Postgres + Redis + Python services + observability stack + future local Ollama experiments.

### 3. Latency advantage

On LAN, network latency between frontend (browser) and backend is negligible. Helps meet aggressive p95 targets (< 200ms on GET endpoints).

### 4. Privacy and data sovereignty

All data stays on Frederick's hardware. No third-party hosting provider has access to health, fitness, financial, or journal data. Aligns with the project's core privacy stance (NFR-PRIV-001).

### 5. Self-hosting skill demonstration

For a portfolio targeting Data/ML/Agent Engineering roles, showing operational maturity (Docker orchestration, observability stack, backup strategy, network configuration) is a distinguishing factor.

### 6. Migration path exists if needed

If the i5 saturates or fails permanently, the entire stack is Docker-Composed → can be migrated to Hetzner Cloud (~5€/month) or any VPS in hours, not weeks.

## Alternatives considered

### A. Mac Mini M4 purchase

**Pros**: Modern hardware, low power consumption, capable of running quality local LLMs (Llama 3.3 70B or Qwen 2.5 14B).
**Cons**: 700-900€ upfront cost before MVP exists. Premature optimization. Cloud LLM API is cost-effective enough at MVP scale.
**Verdict**: Rejected for MVP. Reconsider in Phase 4+ if local LLM becomes important.

### B. Cloud VPS (Hetzner, Railway, Scaleway)

**Pros**: Higher reliability (no home FAI dependency), no electricity bill at home, easier external access.
**Cons**: Recurring 10-30€/month for sufficient resources. Data leaves Frederick's home. Doesn't demonstrate self-host skill on portfolio.
**Verdict**: Rejected. Held in reserve as fallback if i5 fails.

### C. Hybrid (data on i5, compute on cloud)

**Pros**: Best of both worlds in theory.
**Cons**: Network complexity (Postgres over WAN = high latency), increased attack surface, doesn't simplify anything.
**Verdict**: Rejected.

### D. Raspberry Pi 5

**Pros**: Lowest cost (~80€), low power.
**Cons**: 8GB RAM ceiling, insufficient for Postgres + Redis + observability + agents + MCP servers. Would severely constrain growth.
**Verdict**: Rejected.

## Consequences

### Positive

- Zero hardware acquisition cost
- All data on Frederick's hardware (privacy + sovereignty)
- Latency advantage on LAN
- Demonstrable self-host skills for portfolio
- Migration path remains open

### Negative

- Single point of failure (if i5 dies, the project is down until replacement)
- Power outages and FAI outages count against uptime SLO
- Frederick is the sole operator (no 24/7 NOC)
- Updates and reboots cause downtime (limits achievable uptime to ~99%)
- Internet exposure requires careful network setup (Tailscale)

### Mitigations

- Backup strategy 3-2-1 (NFR-REL-003) — Off-site Backblaze B2 backups ensure data survives even hardware loss
- Docker Compose ensures the whole stack can be rebuilt in < 1h on any Linux box
- Documented runbook for disaster recovery (Phase 1 deliverable)
- Hetzner Cloud as documented fallback (Phase 4+ playbook)

## Links

- [SPECIFICATIONS.md](../SPECIFICATIONS.md) — Section 3 (Technical Decisions)
- [NON_FUNCTIONAL_REQUIREMENTS.md](../NON_FUNCTIONAL_REQUIREMENTS.md) — Section 3 (Reliability), Section 11 (Compatibility)
- [ADR-004](./ADR-004-network-exposure.md) — Network exposure
