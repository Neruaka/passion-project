# ADR-002 — LLM integration: 3-tier routing with MCP-first integrations

## Status

**Accepted** — 2026-05-17

## Context

The PASSION agent will make a significant volume of LLM calls (estimated 50-100/day during active use, up to 1000/day peak). The system needs to integrate multiple data sources (Hevy for workouts, Cronometer for nutrition) and exposes a quality-cost tradeoff that must be managed explicitly.

Constraints:
- Monthly LLM budget: max 45€/month (= ~1.5€/day)
- Frederick has consumer subscriptions to Claude Pro, ChatGPT Plus, Gemini Advanced — but **these do NOT include API access** (separate billing model)
- Gemini API offers a generous free tier (1500 req/day on Gemini 2.5 Flash) — independent from Gemini Advanced subscription
- Privacy concern: Gemini free tier may train on submitted data; Anthropic API does not

Frederick is preparing the Anthropic "MCP Advanced Topics" certification, making MCP a strategic learning vector.

## Decision

### Decision 1: 3-tier LLM routing from MVP

Route each LLM call by complexity level:

```
🟢 LEVEL 1 — Simple frequent tasks (~60% volume)
   └─ Gemini 2.5 Flash (free tier)
   └─ Use cases: classification, tag extraction, short summaries, JSON parsing
   └─ Cost: 0€

🟡 LEVEL 2 — Medium tasks (~30% volume)
   └─ Claude Haiku 4.5
   └─ Use cases: workout suggestions, nutrition plan, plateau analysis
   └─ Cost: ~$1/M input + $5/M output

🔴 LEVEL 3 — Complex tasks (~10% volume)
   └─ Claude Sonnet 4.5
   └─ Use cases: detailed contextual coaching, agent debugging, complex reasoning
   └─ Cost: $3/M input + $15/M output
```

A `@sensitive` decorator forces routing to Anthropic-only for privacy-sensitive prompts (blood panels, journal entries).

Routing config stored in `config/llm_routing.yaml` for hot-swap without redeploy.

### Decision 2: MCP-first for external integrations

Use existing MCP servers when available (read-only or stable consumption):
- **hevy-mcp** (chrisdoc) for Hevy integration
- **cronometer-mcp** (community, GWT-RPC-based) for Cronometer integration

Build custom MCP servers only when:
- No mature solution exists
- We need write capabilities not available in existing servers
- We need application-level business logic on top of the integration

Phase 4+ migration path:
- Replace `hevy-mcp` (Node.js) with `passion-hevy-mcp` (Python custom)
- Replace `cronometer-mcp` (GWT-RPC) with a more stable solution if Cronometer publishes an official API

## Rationale

### Why 3-tier routing from MVP (not later)

1. **Budget discipline**: Without routing, all calls go to Sonnet → estimated 80-120€/month, blowing past the 45€ cap immediately.
2. **Skill development**: LLM routing is a real MLOps skill. Showing it on a portfolio project is differentiating.
3. **Cost visibility**: Tracking per-tier metrics from day 1 produces clean Grafana dashboards.
4. **Estimated 60% free**: ~60% of calls go to Gemini Flash free tier → significant cost savings.
5. **Estimated real cost: 20-35€/month** — well under the cap, with margin for growth.

### Why MCP-first

1. **Time-to-value**: hevy-mcp + cronometer-mcp work out of the box. Building these from scratch = 2-4 weeks of integration work.
2. **MCP learning vector**: Frederick's Anthropic certification + the project = applied MCP practice from day one.
3. **Architecture coherence**: Inspired by PASSION/PACT, "MCP everywhere" matches the project's design vision.
4. **Future-proofing**: When we later build `passion-hevy-mcp`, we will have lived with the consumption pattern long enough to know exactly what to build.

### Build vs Buy framework applied

| Component | Buy (existing MCP) | Build (custom) |
|---|---|---|
| Hevy integration | ✅ hevy-mcp (community) | Phase 4+ |
| Cronometer integration | ✅ cronometer-mcp (community) | Phase 4+ |
| Brain orchestrator | ❌ | ✅ — differentiator |
| LLM router | ❌ | ✅ — core business logic |
| Specialized agents | ❌ | ✅ — differentiator |

## Alternatives considered

### A. Single-model approach (Claude Sonnet only)

**Pros**: Simpler code, predictable quality.
**Cons**: ~80-120€/month, blows past budget cap. No skill development on routing.
**Verdict**: Rejected — financially unsustainable.

### B. Local LLMs only (Ollama + Llama 3.3)

**Pros**: Zero recurring cost, full privacy, full self-host vibe.
**Cons**: Quality gap on agent tasks (planning, tool use, structured output), GPU/CPU intensive (would saturate i5 32GB), slower iteration.
**Verdict**: Rejected for MVP, considered for Phase 4+ as additional fallback for very frequent simple tasks.

### C. Build all integrations from scratch (no MCP)

**Pros**: Full control, deep understanding of each API.
**Cons**: 4-6 weeks of integration work upfront, delays MVP, doesn't leverage MCP learning.
**Verdict**: Rejected.

### D. Use Cronometer's CSV export instead of cronometer-mcp

**Pros**: No GWT-RPC fragility risk.
**Cons**: Manual export needed (not 24/7 autonomous), latency too high for real-time coaching.
**Verdict**: Rejected.

## Consequences

### Positive

- Costs predictable and capped (45€/month hard cap enforced in code)
- Faster MVP delivery (2-4 weeks saved on integrations)
- LLM routing skill demonstrable on portfolio
- MCP learning compounded with Anthropic certification
- Easy fallback mechanism (when Anthropic budget exceeded → Gemini Flash free)

### Negative

- 2 third-party Node.js MCP servers to deploy alongside the Python stack (cronometer-mcp and hevy-mcp)
- cronometer-mcp may break when Cronometer updates their web client (GWT-RPC reverse-engineered)
- Routing logic adds complexity (3 model SDKs to maintain)

### Mitigations

- Both MCP servers run in their own Docker containers, isolated from Python backend — failure of one doesn't crash the others
- A `routing.py` abstraction means switching models = changing config, not code
- Monitoring & alerting on MCP server health (Grafana dashboard)
- Fallback chain: Sonnet fails → Haiku → Gemini Flash → cached/template response

## Links

- [SPECIFICATIONS.md](../SPECIFICATIONS.md) — Section 3 (Technical Decisions)
- [NON_FUNCTIONAL_REQUIREMENTS.md](../NON_FUNCTIONAL_REQUIREMENTS.md) — Section 7 (Cost)
- [hevy-mcp on GitHub](https://github.com/chrisdoc/hevy-mcp)
- [cronometer-mcp on GitHub](https://github.com/pshortino/cronometer-mcp)
- [Anthropic MCP Advanced Topics certification](https://www.anthropic.com)
