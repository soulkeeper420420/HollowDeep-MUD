import test from 'node:test';
import assert from 'node:assert/strict';
import { createAnsiParser } from '../lib/ansi-parser.mjs';

const plain = tokens => tokens.map(token => token.text).join('');

test('normal text, Unicode, line breaks and tabs survive; terminal controls do not', () => {
  const parser = createAnsiParser();
  assert.deepEqual(parser.push('A \u2726 dragon\r\n\tB\0\b\x07\x7f\x85!'), [{text:'A ✦ dragon\n\tB!'}]);
  assert.deepEqual(parser.push(''), []);
  assert.throws(() => parser.push(null), TypeError);
});

test('SGR styles survive arbitrary network chunk boundaries', () => {
  const parser = createAnsiParser();
  assert.deepEqual(parser.push('plain\x1b'), [{text:'plain'}]);
  assert.deepEqual(parser.push('['), []);
  assert.deepEqual(parser.push('1;3'), []);
  assert.deepEqual(parser.push('1mred'), [{text:'red',color:'#e58f85',bold:true}]);
  assert.deepEqual(parser.push(' again'), [{text:' again',color:'#e58f85',bold:true}]);
  assert.deepEqual(parser.push('\x1b[22m normal-weight\x1b[39m default'), [
    {text:' normal-weight',color:'#e58f85'}, {text:' default'},
  ]);
  assert.deepEqual(parser.push('\x1b[1;94mBlue\x1b[mreset'), [
    {text:'Blue',color:'#b3d2ef',bold:true}, {text:'reset'},
  ]);
});

test('every possible split of an ANSI stream has the same text and formatting', () => {
  const stream = 'A\x1b[32mB\x1b[1mC\x1b[0mD';
  const expected = [
    { text:'A',color:undefined,bold:false },
    { text:'B',color:'#a6c295',bold:false },
    { text:'C',color:'#a6c295',bold:true },
    { text:'D',color:undefined,bold:false },
  ];
  const chars = tokens => tokens.flatMap(token => [...token.text].map(text => ({text,color:token.color,bold:!!token.bold})));
  for (let i = 0; i <= stream.length; i++) {
    const parser = createAnsiParser();
    assert.deepEqual(chars([...parser.push(stream.slice(0,i)), ...parser.push(stream.slice(i))]), expected);
  }
});

test('OSC title, clipboard, and hyperlink commands never become output or HTML', () => {
  const parser = createAnsiParser();
  assert.equal(plain(parser.push('A\x1b]52;c;secret')), 'A');
  assert.deepEqual(parser.push('clipboard-payload\x1b'), []);
  assert.equal(plain(parser.push('\\B\x1b]0;title\x07C')), 'BC');
  assert.equal(plain(parser.push('\x1b]8;;https://example.com\x1b\\link\x1b]8;;\x1b\\')), 'link');
  assert.deepEqual(parser.push('<script>alert(1)</script>'), [{text:'<script>alert(1)</script>'}]);
});

test('non-SGR CSI, character sets, DCS and APC are discarded across calls', () => {
  const parser = createAnsiParser();
  assert.equal(plain(parser.push('before\x1b[2J\x1b[10;20H\x1b(?')), 'before');
  assert.equal(plain(parser.push('after\x1bPprivate')), 'after');
  assert.deepEqual(parser.push(' device data\x1b'), []);
  assert.equal(plain(parser.push('\\visible\x1b_hidden\x1b\\end')), 'visibleend');
});

test('C1 equivalents are parsed and control strings use constant storage', () => {
  const parser = createAnsiParser();
  assert.deepEqual(parser.push('\u009b33mgold\u009b0m'), [{text:'gold',color:'#e1bd7e'}]);
  assert.equal(plain(parser.push('A\u009d52;c;hidden\u009cB')), 'AB');
  assert.deepEqual(parser.push('\x1b]52;' + 'x'.repeat(100000)), []);
  assert.deepEqual(parser.push('x'.repeat(100000)), []);
  assert.deepEqual(parser.push('\x07visible'), [{text:'visible'}]);
  assert.deepEqual(parser.push('\x1b[' + '1;'.repeat(100000)), []);
  assert.deepEqual(parser.push('mnormal'), [{text:'normal'}]);
});

test('unsupported extended colors do not accidentally activate bold or basic colors', () => {
  const parser = createAnsiParser();
  assert.deepEqual(parser.push('\x1b[38;2;1;31;32mtext'), [{text:'text'}]);
  assert.deepEqual(parser.push('\x1b[48;5;1mtext'), [{text:'text'}]);
  assert.deepEqual(parser.push('\x1b[1;38;5;200mtext'), [{text:'text',bold:true}]);
});

test('reset discards unfinished controls and styling between connections', () => {
  const parser = createAnsiParser();
  parser.push('\x1b[1;31mred\x1b]unfinished');
  parser.reset();
  assert.deepEqual(parser.push('new realm'), [{text:'new realm'}]);
});
