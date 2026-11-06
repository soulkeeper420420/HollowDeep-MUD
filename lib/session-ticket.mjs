/** Web Crypto only: compatible with the Site's Cloudflare Worker runtime. */
const encode = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const encoder = new TextEncoder();

function privateKeyBytes(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9+/]{64}$/.test(value)) throw new Error('Invalid ticket signing configuration.');
  const bytes = Uint8Array.from(atob(value), byte => byte.charCodeAt(0));
  if (bytes.length !== 48 || btoa(String.fromCharCode(...bytes)) !== value) throw new Error('Invalid ticket signing configuration.');
  return bytes;
}

export async function createSessionTicket({ userId, privateKeyPkcs8, secret }, cryptoApi = globalThis.crypto, now = Math.floor(Date.now() / 1000)) {
  if (typeof userId !== 'string' || !userId.trim() || userId.length > 256 || !Number.isSafeInteger(now)) throw new Error('Authenticated user required.');
  if (privateKeyPkcs8 && secret) throw new Error('Configure exactly one signing method.');
  const claims = { sub:userId, exp:now + 60, nonce:cryptoApi.randomUUID() };
  if (privateKeyPkcs8) {
    claims.aud = 'hollowdeep-mordor-bridge';
    const payload = encode(encoder.encode(JSON.stringify(claims)));
    const key = await cryptoApi.subtle.importKey('pkcs8', privateKeyBytes(privateKeyPkcs8), { name:'Ed25519' }, false, ['sign']);
    const signed = 'ed25519.' + payload;
    const signature = encode(new Uint8Array(await cryptoApi.subtle.sign('Ed25519', key, encoder.encode(signed))));
    return `${signed}.${signature}`;
  }
  if (typeof secret !== 'string' || encoder.encode(secret).length < 32) throw new Error('Invalid ticket signing configuration.');
  const payload = encode(encoder.encode(JSON.stringify(claims)));
  const key = await cryptoApi.subtle.importKey('raw', encoder.encode(secret), { name:'HMAC', hash:'SHA-256' }, false, ['sign']);
  const signature = encode(new Uint8Array(await cryptoApi.subtle.sign('HMAC', key, encoder.encode(payload))));
  return `${payload}.${signature}`;
}
