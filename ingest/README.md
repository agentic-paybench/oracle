# ingest

Builds the served capability records: `build_capabilities.py` renders
`data/rail-facts.json` through the schema into signed VC files under
`docs/site/capabilities/`. `signer/` holds the offline dev-key VC signer
(ES256; non-production key, see its README).
