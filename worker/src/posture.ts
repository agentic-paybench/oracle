/**
 * ADR-009 canEmit: the fail-closed Policy Decision Point, TypeScript side.
 *
 * The oracle OWNS the PDP in Python (`pdp/pdp.py`, `pdp/mechanics.py`,
 * `pdp/config.py`, `pdp/gates.py`) and the shared config at repo-root
 * `config/regulatory_posture.{live,testnet}.json`. This module MIRRORS that
 * contract for the one mechanic the right-of-reply surface gates on
 * (`published-rankings`, required gate `G_S21`); it does NOT fork the PDP
 * and never edits the Python side. The config JSON is the shared contract.
 *
 * A Worker has no runtime filesystem, so both configs are bundled at build time
 * and selected by the `POSTURE_CONFIG` var. A gate flip is a config-value change
 * plus a redeploy, exactly as ADR-009 requires; it is never a code change.
 *
 * Fail-closed, everywhere: unknown mechanic, unknown/missing gate, unknown
 * `POSTURE_CONFIG`, or a malformed config all deny. Default deny.
 *
 * The gates NEVER share: `G_S21` (financial promotion, the named-rail table) is
 * the ONLY gate this module consults. The scored query's gates (`G_AUTH`/`G_QF`)
 * are deliberately not read here; clearing one never opens the other (ADR-009).
 */

// The shared config is the single source of truth. These relative imports reach
// oracle/config/ (consume, do not copy). Bundled at build time by wrangler/esbuild.
import liveConfigRaw from "../../config/regulatory_posture.live.json";
import testnetConfigRaw from "../../config/regulatory_posture.testnet.json";

/** The four regulatory gates keyed in the regulatory_posture config (ADR-009). */
export const GATE_KEYS = ["G_AUTH", "G_QF", "G_S21", "G_CUSTODY"] as const;
export type GateKey = (typeof GATE_KEYS)[number];

const OPEN = "open";
const CLOSED = "closed";

/** Known posture enum names (mirrors pdp.posture.Posture). An unknown name fails closed. */
const KNOWN_POSTURES = new Set([
  "OFFLINE_TESTNET_ONLY",
  "FIRST_PARTY_DEMO",
  "LIVE_AUTHORISED",
]);

export interface PostureConfig {
  config_id: string;
  regulatory_posture: string;
  gates: Record<string, string>;
  audit?: unknown;
}

export interface Decision {
  mechanic: string;
  allowed: boolean;
  rationale: string;
}

/**
 * A gate is open only if explicitly "open"; unknown/missing = closed.
 * Mirrors pdp.gates.is_open exactly.
 */
export function gateOpen(gates: Record<string, string> | undefined, key: string): boolean {
  return !!gates && gates[key] === OPEN;
}

/**
 * The right-of-reply mechanic registry. Scoped to what this surface gates on.
 * `requiredGate: null` would mean "no gate" (parity with pdp's ungated mechanics);
 * RoR only ever gates published-rankings, whose required gate is G_S21.
 */
export interface Mechanic {
  id: string;
  requiredGate: GateKey | null;
}

export const MECHANICS: Record<string, Mechanic> = {
  "published-rankings": {
    id: "published-rankings",
    requiredGate: "G_S21",
  },
};

/**
 * Validate a raw imported config, fail-closed. Mirrors pdp.config.load_config:
 * a missing/unknown posture, a missing gates map, or any gate value that is not
 * exactly "open"/"closed" yields null (deny), never a permissive default.
 */
export function validateConfig(raw: unknown): PostureConfig | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  if (typeof r.regulatory_posture !== "string" || !KNOWN_POSTURES.has(r.regulatory_posture)) {
    return null;
  }
  const gates = r.gates;
  if (!gates || typeof gates !== "object") return null;
  for (const value of Object.values(gates as Record<string, unknown>)) {
    if (value !== OPEN && value !== CLOSED) return null; // malformed -> fail-closed
  }
  return {
    config_id: typeof r.config_id === "string" ? r.config_id : "unknown",
    regulatory_posture: r.regulatory_posture,
    gates: gates as Record<string, string>,
    audit: r.audit,
  };
}

/** The two bundled posture configs, keyed by their POSTURE_CONFIG discriminator. */
const CONFIGS: Record<string, unknown> = {
  live: liveConfigRaw,
  testnet: testnetConfigRaw,
};

/**
 * Select and validate the posture config named by POSTURE_CONFIG.
 * Default is "live" (most restrictive). An unknown name fails closed (null).
 */
export function selectConfig(name?: string): PostureConfig | null {
  const key = name && name.length > 0 ? name : "live";
  const raw = CONFIGS[key];
  if (raw === undefined) return null; // unknown POSTURE_CONFIG -> fail-closed
  return validateConfig(raw);
}

/**
 * The decision point. A mechanic emits iff it is known AND (its required gate is
 * open under a valid config). Default deny. Faithful to pdp.pdp.can_emit for the
 * gate-predicate path; RoR's one mechanic (published-rankings) carries no ADR invariants and
 * is not posture-governed, so no EmitContext is needed.
 */
export function canEmit(mechanicId: string, config: PostureConfig | null): Decision {
  const mech = MECHANICS[mechanicId];
  if (!mech) {
    return { mechanic: mechanicId, allowed: false, rationale: "unknown mechanic -> deny (fail-closed)" };
  }
  if (!config) {
    return {
      mechanic: mechanicId,
      allowed: false,
      rationale: "missing or malformed posture config -> deny (fail-closed)",
    };
  }
  if (mech.requiredGate === null) {
    return { mechanic: mechanicId, allowed: true, rationale: `no gate; cleared under '${config.config_id}'` };
  }
  if (!gateOpen(config.gates, mech.requiredGate)) {
    return {
      mechanic: mechanicId,
      allowed: false,
      rationale: `required gate ${mech.requiredGate} closed under config '${config.config_id}'`,
    };
  }
  return {
    mechanic: mechanicId,
    allowed: true,
    rationale: `${mech.requiredGate} open; cleared under config '${config.config_id}'`,
  };
}

/** Convenience for the Worker: decide against the config named by POSTURE_CONFIG. */
export function canEmitFromEnv(mechanicId: string, postureConfigName?: string): Decision {
  return canEmit(mechanicId, selectConfig(postureConfigName));
}
