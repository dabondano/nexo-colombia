import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiBaseUrl } from "@/lib/api";
import type { Role } from "@/lib/staff-labels";

export type { Role } from "@/lib/staff-labels";
export { ROLE_LABELS } from "@/lib/staff-labels";

/**
 * Data access for the staff panel. The session token lives only in an
 * HTTP-only cookie and is sent to the API from the server; the API checks the
 * session and the role on every request. Pages here only decide what to show.
 */

export const SESSION_COOKIE = "nexo_sesion";

export type StaffUser = {
  id: string;
  email: string;
  display_name: string;
  role: Role;
  must_change_password: boolean;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};

export type StaffResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; reason: string };

export async function sessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

export async function staffRequest<T>(
  path: string,
  init: { method?: string; body?: unknown; token?: string; params?: Record<string, string | number | undefined> } = {},
): Promise<StaffResult<T>> {
  const token = init.token ?? (await sessionToken());
  const url = new URL(`/api/v1${path}`, apiBaseUrl());
  for (const [key, value] of Object.entries(init.params ?? {})) {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }
  try {
    const response = await fetch(url, {
      method: init.method ?? "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      let reason = `La API respondió con el código ${response.status}.`;
      try {
        const detail = (await response.json()).detail;
        if (typeof detail === "string") reason = detail;
        else if (Array.isArray(detail)) reason = "Revise los datos del formulario.";
      } catch {
        // Keep the generic reason.
      }
      return { ok: false, status: response.status, reason };
    }
    if (response.status === 204) return { ok: true, data: undefined as T };
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, status: 0, reason: "No fue posible conectar con la API de NEXO." };
  }
}

/** The signed-in staff member, or null. */
export async function currentStaff(): Promise<StaffUser | null> {
  if (!(await sessionToken())) return null;
  const result = await staffRequest<StaffUser>("/auth/me");
  return result.ok ? result.data : null;
}

/**
 * For panel pages: sends visitors to the sign-in page and staff with an issued
 * password to the password page. Returns the user and whether the role may see
 * the page (administrators may see every page).
 */
export async function requireStaff(
  roles: Role[] = [],
  { allowPasswordChange = false } = {},
): Promise<{ user: StaffUser; allowed: boolean }> {
  const user = await currentStaff();
  if (!user) redirect("/ingresar");
  if (user.must_change_password && !allowPasswordChange) redirect("/panel/contrasena");
  const allowed = roles.length === 0 || user.role === "admin" || roles.includes(user.role);
  return { user, allowed };
}

const timestamp = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Bogota",
});

export function formatTimestamp(value: string | null): string {
  return value ? `${timestamp.format(new Date(value))} (hora de Colombia)` : "Nunca";
}

export type SyncRun = {
  id: string;
  source_name: string;
  source_ref: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  rows_seen: number;
  rows_new: number;
  rows_changed: number;
  rows_rejected: number;
  error: string | null;
};
