import { describe, expect, it } from "vitest";

import { getApiBaseUrl } from "@/lib/api";

describe("web architecture helpers", () => {
  it("defaults API base URL for local development", () => {
    expect(getApiBaseUrl()).toContain("http");
  });
});
