"use client";

import { useActionState } from "react";
import {
  changePassword,
  createMapping,
  createUser,
  deleteMapping,
  recordReview,
  resetPassword,
  signIn,
  updateUser,
  type FormState,
} from "@/app/panel/actions";
import type { Role } from "@/lib/staff-labels";
import { ROLE_LABELS } from "@/lib/staff-labels";

const fieldClass = "w-full rounded border border-rule bg-surface px-3 py-2 text-base text-ink";
const buttonClass =
  "rounded bg-brand px-5 py-2 font-medium text-brand-ink hover:opacity-90 disabled:opacity-60";
const secondaryClass =
  "rounded border border-rule bg-surface px-4 py-2 text-brand hover:underline disabled:opacity-60";

function Feedback({ state }: { state: FormState }) {
  return (
    <div aria-live="polite" className="flex flex-col gap-2">
      {state.error ? (
        <p role="alert" className="rounded border border-warn bg-surface p-3 text-sm text-warn">
          {state.error}
        </p>
      ) : null}
      {state.message ? <p className="text-sm text-ok">{state.message}</p> : null}
      {state.issued ? (
        <div className="rounded border border-rule bg-paper p-3 text-sm">
          <p>
            Contraseña de un solo uso para <strong>{state.issued.email}</strong>:
          </p>
          <p className="mt-1 font-mono text-base break-all">{state.issued.password}</p>
          <p className="mt-1 text-ink-muted">
            Se muestra una sola vez. Entréguela por un canal seguro; la persona deberá cambiarla
            al ingresar.
          </p>
        </div>
      ) : null}
    </div>
  );
}

function Input(props: {
  name: string;
  label: string;
  type?: string;
  autoComplete?: string;
  required?: boolean;
  maxLength?: number;
  defaultValue?: string;
}) {
  const id = `campo-${props.name}`;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium">
        {props.label}
      </label>
      <input
        id={id}
        name={props.name}
        type={props.type ?? "text"}
        autoComplete={props.autoComplete}
        required={props.required ?? true}
        maxLength={props.maxLength ?? 320}
        defaultValue={props.defaultValue}
        className={fieldClass}
      />
    </div>
  );
}

export function LoginForm() {
  const [state, action, pending] = useActionState(signIn, {});
  return (
    <form action={action} className="flex max-w-md flex-col gap-4 rounded border border-rule bg-surface p-5">
      <Input name="email" label="Correo" type="email" autoComplete="username" defaultValue={state.values?.email} />
      <Input name="password" label="Contraseña" type="password" autoComplete="current-password" maxLength={128} />
      <Feedback state={state} />
      <div>
        <button type="submit" className={buttonClass} disabled={pending}>
          {pending ? "Ingresando…" : "Ingresar"}
        </button>
      </div>
    </form>
  );
}

export function PasswordForm() {
  const [state, action, pending] = useActionState(changePassword, {});
  return (
    <form action={action} className="flex max-w-md flex-col gap-4 rounded border border-rule bg-surface p-5">
      <Input name="current_password" label="Contraseña actual" type="password" autoComplete="current-password" maxLength={128} />
      <Input name="new_password" label="Nueva contraseña (al menos 12 caracteres)" type="password" autoComplete="new-password" maxLength={128} />
      <Input name="confirm_password" label="Repita la nueva contraseña" type="password" autoComplete="new-password" maxLength={128} />
      <Feedback state={state} />
      <div>
        <button type="submit" className={buttonClass} disabled={pending}>
          {pending ? "Guardando…" : "Cambiar contraseña"}
        </button>
      </div>
    </form>
  );
}

function RoleSelect({ id, defaultValue }: { id: string; defaultValue?: Role | "" }) {
  return (
    <select id={id} name="role" defaultValue={defaultValue ?? ""} required className={fieldClass}>
      {defaultValue ? null : <option value="">Elija un rol</option>}
      {(Object.keys(ROLE_LABELS) as Role[]).map((role) => (
        <option key={role} value={role}>
          {ROLE_LABELS[role]}
        </option>
      ))}
    </select>
  );
}

export function CreateUserForm() {
  const [state, action, pending] = useActionState(createUser, {});
  return (
    <form action={action} className="flex flex-col gap-4 rounded border border-rule bg-surface p-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <Input name="display_name" label="Nombre" maxLength={200} defaultValue={state.values?.display_name} />
        <Input name="email" label="Correo" type="email" defaultValue={state.values?.email} />
        <div className="flex flex-col gap-1">
          <label htmlFor="campo-rol-nuevo" className="text-sm font-medium">
            Rol
          </label>
          <RoleSelect id="campo-rol-nuevo" defaultValue={(state.values?.role as Role | undefined) ?? ""} />
        </div>
      </div>
      <Feedback state={state} />
      <div>
        <button type="submit" className={buttonClass} disabled={pending}>
          {pending ? "Creando…" : "Crear cuenta"}
        </button>
      </div>
    </form>
  );
}

export function UserControls({
  id,
  email,
  role,
  isActive,
}: {
  id: string;
  email: string;
  role: Role;
  isActive: boolean;
}) {
  const [updateState, update, updating] = useActionState(updateUser, {});
  const [toggleState, toggle, toggling] = useActionState(updateUser, {});
  const [resetState, reset, resetting] = useActionState(resetPassword, {});
  const roleId = `rol-${id}`;
  return (
    <div className="flex flex-col gap-3">
      <form action={update} className="flex flex-wrap items-end gap-3">
        <input type="hidden" name="id" value={id} />
        <div className="flex min-w-48 flex-col gap-1">
          <label htmlFor={roleId} className="text-sm font-medium">
            Rol de {email}
          </label>
          <RoleSelect id={roleId} defaultValue={role} />
        </div>
        <button type="submit" className={secondaryClass} disabled={updating}>
          Guardar rol
        </button>
      </form>
      <div className="flex flex-wrap gap-3">
        <form action={toggle}>
          <input type="hidden" name="id" value={id} />
          <input type="hidden" name="is_active" value={isActive ? "false" : "true"} />
          <button type="submit" className={secondaryClass} disabled={toggling}>
            {isActive ? `Desactivar a ${email}` : `Reactivar a ${email}`}
          </button>
        </form>
        <form action={reset}>
          <input type="hidden" name="id" value={id} />
          <button type="submit" className={secondaryClass} disabled={resetting}>
            Restablecer contraseña de {email}
          </button>
        </form>
      </div>
      <Feedback state={updateState} />
      <Feedback state={toggleState} />
      <Feedback state={resetState} />
    </div>
  );
}

export function ReviewForm({ contentType, contentKey }: { contentType: string; contentKey: string }) {
  const [state, action, pending] = useActionState(recordReview, {});
  return (
    <form action={action} className="flex flex-col gap-4 rounded border border-rule bg-surface p-5">
      <input type="hidden" name="content_type" value={contentType} />
      <input type="hidden" name="content_key" value={contentKey} />
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">Decisión</legend>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="decision"
            value="approved"
            required
            defaultChecked={state.values?.decision === "approved"}
          />{" "}
          Aprobar el contenido tal
          como se publica ahora
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="decision"
            value="changes_requested"
            required
            defaultChecked={state.values?.decision === "changes_requested"}
          />{" "}
          Pedir cambios
        </label>
      </fieldset>
      <div className="flex flex-col gap-1">
        <label htmlFor="campo-notas" className="text-sm font-medium">
          Notas para el equipo (obligatorias si pide cambios; no se publican)
        </label>
        <textarea
          id="campo-notas"
          name="notes"
          rows={5}
          maxLength={5000}
          defaultValue={state.values?.notes}
          className={fieldClass}
        />
      </div>
      <Feedback state={state} />
      <div>
        <button type="submit" className={buttonClass} disabled={pending}>
          {pending ? "Registrando…" : "Registrar revisión"}
        </button>
      </div>
    </form>
  );
}

export type InstitutionOption = { id: string; name: string; detail: string | null };

export function MappingForm({
  kind,
  sourceValue,
  options,
}: {
  kind: string;
  sourceValue: string;
  options: InstitutionOption[];
}) {
  const [state, action, pending] = useActionState(createMapping, {});
  return (
    <form action={action} className="flex flex-col gap-4 rounded border border-rule bg-surface p-5">
      <input type="hidden" name="kind" value={kind} />
      <input type="hidden" name="source_value" value={sourceValue} />
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">Entidad del directorio</legend>
        {options.map((option) => (
          <label key={option.id} className="flex items-start gap-2">
            <input
              type="radio"
              name="institution_id"
              value={option.id}
              required
              className="mt-1"
              defaultChecked={state.values?.institution_id === option.id}
            />
            <span>
              {option.name}
              {option.detail ? <span className="block text-sm text-ink-muted">{option.detail}</span> : null}
            </span>
          </label>
        ))}
      </fieldset>
      <div className="flex flex-col gap-1">
        <label htmlFor="campo-motivo" className="text-sm font-medium">
          En qué se basa el vínculo (se muestra en las páginas públicas)
        </label>
        <textarea
          id="campo-motivo"
          name="note"
          rows={3}
          minLength={10}
          maxLength={1000}
          required
          defaultValue={state.values?.note}
          className={fieldClass}
        />
      </div>
      <Feedback state={state} />
      <div>
        <button type="submit" className={buttonClass} disabled={pending}>
          {pending ? "Guardando…" : "Guardar el vínculo"}
        </button>
      </div>
    </form>
  );
}

export function DeleteMappingForm({ id, kind, label }: { id: string; kind: string; label: string }) {
  const [state, action, pending] = useActionState(deleteMapping, {});
  return (
    <form action={action} className="flex flex-col gap-2">
      <input type="hidden" name="id" value={id} />
      <input type="hidden" name="kind" value={kind} />
      <div>
        <button type="submit" className={secondaryClass} disabled={pending} aria-label={label}>
          {pending ? "Eliminando…" : "Eliminar"}
        </button>
      </div>
      <Feedback state={state} />
    </form>
  );
}
