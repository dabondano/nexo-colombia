/**
 * Per-IP limit on staff sign-in and panel forms, for hosts without a reverse
 * proxy that can do it (Render; on the Oracle setup, Caddy does it instead).
 *
 * Enabled only when NEXO_CLIENT_IP_HEADER names a header that the hosting
 * platform sets and visitors cannot forge (on Render: "true-client-ip", set by
 * Cloudflare; X-Forwarded-For can be forged there). The counts live in memory,
 * which is right for one server process. Per-account lockout in the API applies
 * either way.
 */

export const LIMIT = 10;
export const WINDOW_MS = 60_000;

type Window = { start: number; count: number };

export class FixedWindowLimiter {
  private readonly windows = new Map<string, Window>();
  private readonly limit: number;
  private readonly windowMs: number;

  constructor(limit = LIMIT, windowMs = WINDOW_MS) {
    this.limit = limit;
    this.windowMs = windowMs;
  }

  /** Counts one request; true while the key is within its limit. */
  allow(key: string, now = Date.now()): boolean {
    const current = this.windows.get(key);
    if (!current || now - current.start >= this.windowMs) {
      this.windows.set(key, { start: now, count: 1 });
      this.prune(now);
      return true;
    }
    current.count += 1;
    return current.count <= this.limit;
  }

  /** Drops finished windows so memory stays bounded. */
  private prune(now: number) {
    if (this.windows.size < 10_000) return;
    for (const [key, window] of this.windows) {
      if (now - window.start >= this.windowMs) this.windows.delete(key);
    }
  }
}

/** The visitor's IP from the configured trusted header, or null when not configured. */
export function clientIp(headers: Headers, headerName = process.env.NEXO_CLIENT_IP_HEADER): string | null {
  if (!headerName) return null;
  const value = headers.get(headerName)?.split(",")[0]?.trim();
  return value ? value : null;
}

export function isStaffForm(method: string, pathname: string): boolean {
  if (method !== "POST") return false;
  return (
    pathname === "/ingresar" ||
    pathname.startsWith("/ingresar/") ||
    pathname === "/panel" ||
    pathname.startsWith("/panel/")
  );
}
