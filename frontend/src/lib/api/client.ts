// Typed API client. Wraps fetch with auth + base URL.
// Talks to the FastAPI backend through Caddy (Tailscale-only).
// TODO(sprint-1): implement request<T>(), auth header injection, error handling.

const API_BASE = "/api/v1";

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  throw new Error("Implement in sprint 1");
}
