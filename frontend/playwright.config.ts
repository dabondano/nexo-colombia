import { defineConfig, devices } from "@playwright/test";

/**
 * Interface and accessibility tests. They expect the web app at E2E_BASE_URL
 * (default http://localhost:3000), backed by an API loaded with the sample
 * data of `python -m tests.seed_ui` (backend). See e2e/README.md.
 */
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    locale: "es-CO",
    trace: "retain-on-failure",
    launchOptions: executablePath ? { executablePath } : {},
  },
  projects: [
    { name: "escritorio", use: { ...devices["Desktop Chrome"] } },
    { name: "telefono", use: { ...devices["Pixel 7"] } },
  ],
});
