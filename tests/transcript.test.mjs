import test from 'node:test';
import assert from 'node:assert/strict';
import { transcriptText, searchTranscript } from '../lib/transcript.mjs';

test('output frames reconstruct one transcript without added line breaks or ANSI escapes', () => {
  const entries = [
    {kind: 'system', text: 'Connected'},
    {kind: 'output', text: '\u001b[31mNorth ga', tokens: [{text: 'North ga', color: 'red'}]},
    {kind: 'output', text: 'te\u001b[0m\n> ', tokens: [{text: 'te\n> '}]},
    {kind: 'input', text: 'look\n'},
  ];
  const text = transcriptText(entries);
  assert.equal(text, 'Connected\nNorth gate\n> look\n');
  assert.deepEqual(searchTranscript(text, 'north gate'), [{line: 2, text: 'North gate'}]);
});

test('search handles literal punctuation and returns matching logical lines', () => {
  const text = 'one\n[Ancient shrine]\nTwo ANCIENT travelers\n';
  assert.deepEqual(searchTranscript(text, '['), [{line: 2, text: '[Ancient shrine]'}]);
  assert.equal(searchTranscript(text, 'ancient').length, 2);
  assert.deepEqual(searchTranscript(text, ' '), []);
});
