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
  index.rails.push({ railId, railName: vc.credentialSubject.railName, vc: `capabilities/${f}` });
}

await writeFile(resolve(OUT, 'index.json'), JSON.stringify(index, null, 2) + '\n');
console.log(`signed ${files.length} enveloped VC-JOSE credentials -> ${OUT}`);
