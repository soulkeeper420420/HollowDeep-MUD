import assert from 'node:assert/strict';
import test from 'node:test';
import { CHRONICLE_QUESTS, CODEX_CATEGORIES, CODEX_CLASS_COUNT, CODEX_ENTRIES, CODEX_SPELL_COUNT, commandHref, searchCodex } from '../lib/realm-codex.mjs';
import { validateCommand } from '../lib/client-utils.mjs';

test('library class roster reflects the ten playable Mordor classes', () => {
  assert.equal(CODEX_CLASS_COUNT, 10);
  assert.deepEqual(searchCodex('', 'Classes').map(entry => entry.title).sort(), ['Assassin', 'Barbarian', 'Bard', 'Cleric', 'Fighter', 'Mage', 'Monk', 'Paladin', 'Ranger', 'Thief']);
  assert.equal(CODEX_SPELL_COUNT, searchCodex('', 'Spells').length);
  assert.ok(CODEX_SPELL_COUNT >= 20);
});

test('every topic has a unique ID, recognized category, source and valid prepared commands', () => {
  assert.equal(new Set(CODEX_ENTRIES.map(entry => entry.id)).size, CODEX_ENTRIES.length);
  for (const entry of CODEX_ENTRIES) {
    assert.ok(CODEX_CATEGORIES.includes(entry.category));
    assert.ok(entry.source && entry.title && entry.paragraphs.length >= 2);
    for (const command of [entry.command, ...entry.relatedCommands]) {
      assert.equal(validateCommand(command).ok, true, command);
      assert.equal(new URL(commandHref(command), 'https://hollowdeep.example').searchParams.get('command'), command);
    }
  }
});

test('search combines terms across topic text and keeps category boundaries', () => {
  assert.ok(searchCodex('hidden backstab', 'Combat').some(entry => entry.id === 'command-backstab'));
  assert.equal(searchCodex('mage', 'Classes').length, 1);
  assert.deepEqual(searchCodex('impossible-topic'), []);
  assert.deepEqual(searchCodex('', 'Not a category'), []);
  assert.ok(searchCodex('ＴＲＡＩＮ', 'Progression').some(entry => entry.id === 'command-train'));
  assert.ok(searchCodex('', 'Progression').every(entry => entry.category === 'Progression'));
});

test('prepared command links cannot encode control characters, malformed Unicode or oversized UTF-8 input', () => {
  for (const command of ['', null, 'say hello\nquit', 'look\r', 'say\u0085hello', 'say\u2028hello', '\ud800', 'é'.repeat(129)]) assert.equal(commandHref(command), '/');
  assert.equal(new URL(commandHref('say <hello> & welcome?'), 'https://hollowdeep.example').searchParams.get('command'), 'say <hello> & welcome?');
});

test('Chronicles are explicitly separate extensions with bounded cosmetic goals', () => {
  const chronicles = searchCodex('', 'Chronicles');
  assert.deepEqual(chronicles.map(entry => entry.command), ['hcommands', 'hclass', 'hquest', 'hprofile']);
  for (const entry of chronicles) {
    assert.equal(entry.extension, true);
    assert.ok(entry.tags.includes('Hollowdeep extension'));
    assert.equal(entry.tags.includes('Original engine'), false);
    assert.equal(entry.source, 'engine/extensions/hollowdeep.c');
  }
  assert.deepEqual(CHRONICLE_QUESTS.map(({ id, rooms, level, badge }) => [id, rooms, level, badge]), [
    ['first-steps', 3, 1, 'Wayfarer'], ['mapmaker', 10, 1, 'Pathfinder'],
    ['apprentice', 3, 3, 'Adept'], ['veteran', 10, 5, 'Veteran'],
  ]);
  const quest = chronicles.find(entry => entry.command === 'hquest');
  assert.match(quest.paragraphs.join(' '), /real room counts only once/);
  assert.match(quest.paragraphs.join(' '), /do not award gold, experience, or class abilities/);
});
