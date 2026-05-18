# ADR-001 — Backend language: Python (FastAPI)

## Status

**Accepted** — 2026-05-15

## Context

The PASSION project requires a backend language for:
- API server (REST + WebSocket)
- Brain orchestrator with agent loop
- LangGraph-based multi-agent system
- Integration with multiple MCP servers
- Background job scheduling
- LLM router with cost tracking

Frederick's background:
- Strong MERN stack experience (MongoDB, Express, React, Node.js)
- M1 Data & AI student at IPSSI Paris (Python-centric curriculum)
- Career repositioning towards Data Engineering / ML Engineering / Agent Engineering
- "A little Python" in his own words — area to deepen significantly

## Decision

**Use Python 3.12+ with FastAPI for the entire backend.**

Frontend remains Next.js (TypeScript) for the dashboard UI.

## Rationale

### 1. AI/Agent ecosystem is Python-dominant

LangChain, LangGraph, CrewAI, AutoGen, LlamaIndex, DSPy — all originated in Python. JavaScript bindings exist (LangChain.js) but consistently lag 6+ months behind feature-wise and have less community support. The MCP Python SDK is mature and well-supported.

### 2. Career repositioning value

The roles Frederick targets (Data Engineer, ML Engineer, Agent Engineer) are ~90% Python-based. Using Python deeply for the portfolio project directly addresses his stated career gap and provides daily Python practice.

### 3. Integration with academic context

Frederick's M1 Data & AI uses Python. Cross-pollination between coursework and the portfolio project accelerates learning on both fronts.

### 4. Simplicity over polyglot architecture

A mixed Node.js/Python architecture was considered but rejected. Inter-service communication overhead and dual ecosystem maintenance would consume ~30% of available time budget (10-20h/week). Single-language backend = faster iteration.

### 5. FastAPI specifics

- Native async (uvicorn ASGI)
- Pydantic v2 for type-safe request/response (and stricter inputs validation)
- Auto-generated OpenAPI/Swagger docs
- Industry standard in 2026 for modern Python APIs

## Alternatives considered

### A. Node.js (Express or Fastify)

**Pros**: Frederick already knows MERN, fastest time-to-first-feature.
**Cons**: Agent framework ecosystem is weaker, doesn't address career gap, doesn't reinforce M1 learning.
**Verdict**: Rejected. Short-term velocity gain not worth long-term career cost.

### B. Mixed Node.js + Python

**Pros**: Use Node.js for the API layer (Frederick's strength), Python for agents only.
**Cons**: Two ecosystems to maintain, inter-service communication overhead, deployment complexity doubled, ~30% time tax on a project already tight on hours.
**Verdict**: Rejected. Pragmatic for a team of 5, overkill for a solo project at 10-20h/week.

### C. Go or Rust

**Pros**: Performance, single binary deployment.
**Cons**: Frederick has zero experience, would add months to learning curve, agent ecosystem nonexistent in these languages.
**Verdict**: Rejected.

## Consequences

### Positive

- Single language to maintain across the entire backend stack
- Direct alignment with target job market (90% Python roles)
- Reinforces M1 Data & AI coursework concepts in practice
- Access to the strongest agent/ML ecosystem in 2026
- LangGraph, MCP SDK, and most reference implementations work natively
- FastAPI's auto-generated OpenAPI docs reduce documentation overhead

### Negative

- Steeper learning curve than Node.js (Frederick's comfort zone)
- Initial development pace slower than what Node.js would allow
- Different deployment story than Frederick's current MERN-based diocese project

### Mitigations

- Frontend remains Next.js (familiar territory) — Frederick can ship UI quickly
- FastAPI's syntax is close enough to Express for the learning curve to be manageable
- Strong Python typing (mypy strict mode) reduces runtime surprise compared to "Python is loose"

## Links

- [SPECIFICATIONS.md](../SPECIFICATIONS.md) — Section 3 (Technical Decisions)
- [NON_FUNCTIONAL_REQUIREMENTS.md](../NON_FUNCTIONAL_REQUIREMENTS.md) — Section 8 (Maintainability)
