import { describe, expect, it } from "vitest";

import { getApiBaseUrl } from "@/lib/api";

describe("web architecture helpers", () => {
  it("defaults API base URL to the same-origin /backend rewrite", () => {
    expect(getApiBaseUrl()).toBe("/backend");
  });
});
