import { describe, expect, it } from "vitest";
import {
  canEmit,
  canEmitFromEnv,
  gateOpen,
  selectConfig,
  validateConfig,
  type PostureConfig,
} from "../src/posture.js";

const PUBLISHED_RANKINGS = "published-rankings";

/** Build a throwaway config with the given gate map (never committed as a real config). */
function cfg(gates: Record<string, string>, id = "test"): PostureConfig {
  return { config_id: id, regulatory_posture: "FIRST_PARTY_DEMO", gates };
}

describe("ADR-009 canEmit(G_S21) mirror", () => {
  it("denies published-rankings when G_S21 is closed", () => {
    const d = canEmit(PUBLISHED_RANKINGS, cfg({ G_S21: "closed", G_AUTH: "closed" }));
    expect(d.allowed).toBe(false);
    expect(d.rationale).toContain("G_S21");
  });

  it("allows published-rankings when G_S21 is open", () => {
    const d = canEmit(PUBLISHED_RANKINGS, cfg({ G_S21: "open" }));
    expect(d.allowed).toBe(true);
  });

  it("decouples G_S21 from the authorisation-path gates: opening G_AUTH/G_QF does NOT open published-rankings", () => {
    // The scored query's gates must never unlock the named-rail table.
    const d = canEmit(PUBLISHED_RANKINGS, cfg({ G_S21: "closed", G_AUTH: "open", G_QF: "open" }));
    expect(d.allowed).toBe(false);
  });

  it("fails closed on an unknown mechanic", () => {
    expect(canEmit("no-such-mechanic", cfg({ G_S21: "open" })).allowed).toBe(false);
  });

  it("fails closed on a null (missing/malformed) config", () => {
    expect(canEmit(PUBLISHED_RANKINGS, null).allowed).toBe(false);
  });

  it("treats a missing G_S21 key as closed (fail-closed)", () => {
    expect(canEmit(PUBLISHED_RANKINGS, cfg({ G_AUTH: "open" })).allowed).toBe(false);
  });
});

describe("config validation is fail-closed (mirrors pdp.config.load_config)", () => {
  it("rejects a config with an unknown regulatory_posture", () => {
    expect(validateConfig({ regulatory_posture: "WIDE_OPEN", gates: { G_S21: "open" } })).toBeNull();
  });

  it("rejects a config with a non-open/closed gate value", () => {
    expect(
      validateConfig({ regulatory_posture: "FIRST_PARTY_DEMO", gates: { G_S21: "maybe" } }),
    ).toBeNull();
  });

  it("rejects a config missing the gates map", () => {
    expect(validateConfig({ regulatory_posture: "FIRST_PARTY_DEMO" })).toBeNull();
  });

  it("rejects non-object input", () => {
    expect(validateConfig(null)).toBeNull();
    expect(validateConfig("nope")).toBeNull();
  });
});

describe("gateOpen mirrors pdp.gates.is_open", () => {
  it("is open only for an explicit 'open'", () => {
    expect(gateOpen({ G_S21: "open" }, "G_S21")).toBe(true);
    expect(gateOpen({ G_S21: "closed" }, "G_S21")).toBe(false);
    expect(gateOpen({}, "G_S21")).toBe(false);
    expect(gateOpen(undefined, "G_S21")).toBe(false);
  });
});

describe("the bundled shared configs (the real contract) keep published-rankings closed at Day-0", () => {
  it("selects 'live' by default and denies published-rankings (G_S21 closed)", () => {
    const live = selectConfig("live");
    expect(live).not.toBeNull();
    expect(live!.config_id).toBe("live");
    expect(canEmitFromEnv(PUBLISHED_RANKINGS, undefined).allowed).toBe(false); // default POSTURE_CONFIG
    expect(canEmitFromEnv(PUBLISHED_RANKINGS, "live").allowed).toBe(false);
  });

  it("also keeps published-rankings closed under the testnet config (G_S21 closed there too)", () => {
    const testnet = selectConfig("testnet");
    expect(testnet).not.toBeNull();
    expect(testnet!.config_id).toBe("testnet");
    expect(canEmitFromEnv(PUBLISHED_RANKINGS, "testnet").allowed).toBe(false);
  });

  it("fails closed for an unknown POSTURE_CONFIG name", () => {
    expect(selectConfig("staging")).toBeNull();
    expect(canEmitFromEnv(PUBLISHED_RANKINGS, "staging").allowed).toBe(false);
  });
});
