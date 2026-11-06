import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync, sign, webcrypto } from 'node:crypto';
import { createSessionTicket } from '../../lib/session-ticket.mjs';
import { loadTicketPublicKey, verifyTicket } from '../protocol.mjs';

const pair = generateKeyPairSync('ed25519');
const privateKeyPkcs8 = pair.privateKey.export({ format:'der', type:'pkcs8' }).toString('base64');
const publicKeySpki = pair.publicKey.export({ format:'der', type:'spki' }).toString('base64');
const key = loadTicketPublicKey(publicKeySpki);
const cryptoApi = { subtle:webcrypto.subtle, randomUUID:() => 'b9734807-b5e2-4be9-b613-79ff900a6022' };

test('Worker WebCrypto ticket verifies with only the host public key', async () => {
  const ticket = await createSessionTicket({ userId:'player-id', privateKeyPkcs8 }, cryptoApi, 1000);
  assert.match(ticket, /^ed25519\./);
  assert.deepEqual(verifyTicket(ticket, key, 1000), {
    sub:'player-id', exp:1060, nonce:cryptoApi.randomUUID(), aud:'hollowdeep-mordor-bridge',
  });
  assert.throws(() => verifyTicket(ticket, key, 1060));
});

test('algorithm selection cannot fall back from public key to HMAC', async () => {
  const secret = 'legacy-test-secret-at-least-32-bytes';
  const asymmetric = await createSessionTicket({ userId:'player-id', privateKeyPkcs8 }, cryptoApi, 1000);
  const legacy = await createSessionTicket({ userId:'player-id', secret }, cryptoApi, 1000);
  assert.throws(() => verifyTicket(asymmetric, secret, 1000));
  assert.throws(() => verifyTicket(legacy, key, 1000));
  assert.equal(verifyTicket(legacy, secret, 1000).sub, 'player-id');
  await assert.rejects(createSessionTicket({ userId:'player-id', privateKeyPkcs8, secret }, cryptoApi, 1000));
});

test('wrong key, altered claims, malformed signatures and prefixes are rejected', async () => {
  const ticket = await createSessionTicket({ userId:'player-id', privateKeyPkcs8 }, cryptoApi, 1000);
  const wrong = generateKeyPairSync('ed25519').publicKey;
  assert.throws(() => verifyTicket(ticket, wrong, 1000));
  const [prefix, body, signature] = ticket.split('.');
  const altered = Buffer.from(JSON.stringify({ ...JSON.parse(Buffer.from(body, 'base64url')), sub:'owner' })).toString('base64url');
  for (const invalid of [`${prefix}.${altered}.${signature}`, `rsa.${body}.${signature}`, `${prefix}.${body}.AA`, `${ticket}=`, `${ticket}.extra`]) {
    assert.throws(() => verifyTicket(invalid, key, 1000));
  }
});

test('even a correctly signed ticket must have the expected audience and lifetime', () => {
  for (const claims of [
    { sub:'p', exp:1060, nonce:cryptoApi.randomUUID(), aud:'another-bridge' },
    { sub:'p', exp:1061, nonce:cryptoApi.randomUUID(), aud:'hollowdeep-mordor-bridge' },
    { sub:'p', exp:1060, nonce:'short', aud:'hollowdeep-mordor-bridge' },
  ]) {
    const signed = 'ed25519.' + Buffer.from(JSON.stringify(claims)).toString('base64url');
    const ticket = signed + '.' + sign(null, Buffer.from(signed), pair.privateKey).toString('base64url');
    assert.throws(() => verifyTicket(ticket, key, 1000));
  }
});

test('key import rejects private material, wrong algorithms and malformed base64', () => {
  for (const invalid of [privateKeyPkcs8, publicKeySpki + '=', '', 'x'.repeat(60), null]) {
    assert.throws(() => loadTicketPublicKey(invalid));
  }
});

test('signer rejects missing identity and invalid private configuration', async () => {
  for (const userId of ['', ' ', 'x'.repeat(257), null]) {
    await assert.rejects(createSessionTicket({ userId, privateKeyPkcs8 }, cryptoApi, 1000));
  }
  await assert.rejects(createSessionTicket({ userId:'p', privateKeyPkcs8:publicKeySpki }, cryptoApi, 1000));
  await assert.rejects(createSessionTicket({ userId:'p' }, cryptoApi, 1000));
});
