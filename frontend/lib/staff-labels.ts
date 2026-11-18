/** Labels shared by staff pages and client forms (no server code here). */

export type Role = "admin" | "data_steward" | "legal_reviewer";

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Administración",
  data_steward: "Gestión de datos",
  legal_reviewer: "Revisión jurídica",
};

export const AUDIT_ACTIONS: Record<string, string> = {
  sign_in: "Ingreso",
  sign_in_failed: "Ingreso fallido",
  sign_out: "Salida",
  password_changed: "Cambio de contraseña",
  password_reset: "Contraseña restablecida",
  user_created: "Cuenta creada",
  user_updated: "Cuenta modificada",
  sync_run: "Sincronización de datos",
  review_recorded: "Revisión jurídica registrada",
};

export const STATUS_LABELS: Record<string, string> = {
  succeeded: "Completada",
  failed: "Fallida",
  running: "En curso",
};

export const DECISION_LABELS: Record<string, string> = {
  approved: "Aprobado",
  changes_requested: "Cambios pedidos",
};
