import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Sample accounts created by `python -m tests.seed_ui` (backend); never real ones.
const PASSWORD = "clave-de-ejemplo-para-pruebas";
const ADMIN = "admin@nexo.example";
const STEWARD = "datos@nexo.example";
const REVIEWER = "revision@nexo.example";

const WCAG_22_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"];

async function signIn(page: Page, email: string, password = PASSWORD) {
  await page.goto("/ingresar");
  await page.getByLabel("Correo").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Ingresar" }).click();
}

async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(WCAG_22_AA).analyze();
  expect(results.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
}

test.describe.configure({ mode: "serial" });

test("el panel exige ingresar y no revela si la cuenta existe", async ({ page }) => {
  await page.goto("/panel/usuarios");
  await expect(page).toHaveURL(/\/ingresar$/);
  await expectAccessible(page);
  await signIn(page, "nadie@nexo.example", "una-clave-cualquiera");
  await expect(page.getByRole("alert").filter({ hasText: "Correo" })).toHaveText(
    "Correo o contraseña incorrectos, o la cuenta no está disponible.",
  );
  const cookies = await page.context().cookies();
  expect(cookies.find((c) => c.name === "nexo_sesion")).toBeUndefined();
});

test("administración: crear una cuenta que luego debe cambiar su contraseña", async ({
  page,
  browser,
}) => {
  await signIn(page, ADMIN);
  await expect(page).toHaveURL(/\/panel$/);
  const cookie = (await page.context().cookies()).find((c) => c.name === "nexo_sesion");
  expect(cookie?.httpOnly).toBe(true);
  expect(cookie?.sameSite).toBe("Strict");
  await expectAccessible(page);

  await page.getByRole("link", { name: "Cuentas", exact: true }).first().click();
  await expect(page.getByRole("heading", { level: 1, name: "Cuentas del equipo" })).toBeVisible();
  await expectAccessible(page);
  const email = `nueva-${Date.now()}@nexo.example`;
  const form = page.getByRole("region", { name: "Nueva cuenta" });
  await form.getByLabel("Nombre").fill("Persona nueva de ejemplo");
  await form.getByLabel("Correo").fill(email);
  await form.getByLabel("Rol").selectOption({ label: "Gestión de datos" });
  await form.getByRole("button", { name: "Crear cuenta" }).click();
  const issued = form.locator("p.font-mono");
  await expect(issued).toBeVisible();
  const temporary = (await issued.textContent())!.trim();

  // The new person signs in on another browser and must choose a password first.
  const other = await browser.newContext();
  const newPage = await other.newPage();
  await signIn(newPage, email, temporary);
  await expect(newPage).toHaveURL(/\/panel\/contrasena$/);
  await newPage.goto("/panel/sincronizaciones");
  await expect(newPage).toHaveURL(/\/panel\/contrasena$/);
  await expectAccessible(newPage);
  await newPage.getByLabel("Contraseña actual").fill(temporary);
  await newPage.getByLabel("Nueva contraseña (al menos 12 caracteres)").fill("frase propia de prueba");
  await newPage.getByLabel("Repita la nueva contraseña").fill("frase propia de prueba");
  await newPage.getByRole("button", { name: "Cambiar contraseña" }).click();
  await expect(newPage).toHaveURL(/\/panel$/);
  await expect(newPage.getByRole("link", { name: "Sincronizaciones" }).first()).toBeVisible();
  await expect(newPage.getByRole("link", { name: "Cuentas", exact: true })).toHaveCount(0);
  await other.close();

  await page.getByRole("link", { name: "Registro de auditoría" }).first().click();
  const log = page.getByRole("listitem");
  await expect(log.filter({ hasText: "Cuenta creada" }).filter({ hasText: email })).toBeVisible();
  await expect(log.filter({ hasText: "Ingreso fallido" }).first()).toBeVisible();
  await expectAccessible(page);
});

test("gestión de datos: sincronizaciones y filas rechazadas, sin acceso a cuentas", async ({
  page,
}) => {
  await signIn(page, STEWARD);
  await page.getByRole("link", { name: "Sincronizaciones" }).first().click();
  const table = page.getByRole("table", { name: "Sincronizaciones de datos" });
  await expect(table.getByRole("rowheader", { name: "Proyectos de Ley" }).first()).toBeVisible();
  await expectAccessible(page);
  await table.getByRole("link", { name: /filas rechazadas de Proyectos de Ley/ }).first().click();
  await expect(page.getByText("Fila de relleno del sistema de origen").first()).toBeVisible();
  await expectAccessible(page);
  await page.getByRole("link", { name: "Calidad de los datos" }).first().click();
  await expect(page.getByRole("heading", { name: "SECOP II - Contratos Electrónicos" })).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("Ninguna fuente tiene avisos.");
  await expectAccessible(page);
  await page.goto("/panel/usuarios");
  await expect(page.getByText("Su rol no permite ver esta sección.")).toBeVisible();
});

test("revisión jurídica: sin acceso a sincronizaciones; cerrar sesión", async ({ page }) => {
  await signIn(page, REVIEWER);
  await expect(page.getByRole("heading", { name: "Revisión jurídica" })).toBeVisible();
  await page.goto("/panel/sincronizaciones");
  await expect(page.getByText("Su rol no permite ver esta sección.")).toBeVisible();
  await page.goto("/panel/calidad");
  await expect(page.getByText("Su rol no permite ver esta sección.")).toBeVisible();
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/ingresar$/);
  await page.goto("/panel");
  await expect(page).toHaveURL(/\/ingresar$/);
});

test("revisión jurídica: aprobar una lección y pedir cambios en un artículo", async ({ page }) => {
  await signIn(page, REVIEWER);
  await page.getByRole("link", { name: "Revisión jurídica" }).first().click();
  await expect(page.getByRole("heading", { level: 1, name: "Revisión jurídica" })).toBeVisible();
  await expectAccessible(page);

  await page.getByRole("link", { name: "Cómo está organizado el Estado" }).click();
  await expect(page.getByRole("heading", { level: 1, name: /^Lección:/ })).toBeVisible();
  await expectAccessible(page);
  await page.getByLabel("Aprobar el contenido tal como se publica ahora").check();
  await page.getByRole("button", { name: "Registrar revisión" }).click();
  await expect(page.getByText("Revisión registrada.")).toBeVisible();
  await expect(page.getByText("Corresponde al contenido actual").first()).toBeVisible();

  await page.goto("/aprender/estructura-del-estado");
  await expect(page.getByRole("note").filter({ hasText: "Estado del contenido" })).toContainText(
    "Revisado por el equipo de revisión jurídica de NEXO",
  );

  await page.goto("/panel/revision/articulo/articulo-11");
  await page.getByLabel("Pedir cambios").check();
  await page.getByRole("button", { name: "Registrar revisión" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "notas" })).toBeVisible();
  const note = `Nota interna de prueba ${Date.now()}`;
  await page.getByLabel(/Notas para el equipo/).fill(note);
  await page.getByRole("button", { name: "Registrar revisión" }).click();
  await expect(page.getByText(note)).toBeVisible();

  await page.goto("/constitucion/articulo-11");
  await expect(page.getByRole("heading", { level: 1, name: /Artículo 11/ })).toBeVisible();
  await expect(page.getByText(note)).toHaveCount(0);
  await expect(page.getByText("Revisión jurídica:")).toHaveCount(0);
});
