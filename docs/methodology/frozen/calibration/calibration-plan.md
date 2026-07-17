# PayBench calibration sourcing plan

**Status: STARTED 2026-06-04** (Friday-1 "calibration sourcing started" deliverable). Companion to `paybench/methodology/methodology.md` §6–§7.

## What we calibrate

Per-rail **settlement-finality distributions** for the **5 settling rails** that race on the Day-0 finality benchmark (AP2/R6 is on the Day-30 authorization-latency dimension per methodology §8 Resolution B, so it is out of scope here):

- **R1** x402-Base
- **R2** x402-Stellar
- **R9** x402-Solana
- **R10** MPP-on-Tempo (Stripe PSP)
- **R11** MPP-on-Lightning (Lightspark)

A "calibrated fixture" needs a *distribution*, not a point estimate. The Day-0 metrics — BT MLE on pairwise finality races, pass@k = P(finality ≤ k s), Wilson LB CIs — all sample finality times, so each rail needs a central tendency **and** a characterised spread/tail.

**Motivating evidence (why point estimates fail).** The R1 Friday-1 reference run logged **6.781s** (two-org) vs **2.521s** (single-org) — ~2.7× spread across just two trials. Calibration must capture that variance, not average it away.

## Sources (per methodology §7)

Three source types, combined per rail:

1. **First-party testnet/devnet observations** — our own POC adapter runs (most defensible; reproducible). Today: R1 (Base Sepolia), R9 (Solana devnet), R3 Lightning regtest (informs R11).
2. **Rail documentation** — published finality semantics (block times, confirmation depth, ledger close, HTLC resolution).
3. **Public telemetry** — e.g. x402scan for x402 rails; explorers for block-time distributions.

## Per-rail status

Documentary sweep done 2026-06-04; **first-party n=30 now complete for all 5 settling rails (2026-06-04/05)** — empirical log-normal parameters replace the doc seeds (provenance files alongside).

| Rail | Finality model | Median (s) | sigma_log (tail) | Confidence | First-party next |
|---|---|---|---|---|---|
| R1 x402-Base | probabilistic, soft@block | **2.05** | 0.082 | high | **first-party n=30 done 2026-06-04** |
| R2 x402-Stellar | deterministic @ ledger close | **2.74** | 0.116 | high (manual)² | **first-party n=30 done 2026-06-04 (manual path)** |
| R9 x402-Solana | probabilistic, 32-slot **finalized** | **14.63** | 0.057 (devnet)¹ | high (central) | **first-party n=30 done 2026-06-04** |
| R10 MPP-on-Tempo | deterministic BFT (Simplex) | **1.75** | 0.177 | high (real-rail)³ | **first-party n=30 done 2026-06-04** |
| R11 MPP-on-Lightning | Spark FROST+SSP ceremony (HTLC sub-second) | **16.52** | 0.156 | high (real-rail, Spark-path)⁴ | **first-party n=30 done 2026-06-05** |

Three load-bearing cautions from the *original documentary* sweep, now mostly resolved by first-party runs: (1) **Solana `finalized` ≠ `confirmed`** — the ~1–2s figure is confirmed/optimistic; true finality is ~13s (~10× difference, the most likely source of a wrong fixture). Methodology §3 already commits to `finalized` — correct. (2) **R10 Tempo was flagged genuinely thin** (no measured variance) — now resolved by the real-rail n=30. (3) **Stellar + Lightning tails** are real but under-quantified — Stellar resolved by first-party; R11 Lightning resolved below. The x402 facilitator envelope (~0.5–0.7s, near-constant) is folded into R1/R2/R9 medians. **The single biggest fixture correction came from R11** (see ⁴): the doc-proxy assumed sub-second "Lightning = instant" (0.8s); the real MPP-on-Lightning-via-Spark path measured **16.5s** — a ~20× miss — because the Spark operator ceremony, not the Lightning HTLC, sets finality.

¹ **R9 first-party update (2026-06-04).** n=30 devnet run (0 failures) gave empirical finalized median **14.63s** (confirming the 13.5s doc estimate) with σ_log 0.057 — but that σ is from *quiet devnet* and understates mainnet congestion (one devnet excursion already hit 19.46s; docs say 10–20s+). Central tendency is now high-confidence empirical; **the published-fixture σ should be widened toward ~0.15–0.25 (doc-informed)** until a mainnet/congested run is captured. The same run captured confirmed-level latency (median 2.27s) for free — that feeds the future Day-30 authorization-latency dimension. Samples committed at `samples/R9-x402-solana.samples.jsonl`.

**R1 first-party update (2026-06-04).** n=30 Base Sepolia run (0 failures) gave empirical median **2.05s**, σ_log **0.082** — the doc seed (3.0 / 0.45) **over-estimated both** the median and the spread. Base soft finality is genuinely ~2s and tight (stable 2s blocks, ~0 reorg), so R1 carries less tail-risk than R9. Measures soft finality (request→200, incl. facilitator settle), not hard L1 (~20min, excluded). Samples committed at `samples/R1-x402-base.samples.jsonl`.

² **R2 first-party update (2026-06-04).** n=30 (0 failures) on the **manual direct-payment path** (classic USDC payment via Horizon `submitTransaction`, resolves at ledger close) gave median **2.74s**, σ_log 0.116 — well below the 6.0s doc seed (which over-assumed a full ledger close + facilitator; real submit→inclusion averages ~half a ledger interval). This is a **lower bound** on the spec x402-on-Stellar number: the OZ-facilitator path adds a verify+settle round-trip. The spec adapter is wired (`server.ts` + `createAuthHeaders`) and pending the free OZ testnet key — re-measure on the spec path once keyed and raise the median accordingly. Samples at `samples/R2-x402-stellar.samples.jsonl`. **Update:** OZ key obtained 2026-06-04; spec path **validated end-to-end** (tx `7cd8a08…` on stellar.expert) — optional spec n=30 re-measure deferred.

³ **R10 first-party update (2026-06-04).** n=30 **real-rail** on Moderato testnet (mppx, pure-Tempo, pathUSD TIP-20) gave median **1.75s**, σ_log 0.177 — request→200 (full MPP flow); underlying Tempo settlement is ~500ms. **Supersedes the doc-proxy 1.0s LOW estimate *and* the "Partial / mock per Variant E" status:** MPP-on-Tempo is real-rail-buildable today (no Stripe, no API key, non-custodial). Only the Stripe-mediated *acceptance* leg stays Variant-E (US-only, testnet-simulated). The earlier "Tempo is genuinely thin / no measured variance" caution is now resolved. Samples at `samples/R10-mpp-tempo.samples.jsonl`.

⁴ **R11 first-party update (2026-06-05).** n=30 **real-rail** MPP-on-Lightning via the `@buildonspark/lightning-mpp-sdk` (extends mppx; Spark hosted regtest, 0 failures) gave median **16.52s**, σ_log 0.156 — request→200 for the full L402-family flow (402 + BOLT11 + Lightning pay + preimage + 200). **Supersedes the doc-proxy 0.8s / σ 0.80 estimate *and* the "access pending / mock per Variant E" status — a ~20× correction, the largest in the calibration set.** CRITICAL ATTRIBUTION: this is the MPP-on-Lightning-**via-Spark** number, **not** raw Lightning HTLC speed (which is sub-second). Each payment is a multi-round-trip to Spark's hosted operators — FROST threshold-signing + SSP preimage swap — and that ceremony dominates, landing R11 in the same finality band as R9 Solana-`finalized` (14.63s). A raw-LND L402 path (cf. R3 Polar regtest) would settle the Lightning leg far faster; R11 benchmarks the Spark production path specifically. Measured on Spark's *hosted regtest*; σ_log 0.156 is quiet-regtest and likely understates mainnet (widen toward doc-informed spread until a mainnet run is captured, same caution as R9). The doc-proxy file even mis-labelled MPP as "Lightning Multi-Path Payments" — corrected: MPP = Machine Payments Protocol, same envelope as R10. Samples at `samples/R11-mpp-lightning.samples.jsonl`.

## Distribution approach (RECOMMENDED — to confirm)

- **Default family: log-normal** — finality times are positive, right-skewed, bounded below by the rail mechanism; log-normal fits that shape and is parameter-light (μ, σ).
- **Empirical / bootstrap** where first-party samples are rich enough (target n ≥ 30 per rail).
- **Parametric from docs + telemetry** where first-party samples are thin: doc-derived central estimate sets the location; public telemetry / block-time variance sets the spread.
- Each fixture **records which approach + parameters it used** in its provenance file. No rail silently uses a different method without it being on the record.

## Provenance schema

One provenance file per fixture (`provenance/<rail>-finality.provenance.yaml`), recording: rail, dimension, distribution family + parameters, every source (type / ref / date / sample size), calibration date, confidence, and the content hash of the generated fixture. Template at `provenance/_TEMPLATE.provenance.yaml`. Seed example at `provenance/R1-x402-base-finality.provenance.yaml`.

## Reproducibility

Seeded RNG drives all sampling; fixtures are content-addressed (hash recorded in provenance). Same seed + same fixtures → bit-for-bit reproducible run (methodology §5.4 fix-list item 6, §6).

## Sourcing method — DECIDED: Hybrid (C), 2026-06-04

First-party measurement where adapters run; rail docs + public telemetry for spread/tail. Documentary track done (table above). First-party track: **ALL 5 settling rails done (n=30 each, 0 failures, 2026-06-04/05)** — empirical distributions now replace the doc-derived medians (harnesses: `poc/rail-x402-base/measure_finality.py`, `poc/rail-solana-x402/src/measure-finality.ts`, `poc/rail-stellar-x402/src/measure-finality-manual.ts`, `poc/rail-tempo-mpp/src/measure-finality.ts`, `poc/rail-lightning-mpp/src/measure-finality.ts`). R2 = manual path (spec x402-on-Stellar validated end-to-end with the OZ key; spec re-measure deferred). **R10 = real-rail MPP-on-Tempo** (mppx, Moderato testnet). **R11 = real-rail MPP-on-Lightning** (`@buildonspark/lightning-mpp-sdk`, Spark hosted regtest) — supersedes its doc-proxy/"access pending" + "mock per Variant E" status; the Spark FROST+SSP ceremony (not the Lightning HTLC) sets the ~16.5s finality (see ⁴). **Calibration first-party track is complete; next is fixture generation + content-addressing.**
