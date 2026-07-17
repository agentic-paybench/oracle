// Verify every enveloped VC-JOSE credential in docs/site/capabilities against
// the published DID document's P-256 public key. Used by CI. Exits non-zero
// on any failure.

import { jwtVerify, importJWK } from 'jose';
import { readdir, readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const OUT = resolve(REPO, 'docs', 'site', 'capabilities');
const DID_DOC = resolve(REPO, 'docs', 'site', '.well-known', 'did.json');

const didDoc = JSON.parse(await readFile(DID_DOC, 'utf8'));
const pubJwk = didDoc.verificationMethod[0].publicKeyJwk;
if (pubJwk.crv !== 'P-256') {
  console.error('FAIL: DID key is not P-256:', pubJwk.crv);
  process.exit(1);
}
const key = await importJWK(pubJwk, 'ES256');

const files = (await readdir(OUT)).filter((f) => f.endsWith('.vc.json')).sort();
let ok = 0;
for (const f of files) {
  const env = JSON.parse(await readFile(resolve(OUT, f), 'utf8'));
  const jwt = env.id.replace(/^data:application\/vc\+jwt,/, '');
  const { protectedHeader } = await jwtVerify(jwt, key);
  if (protectedHeader.alg !== 'ES256') {
    console.error(`FAIL ${f}: alg ${protectedHeader.alg} != ES256`);
    process.exit(1);
  }
  ok++;
}
console.log(`verify: ${ok} enveloped VC-JOSE credentials OK (ES256/P-256)`);
