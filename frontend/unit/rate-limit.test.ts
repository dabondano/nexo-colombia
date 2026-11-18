import assert from "node:assert/strict";
import { test } from "node:test";
import { FixedWindowLimiter, clientIp, isStaffForm } from "../lib/rate-limit.ts";

test("allows the limit, then refuses until the window ends", () => {
  const limiter = new FixedWindowLimiter(3, 60_000);
  const results = [0, 1, 2, 3].map(() => limiter.allow("203.0.113.5", 1_000));
  assert.deepEqual(results, [true, true, true, false]);
  assert.equal(limiter.allow("198.51.100.7", 1_000), true, "other addresses are counted apart");
  assert.equal(limiter.allow("203.0.113.5", 61_000), true, "a new window starts after a minute");
});

test("reads the IP only from the configured header", () => {
  const headers = new Headers({
    "true-client-ip": "203.0.113.5",
    "x-forwarded-for": "6.6.6.6, 10.0.0.1",
  });
  assert.equal(clientIp(headers, "true-client-ip"), "203.0.113.5");
  assert.equal(clientIp(headers, undefined), null, "disabled when no header is configured");
  assert.equal(clientIp(new Headers(), "true-client-ip"), null);
});

test("limits only staff form submissions", () => {
  assert.equal(isStaffForm("POST", "/ingresar"), true);
  assert.equal(isStaffForm("POST", "/panel/usuarios"), true);
  assert.equal(isStaffForm("GET", "/ingresar"), false);
  assert.equal(isStaffForm("POST", "/buscar"), false);
  assert.equal(isStaffForm("POST", "/panelista"), false);
});
