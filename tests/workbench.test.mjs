import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import { MAX_FILE_BYTES, addFile, createPatch, deleteFile, importTextFiles, parseProject, renameFile, serializeProject, starterProject, updateFile, validatePath, validateProject } from '../lib/workbench.mjs';
const project = files => validateProject({ format: 'hollowdeep-workshop', version: 1, name: 'Test realm', files });
const file = (path, content) => ({ path, content, baseContent: content });

test('untrusted project paths cannot target parent, absolute, hidden, or platform-specific paths', () => {
  for (const path of ['../server.c', '/tmp/server.c', 'src/../../server.c', 'src//server.c', 'src/./server.c', 'C:/server.c', 'src\\server.c', '.env', 'src/.keys.txt', 'src/file\n.c', 'src/evil\t.c', 'src/a.c/']) assert.throws(() => validatePath(path), path);
  assert.equal(validatePath('src/command_extensions.c'), 'src/command_extensions.c');
  assert.equal(validatePath('Makefile'), 'Makefile');
  assert.equal(validatePath('extensions/help.84'), 'extensions/help.84');
  assert.equal(validatePath('extensions/help.-2'), 'extensions/help.-2');
  assert.throws(() => validatePath('extensions/help.-3'));
  assert.equal(validatePath('COPYRIGHT'), 'COPYRIGHT');
});
test('corrupt, duplicate, binary and oversized imports fail without partial project changes', () => {
  const start = starterProject();
  assert.throws(() => parseProject('{'));
  assert.throws(() => parseProject(JSON.stringify({ format: 'other', version: 1, name: 'Oops', files: [] })));
  assert.throws(() => project([file('a.c', 'one'), file('a.c', 'two')]));
  assert.throws(() => project([file('a.c', '\0binary')]));
  assert.throws(() => project([file('a.c', '\ud800')]));
  assert.throws(() => project([file('a.c', 'x'.repeat(MAX_FILE_BYTES + 1))]));
  assert.throws(() => importTextFiles(start, [{ path: 'new.c', content: 'ok' }, { path: '../bad.c', content: 'no' }]));
  assert.equal(start.files.length, 1);
});
test('JSON round trips preserve original copies and pending file deletions', () => {
  let draft = project([file('src/commands.c', 'original\n')]);
  draft = updateFile(draft, 'src/commands.c', 'edited\n');
  draft = renameFile(draft, 'src/commands.c', 'src/features.c');
  const saved = parseProject(serializeProject(draft));
  assert.deepEqual(saved, draft);
  assert.deepEqual(saved.files[0], { path: 'src/commands.c', content: null, baseContent: 'original\n' });
  assert.deepEqual(saved.files[1], { path: 'src/features.c', content: 'edited\n', baseContent: null });
});
test('escaped text exports remain importable within the decoded project budget', () => {
  const original = project(Array.from({length: 3}, (_, i) => file(`source${i}.txt`, '\u0001'.repeat(300000))));
  const exported = serializeProject(original);
  assert.ok(Buffer.byteLength(exported) > 8 * 1024 * 1024);
  assert.deepEqual(parseProject(exported), original);
});
test('active source paths cannot be both files and directories', () => {
  assert.throws(() => project([file('path.c', 'file'), file('path.c/child.c', 'nested')]), /directory/);
  assert.throws(() => project([file('path.c/child.c', 'nested'), file('path.c', 'file')]), /directory/);
  assert.doesNotThrow(() => project([{path: 'path.c', content: null, baseContent: 'old file'}, file('path.c/child.c', 'nested')]));
});
test('plain source imports establish baselines; deleting a new file cancels the change', () => {
  let draft = importTextFiles(project([]), [{ path: 'foo.c', content: 'old' }]);
  assert.equal(createPatch(draft), '');
  draft = addFile(draft, 'new.c', 'new');
  draft = deleteFile(draft, 'new.c');
  assert.equal(createPatch(draft), '');
  assert.throws(() => renameFile(draft, 'foo.c', 'foo/../bad.c'));
  assert.throws(() => addFile(draft, 'foo.c', 'duplicate'));
});
test('exported patches apply to real files including CRLF, no final newline, new empty files and deletes', () => {
  const original = project([file('src/edited.c', 'line one\nline two\n'), file('src/windows.c', 'first\r\nsecond\r\n'), file('src/nonl.c', 'old without newline'), file('src/deleted.c', 'remove\n'), file('empty.txt', '')]);
  let draft = updateFile(original, 'src/edited.c', 'new first\nnew second\nnew third\n');
  draft = updateFile(draft, 'src/windows.c', 'first\r\nchanged\r\n');
  draft = updateFile(draft, 'src/nonl.c', 'new without newline');
  draft = deleteFile(draft, 'src/deleted.c');
  draft = renameFile(draft, 'empty.txt', 'renamed-empty.txt');
  draft = addFile(draft, 'src/new.c', 'hello\n');
  const directory = mkdtempSync(join(tmpdir(), 'hollowdeep-workbench-'));
  try {
    execFileSync('git', ['init', '-q'], { cwd: directory, stdio: 'inherit' });
    for (const entry of original.files) { mkdirSync(dirname(join(directory, entry.path)), { recursive: true }); writeFileSync(join(directory, entry.path), entry.content); }
    const patch = createPatch(draft);
    writeFileSync(join(directory, 'changes.patch'), patch);
    execFileSync('git', ['apply', '--check', 'changes.patch'], { cwd: directory, stdio: 'inherit' });
    execFileSync('git', ['apply', 'changes.patch'], { cwd: directory, stdio: 'inherit' });
    for (const entry of draft.files) {
      if (entry.content === null) assert.equal(existsSync(join(directory, entry.path)), false, entry.path);
      else assert.equal(readFileSync(join(directory, entry.path), 'utf8'), entry.content, entry.path);
    }
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
