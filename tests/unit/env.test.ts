import { afterEach, describe, expect, it } from "vitest";

import { tryGetServerEnv } from "@/lib/env";

const ORIGINAL = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL };
});

describe("env validation", () => {
  it("accepts a valid configuration", () => {
    process.env.DATABASE_URL =
      "postgresql://peacock:peacock@localhost:5432/peacock_one";
    process.env.AUTH_SECRET = "a".repeat(32);
    process.env.APP_URL = "http://localhost:3000";

    const env = tryGetServerEnv();
    expect(env).not.toBeNull();
    expect(env?.DATABASE_URL).toContain("postgresql://");
  });

  it("rejects a short AUTH_SECRET", () => {
    process.env.DATABASE_URL =
      "postgresql://peacock:peacock@localhost:5432/peacock_one";
    process.env.AUTH_SECRET = "too-short";
    process.env.APP_URL = "http://localhost:3000";

    expect(tryGetServerEnv()).toBeNull();
  });
});
