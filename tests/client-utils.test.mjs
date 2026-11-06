import test from 'node:test';
import assert from 'node:assert/strict';
import { validateCommand, filterCommands, readFavorites, readJournal, journalText, connectionText, composeSocial, composeCombat, createPreferenceStore } from '../lib/client-utils.mjs';

test('command validation enforces actual UTF-8 bytes without silently truncating player input', () => {
  assert.deepEqual(validateCommand('look'), { ok: true });
  assert.deepEqual(validateCommand(''), { ok: true });
  assert.equal(validateCommand('é'.repeat(128)).ok, true);
  assert.equal(validateCommand('é'.repeat(129)).ok, false);
  assert.equal(validateCommand('🙂'.repeat(64)).ok, true);
  assert.equal(validateCommand('🙂'.repeat(65)).ok, false);
  for (const text of ['north\nsouth', 'say hi\rquit', '\x1b[31mlook', '\x00', '\u2028', '\u009b']) assert.equal(validateCommand(text).ok, false);
  assert.equal(validateCommand('\ud800').ok, false);
  assert.equal(validateCommand('\udc00').ok, false);
});

test('palette search and favorites work together across descriptions and categories', () => {
  assert.deepEqual(filterCommands('room description').map(c => c.id), ['look']);
  assert.deepEqual(filterCommands(' NORTH ', 'Navigation').map(c => c.id), ['north']);
  assert.deepEqual(filterCommands('', 'Favorites', ['look', 'who']).map(c => c.id), ['look', 'who']);
  assert.deepEqual(filterCommands('look', 'Combat'), []);
  assert.ok(filterCommands('', 'Combat').every(c => c.caution));
});

test('corrupt and outdated saved favorites cannot break the palette', () => {
  assert.deepEqual(readFavorites('not json'), []);
  assert.deepEqual(readFavorites('{"look":true}'), []);
  assert.deepEqual(readFavorites('["look","look","removed",null,"who"]'), ['look', 'who']);
});

test('journal loading rejects invalid entries, keeps order, deduplicates and enforces capacity', () => {
  const good = { id: 'one', text: '<script>not markup</script>\nA clue.', createdAt: '2026-10-29T18:00:00.000Z' };
  const parsed = readJournal(JSON.stringify([good, good, { ...good, id: 'two', createdAt: 'invalid' }, { ...good, id: 'three', text: ' ' }, { ...good, id: 'four', text: 'x'.repeat(4001) }]));
  assert.deepEqual(parsed, [good]);
  assert.deepEqual(readJournal('{bad'), []);
  const long = Array.from({ length: 120 }, (_, n) => ({ ...good, id: String(n) }));
  assert.equal(readJournal(JSON.stringify(long)).length, 100);
  const exported = journalText(parsed);
  assert.ok(exported.includes('A clue.'));
  assert.ok(exported.includes(good.createdAt));
  assert.deepEqual(readJournal(JSON.stringify([{...good,id:''},{...good,id:' '},null,5])), []);
});

test('native connection export requires configured host/port and never fabricates an address', () => {
  assert.match(connectionText('mud.example.test', 4040), /Hostname: mud\.example\.test\nPort: 4040\nProtocol: Telnet/);
  assert.match(connectionText('[::1]', 4040), /Hostname: \[::1\]/);
  for (const [host, port] of [['', 4040], ['https://mud.example.test', 4040], ['mud\nPort: 80', 4040], ['mud.example.test', 0], ['mud.example.test', 65536], ['mud.example.test', 4.5], ['a..test',4040],['a-.test',4040],['[::::]',4040],['a'.repeat(64)+'.test',4040]]) assert.throws(() => connectionText(host, port));
});

test('social composer prepares explicit room and direct messages without allowing injected commands', () => {
  assert.deepEqual(composeSocial('say', '', ' Hail, traveler! '), {ok:true,command:'say Hail, traveler!'});
  assert.deepEqual(composeSocial('tell', 'Thorin', 'Meet at the gate.'), {ok:true,command:'tell Thorin Meet at the gate.'});
  assert.equal(composeSocial('tell', 'Thorin north', 'hello').ok, false);
  assert.equal(composeSocial('tell', '', 'hello').ok, false);
  assert.equal(composeSocial('say', '', 'hello\nkill goblin').ok, false);
  assert.equal(composeSocial('say', '', ' ').ok, false);
  assert.equal(composeSocial('broadcast', '', 'hello').ok, false);
  assert.equal(composeSocial('say', '', 'é'.repeat(126)).ok, true);
  assert.equal(composeSocial('say', '', 'é'.repeat(127)).ok, false);
});

test('combat composer only prepares named actions and preserves spell syntax for review', () => {
  assert.deepEqual(composeCombat('kill', ' goblin '), {ok:true,command:'kill goblin'});
  assert.deepEqual(composeCombat('cast', '"magic missile" goblin'), {ok:true,command:'cast "magic missile" goblin'});
  assert.equal(composeCombat('kill','').ok, false);
  assert.equal(composeCombat('cast','spark\rquit').ok, false);
  assert.equal(composeCombat('delete','Thorin').ok, false);
  assert.equal(composeCombat('kill','x'.repeat(252)).ok, false);
});

test('preferences survive quota failure and remounts in this tab without corrupting saved data', () => {
  const store = createPreferenceStore('favorites');
  const existing = new Map([['favorites','["look"]']]);
  const storage = {getItem:key=>existing.get(key),setItem:()=>{throw new Error('Quota exceeded');}};
  assert.deepEqual(store.read(storage,readFavorites),['look']);
  assert.equal(store.write(storage,['who','look']),false);
  assert.deepEqual(store.read(storage,readFavorites),['who','look']);
  assert.deepEqual(store.read(undefined,readFavorites),['who','look']);
  assert.equal(existing.get('favorites'),'["look"]');
  const absent = createPreferenceStore('none');
  assert.deepEqual(absent.read(undefined,readJournal),[]);
  assert.equal(absent.write(undefined,[]),false);
});

test('preferences use persistent storage when available and tolerate invalid initial records', () => {
  const existing = new Map([['favorites','bad json']]);
  const storage = {getItem:key=>existing.get(key),setItem:(key,value)=>existing.set(key,value)};
  const store = createPreferenceStore('favorites');
  assert.deepEqual(store.read(storage,readFavorites),[]);
  assert.equal(store.write(storage,['who']),true);
  assert.equal(existing.get('favorites'),'["who"]');
  const remounted = createPreferenceStore('favorites');
  assert.deepEqual(remounted.read(storage,readFavorites),['who']);
});

test('expanded catalog exposes source-backed class actions and meaningful costs', () => {
  const progress = filterCommands('', 'Progression');
  assert.deepEqual(progress.map(c => c.id), ['train', 'study', 'pray', 'save']);
  assert.match(filterCommands('flee', 'Combat')[0].description, /drops your wielded weapon/);
  assert.match(filterCommands('backstab', 'Combat')[0].description, /Hidden thieves and assassins/);
  assert.match(filterCommands('group', 'Social').find(c => c.id === 'group').description, /following you/);
  assert.ok(filterCommands('', 'Combat').every(c => c.caution));
  const all = filterCommands('');
  assert.equal(new Set(all.map(c => c.id)).size, all.length);
  assert.ok(all.every(c => validateCommand(c.command).ok));
});

test('group chat and roleplay compose real Mordor commands and keep injection limits', () => {
  assert.deepEqual(composeSocial('gtalk', '', ' Hold the passage. '), { ok: true, command: 'gtalk Hold the passage.' });
  assert.deepEqual(composeSocial('emote', '', 'raises a lantern.'), { ok: true, command: 'emote raises a lantern.' });
  for (const channel of ['gtalk', 'emote']) {
    assert.equal(composeSocial(channel, '', 'hello\nquit').ok, false);
    assert.equal(composeSocial(channel, '', 'é'.repeat(125)).ok, true);
    assert.equal(composeSocial(channel, '', 'é'.repeat(126)).ok, false);
  }
});
