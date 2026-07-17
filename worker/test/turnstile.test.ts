import { describe, expect, it } from "vitest";
import { makeTurnstileVerifier } from "../src/capture.js";

describe("Turnstile verifier posture semantics", () => {
  it("live posture with NO secret fails closed (never bypasses)", async () => {
    const verify = makeTurnstileVerifier(undefined, "live");
    expect(await verify("any-token", null)).toBe(false);
    expect(await verify("", null)).toBe(false);
  });

  it("testnet posture with no secret does not enforce Turnstile (accepts any non-empty token)", async () => {
    const verify = makeTurnstileVerifier(undefined, "testnet");
    expect(await verify("real-widget-token-from-test-sitekey", null)).toBe(true);
    expect(await verify("", null)).toBe(false); // still requires a token to be present
  });
});
