"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { LESSONS } from "@/lib/lessons";
import { lessonFingerprint } from "@/lib/review";
import { SESSION_COOKIE, sessionToken, staffRequest, type Role, type StaffUser } from "@/lib/staff";

/**
 * Server actions of the staff panel. Each one is a public endpoint in effect,
 * so none trusts the page that called it: the API checks the session and the
 * role of every request. Next.js rejects actions posted from other origins.
 */

export type FormState = {
  error?: string;
  message?: string;
  issued?: { email: string; password: string };
  // What was typed, returned with an error so the form can show it again (never passwords).
  values?: Record<string, string>;
};

const ROLES: Role[] = ["admin", "data_steward", "legal_reviewer"];

function text(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

export async function signIn(_state: FormState, formData: FormData): Promise<FormState> {
  const email = text(formData, "email").trim();
  const password = text(formData, "password");
  if (!email || !password) return { error: "Escriba su correo y su contraseña.", values: { email } };

  const result = await staffRequest<{ token: string; expires_at: string; user: StaffUser }>(
    "/auth/login",
    { method: "POST", body: { email, password }, token: "" },
  );
  if (!result.ok) return { error: result.reason, values: { email } };

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
  const values = {
    email: text(formData, "email"),
    display_name: text(formData, "display_name"),
    role,
  };
  if (!ROLES.includes(role)) return { error: "Elija un rol.", values };
  const result = await staffRequest<{ user: StaffUser; temporary_password: string }>(
    "/admin/users",
    {
      method: "POST",
      body: { email: text(formData, "email").trim(), display_name: text(formData, "display_name").trim(), role },
    },
  );
  if (!result.ok) return { error: result.reason, values };
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

export async function recordReview(_state: FormState, formData: FormData): Promise<FormState> {
  const type = text(formData, "content_type");
  const key = text(formData, "content_key");
  const decision = text(formData, "decision");
  const values = { decision, notes: text(formData, "notes") };
  if (decision !== "approved" && decision !== "changes_requested") {
    return { error: "Elija una decisión.", values };
  }
  let fingerprint: string | undefined;
  if (type === "lesson") {
    // Computed here, from the lesson as published, never taken from the form.
    const lesson = LESSONS.find((item) => item.slug === key);
    if (!lesson) return { error: "Lección no encontrada." };
    fingerprint = lessonFingerprint(lesson);
  } else if (type !== "constitution_provision") {
    return { error: "Tipo de contenido no válido." };
  }
  const result = await staffRequest("/reviews", {
    method: "POST",
    body: { content_type: type, content_key: key, fingerprint, decision, notes: values.notes },
  });
  if (!result.ok) return { error: result.reason, values };
  revalidatePath("/panel/revision", "layout");
  return { message: "Revisión registrada." };
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

const MAPPING_KINDS = ["budget_entity", "contract_entity"];

export async function createMapping(_state: FormState, formData: FormData): Promise<FormState> {
  const kind = text(formData, "kind");
  const institution = text(formData, "institution_id");
  const values = { institution_id: institution, note: text(formData, "note") };
  if (!MAPPING_KINDS.includes(kind)) return { error: "Tipo de vínculo no válido." };
  if (!institution) return { error: "Elija la entidad del directorio.", values };
  if (values.note.trim().length < 10) {
    return { error: "Escriba en qué se basa el vínculo (al menos 10 caracteres).", values };
  }
  const result = await staffRequest("/admin/entity-mappings", {
    method: "POST",
    body: {
      kind,
      source_value: text(formData, "source_value"),
      institution_id: institution,
      note: values.note,
    },
  });
  if (!result.ok) return { error: result.reason, values };
  revalidatePath("/panel/vinculos");
  redirect(`/panel/vinculos?tipo=${kind}&creado=1`);
}

export async function deleteMapping(_state: FormState, formData: FormData): Promise<FormState> {
  const id = text(formData, "id");
  const kind = text(formData, "kind");
  const result = await staffRequest(`/admin/entity-mappings/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!result.ok) return { error: result.reason };
  revalidatePath("/panel/vinculos");
  redirect(`/panel/vinculos?tipo=${MAPPING_KINDS.includes(kind) ? kind : "budget_entity"}&eliminado=1`);
}
