// Generate the Day-0 DEV ECDSA P-256 signing key (ES256) and publish the DID
// document (public key only). The private JWK is written to .dev-keys/ which is
// gitignored and NEVER committed. Rotate to a hardware PIV P-256 key at the
// maintainer key ceremony (same curve = key rotation, not rework).
//
// AP2 v0.2 mandates P-256 and forbids Ed25519; this signer only ever uses ES256.

import { generateKeyPair, exportJWK, base64url } from 'jose';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const DEV_KEYS = resolve(HERE, '.dev-keys');
const DID_DOC = resolve(REPO, 'docs', 'site', '.well-known', 'did.json');

const { publicKey, privateKey } = await generateKeyPair('ES256', { extractable: true });
const pubJwk = await exportJWK(publicKey);   // { kty, crv, x, y }
const privJwk = await exportJWK(privateKey); // includes d

// did:jwk is self-contained: no domain needed for a dev key.
const did = 'did:jwk:' + base64url.encode(JSON.stringify(pubJwk));
const vmId = did + '#0';

const didDocument = {
  '@context': [
    'https://www.w3.org/ns/did/v1',
    'https://w3id.org/security/suites/jws-2020/v1'
  ],
  id: did,
  verificationMethod: [
    { id: vmId, type: 'JsonWebKey2020', controller: did, publicKeyJwk: pubJwk }
  ],
  assertionMethod: [vmId],
  'x-alg': 'ES256',
  'x-note': 'DEV key (non-production). Rotate to hardware PIV P-256 at the maintainer key ceremony.'
};

await mkdir(dirname(DID_DOC), { recursive: true });
await writeFile(DID_DOC, JSON.stringify(didDocument, null, 2) + '\n');

await mkdir(DEV_KEYS, { recursive: true });
await writeFile(
  resolve(DEV_KEYS, 'dev-p256.private.jwk'),
  JSON.stringify({ ...privJwk, kid: vmId, alg: 'ES256' }, null, 2) + '\n',
  { mode: 0o600 }
);
await writeFile(resolve(DEV_KEYS, 'issuer.did'), did + '\n');

console.log('keygen: dev P-256 (ES256) key generated');
console.log('  issuer DID :', did.slice(0, 32) + '...');
console.log('  DID doc    :', DID_DOC);
console.log('  private key:', resolve(DEV_KEYS, 'dev-p256.private.jwk'), '(gitignored, dev only)');
