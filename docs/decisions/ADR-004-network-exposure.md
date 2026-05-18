# ADR-004 — Network exposure: Tailscale-only access (zero public exposure)

## Status

**Accepted** — 2026-05-17

## Context

PASSION will store extremely sensitive data:
- Workout history (fitness identity)
- Nutrition logs (eating patterns)
- Sleep, HR, HRV data (health surveillance)
- Blood panels (medical data)
- Personal journal (Phase 4+)
- API credentials for multiple services
- CGM data (Phase 4+, glucose patterns)

The system runs 24/7 on a residential French internet connection. Access is needed from:
- Frederick's laptop (work + home)
- Frederick's Android phone (Tasker pushing Health Connect data hourly)
- Potentially Frederick's tablet

Multiple network exposure strategies exist, with significantly different security profiles.

## Decision

**Tailscale-only access. Zero public exposure of the application.**

- All services (frontend, backend, observability stack) bind to the Tailscale IP only
- Caddy reverse proxy listens on the Tailscale network interface, not the public WAN interface
- No port forwarding configured on the home router
- No Cloudflare Tunnel (no public ingress)
- Tasker on Android joins the same tailnet to push data
- HTTPS via Tailscale Funnel certificate (or Tailscale MagicDNS + internal ACME)

## Rationale

### 1. Zero-trust networking by design

With Tailscale, every device on the tailnet has its own cryptographic identity (WireGuard keys). No "inside vs outside" — every connection is authenticated and encrypted end-to-end. Even if Frederick's home router is compromised, attackers cannot reach the application without compromised Tailscale credentials.

### 2. Microscopic attack surface

Compared to a publicly exposed application:

| Threat | Public-exposed | Tailscale-only |
|---|---|---|
| Brute force on login page | Yes, constantly | Impossible (no public endpoint) |
| Discovery via Shodan/Censys | Yes | No (no public open ports) |
| Zero-day in Caddy/FastAPI | Exposed | Mitigated (attacker must first join tailnet) |
| Bot traffic / scraping | Yes | None |
| DDoS | Vulnerable | Tailscale handles capacity |

### 3. Free tier sufficient

Tailscale free tier (personal use): up to 100 devices, 3 users. Frederick uses 2-3 devices. Generous beyond all reasonable needs.

### 4. ACL fine-grain control

Tailscale ACLs allow per-device permissions. Example: the Android phone (Tasker) can ONLY hit `/api/v1/health/ingest`, while the laptop has full dashboard access. This implements least-privilege at the network layer, separate from app-layer auth.

### 5. Simplicity of setup

- Install Tailscale client on i5: 5 minutes
- Install Tailscale on Android: install app + sign in: 2 minutes
- Configure Caddy to bind to Tailscale IP: 1 config change
- No router configuration, no DNS records, no ACME certificate procurement (Tailscale handles it)

### 6. HTTPS with proper certificates

Tailscale issues legitimate Let's Encrypt certificates for `*.tail-xxx.ts.net` domains via Tailscale Funnel (opt-in feature) or via Tailscale Cert. Browsers don't show certificate warnings.

## Alternatives considered

### A. Public exposure with strong auth (port forward + Caddy + bcrypt login)

**Pros**: Simpler mental model (familiar), accessible from anywhere with internet.
**Cons**: Continuous brute force attempts, dependent on app-layer security only, requires careful Caddy hardening, exposed to zero-days in dependencies, scraped/indexed by bots.
**Verdict**: Rejected. Risk profile incompatible with the sensitivity of stored data.

### B. Public exposure with Cloudflare Tunnel + Cloudflare Access (Zero Trust)

**Pros**: Free tier exists, no port forwarding needed, integrates with Google/GitHub SSO, DDoS protection included.
**Cons**: Cloudflare can decrypt traffic (MITM by design), adds external dependency, more complex setup than Tailscale, gives Cloudflare visibility on all traffic.
**Verdict**: Rejected for MVP. Could be reconsidered if multi-user access ever needed (not the case here).

### C. Tailscale + Cloudflare Tunnel (hybrid)

**Pros**: Public-accessible while still gated.
**Cons**: Two systems to maintain. The Cloudflare Tunnel adds risk for marginal accessibility benefit (Tailscale already works on all Frederick's devices).
**Verdict**: Rejected.

### D. WireGuard self-managed (no Tailscale)

**Pros**: Pure self-host vibe, no third-party dependency.
**Cons**: Significant config complexity (NAT traversal, peer discovery, key rotation), no built-in MagicDNS, no ACL UI. Several days of additional setup work.
**Verdict**: Rejected for MVP. Could be reconsidered in Phase 4+ if Tailscale changes its free tier.

### E. SSH tunneling

**Pros**: Built into everything.
**Cons**: Doesn't scale for multi-service access (would need a tunnel per service), poor UX for mobile, no MagicDNS.
**Verdict**: Rejected.

## Consequences

### Positive

- Drastically reduced attack surface
- No public endpoints to harden
- Free service that scales for personal needs
- Built-in ACLs for least-privilege networking
- HTTPS handled transparently
- Easy to add/remove devices

### Negative

- Frederick can only access from devices on his tailnet
- Friend / family demos require them to join the tailnet (acceptable: single-user system anyway)
- Tailscale is a centralized control plane (key escrow concern — partially mitigated by tailnet lock feature)
- If Tailscale changes its free tier terms, migration required

### Mitigations

- Critical: regularly audit Tailscale ACLs (quarterly)
- Use Tailscale Tailnet Lock for high-assurance key management
- Document a fallback migration path to WireGuard (Phase 4+ playbook)
- Keep Caddy config ready to bind to public interfaces if Tailscale-less mode ever needed

## Links

- [SPECIFICATIONS.md](../SPECIFICATIONS.md) — Section 3 (Technical Decisions)
- [NON_FUNCTIONAL_REQUIREMENTS.md](../NON_FUNCTIONAL_REQUIREMENTS.md) — Section 4 (Security), Section 12 (Privacy)
- [ADR-003](./ADR-003-hosting-strategy.md) — Self-hosting on i5
- [Tailscale official docs](https://tailscale.com/kb)
