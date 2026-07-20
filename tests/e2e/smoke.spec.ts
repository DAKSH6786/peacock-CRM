import { expect, test } from "@playwright/test";

test.describe("smoke", () => {
  test("login page renders brand and form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Peacock One").first()).toBeVisible();
    await expect(page.getByLabel("Work email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
  });

  test("health endpoint responds with JSON", async ({ request }) => {
    const response = await request.get("/api/health");
    expect([200, 503]).toContain(response.status());
    const body = await response.json();
    expect(body.service).toBe("peacock-one");
    expect(body.checks.database).toBeTruthy();
  });
});
