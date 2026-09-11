posture-class: level1-measurement

# Authorization-primitive latency (DIM-02): named-rail findings

Version 1.0, for the measurement run of 2026-06-28. This artefact is frozen per dated run: a correction or a re-measurement is published as a new dated version and this one is kept. It is served on the oracle site only while the ADR-009 display gate `G_S21` is open, and its publication carries an audit record.

## What this page is

This page reports authorization-primitive latency (the PayBench dimension DIM-02, internally RAPL) for six named payment rails, measured by Everyday AI Ltd against test networks it operates or funds itself.

These figures are a measurement, not a recommendation: no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use.

Rails are listed alphabetically by rail name. That ordering is fixed and carries no performance meaning.

The same measurement protocol, pre-registered before any run, was applied identically to every rail.

No ranking is stated on this page, no winner is named, and there is no route from this page to transact on any rail.

## Scope of the measurement

Every figure below comes from first-party runs on test networks (Base Sepolia, Stellar testnet, Solana devnet, Tempo Moderato testnet, a Spark hosted regtest, and an in-process AP2 verifier). No funds moved on any production network. The traffic was self-originated by the measuring party; no third party's payments were observed. These are the calibration and pilot evidence attached to the pre-registration, not a production result, and they say nothing about how any of these rails behaves under other parties' production load.

Measurement window: 2026-06-22 to 2026-06-28. Calibration parameters fixed 2026-06-29.

The version of the Agent Payments Protocol against which R6 was measured is the Google AP2 reference implementation at repository commit e1ea56d, captured on 2026-06-28. AP2 is under active change, so that pin is stated here rather than left implicit.

## What was measured

The clock starts when the pay command is on the wire with its payload constructed, and stops at the last byte of the authorization-primitive decision. A same-path TCP and TLS round-trip baseline is subtracted, and both the raw and the corrected figure are retained in the record. The backing-service hop (a facilitator call, a chain remote-procedure-call read, or a Lightning node round trip) is authorization work and is never subtracted from the end-to-end figure.

Two primitives are reported separately and are never combined into one figure:

- Payment validation (primitive A): a payment authorization presented to a verifier, up to the accept or decline decision.
- Challenge issuance (primitive B): the emission of a payment challenge, either an HTTP 402 response or a minted invoice.

The anchored methodology calls these two the A and B sub-groupings of the dimension; this page uses "primitive A" and "primitive B" for the same two things, so that no word on this page reads as a placing.

Within each primitive, rails are grouped by work class. A local-complete rail does no per-call network round trip in steady state; a network-dependent rail makes one. Figures are comparable inside a work class and are not comparable across work classes; nothing on this page compares them.

## Reading the columns

- Rail is the rail's own name, written in full. R-number is the project's internal identifier for the same rail, carried beside the name for reference only; it is not the sort key and it carries no meaning here beyond identity.
- Median, P95 and P99 are the pre-registered headline tuple, in milliseconds, at the stated topology.
- N is the number of trials at that topology.
- Topology names the measuring vantage: T1 is a self-hosted development machine, T2a is a GitHub Codespaces host on Azure, T2b is an Oracle Cloud host in uk-london-1. T2b is the citable named-region vantage.
- The 95 percent interval is an interval for the median, derived after the fact from the pre-registered per-rail lognormal parameters as median times exp(plus or minus 1.96 sigma divided by the square root of N). It is a descriptive addition outside the frozen plan, whose latency headline is the percentile tuple; it is disclosed here rather than presented as a pre-registered quantity.
- A dash means the quantity is not in the anchored record. Nothing is reconstructed to fill a gap.

## Primitive A, payment validation

### Work class: local-complete

| Rail | R-number | Variant | median (ms) | P95 (ms) | P99 (ms) | 95 percent interval for the median (ms) | N | topology | date |
|---|---|---|---|---|---|---|---|---|---|
| Google Cloud with AP2 | R6 | delegated payment-condition chain | 1.58 | 1.60 | 1.62 | 1.575 to 1.585 | 30 | in-process, topology-invariant | 2026-06-28 |
| Machine Payments Protocol on Tempo | R10 | session voucher | 8.2 | - | - | 8.046 to 8.357 | 30 | T2b | 2026-06-28 |

Notes for this table. The AP2 figure is the delegated payment-condition variant, which verifies a two-signature chain; the single-token human-present variant of the same rail is 0.68 at the median, 0.71 at P95 and 0.76 at P99 over 30 trials. AP2 runs in process with no transport, so it is topology-invariant by construction; a sidecar deployment would add an inter-process hop. The Tempo session-voucher figure is the warm path, where a cached voucher is accepted with no per-call network read; the cold path, when the time-to-live expires and one chain read is made, is approximately 360 ms. The same rail measures 11.2 at the median at T2a and 19.5 at the median at T1, because a local-complete rail's median tracks the measuring host's processor rather than the network path.

### Work class: network-dependent

| Rail | R-number | median (ms) | P95 (ms) | P99 (ms) | 95 percent interval for the median (ms) | N | topology | date |
|---|---|---|---|---|---|---|---|---|
| x402 on Base | R1 | 492 | 576 | 726 | 475.4 to 509.2 | 30 | T2b | 2026-06-28 |
| x402 on Solana | R9 | 212 | 370 | 416 | 187.8 to 239.3 | 30 | T2b | 2026-06-28 |
| x402 on Stellar | R2 | 289 | 366 | 553 | 276.0 to 302.7 | 40 | T2b | 2026-06-28 |

Notes for this table. Each of these rails makes one backing-service call per authorization: x402 on Base reaches a facilitator that reads a Base Sepolia node, x402 on Solana reaches the x402.org facilitator, x402 on Stellar reaches an OpenZeppelin facilitator. The local computation floor is below one millisecond in all three cases, so the end-to-end figure is dominated by that backing service. Absolute medians move with the measuring host's route: at T1 the same three rails measure 777 on Base, 400 on Solana and 464 on Stellar, and at T2a they measure 420 on Base, 180 on Solana and 364 on Stellar. A reader who wants an absolute number for a network-dependent rail should take the per-topology spread and not a single figure. Declined authorizations were zero percent of trials in every rail and topology cell, so the pre-registered fallback estimator did not fire.

## Primitive B, challenge issuance

### Work class: local-complete

| Rail | R-number | Variant | median (ms) | P95 (ms) | P99 (ms) | 95 percent interval for the median (ms) | N | topology | date |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Tempo | R10 | 402 emission | 2.95 | - | - | 2.806 to 3.102 | 30 | T2b representative | 2026-06-28 |
| x402 on Base | R1 | 402 emission | 3.0 | - | - | 2.918 to 3.084 | 30 | T2b representative | 2026-06-28 |
| x402 on Solana | R9 | 402 emission | 2.2 | - | - | 2.159 to 2.241 | 30 | T2b representative | 2026-06-28 |
| x402 on Stellar | R2 | 402 emission | 1.60 | - | - | 1.509 to 1.697 | 30 | T2b representative | 2026-06-28 |

Notes for this table. Each of these emissions is assembled locally from a template with no network call, so the median is topology-invariant while the tails widen on a shared cloud host. The anchored record states the group range as approximately 1.6 to 3.0 ms across the three topologies; the per-rail medians shown here are the calibrated representative-topology parameters from the fixture provenance files, and P95 and P99 are not in the anchored record for this group.

### Work class: network-dependent

| Rail | R-number | Variant | median (ms) | P95 (ms) | P99 (ms) | 95 percent interval for the median (ms) | N | topology | date |
|---|---|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning | R11 | BOLT11 invoice mint | 552 | - | - | 521.8 to 583.9 | 30 | T2b | 2026-06-28 |

Notes for this table. Minting an invoice requires a round trip to a Spark Lightning node, which is why this emission sits in a different work class from the four above and is not comparable with them. The same rail measures 936 at the median at T1 and 771 at the median at T2a, with a P99 of 1357 at T2a.

## Provenance

The measurement method was pre-registered and externally anchored before any run, so that the design could not be adjusted to the result. The dimension pre-registration carries OSF digital object identifier 10.17605/OSF.IO/UFQG5, the signed git tag paybench-rapl-prereg-v1, an OpenTimestamps proof anchored in Bitcoin block 955977, and Rekor transparency-log entry 2012836917. The manifest digest is 46a19eab. The settlement-finality methodology it builds on is frozen at version 1.2 with OSF digital object identifier 10.17605/OSF.IO/XGFUJ and the signed tag paybench-prereg-v1.2.

This measurement follows the frozen and anchored DIM-02 pre-registration (OSF DOI 10.17605/OSF.IO/UFQG5; Bitcoin block 955977; Rekor 2012836917). The frozen text of that record includes a finding ordering three rails on this dimension. That statement is part of the frozen methodology and was fixed before this page existed. This page does not assert any ordering: the table is listed alphabetically, the order carries no performance meaning, and nothing here is a recommendation to use any rail.

The figures above are data; any comparison a reader draws from them is the reader's own.

## Corrections and right of reply

Any operator of a rail or facilitator named on this page may respond through the structured right-of-reply channel at https://reply.agentic-paybench.dev/. Replies about a factual data error, a methodology defect, a mischaracterisation, a confidentiality objection, or a jurisdictional objection are reviewed before publication; replies about methodology framing, a change since the measurement window, or the scope of the environment tested are published promptly with a badge saying the review is pending. The response cap and visibility policy is linked from that page. Corrections to anything here are also welcome by email at mblake@everydayai.link.
