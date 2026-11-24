import { expect, test } from "@playwright/test";

test("la búsqueda del encabezado lleva a un registro y a su origen", async ({ page }) => {
  await page.goto("/");
  const box = page.getByRole("searchbox", { name: "Buscar en NEXO Colombia" });
  await box.fill("salud mental");
  await box.press("Enter");
  await expect(page).toHaveURL(/\/buscar\?q=salud\+mental/);
  await page.getByRole("link", { name: "Salud mental (ejemplo)" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Salud mental (ejemplo)" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Origen de este registro" })).toBeVisible();
});

test("los filtros y la paginación del directorio de instituciones", async ({ page }) => {
  await page.goto("/instituciones");
  await expect(page.getByRole("status").filter({ hasText: "33 entidades" })).toBeVisible();
  await page.getByRole("link", { name: "Siguiente" }).click();
  await expect(page).toHaveURL(/pagina=2/);
  await page.goto("/instituciones");
  await page.getByLabel("Orden", { exact: true }).selectOption({ label: "NACIONAL (1)" });
  await page.getByRole("button", { name: "Buscar" }).last().click();
  await expect(page.getByRole("status").filter({ hasText: "1 entidad" })).toBeVisible();
  await expect(page.getByRole("link", { name: "MINISTERIO DE EJEMPLO Y PROTECCIÓN SOCIAL" })).toBeVisible();
});

test("un proyecto enlaza a sus autores y el autor a sus proyectos", async ({ page }) => {
  await page.goto("/legislacion?q=educacion");
  await page.getByRole("link", { name: "Educación rural (ejemplo)" }).click();
  const authors = page.getByRole("region", { name: "Autores con ficha de representante" });
  await expect(authors.getByText("Hipótesis analítica")).toBeVisible();
  await authors.getByRole("link", { name: "Autor De Prueba" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Autor De Prueba" })).toBeVisible();
  await expect(page.getByText("Fundamento de la curul", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Educación rural (ejemplo)" })).toBeVisible();
});

test("la Constitución: del índice a un artículo y a su vecino", async ({ page }) => {
  await page.goto("/constitucion");
  await page.getByRole("link", { name: /^Artículo 11\b/ }).first().click();
  await expect(page.getByRole("heading", { level: 1, name: /Artículo 11/ })).toBeVisible();
  await page.getByRole("link", { name: "Siguiente: Artículo 12" }).click();
  await expect(page.getByRole("heading", { level: 1, name: /Artículo 12\b/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Anterior: Artículo 11" })).toBeVisible();
});

test("los registros que no existen responden 404", async ({ request }) => {
  const missing = "00000000-0000-0000-0000-000000000000";
  for (const path of [
    `/instituciones/${missing}`,
    `/legislacion/${missing}`,
    `/representantes/${missing}`,
    "/presupuesto/00-00-00",
    `/contratos/${missing}`,
    "/constitucion/articulo-999",
    "/aprender/no-existe",
    "/no-existe",
  ]) {
    const response = await request.get(path);
    expect(response.status(), path).toBe(404);
  }
});

test("el enlace para saltar al contenido mueve el foco", async ({ page, isMobile }) => {
  test.skip(isMobile, "Teclado físico");
  await page.goto("/instituciones");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Saltar al contenido" });
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#contenido$/);
  await expect(page.locator("main#contenido")).toBeFocused();
});

test("el foco se ve sobre el encabezado oscuro (contraste 3:1)", async ({ page, isMobile }) => {
  test.skip(isMobile, "Teclado físico");
  await page.goto("/");
  await page.getByRole("link", { name: "Aprender" }).first().focus();
  const outline = await page.evaluate(() => getComputedStyle(document.activeElement as Element).outlineColor);
  // --focus-on-brand (#f2c14e), not --accent (#8a5a00).
  expect(outline).toBe("rgb(242, 193, 78)");
});

test("la navegación marca la sección actual", async ({ page }) => {
  await page.goto("/representantes");
  const nav = page.getByRole("navigation", { name: "Navegación principal" });
  await expect(nav.getByRole("link", { name: "Representantes" })).toHaveAttribute("aria-current", "page");
  await expect(nav.getByRole("link", { name: "Inicio" })).not.toHaveAttribute("aria-current", "page");
});

test("el presupuesto: del total a una entidad, con la nota sobre la vigencia", async ({ page }) => {
  await page.goto("/presupuesto");
  await expect(page.getByText("La fuente no indica la vigencia").first()).toBeVisible();
  await page.getByLabel("Sector", { exact: true }).selectOption({ label: "OTRO SECTOR (1)" });
  await page.getByRole("button", { name: "Buscar" }).last().click();
  await page.getByRole("link", { name: "MINISTERIO DE EJEMPLO" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "MINISTERIO DE EJEMPLO" })).toBeVisible();
  await expect(page.getByText("80,0 % de la apropiación").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Origen de este registro" })).toBeVisible();
});

test("el presupuesto y el directorio se enlazan, y el historial muestra cada actualización", async ({
  page,
}) => {
  await page.goto("/buscar?q=agencia+de+ejemplo&tipo=budget_entity");
  await page.getByRole("link", { name: "AGENCIA DE EJEMPLO" }).click();
  await expect(page).toHaveURL(/\/presupuesto\/99-01-00$/);
  const directory = page.getByRole("region", { name: "En el directorio de entidades" });
  await expect(directory.getByText("Hipótesis analítica")).toBeVisible();
  const history = page.getByRole("region", { name: "Cifras en cada actualización de la fuente" });
  await expect(history.getByRole("row")).toHaveCount(3);
  await directory.getByRole("link", { name: "Agencia de Ejemplo" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Agencia de Ejemplo" })).toBeVisible();
  await page
    .getByRole("region", { name: "Presupuesto" })
    .getByRole("link", { name: /Ejecución presupuestal de AGENCIA DE EJEMPLO/ })
    .click();
  await expect(page).toHaveURL(/\/presupuesto\/99-01-00$/);
});

test("contratos: de la lista a un contrato, a la entidad y a sus contratos", async ({ page }) => {
  await page.goto("/contratos");
  await expect(page.getByText("últimos 90 días").first()).toBeVisible();
  await page.getByLabel("Tipo de contrato").selectOption({ label: "Prestación de servicios (1)" });
  await page.getByRole("button", { name: "Buscar" }).last().click();
  await expect(page.getByRole("status").filter({ hasText: "1 contrato" })).toBeVisible();
  await page.getByRole("link", { name: /servicios profesionales de ejemplo/ }).click();
  // Natural persons are not named (A-015).
  await expect(page.getByText("Persona natural").first()).toBeVisible();
  await expect(page.getByText("PERSONA DE EJEMPLO")).toHaveCount(0);
  await expect(page.getByText(/no muestra el nombre ni el documento/)).toBeVisible();
  const entity = page.getByRole("region", { name: "En el directorio de entidades" });
  await entity.getByRole("link", { name: "Agencia de Ejemplo" }).click();
  await page
    .getByRole("region", { name: "Contratos" })
    .getByRole("link", { name: /Ver 2 contratos firmados/ })
    .click();
  await expect(page.getByRole("status").filter({ hasText: "2 contratos" })).toBeVisible();
  await expect(page.getByText("EMPRESA DE EJEMPLO S.A.S.")).toBeVisible();
});

test("el inicio muestra cada conjunto de datos con su cifra y su fuente", async ({ page }) => {
  await page.goto("/");
  for (const label of [
    "Explorar el directorio de instituciones",
    "Ver los representantes",
    "Ver el presupuesto",
    "Explorar los contratos",
  ]) {
    await expect(page.getByRole("link", { name: label })).toBeVisible();
  }
  await expect(page.getByText("entidades públicas", { exact: true })).toBeVisible();
  // The source of each figure links to the official dataset.
  const source = page.getByRole("link", { name: "Representantes período 2026-2027" });
  await expect(source).toHaveAttribute("href", /datos\.gov\.co/);
});

test("Fuentes lista cada fuente con su enlace oficial", async ({ page }) => {
  await page.goto("/fuentes");
  for (const name of ["Representantes período 2026-2027", "Proyectos de Ley"]) {
    await expect(page.getByRole("link", { name }).first()).toHaveAttribute("href", /^https:\/\//);
  }
});

test("una lección: pasos con artículos, glosario y repaso con respuesta", async ({ page }) => {
  await page.goto("/aprender");
  await page.getByRole("link", { name: "Cómo está organizado el Estado" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Cómo está organizado el Estado" })).toBeVisible();
  await expect(page.getByRole("link", { name: /^artículo \d+/ }).first()).toHaveAttribute(
    "href",
    /^\/constitucion\/articulo-/,
  );
  await expect(page.getByRole("heading", { name: "Glosario" })).toBeVisible();
  const quiz = page.getByRole("region", { name: "Repaso" });
  const firstAnswer = quiz.getByText("Ver la respuesta").first();
  await firstAnswer.click();
  await expect(quiz.locator("details[open]").first()).toContainText("Constitución, artículo");
});
