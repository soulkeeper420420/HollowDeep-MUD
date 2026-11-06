import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { TelnetDecoder, verifyTicket, validateInput } from '../protocol.mjs';

const IAC = 255, WILL = 251, WONT = 252, DO = 253, DONT = 254, SB = 250, SE = 240;
function parse(chunks) {
  const output = [], replies = [], echo = [], events = [];
  const decoder = new TelnetDecoder({
    output: buffer => { output.push(buffer); events.push(['text', buffer.toString('latin1')]); },
    reply: buffer => replies.push([...buffer]),
    echo: enabled => { echo.push(enabled); events.push(['echo', enabled]); },
  });
  for (const chunk of chunks) decoder.push(chunk);
  return { output:Buffer.concat(output), replies, echo, events };
}
const sequence = (...parts) => Buffer.concat(parts.map(part => typeof part === 'string' ? Buffer.from(part) : Buffer.from(part)));

test('Telnet parsing is invariant at every packet split and byte-by-byte', () => {
  const input = sequence('Welcome\x1b[31mred\x1b[0m\r\0', [IAC,WILL,1], 'Password: ',
    [IAC,WONT,1,IAC,SB,24,1,2,IAC,IAC,SE,IAC,SE], 'Done\r\n', [IAC,IAC]);
  const expected = sequence('Welcome\x1b[31mred\x1b[0m\rPassword: Done\r\n', [IAC]);
  for (let split = 0; split <= input.length; split++) {
    const result = parse([input.subarray(0,split),input.subarray(split)]);
    assert.deepEqual(result.output, expected, `output at split ${split}`);
    assert.deepEqual(result.replies, [[IAC,DO,1],[IAC,DONT,1]]);
    assert.deepEqual(result.echo, [false,true]);
  }
  assert.deepEqual(parse([...input].map(byte=>Buffer.from([byte]))).output, expected);
});

test('password echo events are delivered before the associated prompt text', () => {
  const { events } = parse([sequence('Login: ',[IAC,WILL,1],'Password: ',[IAC,WONT,1],'Welcome')]);
  assert.deepEqual(events, [
    ['text','Login: '], ['echo',false], ['text','Password: '], ['echo',true], ['text','Welcome'],
  ]);
});

test('accepted Telnet options settle without reply loops and can be renegotiated', () => {
  const result = parse([Buffer.from([
    IAC,WILL,1,IAC,WILL,1,IAC,WONT,1,IAC,WONT,1,IAC,WILL,1,
    IAC,DO,3,IAC,DO,3,IAC,DONT,3,IAC,DONT,3,IAC,DO,3,
    IAC,WILL,3,IAC,WILL,3,IAC,WONT,3,
  ])]);
  assert.deepEqual(result.echo, [false,true,false]);
  assert.deepEqual(result.replies, [
    [IAC,DO,1],[IAC,DONT,1],[IAC,DO,1],
    [IAC,WILL,3],[IAC,WONT,3],[IAC,WILL,3],
    [IAC,DO,3],[IAC,DONT,3],
  ]);
});

test('unsupported options, standalone commands and subnegotiations do not leak into game output', () => {
  const result = parse([sequence('before',[IAC,WILL,24,IAC,DO,31,IAC,DO,1,IAC,241,IAC,249],
    [IAC,SB,31,0,80,0,24,IAC,SE], 'after')]);
  assert.equal(result.output.toString(),'beforeafter');
  assert.deepEqual(result.replies,[[IAC,DONT,24],[IAC,WONT,31],[IAC,WONT,1]]);
  assert.deepEqual(result.echo,[]);
});

const secret = 'test-secret-with-at-least-32-bytes';
const claims = {sub:'site-user',exp:1060,nonce:'unpredictable-unique-nonce'};
const signBody = body => body + '.' + createHmac('sha256',secret).update(body).digest('base64url');
const sign = payload => signBody(Buffer.from(JSON.stringify(payload)).toString('base64url'));

test('a signed ticket is usable before expiry, including the 60-second lifetime boundary', () => {
  assert.deepEqual(verifyTicket(sign(claims),secret,1000),claims);
  assert.deepEqual(verifyTicket(sign(claims),secret,1059),claims);
  assert.throws(()=>verifyTicket(sign(claims),secret,1060));
  assert.throws(()=>verifyTicket(sign({...claims,exp:1061}),secret,1000));
  assert.throws(()=>verifyTicket(sign({...claims,exp:999}),secret,1000));
});

test('tickets reject tampering, wrong keys, malformed encodings and oversized bodies', () => {
  const ticket = sign(claims);
  const [body,signature] = ticket.split('.');
  assert.throws(()=>verifyTicket(ticket,'wrong-secret',1000));
  assert.throws(()=>verifyTicket(Buffer.from(JSON.stringify({...claims,sub:'another-user'})).toString('base64url')+'.'+signature,secret,1000));
  for (const invalid of ['', body, `${ticket}.more`,`${body}=.${signature}`,`${body}.${signature}=`,`${body}.AA`, 'a'.repeat(4097), null, {}]) {
    assert.throws(()=>verifyTicket(invalid,secret,1000));
  }
  assert.throws(()=>verifyTicket(ticket,'',1000));
  assert.throws(()=>verifyTicket(ticket,secret,NaN));
});

test('tickets reject alternate base64url spellings of an otherwise valid signature or payload', () => {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  const [body,signature] = sign(claims).split('.');
  const last = alphabet.indexOf(signature.at(-1));
  const alias = signature.slice(0,-1)+alphabet[last+1];
  assert.deepEqual(Buffer.from(alias,'base64url'),Buffer.from(signature,'base64url'));
  assert.throws(()=>verifyTicket(`${body}.${alias}`,secret,1000));
  let payload = {...claims};
  let encoded = Buffer.from(JSON.stringify(payload)).toString('base64url');
  while (encoded.length % 4 === 0) { payload.extra = (payload.extra || '')+'x'; encoded = Buffer.from(JSON.stringify(payload)).toString('base64url'); }
  const payloadAlias = encoded.slice(0,-1)+alphabet[alphabet.indexOf(encoded.at(-1))+1];
  assert.deepEqual(Buffer.from(payloadAlias,'base64url'),Buffer.from(encoded,'base64url'));
  assert.throws(()=>verifyTicket(signBody(payloadAlias),secret,1000));
});

test('tickets reject invalid claims and signed non-UTF8 JSON', () => {
  for (const payload of [null, [], 'user', {...claims,sub:''}, {...claims,sub:'   '}, {...claims,sub:'x'.repeat(257)},
    {...claims,nonce:'short'}, {...claims,nonce:'x'.repeat(129)}, {...claims,nonce:'bad nonce value here'},
    {...claims,exp:'1060'}, {...claims,exp:1000.5}, {...claims,exp:Number.MAX_SAFE_INTEGER+1}]) {
    assert.throws(()=>verifyTicket(sign(payload),secret,1000));
  }
  const badUtf8 = Buffer.concat([Buffer.from('{"sub":"'),Buffer.from([0xff]),Buffer.from('","exp":1060,"nonce":"unique-nonce-value"}')]);
  assert.throws(()=>verifyTicket(signBody(badUtf8.toString('base64url')),secret,1000));
});

const input = data => JSON.stringify({type:'input',data});
test('commands preserve text, intentional whitespace and empty prompt responses', () => {
  for (const command of ['say Hello, traveler!', '', '  keep these spaces  ', 'look', 'é'.repeat(128), '⚔'.repeat(85)]) {
    assert.equal(validateInput(input(command)),command);
  }
  assert.equal(validateInput(input('x'.repeat(256))).length,256);
});

test('commands enforce UTF8 byte length and reject multiline, control and malformed Unicode input', () => {
  for (const data of ['north\nsouth','look\r\nquit','\x1b[31mlook','x'.repeat(257),'é'.repeat(129),'⚔'.repeat(86),'bad\ud800','\udc00']) {
    assert.throws(()=>validateInput(input(data)));
  }
  for (let code = 0; code <= 0x1f; code++) assert.throws(()=>validateInput(input(String.fromCharCode(code))));
  for (let code = 0x7f; code <= 0x9f; code++) assert.throws(()=>validateInput(input(String.fromCharCode(code))));
  for (const code of [0x2028,0x2029]) assert.throws(()=>validateInput(input(String.fromCharCode(code))));
});

test('commands reject malformed JSON and unexpected protocol shapes', () => {
  for (const message of ['{bad','null','[]','"look"','42',JSON.stringify({type:'admin',data:'look'}),JSON.stringify({type:'input',data:42}),JSON.stringify({type:'input'})]) {
    assert.throws(()=>validateInput(message));
  }
});
