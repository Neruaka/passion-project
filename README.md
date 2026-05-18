# PASSION-FR — Personal AI Operating System

> An autonomous AI agent running 24/7 on a self-hosted Linux server, designed as a comprehensive life-management system covering fitness, health, finance, career, journaling, and more.

[![Status](https://img.shields.io/badge/status-requirements%20locked-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Python](https://img.shields.io/badge/python-3.12+-blue)]()
[![Next.js](https://img.shields.io/badge/next.js-15-black)]()
[![PostgreSQL](https://img.shields.io/badge/postgres-16+-blue)]()
[![LangGraph](https://img.shields.io/badge/agents-LangGraph-purple)]()

---

## 🙏 Inspiration & Attribution

This project is **heavily inspired by [PASSION/PACT](https://github.com/DareDev256)**, the personal AI operating system built by **James Dare ([DareDev256](https://github.com/DareDev256))**. PASSION is an autonomous AI agent + dashboard system that lives 24/7 on a Mac Mini in Toronto and assists its creator across every domain of his life.

Discovering PASSION was a turning point — it crystallized what a deeply personal, deeply useful AI system could look like when built with conviction. **The vision, the modular agent architecture, the "always-on" philosophy, the gamified dashboard, and many of the core ideas in this project are direct echoes of James's work.**

That said, this is not a fork or a clone:
- **Different context**: tailored to my life (Type 1 diabetes management with CGM data, French banking integrations, M1 Data & AI academic context, French ecosystem)
- **Different stack**: Python (FastAPI + LangGraph) instead of James's primarily TypeScript stack
- **Different goal**: a portfolio piece for my Data Engineering / ML Engineering / Agent Engineering repositioning, in addition to its daily-utility purpose
- **Different scope at MVP**: focused first on the Fitness agent before expanding to other domains

**Massive respect to James for showing what's possible.** If you're reading this and you haven't seen PASSION yet, go look at it — it's one of the most impressive personal AI projects out there.

---

## 🎯 What is this?

PASSION-FR is my attempt at building a **personal AI operating system**: an autonomous agent system that runs on my home server 24/7, ingests data from the various services I use (fitness tracker, nutrition tracker, health metrics, etc.), maintains long-term memory, makes contextual recommendations, and helps me manage the complexity of modern adult life.

It is **single-user** (just me) and **fully self-hosted** (no cloud dependencies beyond LLM APIs).

### Core capabilities (MVP scope)

**🧠 Brain**
- Autonomous orchestration loop (Think → Plan → Execute → Reflect)
- Long-term memory with vector search (RAG)
- Real-time chat interface ("Direct Line")
- Multi-tier LLM routing (Gemini Flash / Claude Haiku / Claude Sonnet) for cost optimization

**💪 Fitness agent (MVP focus)**
- Auto-sync workouts from [Hevy](https://www.hevyapp.com) via [hevy-mcp](https://github.com/chrisdoc/hevy-mcp)
- Auto-detect personal records (1RM estimate, reps, volume)
- Detect plateaus, regressions, and "behind schedule" alerts (context-aware: cutting/bulking)
- Adaptive workout suggestions based on recovery state, sleep, HRV
- Adaptive nutrition plan synced with [Cronometer](https://cronometer.com) via [cronometer-mcp](https://github.com/pshortino/cronometer-mcp)
- Body scanner showing per-muscle-group recovery status
- Weekly challenges + gamification (streaks, missions, XP)

**🩺 Health metrics ingestion**
- Sleep, HR, HRV, NEAT, steps from Mi Band 9 Pro via Health Connect → Tasker → API
- Manual entry for blood panels and body composition
- Daily snapshot dashboard

**🔔 Notifications**
- Push notifications via [ntfy.sh](https://ntfy.sh) (briefings, alerts, PR celebrations)
- Email briefings via [Resend](https://resend.com)

### Future scope (Phase 4+)

- **Career agent**: automated job hunting across multiple boards
- **Journal agent**: NLP analysis of personal entries → metrics + insights
- **Finance agent**: integration with BNP Paribas and Revolut (open banking via Bridge/Powens)
- **Social publisher**: scheduled posts on LinkedIn, Reddit, Twitter
- **Code agent**: multi-repo orchestration across GitHub/GitLab
- **Intel radar**: filtered Reddit + HN + RSS aggregator
- **CGM integration**: Dexcom G6 + YpsoPump + CamAPS FX data via xDrip+/Nightscout

---

## 📚 Documentation

This project follows a **specifications-first** approach. Before writing any code, the entire system has been documented in extensive detail:

| Document | Description | Status |
|---|---|---|
| [docs/SPECIFICATIONS.md](docs/SPECIFICATIONS.md) | Functional requirements: 33 user stories with Gherkin acceptance criteria | ✅ Locked |
| [docs/NON_FUNCTIONAL_REQUIREMENTS.md](docs/NON_FUNCTIONAL_REQUIREMENTS.md) | 52 NFRs across 11 categories (performance, security, observability, etc.) | ✅ Locked |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records (ADRs) | 4 written, more coming |
| docs/ARCHITECTURE.md | C4 diagrams, data flows, API contracts | 🔜 In progress |
| docs/ROADMAP.md | Phase breakdown + sprint planning | 🔜 Coming |

If you're a recruiter or curious about how serious specifications-first engineering looks, [start here](docs/SPECIFICATIONS.md).

---

## 🏗️ Architecture (high-level)

```
┌────────────────────────────────────────────────────────────────┐
│              User (me) — laptop + Android phone                │
└─────────────────────────────┬──────────────────────────────────┘
                              │ Tailscale (zero-trust mesh VPN)
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                  Self-hosted i5 32GB Linux                     │
│                                                                 │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐  │
│  │ Next.js 15   │◄──►│ FastAPI backend │◄──►│ PostgreSQL   │  │
│  │ dashboard    │    │ + LangGraph     │    │ + pgvector   │  │
│  └──────────────┘    │ + Celery        │    └──────────────┘  │
│                      └────────┬────────┘                       │
│                               │                                │
│                  ┌────────────┼────────────┐                  │
│                  │            │            │                  │
│           ┌──────▼─────┐ ┌────▼─────┐ ┌────▼──────┐          │
│           │ hevy-mcp   │ │cronometer│ │ Redis     │          │
│           │ (Node.js)  │ │  -mcp    │ │ + queues  │          │
│           └────────────┘ └──────────┘ └───────────┘          │
│                                                                 │
│  Observability: Prometheus + Loki + Tempo + Grafana            │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼ External APIs
        ┌────────────┬────────────┬────────────┬────────────┐
        │ Anthropic  │ Gemini API │  Hevy API  │ Cronometer │
        │ (Claude)   │ (free tier)│            │            │
        └────────────┴────────────┴────────────┴────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed C4 diagrams (coming).

---

## 🛠️ Tech Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI + Pydantic v2
- **Agents**: LangGraph
- **LLMs**: Claude Sonnet 4.5, Claude Haiku 4.5, Gemini 2.5 Flash (3-tier cost routing)
- **Database**: PostgreSQL 16+ with pgvector for RAG
- **Cache + Queues**: Redis 7+
- **Background jobs**: Celery
- **MCP integrations**: hevy-mcp (Hevy), cronometer-mcp (Cronometer)

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **i18n**: next-intl (French UI, English code/docs)

### Infrastructure
- **Container orchestration**: Docker + docker-compose
- **Reverse proxy**: Caddy (automatic HTTPS)
- **Network access**: Tailscale only (zero public exposure)
- **Observability**: Prometheus + Loki + Tempo + Grafana
- **CI/CD**: GitHub Actions

### Storage & Backups
- **Production**: i5 internal SSD
- **Local backups**: external USB drive (daily pg_dump, encrypted with `age`)
- **Off-site backups**: Backblaze B2 (weekly, encrypted, ~$0.07/month)

See [ADR-001](docs/decisions/ADR-001-backend-language.md) for the rationale behind the Python choice and [ADR-002](docs/decisions/ADR-002-llm-integration-strategy.md) for the LLM routing strategy.

---

## 💰 Monthly Cost

The project is designed to run for **under 45€/month** total, hard-capped via in-code budget enforcement.

| Item | Monthly cost |
|---|---|
| Anthropic API (estimated, with routing) | 15-25€ |
| Cronometer Gold | ~5€ |
| Backblaze B2 backups | ~$0.07 |
| Electricity (i5 24/7) | 5-10€ |
| Domain (optional) | ~1€ |
| **Total** | **26-41€/month** |

One-time costs: Hevy Pro Lifetime (~70€), Tasker + AutoHealth Connect (~7€).

---

## 🗺️ Project Status & Roadmap

This project is in the **specifications phase** — extensive documentation has been produced before writing a single line of application code. This is intentional: specifications-first engineering reduces wasted work and produces a portfolio piece that demonstrates senior-level engineering discipline.

### Phase progress

| Phase | Status | Deliverables |
|---|---|---|
| **Phase 0 — Vision & Scope** | ✅ Complete | Vision, MVP scope, OUT-OF-SCOPE list |
| **Phase 1 — User Stories** | ✅ Complete | 33 stories with Gherkin acceptance criteria |
| **Phase 2 — Non-Functional Requirements** | ✅ Complete | 52 NFRs across 11 categories |
| **Phase 3 — Architecture Decision Records** | 🟡 In progress | 4 ADRs locked, more coming |
| **Phase 4 — Detailed Architecture** | 🔜 Next | C4 diagrams, API contracts, DB schemas |
| **Phase 5 — Sprint Roadmap** | 🔜 Coming | Phase breakdown + estimated effort |
| **Phase 6 — Implementation** | ⏳ Not started | The actual code |

Estimated time to MVP after Phase 5: **3-4 months** at 10-20h/week.

---

## 🧠 Why this matters (for me)

This isn't just a tech project. It's:

1. **A real tool I'll use every day** to manage my fitness transformation, health (Type 1 diabetes with closed-loop insulin therapy), career repositioning, and life logistics.
2. **A portfolio piece for my career repositioning** — I'm transitioning from full-stack web dev to Data Engineering / ML Engineering / Agent Engineering, and this project showcases skills directly relevant to those roles.
3. **A learning vehicle** for Python depth, LangGraph, MCP, RAG, MLOps, observability, and self-hosted infrastructure.
4. **A continuation of my [academic work](https://www.ipssi.com)** — I'm currently completing an M1 in Data & AI.

---

## 📖 About the original PASSION

[James Dare (DareDev256)](https://github.com/DareDev256) describes PASSION on his website:

> *I'm an autonomous AI agent living on a Mac Mini in Toronto. I write code, hunt jobs, scan threats, and learn from every mistake — all while my creator sleeps.*

Numbers as of early 2026:
- **92 modules**
- **109K lines of code**
- **47 repos managed**
- **89.9% PR approval rate**
- **24/7 uptime**

James also built a series of mini-games to train himself ([TypeMaster AI](https://typing-game-kappa-seven.vercel.app/), [Red Team Arena](https://red-team-arena.vercel.app/), [Prompt Craft](https://prompt-craft-jet.vercel.app/), and many others) — a brilliant meta-touch that shows the depth of the system.

This project is a **smaller, more focused, France-adapted spiritual successor**. Different person, different life, different stack — but the same conviction that a personal AI system, built with care, can be one of the most leveraged tools in your life.

---

## 📜 License

MIT License — see [LICENSE](LICENSE).

You're welcome to fork, study, and adapt this project to your own context. If you do, drop a note — I'd love to see how others build their own version.

---

## 🤝 Contact

**Frederick (DareDev256-inspired, but with my own twist)**

- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [your-linkedin](https://linkedin.com/in/your-profile)
- Located in: Paris, France 🇫🇷

If you're a recruiter looking at this project: I'm currently in alternance at the Diocèse de Paris (Service Systèmes d'information) while completing my M1 Data & AI at IPSSI Paris. **Actively seeking** Data Engineering / ML Engineering / Agent Engineering roles for 2026-2027 — open to relocation (Canada, USA, Asia).

---

*This README, like the rest of the docs, was iterated extensively with Claude (Anthropic) as a thinking partner. Building in the open about how AI was used to design and ship this project — full transparency.*
