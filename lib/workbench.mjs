/** Bounded text-only project files. This module never reads or writes a server. */
export const WORKBENCH_KEY = 'hollowdeep-server-workshop-v1';
export const MAX_FILE_BYTES = 384 * 1024;
export const MAX_PROJECT_BYTES = 4 * 1024 * 1024;
// JSON can expand each text byte into a six-byte escape; keep export/import symmetric.
export const MAX_PROJECT_FILE_BYTES = MAX_PROJECT_BYTES * 6 + 64 * 1024;
export const MAX_FILES = 80;
const byteLength = value => new TextEncoder().encode(value).length;

export function validatePath(path) {
  if (typeof path !== 'string' || !path || path.length > 160 || !/^[A-Za-z0-9_][A-Za-z0-9_./-]*$/.test(path)) throw new Error('Use a relative file path with letters, numbers, slashes, dots, underscores, or hyphens.');
  if (path.split('/').some(part => !part || part === '.' || part === '..' || part.startsWith('.'))) throw new Error('File paths cannot contain empty, hidden, or parent directory segments.');
  const name = path.split('/').at(-1);
  if (!/\.(c|h|md|json|sh|txt|patch|cfg|ini|conf|py|js|mjs|ts|tsx|css|html|lua|mk)$/i.test(name) && !/^(Makefile|README|LICENSE|COPYING|COPYRIGHT)$/i.test(name) && !/^help\.(?:-2|\d{1,4})$/.test(name)) throw new Error('Choose a source, text, Markdown, JSON, shell, patch, or configuration file.');
  return path;
}
function validateText(value, label) {
  if (typeof value !== 'string' || /\u0000/.test(value) || !value.isWellFormed()) throw new Error(`${label} must contain valid text, without binary data.`);
  if (byteLength(value) > MAX_FILE_BYTES) throw new Error(`${label} exceeds the 384 KB file limit.`);
  return value;
}
export function validateProject(value) {
  if (!value || value.format !== 'hollowdeep-workshop' || value.version !== 1 || !Array.isArray(value.files)) throw new Error('Choose a Hollowdeep workshop project (version 1).');
  if (typeof value.name !== 'string' || !value.name.trim() || value.name.length > 80) throw new Error('A project name must contain 1–80 characters.');
  if (value.files.length > MAX_FILES) throw new Error('A workshop project can contain at most 80 files, including pending deletions.');
  const paths = new Set(); let bytes = 0;
  const activePaths = new Set();
  const files = value.files.map(file => {
    if (!file || typeof file !== 'object') throw new Error('The project contains an invalid file.');
    const path = validatePath(file.path);
    if (paths.has(path)) throw new Error(`Duplicate file path: ${path}`);
    paths.add(path);
    const content = file.content === null ? null : validateText(file.content, path);
    const baseContent = file.baseContent === null ? null : validateText(file.baseContent, `Original ${path}`);
    if (content === null && baseContent === null) throw new Error(`Empty deleted entry: ${path}`);
    if (content !== null) activePaths.add(path);
    bytes += byteLength(content ?? '') + byteLength(baseContent ?? '');
    return { path, content, baseContent };
  });
  for (const path of activePaths) {
    const parts = path.split('/');
    for (let i = 1; i < parts.length; i++) {
      if (activePaths.has(parts.slice(0, i).join('/'))) throw new Error(`A file cannot also be a directory: ${path}`);
    }
  }
  if (bytes > MAX_PROJECT_BYTES) throw new Error('This project exceeds the 4 MB workshop limit, including original copies.');
  return { format: 'hollowdeep-workshop', version: 1, name: value.name.trim(), files };
}
export function parseProject(raw) {
  if (typeof raw !== 'string' || byteLength(raw) > MAX_PROJECT_FILE_BYTES) throw new Error('The project import is too large.');
  let value;
  try { value = JSON.parse(raw); } catch { throw new Error('This file does not contain valid project JSON.'); }
  return validateProject(value);
}
export function serializeProject(project) { return JSON.stringify(validateProject(project), null, 2) + '\n'; }
export function updateFile(project, path, content) {
  validateText(content, path);
  if (!project.files.some(file => file.path === path && file.content !== null)) throw new Error('Choose an existing file to edit.');
  return validateProject({ ...project, files: project.files.map(file => file.path === path ? { ...file, content } : file) });
}
export function addFile(project, path, content = '', asBaseline = false) {
  validatePath(path); validateText(content, path);
  if (project.files.some(file => file.path === path)) throw new Error('That file path already exists, including pending deletions.');
  return validateProject({ ...project, files: [...project.files, { path, content, baseContent: asBaseline ? content : null }] });
}
export function deleteFile(project, path) {
  return validateProject({ ...project, files: project.files.flatMap(file => file.path !== path ? [file] : file.baseContent === null ? [] : [{ ...file, content: null }]) });
}
export function renameFile(project, oldPath, newPath) {
  const file = project.files.find(item => item.path === oldPath && item.content !== null);
  if (!file) throw new Error('Choose a file to rename.');
  if (oldPath === newPath) return project;
  const added = addFile(project, newPath, file.content);
  return deleteFile(added, oldPath);
}
export function importTextFiles(project, entries) {
  let next = project;
  for (const entry of entries) next = addFile(next, entry.path, entry.content, true);
  return next;
}
export function changedFiles(project) { return project.files.filter(file => file.content !== file.baseContent); }
function lines(text) {
  if (!text) return [];
  const parts = text.split('\n');
  if (text.endsWith('\n')) parts.pop();
  return parts;
}
function patchLines(text, prefix) {
  const result = lines(text).map(line => `${prefix}${line}`);
  if (text && !text.endsWith('\n')) result.push('\\ No newline at end of file');
  return result;
}
/** Full-file hunks keep this diff deterministic without a large diff dependency. */
export function createPatch(project) {
  const valid = validateProject(project);
  return changedFiles(valid).map(file => {
    const before = file.baseContent ?? '', after = file.content ?? '';
    const oldCount = lines(before).length, newCount = lines(after).length;
    const output = [`diff --git a/${file.path} b/${file.path}`];
    if (file.baseContent === null) output.push('new file mode 100644');
    if (file.content === null) output.push('deleted file mode 100644');
    output.push(`--- ${file.baseContent === null ? '/dev/null' : `a/${file.path}`}`, `+++ ${file.content === null ? '/dev/null' : `b/${file.path}`}`);
    if (oldCount || newCount) output.push(`@@ -${oldCount ? 1 : 0},${oldCount} +${newCount ? 1 : 0},${newCount} @@`, ...patchLines(before, '-'), ...patchLines(after, '+'));
    return output.join('\n') + '\n';
  }).join('');
}
export function starterProject() {
  const content = `# Hollowdeep server workshop\n\nLoad the server kit to edit the actual Hollowdeep extension files.\nYou can also import your own .c, .h, .txt, or project JSON files.\n\n## Workflow\n\n1. Load server kit or import your source files.\n2. Edit, then save a draft in this browser.\n3. Download your project as a backup. Export a patch for changed files.\n4. Apply the patch to the matching source checkout on your computer.\n5. Build and test on a development server before updating your game host.\n\nThis editor does not execute code or change the hosted game.\nPlayer saves, passwords, and server secrets do not belong in this project.\n`;
  return validateProject({ format: 'hollowdeep-workshop', version: 1, name: 'Hollowdeep server', files: [{ path: 'WORKSHOP.md', content, baseContent: content }] });
}
