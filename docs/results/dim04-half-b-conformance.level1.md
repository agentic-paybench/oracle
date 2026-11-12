posture-class: level1-measurement

# PayBench DIM-04 Half B: conformance checks on five test-network rails, confirmatory report

Version 1.0, for the confirmatory run of 2026-11-12. This artefact is frozen per dated run: a correction or a re-measurement is published as a new dated version and this one is kept.

The data pre-registration is the signed git tag `paybench-dim4-halfb-prereg-v1` in the public payhelm repository (https://github.com/agentic-paybench/payhelm/blob/paybench-dim4-halfb-prereg-v1/paybench/methodology/dim4-halfb-PRE-REGISTRATION.md), registered on the Open Science Framework with digital object identifier 10.17605/OSF.IO/BMT8P (https://doi.org/10.17605/OSF.IO/BMT8P), its manifest anchored by an OpenTimestamps proof in Bitcoin blocks 975195 and 975221 and by Rekor transparency-log entry 3773957892. It is called "the registration" below.

## 1. What this report covers

This report gives the counts of the confirmatory run registered in the document above. The run was made by Everyday AI Ltd (the company, below). The company is the only payer and the only payee of every payment. The run used test networks only, with test tokens that carry no monetary value.

The design was frozen and externally anchored after the declared exploratory runs and before the confirmatory run or any publication. The places where the company's instrument or the run departed from the registered design are listed in section 9 below and recorded in Addendum 1 to the registration [ADDENDUM 1 CITATION: its tag, DOI and anchors are entered here once it is signed and anchored].

Each count says what happened in this run: k is the number of valid repetitions in which the documented bound held, out of K valid repetitions on this one test deployment, with every VOID and NOT EXERCISED attempt listed by cause. A count is not an estimate of how often this outcome occurs on any network, test or production, and no rate, probability or interval is derived from it.

Rails are listed alphabetically by rail name. That ordering is fixed and carries no performance meaning.

The same measurement protocol was applied identically to every rail. Identically means: the same outcome and void rules, the same repetition rule, the same records and the same reads of each rail's own evidence were applied in every cell; which fault classes apply to a rail, the component at which a fault is injected, and the mechanism each check exercises differ by rail, are listed cell by cell in section 4.8, and make counts across rails not comparable.

Section numbers in that sentence refer to the registration.

These figures are a measurement, not a recommendation: no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use.

Each cell tests a different documented bound on a different software stack, so counts across rails are not the same measurement and are not to be compared.

These conformance checks are a different kind of measurement from the DIM-02 authorization-latency figures: each result here is a count of binary outcomes for one rail under one fault, and none is comparable with, or to be combined with, any figure in that table.

## 2. The run

The run started on 2026-11-12.

The confirmatory order was seeded by the hash of Bitcoin block 975500, 000000000000000000016f5ddbb05bb2dbe7aa5d2439747cafc0a620941db8a3. Each block read it at its start from https://mempool.space/api and https://blockstream.info/api, and both sources returned the same hash. The confirmations at block 1's start were 8 on the three rails that started at 01:42 UTC and 16 on the two that started later. The seed and the ten block schedules were recorded before block 1.

Two blocks ran per rail, on one vantage: a self-hosted machine whose network path originates in South Africa.

Block start and end times, from each rail's driver log (UTC):

| Rail | Block 1 | Block 2 |
|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | 03:22:56 to 04:47:16 | 04:47:38 to 06:12:00 |
| Machine Payments Protocol on Tempo (Moderato testnet) | 01:42:05 to 03:55:23 | 03:55:39 to 06:08:30 |
| x402 on Base (Sepolia) | 03:22:36 to 05:54:50 | 05:55:07 to 08:27:17 |
| x402 on Solana (devnet, Alpenglow) | 01:42:05 to 03:43:52 | 03:44:15 to 05:50:16 |
| x402 on Stellar (testnet) | 01:42:05 to 04:29:34 | 04:29:52 to 07:17:28 |

Times are from the drivers' logs, to the second; every elapsed time in this report is computed from the unrounded timestamps and rounded to the second. The length of a block follows from the number of cells and repetitions on its rail and the registered waits of each check; it measures no property of any rail and supports no ordering.

Each rail's block 2 started 16 to 23 seconds after its block 1 ended (Machine Payments Protocol on Lightning 22 s, Machine Payments Protocol on Tempo 16 s, x402 on Base 17 s, x402 on Solana 23 s, x402 on Stellar 18 s): the time the driver takes to stop the block's services, pause 10 seconds and read the closing balances, and then to read the seed and open the next block.

At 01:42:02 UTC the initial start of Machine Payments Protocol on Lightning and of x402 on Base was refused before any payment: one of the two seed reads (https://mempool.space/api) answered HTTP 502. Both rails were restarted by the founder's decision of 2026-11-12 with the same frozen code, seed and block schedules, one after the other. Their block 1 started at 03:22:56 and 03:22:36 UTC, 1 h 40 min 51 s and 1 h 40 min 31 s after block 1 of the other three rails (01:42:05 UTC). For these two rails the run therefore did not meet the design of the registration's section 7.1 that all five rails run their blocks at the same time; the hours of the day they ran differ from those of the other three. No outcome of any rail had been displayed or written when the restart was decided at 03:21:54 UTC; the drivers of the three running rails scored their records only in memory, to decide replacements. The time between the refused start and the decision was the wait for that decision; in it no code, configuration or file of the two stopped rails was changed, and only the three running rails wrote their records. For these two rails an effect of the time of day cannot be excluded.

The rails did not all run at the same time throughout, as section 7.1 intends; the table gives how many ran in each stretch, from the drivers' logs.

| From | To | Rails running |
|---|---|---|
| 01:42:05 | 03:22:36 | three |
| 03:22:36 | 03:22:56 | four |
| 03:22:56 | 05:50:16 | five |
| 05:50:16 | 06:08:30 | four |
| 06:08:30 | 06:12:00 | three |
| 06:12:00 | 07:17:28 | two |
| 07:17:28 | 08:27:17 | one (1 h 9 min 49 s) |

No block stopped on the funds rule.

## 3. Results per cell

Each cell is one of three kinds (registration, section 4.9): a network-enforcement detector, which "can be VIOLATED only if the test network diverges from its own documented rule"; library or service behaviour, "genuinely open on the stack the company runs"; and a descriptive observation, "with no documented bound to hold or violate". A HELD result from a network-enforcement detector confirms the documented rule on that test network; it is expected, and it is reported as a confirmation, not as a discovery.

Where the run's records give a cell a different kind from the registration's section 4.9, this report gives the registration's kind (section 9 below, item 5).

No cell recorded a VIOLATED repetition, and no cell recorded an unclassified state (registration, section 5.7). The descriptive cells are check 3 on every rail and check 2b on Machine Payments Protocol on Lightning.

### Machine Payments Protocol on Lightning (Spark regtest)

| Cell | Kind | K | Attempts | Valid | k | VIOLATED | VOID, by cause | NOT EXERCISED, by cause | Complete |
|---|---|---|---|---|---|---|---|---|---|
| Check 2a, the credential presented again | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 2b, the payment repeated below the seller | descriptive observation | 10 | 10 | 10 | 0 observed yes, 10 observed no | 0 | 0 | 0 | complete |
| Check 3, a fresh signature inside the validity window | descriptive observation | 10 | 10 | 10 | 0 observed yes, 10 observed no | 0 | 0 | 0 | complete |
| Check 4a, a late artefact through the seller | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 4b, a late artefact direct to the network | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6a, the client drops after sending | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |

Beside every result on this rail: this rail's settlement and death evidence is the hosted operator's wallet and service views. They do not independently prove route-level settlement, and an unexplained absence of a transfer in them would read as HELD. In the exploratory runs, the payer's available balance rose by 408 sats unexplained during the hold-invoice sequence (registration, section 12). No endpoint on this rail reports a version, so void V5 (a network's software version changed during a repetition) does not apply here.

On this rail, whose documents define no definitive failure signal, the death read in check 4 is a measured death observation the company defines, never a documented signal (registration, section 4.4).

### Machine Payments Protocol on Tempo (Moderato testnet)

| Cell | Kind | K | Attempts | Valid | k | VIOLATED | VOID, by cause | NOT EXERCISED, by cause | Complete |
|---|---|---|---|---|---|---|---|---|---|
| Check 2a, the credential presented again | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 2b, the payment repeated below the seller | network-enforcement detector | 10 | 20 | 0 | 0 (no valid repetition) | 0 | 0 | 20 (refusal text not among the registration's reason entries: 'expiring nonce transaction already included') | INCOMPLETE |
| Check 3, a fresh signature inside the validity window | descriptive observation | 10 | 10 | 10 | 10 observed yes, 0 observed no | 0 | 0 | 0 | complete |
| Check 4a, a late artefact through the seller | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 4b, a late artefact direct to the network | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 5a, a duplicate nonce | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6a, the client drops after sending | network-enforcement detector | 20 | 20 | 20 | 20 HELD | 0 | 0 | 0 | complete |
| Check 6c, the drop after broadcast | network-enforcement detector | 20 | 20 | 20 | 20 HELD | 0 | 0 | 0 | complete |
| Check 7, a settlement outcome after a settle that cannot succeed | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |

Checks 6a and 6c on this rail have K = 20 by the frozen K table (registration, section 6.1).

On this rail, whose documents define no definitive failure signal, the death read in check 4 is a measured death observation the company defines, never a documented signal (registration, section 4.4).

Check 2b on Machine Payments Protocol on Tempo is INCOMPLETE: 0 valid repetitions of K = 10 within 20 attempts. In all 20 attempts the test network refused the resent transaction and one transfer was found. The refusal text recorded, "expiring nonce transaction already included", is not among the registration's reason entries, whose entry for this check is the typed code "ExpiringNonceReplay", copied from the node's answer in the exploratory runs; so no attempt counts toward the check, and its Half A cell is not labelled measured. The node reported version tempo/v1.18.3-5c71a4c throughout this run; the registration records tempo/v1.17.0-55a96ba, read on 2026-10-30. The changed text and the changed version were observed together; this run does not show that one caused the other. The cell is INCOMPLETE because the refusal text recorded is not among the registration's reason entries, which section 5.6 matches verbatim. This run therefore establishes neither that the bound held on this rail nor that it did not.

The registration's section 5.6 governs this cell: "A refusal counts toward HELD only when its recorded reason names the mechanism the check exercises (nonce or authorization used, replay, expiry); a refusal for any other recorded reason is NOT EXERCISED, reported and not counted toward K. Each reason entry is a full phrase or a typed code copied verbatim from a recorded response, matched case-sensitively, with the record that showed it cited; an entry carrying a per-request value (an identifier, a timestamp) is a regular expression around the verbatim words; no entry is a single generic word. Only VERIFIED entries attribute a refusal; an entry never seen in a recorded response stays NOT VERIFIED and attributes nothing." Whether a refusal names the mechanism is therefore decided by matching the recorded text against the frozen entries, not by reading it. The table above words this cause from the registration's section 5.6, not from the report tool (section 9 below, item 6).

The 20 attempts, each reported as the registration's section 5.3 requires of an INCOMPLETE cell (the transfers found are the live count; the assurance sweep found the same count for every one, section 7 below):

| Block | Attempt | Refused | Transfers found | Refusal text | Node version at start and end |
|---|---|---|---|---|---|
| 1 | 1 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 2 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 3 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 4 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 5 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 6 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 7 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 8 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 9 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 1 | 10 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 1 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 2 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 3 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 4 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 5 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 6 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 7 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 8 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 9 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |
| 2 | 10 | yes | 1 | "expiring nonce transaction already included" | tempo/v1.18.3-5c71a4c |

### x402 on Base (Sepolia)

| Cell | Kind | K | Attempts | Valid | k | VIOLATED | VOID, by cause | NOT EXERCISED, by cause | Complete |
|---|---|---|---|---|---|---|---|---|---|
| Check 1a, an identical resubmission through the seller | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 1b, an identical resubmission direct to the network | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 3, a fresh signature inside the validity window | descriptive observation | 10 | 10 | 10 | 10 observed yes, 0 observed no | 0 | 0 | 0 | complete |
| Check 4a, a late artefact through the seller | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 4b, a late artefact direct to the network | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 5a, a duplicate nonce | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6a, the client drops after sending | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6b, the facilitator drops before broadcast | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6c, the drop after broadcast | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6d, the facilitator pauses past the seller's timeout | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 7, a settlement outcome after a settle that cannot succeed | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |

### x402 on Solana (devnet, Alpenglow)

| Cell | Kind | K | Attempts | Valid | k | VIOLATED | VOID, by cause | NOT EXERCISED, by cause | Complete |
|---|---|---|---|---|---|---|---|---|---|
| Check 1a, an identical resubmission through the seller | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 1b, an identical resubmission direct to the network | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 3, a fresh signature inside the validity window | descriptive observation | 10 | 10 | 10 | 10 observed yes, 0 observed no | 0 | 0 | 0 | complete |
| Check 4a, a late artefact through the seller | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 4b, a late artefact direct to the network | network-enforcement detector | 10 | 11 | 10 | 10 HELD | 0 | 1 (V2: a read needed to decide the outcome failed after its retries) | 0 | complete |
| Check 6a, the client drops after sending | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6b, the facilitator drops before broadcast | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6c, the drop after broadcast | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6d, the facilitator pauses past the seller's timeout | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 7, a settlement outcome after a settle that cannot succeed | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |

The one VOID on this rail is block 2, check 4b, attempt 4. A read needed to decide its outcome failed after its retries (void V2), and it was replaced by attempt 6 of the same cell. Its live transfer count is absent because the read failed. The assurance sweep found 0 transfers for it, and it stays VOID.

Checks 1a and 4a on this rail: the reason recorded is stated below the x402 on Stellar table.

### x402 on Stellar (testnet)

| Cell | Kind | K | Attempts | Valid | k | VIOLATED | VOID, by cause | NOT EXERCISED, by cause | Complete |
|---|---|---|---|---|---|---|---|---|---|
| Check 1a, an identical resubmission through the seller | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 1b, an identical resubmission direct to the network | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 3, a fresh signature inside the validity window | descriptive observation | 10 | 10 | 10 | 10 observed yes, 0 observed no | 0 | 0 | 0 | complete |
| Check 4a, a late artefact through the seller | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 4b, a late artefact direct to the network | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 5a, a duplicate nonce | network-enforcement detector | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6a, the client drops after sending | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6b, the facilitator drops before broadcast | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6c, the drop after broadcast | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 6d, the facilitator pauses past the seller's timeout | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |
| Check 7, a settlement outcome after a settle that cannot succeed | library or service behaviour | 10 | 10 | 10 | 10 HELD | 0 | 0 | 0 | complete |

### Checks 1a and 4a on x402 on Solana and x402 on Stellar: the reason recorded

On these two rails the pinned facilitator's answer names no mechanism. The recorded reason for a seller refusal in checks 1a and 4a is therefore that answer followed by the company's facilitator's own verify message, which is the network's simulation error as transcribed by the company's facilitator. In both blocks on both rails, the matching below-seller cell (1b beside 1a, 4b beside 4a) recorded the network's own reason naming the same mechanism.

## 4. Check 3 beside each rail's documented statement

Check 3 counts one observable event, SECOND SETTLED: whether a second payment, made against one challenge inside the validity window with a fresh signature, also settled. None of the five documents rules out either answer, so this check can produce no divergence. Where the second payment settled, the company's seller also served the resource twice.

| Rail | Second settled | Documented statement (registration, section 4.3) |
|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | 0 of 10 | "Each BOLT11 invoice MUST use a freshly generated random payment hash."; the operator: "Do not create a second payment just because the first call threw" |
| Machine Payments Protocol on Tempo (Moderato testnet) | 10 of 10 | "Validity windows limit temporal replay windows"; neither draft addresses a fresh signature inside one challenge |
| x402 on Base (Sepolia) | 10 of 10 | the payment-identifier extension is optional; the check runs without it |
| x402 on Solana (devnet, Alpenglow) | 10 of 10 | "If the initial blockhash is still valid, it is possible for both transactions to be accepted by the network." |
| x402 on Stellar (testnet) | 10 of 10 | the payment-identifier extension is optional; the check runs without it |

Every result in this table rests on the company's own seller (registration, section 7.6); the three x402 results also rest on the company's own facilitator, as the paragraph below states.

Machine Payments Protocol on Lightning: its evidence limit is stated below its table in section 3 above.

On x402 on Base, x402 on Solana and x402 on Stellar, each payment of the pair passes through the company's own facilitator, which settles any valid fresh authorization by design. The check therefore measures the rail stack as the company runs it, not a third-party facilitator. The check performs a different action on each rail (registration, section 4.3), so a different answer on one rail is not a difference in safety between rails.

Check 2b on Machine Payments Protocol on Lightning is the other descriptive cell. It retried a completed payment with the same transfer identifier, and a second transfer was observed in 0 of 10 repetitions.

Machine Payments Protocol on Lightning: its evidence limit is stated below its table in section 3 above.

## 5. Check 6: both outcomes

A V6 void is a repetition voided because the check's action has no recorded response (registration, section 5.3).

| Rail | Cell | Safety | Recovery | Recovery cost (the harness's re-payment) | Paid, resource not obtained | Sweep not read | V6 voids in which the payment settled |
|---|---|---|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | 6a | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| Machine Payments Protocol on Tempo (Moderato testnet) | 6a | 20 HELD of 20 | 20 terminal settled; resource obtained | re-paid in 20 of 20, one transfer each | 0 | 0 | 0 |
| Machine Payments Protocol on Tempo (Moderato testnet) | 6c | 20 HELD of 20 | 20 terminal settled; resource obtained | re-paid in 20 of 20, one transfer each | 0 | 0 | 0 |
| x402 on Base (Sepolia) | 6a | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Base (Sepolia) | 6b | 10 HELD of 10 | 10 terminal dead; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Base (Sepolia) | 6c | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Base (Sepolia) | 6d | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Solana (devnet, Alpenglow) | 6a | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Solana (devnet, Alpenglow) | 6b | 10 HELD of 10 | 10 terminal dead; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Solana (devnet, Alpenglow) | 6c | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Solana (devnet, Alpenglow) | 6d | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Stellar (testnet) | 6a | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Stellar (testnet) | 6b | 10 HELD of 10 | 10 terminal dead; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Stellar (testnet) | 6c | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |
| x402 on Stellar (testnet) | 6d | 10 HELD of 10 | 10 terminal settled; resource obtained | re-paid in 10 of 10, one transfer each | 0 | 0 | 0 |

Every result in this table rests on the company's own seller; on the three x402 rails every payment also passes through the company's own facilitator, into which faults 6b, 6c and 6d are injected, and on Machine Payments Protocol on Tempo the fault of check 6c is injected in the company's own seller (registration, sections 4.6 and 7.6).

Machine Payments Protocol on Lightning: its evidence limit is stated below its table in section 3 above.

A check 6 safety HELD says only this: no more than one transfer bound to the original artefact's identifier moved value, and no terminal state read was later contradicted. It does not say which component kept a second transfer from moving (registration, section 9.5). The recovery cost is reported beside the recovery outcome and never counts toward safety.

## 6. Recorded invariants (registration, section 4.10)

| Rail | Invariant | Records | Hold | Do not hold |
|---|---|---|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | the core draft: 402 with a fresh challenge and a problem type on verification failure | 20 | 20 | 0 |
| Machine Payments Protocol on Lightning (Spark regtest) | a fresh payment hash per invoice | 60 | 60 | 0 |
| Machine Payments Protocol on Tempo (Moderato testnet) | the core draft: 402 with a fresh challenge and a problem type on verification failure | 20 | 20 | 0 |
| Machine Payments Protocol on Tempo (Moderato testnet) | validBefore no later than the challenge expires (tests the company's own client, not the network) | 110 | 110 | 0 |
| x402 on Stellar (testnet) | the expiration ledger within the scheme cap (tests the company's own client and the pinned scheme library, not the network; the pinned facilitator tolerates the cap plus 2 ledgers) | 110 | 110 | 0 |

The registration's section 4.10 defines the core-draft count over both Machine Payments Protocol rails together; this table gives it per rail, by applying the same counting rule to each rail's records separately (section 9 below, item 7).

What each row counts:
- The core draft, on each Machine Payments Protocol rail: every presentation the company's seller refused at verification, which are the second presentation of check 2a and the late presentation of check 4a, 10 attempts each.
- A fresh payment hash per invoice: the invoice payment hash recorded by each of the rail's 60 attempts.
- validBefore on Machine Payments Protocol on Tempo: every attempt whose transaction carries a validBefore, which is 110 of the rail's 120 attempts, the 20 NOT EXERCISED attempts of check 2b included. The 10 attempts of check 5a are not counted: that check uses a nonce lane in which the transaction carries no validBefore.
- The expiration ledger on x402 on Stellar: the subject authorization entry of each of the rail's 110 attempts.

Machine Payments Protocol on Lightning: its evidence limit is stated below its table in section 3 above.

## 7. Assurance sweep (registration, section 5.4)

Every block was re-read no sooner than two hours after its end. The times are from the sweep's log, to the second (UTC).

| Rail | Re-read |
|---|---|
| Machine Payments Protocol on Lightning (Spark regtest) | 10:42:15 to 10:42:44 |
| Machine Payments Protocol on Tempo (Moderato testnet) | 10:39:04 to 10:42:03 |
| x402 on Base (Sepolia) | 10:28:28 to 10:34:46 |
| x402 on Solana (devnet, Alpenglow) | 10:35:37 to 10:39:04 |
| x402 on Stellar (testnet) | 10:34:46 to 10:35:37 |

Every attempt on every rail had a sweep row; no re-read failed; no repetition was reclassified or annotated; live and sweep transfer counts were equal for every attempt with a live count; the one attempt without one is the VOID attempt on x402 on Solana in section 3 above, whose sweep count is 0.

## 8. Software versions reported by the endpoints

Void V5 compares the version an endpoint reports at a repetition's start with the version at its end. On every rail where V5 applies, no repetition recorded a change, so V5 fired 0 times.

On four rails, the versions reported throughout the run differ from those read on 2026-10-30 and entered in the registration's section 16.6:

| Rail | Registration (read 2026-10-30) | This run |
|---|---|---|
| Machine Payments Protocol on Tempo (Moderato testnet) | tempo/v1.17.0-55a96ba/x86_64-unknown-linux-gnu | tempo/v1.18.3-5c71a4c/x86_64-unknown-linux-gnu (every record) |
| x402 on Base (Sepolia) | reth/v2.5.2-7134be3/x86_64-unknown-linux-gnu/base/v1.5.0 | reth/v2.5.2-9e380dd/x86_64-unknown-linux-gnu/base/v1.5.4 (every record) |
| x402 on Solana (devnet, Alpenglow) | solana-core 4.4.0-beta.1, feature-set 3993424257 | solana-core 4.4.0, feature-set 2681577653 (every record that carries a read) |
| x402 on Stellar (testnet) | Horizon 30.0.0 | horizon_version 30.0.1, core_version stellar-core 30.0.0 (every record) |

Network software is not under the company's control: the registration recorded these versions as read, it did not pin them, and void V5 controls only a change within a repetition.

On x402 on Solana, two records lack one version read:
- Block 2, check 4b, attempt 4 has no end read. It is the VOID attempt above.
- Block 2, check 1b, attempt 5 has no start read. Under the frozen rule, V5 fires only when both reads exist and differ, so this attempt is HELD; whether the version changed during it cannot be decided from its record.

## 9. Limits

The places where the company's instrument or the run departed from the registration, each with its effect; each is recorded in Addendum 1 to the registration [ADDENDUM 1 CITATION: its tag, DOI and anchors are entered here once it is signed and anchored]:

1. The company's instrument read the seed with one request per source and no retry. The registration's retry rule (section 5.2) covers reads of each rail's settlement and death evidence, not the seed read, so the instrument matched the registered text; it nevertheless let a single HTTP 502 answer from one source stop the start of two rails (section 2 above). This is a fault in the company's instrument, not in any network or source. Its effect is the late start of those two rails described in section 2 above; no outcome depends on it.
2. The registration's section 6.1 names the scorer's fingerprint from before the freeze preparation (bfd23d11a912d6a4935625136f3e59000c1276feb33643be30d232523b878c5d), in the same paragraph that records its change; section 16.5 names the frozen value (52f53699f0b958699680efb39eea61c4289a7879b260b2d5f3370e0478e1a3c9), which is the value this run's scorer and K table carry. The scorer that produced every count is the frozen one, so no outcome is affected.
3. The frozen report tool, given the frozen K table file, read every cell's K as 10 and did not check the scorer's fingerprint, because the file holds the table one level below where the tool reads; the counts in this report come from the same frozen tool given that table directly, which applies K = 20 to checks 6a and 6c on Machine Payments Protocol on Tempo and checks the fingerprint (it matches). No cell's completeness differs between the two.
4. The report tool's evidence-limit text for Machine Payments Protocol on Lightning cites the registration's section 12 for two exploratory balance movements, of which that section carries only the first; this report states that limit in its own words (section 3 above), and no count is affected.
5. The run's records and the frozen report tool label five cells "library or service behaviour" that the registration's section 4.9 names network-enforcement detectors: checks 6a and 6c on Machine Payments Protocol on Tempo, and check 1a on x402 on Base, x402 on Solana and x402 on Stellar. The kind decides no outcome; this report gives the registration's kind.
6. The report tool gives the cause of the 20 NOT EXERCISED attempts of check 2b on Machine Payments Protocol on Tempo as a refusal reason that "does not name the replay mechanism"; this report words that cause from the registration's section 5.6, as a refusal text not among the registration's reason entries, and the count is unchanged.
7. The registration's section 4.10 defines the core-draft invariant count over both Machine Payments Protocol rails together; this report gives it per rail, by the same counting rule applied to each rail's records separately, because the registration's section 10 admits no statistic that combines rails; no count other than that split is affected.

The evidence limit of Machine Payments Protocol on Lightning is stated beside its results in section 3 above.

## 10. What this run does not say

- No rail is ranked, and no recommendation is made. No rail is compared with another.
- It states no latency figure. The test-network settlement finality of the same five rails on the same test networks is the subject of a separate registered run (https://doi.org/10.17605/OSF.IO/UETFW).
- It says nothing about any mainnet, any production facilitator or any production service.
- It states no rate or frequency of any event.
- It says nothing about GCP with AP2, which settles nothing and is measured by no check.
- No result is claimed to have been fixed before any run. The claim is that the design was frozen and anchored after the declared exploratory runs and before the confirmatory run or any publication. The places where the company's instrument or the run departed from the registered design are listed in section 9 above and recorded in Addendum 1 to the registration [ADDENDUM 1 CITATION: its tag, DOI and anchors are entered here once it is signed and anchored].
- The mapping of these cells to the cells of the Half A structural profile is made after this report (registration, section 10); this report states only, where the registration requires it, that a cell moves no label.

## 11. Corrections and right of reply

Any operator of a rail or facilitator named on this page may respond through the structured right-of-reply channel at https://reply.agentic-paybench.dev/. Replies about a factual data error, a methodology defect, a mischaracterisation, a confidentiality objection, or a jurisdictional objection are reviewed before publication; replies about methodology framing, a change since the measurement window, or the scope of the environment tested are published promptly with a badge saying the review is pending. The response cap and visibility policy is linked from that page. Corrections to anything here are also welcome by email at mblake@everydayai.link.
