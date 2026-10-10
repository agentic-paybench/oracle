<!-- posture-class: level1-documentation-profile -->

# Tier-2 documented facts: the statements every served cell carries

Every Tier-2 capability credential on this site that carries a documented structural cell also carries a `notice` object inside its signed subject. The notice repeats the statements below verbatim, names its profile class in a machine-readable `kind` field, and points to this page. This page is the full statement; the notice is its copy in each response.

## Documentation profile (`kind`: `documentation_profile`)

This is a documentation profile, not a recommendation: every cell states what a specification or an operator's own documentation says, no number in this document was produced by executing a payment, no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use.

Every documentation-derived cell cites the primary source it rests on, by URL, with the date it was retrieved.

Rails are listed alphabetically by rail name. That ordering is fixed and carries no performance meaning.

The same thirteen questions were put to all six rails, in the same fixed order, against each rail's own primary documentation: twelve on a single date (2026-10-09) and the thirteenth, offline verifiability, on a single later date (2026-10-10).

## Fee-adjacent cells (`kind`: `fee_quotation`)

The fee fields and the fee-bearer cell (who pays the network fee for a payment) carry these statements as well:

These fee facts are a quotation of published fee documentation, not a recommendation: no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use.

Each fee fact is quoted from the rail's own published fee documentation at the source URL given beside it, retrieved on 2026-10-09.

Every rail's fee facts are quoted from that rail's own published fee documentation, retrieved on the same date by the same procedure.

## How to read a cell

Each cell carries a value, a disposition, a short statement and a provenance object.

- **Provenance label**, from a fixed set of three: documentation-derived, measured, void. No Tier-2 cell carries the label measured.
- **Disposition**, reported separately from the label: positive (a primary source states the property); confirmed absence (a primary source on the subject was read and does not define the property, which is a finding about that source, not a gap in the reading); partial absence (one half of the question is stated and the other is not); void (the property cannot be established either way from the documents read).
- **Profile**, in each cell's provenance: `documentation_profile` or `fee_quotation`, so a cell read on its own still names the statements that govern it.
- **Sources**: every URL the cell rests on, each with its retrieval date, including documents read that did not answer the question.

The record shape is defined by the schema at <https://oracle.agentic-paybench.dev/schema/capability.schema.json>, which pins the statements above byte for byte. Nothing on this page or in any Tier-2 cell is a measurement, and nothing here is a route to transact.
