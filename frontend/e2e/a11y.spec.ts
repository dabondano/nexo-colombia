import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const WCAG_22_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"];

async function expectNoViolations(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(WCAG_22_AA).analyze();
  const summary = results.violations.map(
    (v) => `${v.id} (${v.impact}): ${v.help} — ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`,
  );
  expect(summary, "Infracciones WCAG 2.2 AA").toEqual([]);
}

/** Opens the first record listed on a directory page. */
async function firstRecord(page: Page, listPath: string): Promise<string> {
  await page.goto(listPath);
  const link = page.locator("#titulo-resultados ~ ul a").first();
  const href = await link.getAttribute("href");
  expect(href).toBeTruthy();
  return href as string;
}

const STATIC_PAGES = [
  "/",
  "/buscar?q=ejemplo",
  "/buscar?q=zzzz-sin-resultados",
  "/instituciones",
  "/instituciones?q=ministerio",
  "/legislacion",
  "/representantes",
  "/constitucion",
  "/constitucion/articulo-11",
  "/aprender",
  "/aprender/estructura-del-estado",
  "/fuentes",
  "/no-existe",
];

/**
 * Failed requests and console errors on a page. Two exceptions, both expected:
 * the not-found page answers 404 by design, and lessons link to articles the
 * small sample Constitution does not contain (they exist in the real data), so
 * the prefetch of those articles answers 404 here.
 */
function trackErrors(page: Page, path: string): string[] {
  const errors: string[] = [];
  page.on("response", (response) => {
    if (response.status() < 400) return;
    const url = new URL(response.url());
    if (path === "/no-existe" && url.pathname === "/no-existe") return;
    if (path.startsWith("/aprender/") && url.pathname.startsWith("/constitucion/articulo-")) return;
    errors.push(`${response.status()} ${url.pathname}`);
  });
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource")) {
      errors.push(message.text());
    }
  });
  return errors;
}

for (const path of STATIC_PAGES) {
  test(`sin infracciones WCAG 2.2 AA: ${path}`, async ({ page }) => {
    const errors = trackErrors(page, path);
    await page.goto(path);
    await expect(page.locator("main, #contenido").first()).toBeVisible();
    await expectNoViolations(page);
    await page.waitForLoadState("networkidle");
    expect(errors, "Errores de carga o de consola").toEqual([]);
  });
}

for (const list of ["/instituciones", "/legislacion", "/representantes"]) {
  test(`sin infracciones WCAG 2.2 AA: primera ficha de ${list}`, async ({ page }) => {
    await page.goto(await firstRecord(page, list));
    await expect(page.getByRole("heading", { name: "Origen de este registro" })).toBeVisible();
    await expectNoViolations(page);
  });
}
