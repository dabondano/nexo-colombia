"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { SESSION_COOKIE, sessionToken, staffRequest, type Role, type StaffUser } from "@/lib/staff";

/**
 * Server actions of the staff panel. Each one is a public endpoint in effect,
 * so none trusts the page that called it: the API checks the session and the
 * role of every request. Next.js rejects actions posted from other origins.
 */

export type FormState = { error?: string; message?: string; issued?: { email: string; password: string } };

const ROLES: Role[] = ["admin", "data_steward", "legal_reviewer"];

function text(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

export async function signIn(_state: FormState, formData: FormData): Promise<FormState> {
  const email = text(formData, "email").trim();
  const password = text(formData, "password");
  if (!email || !password) return { error: "Escriba su correo y su contraseña." };

  const result = await staffRequest<{ token: string; expires_at: string; user: StaffUser }>(
    "/auth/login",
    { method: "POST", body: { email, password }, token: "" },
  );
  if (!result.ok) return { error: result.reason };

  (await cookies()).set(SESSION_COOKIE, result.data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    expires: new Date(result.data.expires_at),
  });
  redirect(result.data.user.must_change_password ? "/panel/contrasena" : "/panel");
}

export async function signOut(): Promise<void> {
  const token = await sessionToken();
  if (token) await staffRequest("/auth/logout", { method: "POST", token });
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/ingresar");
}

export async function changePassword(_state: FormState, formData: FormData): Promise<FormState> {
  const current = text(formData, "current_password");
  const next = text(formData, "new_password");
  if (next !== text(formData, "confirm_password")) {
    return { error: "La nueva contraseña y su confirmación no coinciden." };
  }
  const result = await staffRequest("/auth/password", {
    method: "POST",
    body: { current_password: current, new_password: next },
  });
  if (!result.ok) return { error: result.reason };
  redirect("/panel");
}

export async function createUser(_state: FormState, formData: FormData): Promise<FormState> {
  const role = text(formData, "role") as Role;
  if (!ROLES.includes(role)) return { error: "Elija un rol." };
  const result = await staffRequest<{ user: StaffUser; temporary_password: string }>(
    "/admin/users",
    {
      method: "POST",
      body: { email: text(formData, "email").trim(), display_name: text(formData, "display_name").trim(), role },
    },
  );
  if (!result.ok) return { error: result.reason };
  revalidatePath("/panel/usuarios");
  return {
    message: "Cuenta creada.",
    issued: { email: result.data.user.email, password: result.data.temporary_password },
  };
}

export async function updateUser(_state: FormState, formData: FormData): Promise<FormState> {
  const id = text(formData, "id");
  const role = text(formData, "role") as Role;
  const active = text(formData, "is_active");
  const body: { role?: Role; is_active?: boolean } = {};
  if (ROLES.includes(role)) body.role = role;
  if (active === "true" || active === "false") body.is_active = active === "true";
  const result = await staffRequest(`/admin/users/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body,
  });
  if (!result.ok) return { error: result.reason };
  revalidatePath("/panel/usuarios");
  return { message: "Cambios guardados." };
}

export async function resetPassword(_state: FormState, formData: FormData): Promise<FormState> {
  const id = text(formData, "id");
  const result = await staffRequest<{ user: StaffUser; temporary_password: string }>(
    `/admin/users/${encodeURIComponent(id)}/reset-password`,
    { method: "POST" },
  );
  if (!result.ok) return { error: result.reason };
  revalidatePath("/panel/usuarios");
  return {
    message: "Contraseña restablecida.",
    issued: { email: result.data.user.email, password: result.data.temporary_password },
  };
}
