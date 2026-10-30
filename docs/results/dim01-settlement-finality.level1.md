posture-class: level1-measurement

# Settlement finality (DIM-01) on test networks: named-rail findings

Version 1.0, for the confirmatory run of 2026-10-27 to 2026-10-28. This artefact is frozen per dated run: a correction or a re-measurement is published as a new dated version and this one is kept. It is served on the oracle site only while the ADR-009 display gate `G_S21` is open, and its publication carries an audit record.

## What this page is

This page reports settlement finality (the PayBench dimension DIM-01) for five named payment rails on test networks: the time from a paying client's initial request to the client's own evidence that the payment was final at that rail's own reliance level. Everyday AI Ltd made every payment measured, with its own test funds, and was itself both the payer and the payee of every one.

These figures are a measurement, not a recommendation: no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use.

Rails are listed alphabetically by rail name. That ordering is fixed and carries no performance meaning.

The same measurement protocol was applied identically to every rail.

No ranking is stated on this page, no winner is named, and there is no route from this page to transact on any rail.

## Provenance

The method and its analysis plan were frozen and externally anchored after declared exploratory runs and before the confirmatory run, and before publication of any result. The design was revised across several rounds of review with the exploratory data in view, as the pre-registration's revision history records; no exploratory data enters any figure on this page. The figures below are the output of the frozen analysis tool for the confirmatory run, rounded and nothing else.

The data pre-registration is the signed git tag `paybench-dim1-testnet-prereg-v1` in the public payhelm repository (https://github.com/agentic-paybench/payhelm/blob/paybench-dim1-testnet-prereg-v1/paybench/methodology/dim1-testnet-PRE-REGISTRATION.md), registered on the Open Science Framework with digital object identifier 10.17605/OSF.IO/UETFW, its manifest anchored by an OpenTimestamps proof in Bitcoin blocks 971501 and 971504 and by Rekor transparency-log entry 3259214273. It builds on the settlement-finality methodology frozen at version 1.2 (OSF digital object identifier 10.17605/OSF.IO/XGFUJ; signed tag `paybench-prereg-v1.2`) and changes nothing in it.

Addendum 1 to the pre-registration, dated 2026-10-29 and written after the confirmatory run and before publication of any result, corrects one fact. The pre-registration describes the T1 vantage as in England, United Kingdom, and both vantages as in Europe; the T1 host's network path originates in South Africa, and the description was wrong when the document was frozen. No host, configuration or procedure changed between the freeze and the run, and the measurement protocol, the analysis plan and every anchored file are unchanged: one vantage measured from Africa and one from Europe. The addendum is at https://github.com/agentic-paybench/payhelm/blob/paybench/dim1-testnet-frozen/paybench/methodology/dim1-testnet-PRE-REGISTRATION-ADDENDUM-1.md, and the OSF registration carries a versioned update of 2026-10-29 giving the same correction.

## Scope of the measurement

Every payment was made on a test network with tokens that carry no monetary value. No funds moved on any production network, and no other party's payments were observed. The figures describe five pinned test deployments and service paths, not the rails in production, and they say nothing about any production network's finality.

Test-only components sit inside the measurement, and every figure includes their behaviour: on Machine Payments Protocol on Lightning (Spark regtest), Spark's hosted regtest operators, with simulated Lightning routing; on Machine Payments Protocol on Tempo (Moderato testnet), the Stripe-mediated acceptance leg that production may use is not exercised at all; on x402 on Base (Sepolia), the x402 facilitator is the firm's own in-process component; on x402 on Solana (devnet, Alpenglow), the x402.org facilitator as it runs against devnet; on x402 on Stellar (testnet), the OpenZeppelin testnet facilitator.

Solana devnet runs the Alpenglow consensus, under which there is no 32-slot rooting, while Solana mainnet ran, as of the freeze date, the consensus for which the frozen method's reliance level for that rail was written. The figures for x402 on Solana (devnet, Alpenglow) are therefore not representative of Solana mainnet finality, and that rail is not raced (see Diagnostic, not raced, below).

Measurement window: 2026-10-27 06:10 UTC to 2026-10-28 07:13 UTC, in four blocks, two at each vantage. T1 is a self-hosted machine whose network path originates in South Africa; T2 is a Hetzner Cloud machine in Germany. Both ran the same harness from the same frozen file set.

## What was measured

- Primary interval: from the client's initial unpaid request, the request that draws the HTTP 402 payment challenge, to the client's own evidence that the payment reached the rail's pinned reliance level. It deliberately includes the rail's protocol and HTTP exchange as well as settlement.
- Companion interval: from the pay command, the client's commitment of value, to the same end. It is the starting point the authorization-latency measurement (DIM-02) uses.
- Warm-only cut: the scored payments. Cold-inclusive cut: the scored payments together with each runner's warm-up payments at the start of each block.
- pass@k: the share of payments that reached final within k seconds, on the pre-registered grid of 2, 3, 5, 10, 15 and 20 seconds.
- Censored: a payment with no client evidence of the pinned level within 120 seconds of its initial request, or rejected without such evidence, or failed. It stays in the denominator of pass@k as not final at any k, is right-censored at 120 seconds in the percentiles, and is never dropped.
- Races: the four raced rails were measured in pairs. In each trial both rails of a pair executed the same payment scenario at the same moment on a seeded schedule; each of the six pairs ran 500 races, 125 in each block. x402 on Solana (devnet, Alpenglow) was measured alone, on 2,000 solo slots interleaved into the same schedule, and is in no race.

"Final" is defined per rail by each rail's own reliance level, so the figures are not like-for-like security objects:

- Machine Payments Protocol on Lightning (Spark regtest): preimage release.
- Machine Payments Protocol on Tempo (Moderato testnet): Simplex BFT block finality.
- x402 on Base (Sepolia): soft finality, one Base block.
- x402 on Solana (devnet, Alpenglow): commitment `finalized` as devnet reports it.
- x402 on Stellar (testnet): ledger close.

The per-rail figures permit a reader to derive an ordering of their own. Any such ordering is invalid, because each rail's "final" is a different reliance level, and the frozen method's deferral of rail-by-rail scoring applies to it in full.

## Reading the tables

- Rail is the rail's pinned display name, carrying its test network, so no figure can be read as a production network's. R-number is the project's internal identifier for the same rail, carried for reference only; it is not the sort key.
- A pass@k cell gives the share, then two 95 percent intervals, lower bound first: the Wilson score interval, and the robust interval, a block bootstrap that resamples runs of 10, 20 and 50 consecutive scheduled payments and keeps the widest of the three. The interval written first is the one the method leads with: the robust interval wherever consecutive payments are correlated (the dependence flag), otherwise the wider of the two, as the frozen tool marks it.
- P50, P95 and P99 are censoring-aware (Kaplan-Meier, censored at 120 seconds); "not reached" means the percentile falls among the censored payments. The percentiles of the observed payments alone are shown beside them.
- The log-normal median and scale are fitted by censored likelihood, with a 95 percent block-bootstrap interval; the fit to the observed payments alone is shown beside it as a bracket, never as a substitute.
- For the cold-inclusive cut the frozen tool computed no bootstrap, so those cells read "not computed by the tool for this cut"; nothing was recomputed to fill them.
- Flags the method sets are findings about the measurement, not about any rail: every rail carries the vantage-heterogeneity flag, so the per-vantage tables come before the pooled ones; Machine Payments Protocol on Lightning (Spark regtest) carries the dependence flag, set at T2, which also governs its pooled cuts; x402 on Stellar (testnet) carries the block-heterogeneity flag at T1, its two T1 blocks differing beyond the pre-registered test; no rail carries the opponent-dependence flag.
- Every figure is copied from the output of the frozen analysis tool, rounded only: pass@k to three decimals, seconds to two, the log-normal scale to three.

## Results: the four raced rails

### Vantage T1, warm-only primary interval (750 scored payments per rail)

| Rail | R-number | Attempted | Observed | Censored | P50 / P95 / P99, censoring-aware (s) | P50 / P95 / P99, observed only (s) | Log-normal median, censored fit (s; 95 percent interval) | Log-normal scale, censored fit (95 percent interval) | Observed-only fit: median (s), scale |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 750 | 750 | 0 | 10.81 / 14.52 / 16.00 | 10.81 / 14.52 / 16.00 | 10.74 (10.56 to 10.95) | 0.195 (0.182 to 0.209) | 10.74, 0.195 |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 750 | 750 | 0 | 2.25 / 2.90 / 3.22 | 2.25 / 2.90 / 3.22 | 2.28 (2.25 to 2.31) | 0.143 (0.133 to 0.154) | 2.28, 0.143 |
| x402 on Base (Sepolia) | R1 | 750 | 750 | 0 | 2.25 / 2.65 / 2.82 | 2.25 / 2.65 / 2.82 | 2.28 (2.26 to 2.30) | 0.079 (0.074 to 0.083) | 2.28, 0.079 |
| x402 on Stellar (testnet) | R2 | 750 | 749 | 1 | 12.21 / 18.40 / 19.94 | 12.21 / 18.39 / 19.89 | 13.10 (12.80 to 13.42) | 0.206 (0.183 to 0.239) | 13.06, 0.189 |

| Rail | R-number | pass@2 s | pass@3 s | pass@5 s | pass@10 s | pass@15 s | pass@20 s |
|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.001 (Wilson 0.000 to 0.008; robust 0.000 to 0.004) | 0.292 (robust 0.251 to 0.334; Wilson 0.261 to 0.326) | 0.971 (robust 0.956 to 0.984; Wilson 0.956 to 0.981) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 0.152 (robust 0.125 to 0.182; Wilson 0.128 to 0.179) | 0.969 (Wilson 0.954 to 0.979; robust 0.958 to 0.980) | 0.999 (Wilson 0.992 to 1.000; robust 0.996 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) |
| x402 on Base (Sepolia) | R1 | 0.001 (Wilson 0.000 to 0.008; robust 0.000 to 0.004) | 0.996 (Wilson 0.988 to 0.999; robust 0.991 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) |
| x402 on Stellar (testnet) | R2 | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.021 (robust 0.008 to 0.036; Wilson 0.013 to 0.034) | 0.720 (robust 0.687 to 0.753; Wilson 0.687 to 0.751) | 0.991 (Wilson 0.981 to 0.995; robust 0.983 to 0.997) |

### Vantage T2, warm-only primary interval (750 scored payments per rail)

| Rail | R-number | Attempted | Observed | Censored | P50 / P95 / P99, censoring-aware (s) | P50 / P95 / P99, observed only (s) | Log-normal median, censored fit (s; 95 percent interval) | Log-normal scale, censored fit (95 percent interval) | Observed-only fit: median (s), scale |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 750 | 750 | 0 | 6.09 / 7.21 / 8.20 | 6.09 / 7.21 / 8.20 | 5.99 (5.89 to 6.13) | 0.202 (0.159 to 0.261) | 5.99, 0.202 |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 750 | 750 | 0 | 1.31 / 1.63 / 1.81 | 1.31 / 1.63 / 1.81 | 1.30 (1.27 to 1.32) | 0.195 (0.152 to 0.258) | 1.30, 0.195 |
| x402 on Base (Sepolia) | R1 | 750 | 750 | 0 | 1.11 / 1.27 / 1.36 | 1.11 / 1.27 / 1.36 | 1.14 (1.12 to 1.15) | 0.070 (0.065 to 0.076) | 1.14, 0.070 |
| x402 on Stellar (testnet) | R2 | 750 | 750 | 0 | 9.12 / 14.82 / 16.24 | 9.12 / 14.82 / 16.24 | 10.02 (9.86 to 10.19) | 0.218 (0.209 to 0.226) | 10.02, 0.218 |

| Rail | R-number | pass@2 s | pass@3 s | pass@5 s | pass@10 s | pass@15 s | pass@20 s |
|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 0.000 (robust 0.000 to 0.000; Wilson 0.000 to 0.005) | 0.005 (robust 0.001 to 0.011; Wilson 0.002 to 0.014) | 0.063 (robust 0.048 to 0.078; Wilson 0.047 to 0.082) | 0.996 (robust 0.989 to 1.000; Wilson 0.988 to 0.999) | 0.997 (robust 0.991 to 1.000; Wilson 0.990 to 0.999) | 0.997 (robust 0.991 to 1.000; Wilson 0.990 to 0.999) |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 0.996 (Wilson 0.988 to 0.999; robust 0.991 to 1.000) | 0.999 (Wilson 0.992 to 1.000; robust 0.996 to 1.000) | 0.999 (Wilson 0.992 to 1.000; robust 0.996 to 1.000) | 0.999 (Wilson 0.992 to 1.000; robust 0.996 to 1.000) | 0.999 (Wilson 0.992 to 1.000; robust 0.996 to 1.000) | 0.999 (Wilson 0.992 to 1.000; robust 0.996 to 1.000) |
| x402 on Base (Sepolia) | R1 | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) |
| x402 on Stellar (testnet) | R2 | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.005; robust 0.000 to 0.000) | 0.660 (robust 0.623 to 0.701; Wilson 0.625 to 0.693) | 0.957 (robust 0.940 to 0.974; Wilson 0.940 to 0.970) | 1.000 (Wilson 0.995 to 1.000; robust 1.000 to 1.000) |

### Pooled across both vantages, warm-only primary interval (1,500 scored payments per rail)

| Rail | R-number | Attempted | Observed | Censored | P50 / P95 / P99, censoring-aware (s) | P50 / P95 / P99, observed only (s) | Log-normal median, censored fit (s; 95 percent interval) | Log-normal scale, censored fit (95 percent interval) | Observed-only fit: median (s), scale |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 1500 | 1500 | 0 | 7.21 / 13.41 / 15.45 | 7.21 / 13.41 / 15.45 | 8.03 (7.24 to 8.84) | 0.353 (0.330 to 0.366) | 8.03, 0.353 |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 1500 | 1500 | 0 | 1.76 / 2.74 / 3.06 | 1.76 / 2.74 / 3.06 | 1.72 (1.56 to 1.91) | 0.330 (0.302 to 0.350) | 1.72, 0.330 |
| x402 on Base (Sepolia) | R1 | 1500 | 1500 | 0 | 1.97 / 2.51 / 2.76 | 1.97 / 2.51 / 2.76 | 1.61 (1.43 to 1.82) | 0.356 (0.327 to 0.362) | 1.61, 0.356 |
| x402 on Stellar (testnet) | R2 | 1500 | 1499 | 1 | 11.34 / 17.47 / 19.18 | 11.33 / 17.45 / 19.12 | 11.46 (10.91 to 12.02) | 0.251 (0.235 to 0.268) | 11.44, 0.243 |

| Rail | R-number | pass@2 s | pass@3 s | pass@5 s | pass@10 s | pass@15 s | pass@20 s |
|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 0.000 (robust 0.000 to 0.000; Wilson 0.000 to 0.003) | 0.003 (robust 0.001 to 0.005; Wilson 0.001 to 0.007) | 0.032 (robust 0.021 to 0.044; Wilson 0.024 to 0.042) | 0.644 (robust 0.521 to 0.765; Wilson 0.619 to 0.668) | 0.984 (robust 0.975 to 0.991; Wilson 0.976 to 0.989) | 0.999 (robust 0.996 to 1.000; Wilson 0.995 to 1.000) |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 0.574 (robust 0.425 to 0.724; Wilson 0.549 to 0.599) | 0.984 (robust 0.977 to 0.991; Wilson 0.976 to 0.989) | 0.999 (Wilson 0.995 to 1.000; robust 0.997 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) |
| x402 on Base (Sepolia) | R1 | 0.501 (robust 0.328 to 0.683; Wilson 0.475 to 0.526) | 0.998 (Wilson 0.994 to 0.999; robust 0.995 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) |
| x402 on Stellar (testnet) | R2 | 0.000 (Wilson 0.000 to 0.003; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.003; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.003; robust 0.000 to 0.000) | 0.341 (robust 0.228 to 0.454; Wilson 0.317 to 0.365) | 0.839 (robust 0.794 to 0.885; Wilson 0.819 to 0.856) | 0.995 (robust 0.991 to 0.999; Wilson 0.990 to 0.998) |

### Pooled, cold-inclusive cut (scored and warm-up payments)

| Rail | R-number | Attempted | Observed | Censored | P50 / P95 / P99, censoring-aware (s) | P50 / P95 / P99, observed only (s) | Log-normal median, censored fit (s; 95 percent interval) | Log-normal scale, censored fit (95 percent interval) | Observed-only fit: median (s), scale |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 1512 | 1512 | 0 | 7.22 / 13.42 / 15.50 | 7.22 / 13.42 / 15.50 | 8.04 (not computed by the tool for this cut) | 0.353 (not computed by the tool for this cut) | 8.04, 0.353 |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 1512 | 1512 | 0 | 1.76 / 2.74 / 3.09 | 1.76 / 2.74 / 3.09 | 1.72 (not computed by the tool for this cut) | 0.331 (not computed by the tool for this cut) | 1.72, 0.331 |
| x402 on Base (Sepolia) | R1 | 1512 | 1512 | 0 | 1.97 / 2.51 / 2.76 | 1.97 / 2.51 / 2.76 | 1.61 (not computed by the tool for this cut) | 0.356 (not computed by the tool for this cut) | 1.61, 0.356 |
| x402 on Stellar (testnet) | R2 | 1512 | 1511 | 1 | 11.34 / 17.45 / 19.18 | 11.34 / 17.44 / 19.12 | 11.46 (not computed by the tool for this cut) | 0.251 (not computed by the tool for this cut) | 11.44, 0.243 |

| Rail | R-number | pass@2 s | pass@3 s | pass@5 s | pass@10 s | pass@15 s | pass@20 s |
|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 0.000 (Wilson 0.000 to 0.003; robust not computed by the tool for this cut) | 0.003 (Wilson 0.001 to 0.007; robust not computed by the tool for this cut) | 0.032 (Wilson 0.024 to 0.042; robust not computed by the tool for this cut) | 0.644 (Wilson 0.619 to 0.667; robust not computed by the tool for this cut) | 0.983 (Wilson 0.975 to 0.988; robust not computed by the tool for this cut) | 0.999 (Wilson 0.995 to 1.000; robust not computed by the tool for this cut) |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 0.573 (Wilson 0.548 to 0.598; robust not computed by the tool for this cut) | 0.983 (Wilson 0.976 to 0.989; robust not computed by the tool for this cut) | 0.999 (Wilson 0.995 to 1.000; robust not computed by the tool for this cut) | 0.999 (Wilson 0.996 to 1.000; robust not computed by the tool for this cut) | 0.999 (Wilson 0.996 to 1.000; robust not computed by the tool for this cut) | 0.999 (Wilson 0.996 to 1.000; robust not computed by the tool for this cut) |
| x402 on Base (Sepolia) | R1 | 0.501 (Wilson 0.475 to 0.526; robust not computed by the tool for this cut) | 0.997 (Wilson 0.993 to 0.999; robust not computed by the tool for this cut) | 1.000 (Wilson 0.997 to 1.000; robust not computed by the tool for this cut) | 1.000 (Wilson 0.997 to 1.000; robust not computed by the tool for this cut) | 1.000 (Wilson 0.997 to 1.000; robust not computed by the tool for this cut) | 1.000 (Wilson 0.997 to 1.000; robust not computed by the tool for this cut) |
| x402 on Stellar (testnet) | R2 | 0.000 (Wilson 0.000 to 0.003; robust not computed by the tool for this cut) | 0.000 (Wilson 0.000 to 0.003; robust not computed by the tool for this cut) | 0.000 (Wilson 0.000 to 0.003; robust not computed by the tool for this cut) | 0.341 (Wilson 0.317 to 0.365; robust not computed by the tool for this cut) | 0.839 (Wilson 0.819 to 0.856; robust not computed by the tool for this cut) | 0.995 (Wilson 0.990 to 0.998; robust not computed by the tool for this cut) |

### Pooled, companion interval (pay command to the same end), warm-only

| Rail | R-number | Attempted | Observed | Censored | P50 / P95 / P99, censoring-aware (s) | P50 / P95 / P99, observed only (s) | Log-normal median, censored fit (s; 95 percent interval) | Log-normal scale, censored fit (95 percent interval) | Observed-only fit: median (s), scale |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 1500 | 1500 | 0 | 6.58 / 11.50 / 13.16 | 6.58 / 11.50 / 13.16 | 7.06 (6.45 to 7.68) | 0.337 (0.316 to 0.350) | 7.06, 0.337 |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 1500 | 1500 | 0 | 1.29 / 2.03 / 2.26 | 1.29 / 2.03 / 2.26 | 1.30 (1.20 to 1.42) | 0.314 (0.285 to 0.340) | 1.30, 0.314 |
| x402 on Base (Sepolia) | R1 | 1500 | 1500 | 0 | 1.95 / 2.50 / 2.75 | 1.95 / 2.50 / 2.75 | 1.60 (1.41 to 1.81) | 0.358 (0.329 to 0.363) | 1.60, 0.358 |
| x402 on Stellar (testnet) | R2 | 1500 | 1499 | 1 | 8.84 / 14.69 / 16.09 | 8.83 / 14.68 / 16.03 | 9.55 (9.27 to 9.83) | 0.251 (0.237 to 0.272) | 9.53, 0.242 |

| Rail | R-number | pass@2 s | pass@3 s | pass@5 s | pass@10 s | pass@15 s | pass@20 s |
|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 0.000 (robust 0.000 to 0.000; Wilson 0.000 to 0.003) | 0.025 (robust 0.014 to 0.035; Wilson 0.018 to 0.034) | 0.072 (robust 0.057 to 0.089; Wilson 0.060 to 0.086) | 0.842 (robust 0.785 to 0.898; Wilson 0.823 to 0.860) | 0.998 (robust 0.995 to 1.000; Wilson 0.994 to 0.999) | 0.999 (robust 0.996 to 1.000; Wilson 0.995 to 1.000) |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 0.946 (robust 0.925 to 0.966; Wilson 0.933 to 0.956) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) |
| x402 on Base (Sepolia) | R1 | 0.502 (robust 0.330 to 0.683; Wilson 0.477 to 0.527) | 0.998 (Wilson 0.994 to 0.999; robust 0.995 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) | 1.000 (Wilson 0.997 to 1.000; robust 1.000 to 1.000) |
| x402 on Stellar (testnet) | R2 | 0.000 (Wilson 0.000 to 0.003; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.003; robust 0.000 to 0.000) | 0.000 (Wilson 0.000 to 0.003; robust 0.000 to 0.000) | 0.686 (robust 0.653 to 0.718; Wilson 0.662 to 0.709) | 0.968 (robust 0.952 to 0.981; Wilson 0.958 to 0.976) | 0.999 (Wilson 0.996 to 1.000; robust 0.998 to 1.000) |

### Assurance and censoring, pooled warm-only

P(settled given accept) is the share of observed payments that a later re-read of each rail, made no sooner than two hours after each block, confirmed settled. A payment censored by the client but found settled on chain stays censored, because the paying client was told it had not completed.

| Rail | R-number | P(settled given accept) (Wilson 95 percent interval) | Accepted payments re-read | Unverifiable | Censored | Censored, settled on chain | Censored, not checkable | Voided |
|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | R11 | 1.000 (Wilson 0.997 to 1.000) | 1500 | 0 | 0 | 0 | 0 | 0 |
| Machine Payments Protocol on Tempo (Moderato testnet) | R10 | 1.000 (Wilson 0.997 to 1.000) | 1500 | 0 | 0 | 0 | 0 | 0 |
| x402 on Base (Sepolia) | R1 | 1.000 (Wilson 0.997 to 1.000) | 1499 | 1 | 0 | 0 | 0 | 0 |
| x402 on Stellar (testnet) | R2 | 1.000 (Wilson 0.997 to 1.000) | 1499 | 0 | 1 | 0 | 0 | 0 |

### Races realised

| Pair | R-numbers | T2 block 1 | T1 block 1 | T1 block 2 | T2 block 2 | All blocks |
|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) with Machine Payments Protocol on Tempo (Moderato testnet) | R11 and R10 | 125 | 125 | 125 | 125 | 500 |
| Machine Payments Protocol on Lightning (Spark regtest) with x402 on Base (Sepolia) | R11 and R1 | 125 | 125 | 125 | 125 | 500 |
| Machine Payments Protocol on Lightning (Spark regtest) with x402 on Stellar (testnet) | R11 and R2 | 125 | 125 | 125 | 125 | 500 |
| Machine Payments Protocol on Tempo (Moderato testnet) with x402 on Base (Sepolia) | R10 and R1 | 125 | 125 | 125 | 125 | 500 |
| Machine Payments Protocol on Tempo (Moderato testnet) with x402 on Stellar (testnet) | R10 and R2 | 125 | 125 | 125 | 125 | 500 |
| x402 on Base (Sepolia) with x402 on Stellar (testnet) | R1 and R2 | 125 | 125 | 125 | 125 | 500 |

Unpaired payments: zero on every rail. Voided trials: zero. Runner restarts: zero in every block on every rail. No block ended early.

## Diagnostic, not raced

x402 on Solana (devnet, Alpenglow). Measured on the same protocol, but each payment was made alone, without a co-scheduled opponent, so these figures are not load-comparable to the raced table. Its 2,000 solo payments (500, 500, 500, 500 in the four blocks) are reported here, never in the raced tables, and no race statistic includes them.

### Diagnostic, not raced: counts, percentiles and log-normal fit, by cut

| Cut | Rail | R-number | Attempted | Observed | Censored | P50 / P95 / P99, censoring-aware (s) | P50 / P95 / P99, observed only (s) | Log-normal median, censored fit (s; 95 percent interval) | Log-normal scale, censored fit (95 percent interval) | Observed-only fit: median (s), scale |
|---|---|---|---|---|---|---|---|---|---|---|
| Vantage T1, warm-only primary | x402 on Solana (devnet, Alpenglow) | R9 | 1000 | 925 | 75 | 3.53 / not reached / not reached | 3.45 / 5.24 / 7.14 | 4.64 (4.31 to 5.02) | 1.032 (0.890 to 1.164) | 3.49, 0.229 |
| Vantage T2, warm-only primary | x402 on Solana (devnet, Alpenglow) | R9 | 1000 | 882 | 118 | 1.43 / not reached / not reached | 1.40 / 1.91 / 3.66 | 2.63 (2.20 to 3.26) | 1.613 (1.377 to 1.858) | 1.47, 0.184 |
| Pooled, warm-only primary | x402 on Solana (devnet, Alpenglow) | R9 | 2000 | 1807 | 193 | 2.69 / not reached / not reached | 2.56 / 4.67 / 6.43 | 3.50 (3.04 to 4.01) | 1.383 (1.234 to 1.540) | 2.29, 0.480 |
| Pooled, cold-inclusive | x402 on Solana (devnet, Alpenglow) | R9 | 2012 | 1817 | 195 | 2.69 / not reached / not reached | 2.56 / 4.66 / 6.43 | 3.50 (not computed by the tool for this cut) | 1.385 (not computed by the tool for this cut) | 2.29, 0.479 |
| Pooled, companion interval, warm-only | x402 on Solana (devnet, Alpenglow) | R9 | 2000 | 1807 | 193 | 1.91 / not reached / not reached | 1.87 / 2.57 / 3.61 | 2.74 (2.47 to 3.08) | 1.404 (1.247 to 1.567) | 1.75, 0.267 |

### Diagnostic, not raced: pass@k, by cut

| Cut | Rail | R-number | pass@2 s | pass@3 s | pass@5 s | pass@10 s | pass@15 s | pass@20 s |
|---|---|---|---|---|---|---|---|---|
| Vantage T1, warm-only primary | x402 on Solana (devnet, Alpenglow) | R9 | 0.000 (Wilson 0.000 to 0.004; robust 0.000 to 0.000) | 0.266 (robust 0.235 to 0.295; Wilson 0.240 to 0.294) | 0.871 (robust 0.845 to 0.897; Wilson 0.849 to 0.890) | 0.924 (robust 0.903 to 0.943; Wilson 0.906 to 0.939) | 0.925 (robust 0.904 to 0.944; Wilson 0.907 to 0.940) | 0.925 (robust 0.904 to 0.944; Wilson 0.907 to 0.940) |
| Vantage T2, warm-only primary | x402 on Solana (devnet, Alpenglow) | R9 | 0.843 (robust 0.791 to 0.891; Wilson 0.819 to 0.864) | 0.869 (robust 0.831 to 0.906; Wilson 0.847 to 0.889) | 0.882 (robust 0.848 to 0.913; Wilson 0.861 to 0.901) | 0.882 (robust 0.848 to 0.913; Wilson 0.861 to 0.901) | 0.882 (robust 0.848 to 0.913; Wilson 0.861 to 0.901) | 0.882 (robust 0.848 to 0.913; Wilson 0.861 to 0.901) |
| Pooled, warm-only primary | x402 on Solana (devnet, Alpenglow) | R9 | 0.421 (robust 0.285 to 0.552; Wilson 0.400 to 0.443) | 0.568 (robust 0.469 to 0.662; Wilson 0.546 to 0.589) | 0.876 (robust 0.855 to 0.897; Wilson 0.861 to 0.890) | 0.903 (robust 0.881 to 0.922; Wilson 0.889 to 0.915) | 0.903 (robust 0.881 to 0.922; Wilson 0.890 to 0.916) | 0.903 (robust 0.881 to 0.922; Wilson 0.890 to 0.916) |
| Pooled, cold-inclusive | x402 on Solana (devnet, Alpenglow) | R9 | 0.421 (Wilson 0.400 to 0.443; robust not computed by the tool for this cut) | 0.568 (Wilson 0.546 to 0.589; robust not computed by the tool for this cut) | 0.876 (Wilson 0.861 to 0.890; robust not computed by the tool for this cut) | 0.903 (Wilson 0.889 to 0.915; robust not computed by the tool for this cut) | 0.903 (Wilson 0.889 to 0.915; robust not computed by the tool for this cut) | 0.903 (Wilson 0.889 to 0.915; robust not computed by the tool for this cut) |
| Pooled, companion interval, warm-only | x402 on Solana (devnet, Alpenglow) | R9 | 0.596 (robust 0.508 to 0.676; Wilson 0.574 to 0.617) | 0.879 (robust 0.856 to 0.900; Wilson 0.864 to 0.893) | 0.902 (robust 0.881 to 0.921; Wilson 0.889 to 0.915) | 0.903 (robust 0.881 to 0.922; Wilson 0.890 to 0.916) | 0.903 (robust 0.881 to 0.922; Wilson 0.890 to 0.916) | 0.903 (robust 0.881 to 0.922; Wilson 0.890 to 0.916) |

### Diagnostic, not raced: assurance and censoring, pooled warm-only

| Rail | R-number | P(settled given accept) (Wilson 95 percent interval) | Accepted payments re-read | Unverifiable | Censored | Censored, settled on chain | Censored, not checkable | Voided |
|---|---|---|---|---|---|---|---|---|
| x402 on Solana (devnet, Alpenglow) | R9 | 1.000 (Wilson 0.998 to 1.000) | 1807 | 0 | 193 | 189 | 0 | 0 |

## The named disconfirmer, tested

The pre-registration names, before the run, a result that would count against a single-number reading of any rail's finality. Its words: "If the per-rail pass@k curves of two rails cross between the warm-only and cold-inclusive cuts, between the two vantages, or between the software-version strata of section 6.7, the single-number reading of either rail's finality is not supported and the report says so."

Applied to the tool's pass@k figures on the frozen grid (2, 3, 5, 10, 15, 20 s). A pair "crosses" between two cuts when, at some k, the two rails' pass@k stand in one relation in the first cut and the opposite relation in the second (equal values are not a crossing). Which rail of a pair has the larger share is not stated here, for any pair.

- Warm-only against cold-inclusive: no pair crosses (raced rails, and pairs including x402 on Solana).
- Software-version strata: none exist (one x402 on Solana version throughout; no other rail records one), so this limb cannot fire.
- T1 against T2, on the point estimates: three pairs of raced rails cross: Machine Payments Protocol on Tempo with x402 on Base, at k = 2 s; Machine Payments Protocol on Tempo with x402 on Stellar, at k = 20 s; Machine Payments Protocol on Lightning with x402 on Stellar, at k = 20 s. Two pairs including x402 on Solana cross: Machine Payments Protocol on Lightning with x402 on Solana, at k = 10 s; x402 on Solana with x402 on Stellar, at k = 15 s.
- T1 against T2, on the intervals (a crossing counted only where the two rails' intervals do not overlap at either vantage): none of the three raced pairs crosses (in each, the intervals overlap at one vantage at least, on Wilson and on the robust interval alike); both pairs including x402 on Solana still cross (the intervals separate at both vantages, on both interval types).

Result: the clause as written is read on the point estimates with every rail counted. The named disconfirmer fires between the vantages: the single-number reading of finality is not supported for any of the five rails. Robustness reading, not the clause as written: counting a crossing only where the two rails' intervals separate at both vantages and excluding x402 on Solana as not load-comparable, the disconfirmer does not fire; shown for context, it does not govern. Two further facts a reader should weigh regardless of the reading: finality is strongly vantage-dependent at short k for the raced rails even where no crossing fires (the per-vantage tables above lead for that reason), and the k = 20 s crossings are near-ceiling differences of 0.001 to 0.009 in pass@k.

## Disclosures

- The T1 host ran with 16 GB of memory against the 8 GB its pre-registered host pin states; the harness has no memory-dependent behaviour, and the core count and processor were as pinned.
- Every block was launched by hand and then ran unattended.
- During both T1 blocks every interactive session on the T1 host was idle or offline and one scheduled background task was paused; one trivial scheduled check ran throughout; the per-trial host-load readings are in the records either way.
- Only x402 on Solana records a network software version: every observed payment recorded solana-core 4.4.0-beta.1 (1,817 of 1,817); censored payments record none because the version is read after finality. No version changed, so no software-version strata exist.
- On x402 on Base (Sepolia) the firm's own seller account pays each payment's network fee in Base Sepolia test ether; its balance went from 0.010034 on the morning of 2026-10-27 to 0.008862 before the last block, and no funds stop occurred.
- No pause, settle stop, funds stop, runner restart, void, unpaired payment or early end occurred in any block, and no payment's runner started more than 5 seconds after dispatch (the largest gap was 4.7 milliseconds).
- One cosmetic fix outside the frozen file set was made before the run: a doubled host name in a log line of the T2 launch script.
- On x402 on Solana (devnet, Alpenglow), 193 of 2,000 scored payments are censored: the firm's own test traffic met a rate limit, and 189 of the 193 have a settled transaction behind the x402.org facilitator's HTTP 429 responses. The paying client was told those payments had not completed, so they stay censored, as the method requires. The pre-registration predicted that the spacing of these payments would not trip that limit; the prediction did not hold.

## The withheld file

The frozen method computes Bradley-Terry strengths and a pairwise win matrix over the four raced rails. They are computed because the method requires it and are not published: they are written to a file headed WITHHELD, kept only in a private repository, and its existence is disclosed here. Its SHA-256 hash, 27034346e8841a9cc74443be1866b2d253c8b4cb9b9ef9c15d7f5aa9b6195651, was anchored after the analysis ran and before any publication, by an OpenTimestamps proof attested in Bitcoin block 973658 and by a Sigstore signature recorded as Rekor transparency-log entry 3560518693, to show that the computation was done and that the file has not changed since. It is released only if the firm reopens its section 21 Level 2 decision by a recorded ruling.

## What this run does not say

- No rail is ranked, and no recommendation is made.
- No mainnet measurement was made, and nothing here states any production network's finality.
- The pooled figures mix two hosts, two hardware generations and two networks; the per-vantage figures are where a single-host reading lives.
- The pre-registration makes no commitment to publish and no commitment to any display beyond these per-rail quantities. The further diagnostics it lists (sensitivity cuts, probe floors, timing distributions and the rest) are in the firm's analysis record and are not reproduced on this page.

## Corrections and right of reply

Any operator of a rail or facilitator named on this page may respond through the structured right-of-reply channel at https://reply.agentic-paybench.dev/. Replies about a factual data error, a methodology defect, a mischaracterisation, a confidentiality objection, or a jurisdictional objection are reviewed before publication; replies about methodology framing, a change since the measurement window, or the scope of the environment tested are published promptly with a badge saying the review is pending. The response cap and visibility policy is linked from that page. Corrections to anything here are also welcome by email at mblake@everydayai.link.
