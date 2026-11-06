import test from 'node:test';
import assert from 'node:assert/strict';
import { emptyProfile, starterProfile, validateProfile, parseProfile, exportProfile, expandTemplate, resolveAlias } from '../lib/command-workshop.mjs';

test('expands arguments and target literally without recursive expansion', () => {
  assert.deepEqual(expandTemplate('tell $1 $*', 'Mira hello $target', 'goblin'), { ok: true, command: 'tell Mira Mira hello $target' });
  assert.equal(expandTemplate('kill $target', '', 'goblin').command, 'kill goblin');
  assert.equal(expandTemplate('say $$1', 'hello').command, 'say $1');
});
test('missing required arguments and target produce actionable errors', () => {
  assert.match(expandTemplate('kill $target').error, /target/);
  assert.match(expandTemplate('tell $1 $2', 'Mira').error, /\$2/);
});
test('rejects command injection in templates, arguments and saved target', () => {
  for (const bad of ['say hi\nquit', 'look\rkill goblin', 'look\u001b', 'look\u2028quit']) {
    assert.equal(expandTemplate(bad).ok, false);
    assert.equal(expandTemplate('say $*', bad).ok, false);
    assert.equal(expandTemplate('look $target', '', bad).ok, false);
  }
});
test('checks expanded UTF-8 size and invalid Unicode', () => {
  assert.equal(expandTemplate('say $*', 'é'.repeat(127)).ok, false);
  assert.equal(expandTemplate('say $*', 'é'.repeat(126)).ok, true);
  assert.equal(expandTemplate('say $*', '\ud800').ok, false);
});
test('rejects malformed or oversized import, unknown fields, and credentials', () => {
  for (const raw of ['not json', 'null', '[]', 'x'.repeat(32769), JSON.stringify({ ...emptyProfile(), password: 'secret' })]) assert.equal(parseProfile(raw).ok, false);
  assert.equal(validateProfile({ ...emptyProfile(), version: 2 }).ok, false);
});
test('rejects duplicate names, excessive steps and saved password commands', () => {
  assert.equal(validateProfile({ ...emptyProfile(), aliases: [{ name: 'x', template: 'look' }, { name: 'x', template: 'who' }] }).ok, false);
  assert.equal(validateProfile({ ...emptyProfile(), macros: [{ name: 'm', steps: Array(13).fill('look') }] }).ok, false);
  assert.equal(validateProfile({ ...emptyProfile(), aliases: [{ name: 'pw', template: 'password secret' }] }).ok, false);
  assert.equal(expandTemplate('$1 $*', 'password secret').ok, false);
});
test('valid profile export round-trips without including history or runtime state', () => {
  const p = starterProfile();
  assert.deepEqual(parseProfile(exportProfile(p).text).profile, p);
  assert.equal(exportProfile({ ...p, history: ['secret'] }).ok, false);
});
test('slash aliases use explicit matching and unknown names are not sent', () => {
  const p = { ...emptyProfile(), target: 'rat', aliases: [{ name: 'hit', template: 'kill $target' }] };
  assert.deepEqual(resolveAlias('/hit', p), { ok: true, command: 'kill rat', expanded: true });
  assert.equal(resolveAlias('/missing', p).ok, false);
  assert.deepEqual(resolveAlias('look', p), { ok: true, command: 'look', expanded: false });
});
test('password-mode input is never interpreted as an alias', () => {
  const secret = '/hit strange $1\n';
  assert.deepEqual(resolveAlias(secret, emptyProfile(), { hidden: true }), { ok: true, command: secret, expanded: false });
});

test('oversized valid-shaped profiles cannot be exported and then fail import', () => {
  const p = emptyProfile();
  p.macros = Array.from({ length: 12 }, (_, i) => ({ name: `macro${i}`, steps: Array(12).fill('say ' + 'a'.repeat(250)) }));
  assert.equal(validateProfile(p).ok, false);
  assert.equal(exportProfile(p).ok, false);
});
test('profile survives a storage failure in the current tab without capturing arguments', async () => {
  const { getWorkshopProfile, saveWorkshopProfile } = await import('../lib/command-workshop.mjs?storage-test');
  const brokenStorage = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('quota'); } };
  assert.deepEqual(getWorkshopProfile(brokenStorage), emptyProfile());
  const next = starterProfile();
  next.target = 'goblin';
  assert.deepEqual(saveWorkshopProfile(next, brokenStorage), { ok: true, persistent: false });
  assert.deepEqual(getWorkshopProfile(brokenStorage), next);
  assert.equal('args' in getWorkshopProfile(brokenStorage), false);
});
test('corrupt stored profile starts empty without overwriting the original value', async () => {
  const { getWorkshopProfile } = await import('../lib/command-workshop.mjs?corrupt-test');
  let writes = 0;
  const fakeStorage = { getItem() { return '{broken'; }, setItem() { writes += 1; } };
  assert.deepEqual(getWorkshopProfile(fakeStorage), emptyProfile());
  assert.equal(writes, 0);
});
