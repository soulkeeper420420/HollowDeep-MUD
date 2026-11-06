import { createHmac, createPublicKey, timingSafeEqual, verify } from 'node:crypto';

const IAC = 255, DONT = 254, DO = 253, WONT = 252, WILL = 251, SB = 250, SE = 240;
const ECHO = 1, SGA = 3;

/** Incremental Telnet parser. Preserve game text/ANSI, consume protocol commands. */
export class TelnetDecoder {
  constructor({ output, reply, echo }) {
    this.output = output;
    this.reply = reply;
    this.echo = echo;
    this.mode = 'data';
    this.command = 0;
    this.remoteOptions = new Set();
    this.localOptions = new Set();
  }
  push(chunk) {
    const text = [];
    const flush = () => { if (text.length) { this.output(Buffer.from(text)); text.length = 0; } };
    for (const byte of chunk) {
      if (this.mode === 'data') {
        if (byte === IAC) { flush(); this.mode = 'iac'; }
        else if (byte !== 0) text.push(byte);
      } else if (this.mode === 'iac') {
        if (byte === IAC) { text.push(IAC); this.mode = 'data'; }
        else if ([WILL, WONT, DO, DONT].includes(byte)) { this.command = byte; this.mode = 'option'; }
        else if (byte === SB) this.mode = 'subnegotiation';
        else this.mode = 'data';
      } else if (this.mode === 'option') {
        if (this.command === WILL) {
          if (byte === ECHO || byte === SGA) {
            if (!this.remoteOptions.has(byte)) {
              this.remoteOptions.add(byte);
              if (byte === ECHO) this.echo(false);
              this.reply(Buffer.from([IAC, DO, byte]));
            }
          } else this.reply(Buffer.from([IAC, DONT, byte]));
        } else if (this.command === WONT) {
          if (this.remoteOptions.delete(byte)) {
            if (byte === ECHO) this.echo(true);
            this.reply(Buffer.from([IAC, DONT, byte]));
          }
        } else if (this.command === DO) {
          if (byte === SGA) {
            if (!this.localOptions.has(byte)) {
              this.localOptions.add(byte);
              this.reply(Buffer.from([IAC, WILL, byte]));
            }
          } else this.reply(Buffer.from([IAC, WONT, byte]));
        } else if (this.command === DONT && this.localOptions.delete(byte)) {
          this.reply(Buffer.from([IAC, WONT, byte]));
        }
        this.mode = 'data';
      } else if (this.mode === 'subnegotiation') {
        if (byte === IAC) this.mode = 'subnegotiation-iac';
      } else if (this.mode === 'subnegotiation-iac') {
        this.mode = byte === SE ? 'data' : 'subnegotiation';
      }
    }
    flush();
  }
}

/** Only a public SPKI key is installed on the game host; it cannot mint tickets. */
export function loadTicketPublicKey(encoded) {
  if (typeof encoded !== 'string' || !/^[A-Za-z0-9+/]{59}=$/.test(encoded)) throw new Error('Invalid Ed25519 public key.');
  const der = Buffer.from(encoded, 'base64');
  if (der.length !== 44 || der.toString('base64') !== encoded) throw new Error('Invalid Ed25519 public key.');
  const key = createPublicKey({ key:der, format:'der', type:'spki' });
  if (key.asymmetricKeyType !== 'ed25519') throw new Error('The bridge requires an Ed25519 public key.');
  return key;
}

/** Verify a signed ticket. Configuration chooses the algorithm; no key fallback. */
export function verifyTicket(ticket, key, now = Math.floor(Date.now() / 1000)) {
  if (typeof ticket !== 'string' || ticket.length > 4096 || !Number.isSafeInteger(now)) throw new Error('Invalid session ticket.');
  const parts = ticket.split('.');
  const asymmetric = key && typeof key === 'object' && key.asymmetricKeyType === 'ed25519' && key.type === 'public';
  if (!asymmetric && (typeof key !== 'string' || !key)) throw new Error('Invalid session verification key.');
  const offset = asymmetric ? 1 : 0;
  if (parts.length !== 2 + offset || (asymmetric && parts[0] !== 'ed25519') ||
      parts.some(part => !/^[A-Za-z0-9_-]+$/.test(part))) throw new Error('Invalid session ticket.');
  const payload = Buffer.from(parts[offset], 'base64url');
  const signature = Buffer.from(parts[offset + 1], 'base64url');
  if (payload.toString('base64url') !== parts[offset] || signature.toString('base64url') !== parts[offset + 1]) throw new Error('Invalid session ticket.');
  if (asymmetric) {
    if (signature.length !== 64 || !verify(null, Buffer.from('ed25519.' + parts[1]), key, signature)) throw new Error('Invalid session ticket.');
  } else {
    const expected = createHmac('sha256', key).update(parts[0]).digest();
    if (signature.length !== expected.length || !timingSafeEqual(signature, expected)) throw new Error('Invalid session ticket.');
  }
  let claims;
  try { claims = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(payload)); }
  catch { throw new Error('Invalid session ticket.'); }
  if (!claims || Array.isArray(claims) || typeof claims.sub !== 'string' || !claims.sub.trim() || claims.sub.length > 256 ||
      typeof claims.nonce !== 'string' || !/^[A-Za-z0-9_-]{16,128}$/.test(claims.nonce) ||
      !Number.isSafeInteger(claims.exp) || claims.exp <= now || claims.exp > now + 60 ||
      (asymmetric && claims.aud !== 'hollowdeep-mordor-bridge')) {
    throw new Error('Session ticket has expired or is invalid.');
  }
  return claims;
}

export function validateInput(message) {
  let value;
  try { value = JSON.parse(message); } catch { throw new Error('Send a JSON command.'); }
  if (!value || value.type !== 'input' || typeof value.data !== 'string') throw new Error('Invalid command.');
  if (Buffer.byteLength(value.data, 'utf8') > 256 || /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/u.test(value.data) || !value.data.isWellFormed()) {
    throw new Error('Commands must be one line, up to 256 bytes.');
  }
  return value.data;
}
