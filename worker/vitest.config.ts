import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    // The handlers are written to be runtime-agnostic (pure functions + a small
    // PendingStore seam), so the suite runs under plain node with an in-memory
    // fake store; no Miniflare needed. The thin R2 binding glue is exercised by
    // `wrangler dev` in the dry-run.
    environment: "node",
    testTimeout: 20_000,
  },
});
