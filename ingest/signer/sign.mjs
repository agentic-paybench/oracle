// Envelope each unsigned capability VC as a VCDM 2.0 Enveloped Verifiable
// Credential secured with VC-JOSE (ES256 / P-256), using the dev key. Reads
// ingest/build/capabilities/*.vc.json, writes docs/site/capabilities/*.vc.json
// plus capabilities/index.json.

import { SignJWT, importJWK } from 'jose';
import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const BUILD = resolve(REPO, 'ingest', 'build', 'capabilities');
const OUT = resolve(REPO, 'docs', 'site', 'capabilities');
const DEV_KEYS = resolve(HERE, '.dev-keys');

const privJwk = JSON.parse(await readFile(resolve(DEV_KEYS, 'dev-p256.private.jwk'), 'utf8'));
const did = (await readFile(resolve(DEV_KEYS, 'issuer.did'), 'utf8')).trim();
const kid = did + '#0';
const key = await importJWK(privJwk, 'ES256');

await mkdir(OUT, { recursive: true });
const files = (await readdir(BUILD)).filter((f) => f.endsWith('.vc.json')).sort();

const index = { issuer: did, alg: 'ES256', validFrom: '2026-07-17T00:00:00Z',
  note: 'dev-key signed (ES256/P-256), non-production', rails: [] };

for (const f of files) {
  const vc = JSON.parse(await readFile(resolve(BUILD, f), 'utf8'));
  vc.issuer = did; // stamp the real issuer

  const jwt = await new SignJWT(vc)
    .setProtectedHeader({ alg: 'ES256', typ: 'vc+jwt', cty: 'vc', kid })
    .sign(key);

  const enveloped = {
    '@context': 'https://www.w3.org/ns/credentials/v2',
    id: 'data:application/vc+jwt,' + jwt,
    type: 'EnvelopedVerifiableCredential'
  };

  const railId = basename(f, '.vc.json');
  await writeFile(resolve(OUT, f), JSON.stringify(enveloped, null, 2) + '\n');
  const subj = vc.credentialSubject;
  const entry = { railId, railName: subj.railName, vc: `capabilities/${f}` };
  if (subj.displayName) entry.displayName = subj.displayName;
  // Tier-2 widening: the index is itself a served response, so
  // it carries the same notice the credentials carry, unsigned here but
  // byte-identical to the signed copy inside each credential.
  if (subj.notice && !index.notice) index.notice = subj.notice;
  index.rails.push(entry);
}

// Fixed ordering: alphabetical by pinned display name where one exists (the
// notice's fixedOrderingStatement), else by railName. The order carries no
// performance meaning.
const sortKey = (r) => (r.displayName || r.railName).toLowerCase();
index.rails.sort((a, b) => (sortKey(a) < sortKey(b) ? -1 : sortKey(a) > sortKey(b) ? 1 : 0));

await writeFile(resolve(OUT, 'index.json'), JSON.stringify(index, null, 2) + '\n');
console.log(`signed ${files.length} enveloped VC-JOSE credentials -> ${OUT}`);
