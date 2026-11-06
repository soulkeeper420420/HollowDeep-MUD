/** Local command configuration. This module never connects, sends, or executes code. */
/** @typedef {{version: number, target: string, aliases: {name:string,template:string}[], macros: {name:string,steps:string[]}[]}} Profile */
/** @typedef {{ok:false,error:string}} Failure */
export const WORKSHOP_KEY = 'hollowdeep-command-workshop-v1';
export const LIMITS = Object.freeze({ aliases: 24, macros: 12, steps: 12, bytes: 256, fileBytes: 32768 });
const controls = /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/u;
const sensitive = /^(?:password|passwd|passphrase|login|connect|disconnect)\b/i;
const validName = /^[a-z][a-z0-9_-]{0,23}$/;
/** @returns {Failure} */
const fail = error => ({ ok: false, error });
export function emptyProfile() { return { version: 1, target: '', aliases: [], macros: [] }; }
/** @returns {{ok:true} | Failure} */
export function validateLine(value, { allowEmpty = false } = {}) {
  if (typeof value !== 'string' || !value.isWellFormed()) return fail('Enter valid text.');
  if (controls.test(value)) return fail('Use one line without control characters.');
  if (new TextEncoder().encode(value).length > LIMITS.bytes) return fail('A command can contain at most 256 UTF-8 bytes.');
  if (!allowEmpty && !value.trim()) return fail('Enter a command first.');
  return { ok: true };
}
/** @returns {{ok:true} | Failure} */
function validateTemplate(value) {
  const valid = validateLine(value);
  if (!valid.ok) return valid;
  if (sensitive.test(value.trim())) return fail('Login and password commands cannot be saved as shortcuts.');
  return { ok: true };
}
function hasOnly(value, keys) { return value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).every(key => keys.includes(key)); }
/** @returns {{ok:true,profile:Profile} | Failure} */
export function validateProfile(value) {
  if (!hasOnly(value, ['version', 'target', 'aliases', 'macros']) || value.version !== 1) return fail('This is not a version 1 Hollowdeep command profile.');
  if (!validateLine(value.target, { allowEmpty: true }).ok || value.target.length > 60) return fail('Target must be a single line of at most 60 characters.');
  if (!Array.isArray(value.aliases) || value.aliases.length > LIMITS.aliases || !Array.isArray(value.macros) || value.macros.length > LIMITS.macros) return fail('A profile can hold 24 aliases and 12 macros.');
  for (const [kind, entries] of [['alias', value.aliases], ['macro', value.macros]]) {
    const names = new Set();
    for (const item of entries) {
      if (!hasOnly(item, kind === 'alias' ? ['name', 'template'] : ['name', 'steps']) || typeof item.name !== 'string' || !validName.test(item.name)) return fail('Names must begin with a lowercase letter and use up to 24 letters, numbers, dashes, or underscores.');
      if (names.has(item.name)) return fail(`Duplicate ${kind} name: ${item.name}.`);
      names.add(item.name);
      const steps = kind === 'alias' ? [item.template] : item.steps;
      if (!Array.isArray(steps) || !steps.length || steps.length > LIMITS.steps) return fail('A macro needs 1–12 command lines.');
      for (const step of steps) { const result = validateTemplate(step); if (!result.ok) return fail(`${item.name}: ${result.error}`); }
    }
  }
  const profile = { version: 1, target: value.target, aliases: value.aliases.map(({ name, template }) => ({ name, template })), macros: value.macros.map(({ name, steps }) => ({ name, steps: [...steps] })) };
  if (new TextEncoder().encode(JSON.stringify(profile, null, 2) + '\n').length > LIMITS.fileBytes) return fail('This profile exceeds the 32 KB limit. Remove a few commands.');
  return { ok: true, profile };
}
/** @returns {{ok:true,profile:Profile} | Failure} */
export function parseProfile(raw) {
  if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > LIMITS.fileBytes) return fail('Choose a JSON command profile smaller than 32 KB.');
  try { return validateProfile(JSON.parse(raw)); } catch { return fail('The file is not valid JSON.'); }
}
/** @returns {{ok:true,text:string} | Failure} */
export function exportProfile(profile) {
  const parsed = validateProfile(profile);
  if (!parsed.ok) return parsed;
  return { ok: true, text: JSON.stringify(parsed.profile, null, 2) + '\n' };
}
/** @returns {{ok:true,command:string} | Failure} */
export function expandTemplate(template, argumentsText = '', target = '') {
  const templateValidation = validateTemplate(template);
  if (!templateValidation.ok) return templateValidation;
  for (const value of [argumentsText, target]) { const result = validateLine(value, { allowEmpty: true }); if (!result.ok) return result; }
  const allArgs = argumentsText.trim();
  const args = allArgs ? allArgs.split(/ +/) : [];
  let error = '';
  const command = template.replace(/\$\$|\$target\b|\$\*|\$[1-9]\b/g, token => {
    if (token === '$$') return '$';
    const value = token === '$target' ? target.trim() : token === '$*' ? allArgs : args[Number(token[1]) - 1];
    if (!value) error = token === '$target' ? 'Set a target first.' : `Provide an argument for ${token}.`;
    return value ?? '';
  }).trim();
  if (error) return fail(error);
  const final = validateTemplate(command);
  return final.ok ? { ok: true, command } : final;
}
/** Slash aliases are expanded only for visible gameplay input by the caller. */
/** @returns {{ok:true,command:string,expanded:boolean} | Failure} */
export function resolveAlias(line, profile, { hidden = false } = {}) {
  if (hidden || typeof line !== 'string' || !line.startsWith('/')) return { ok: true, command: line, expanded: false };
  const valid = validateLine(line); if (!valid.ok) return valid;
  const match = /^\/([a-z][a-z0-9_-]{0,23})(?: +(.*))?$/.exec(line);
  if (!match) return fail('Use /alias followed by its arguments.');
  const alias = profile.aliases.find(item => item.name === match[1]);
  if (!alias) return fail(`No alias named ${match[1]}. Open Command workshop to create it.`);
  const result = expandTemplate(alias.template, match[2] ?? '', profile.target);
  return result.ok ? { ...result, expanded: true } : result;
}
export function starterProfile() {
  return { version: 1, target: '', aliases: [
    { name: 'scan', template: 'look $target' },
    { name: 'strike', template: 'kill $target' },
    { name: 'greet', template: 'tell $1 Hail, traveler.' },
  ], macros: [{ name: 'check-in', steps: ['look', 'score', 'inventory', 'who'] }] };
}

let memoryProfile;
/** Shared cache lets shortcuts still work if browser storage is denied or full. */
/** @returns {Profile} */
export function getWorkshopProfile(storage) {
  if (memoryProfile) return memoryProfile;
  try {
    const raw = storage?.getItem(WORKSHOP_KEY);
    const parsed = raw ? parseProfile(raw) : null;
    memoryProfile = parsed?.ok ? parsed.profile : emptyProfile();
  } catch { memoryProfile = emptyProfile(); }
  return memoryProfile;
}
/** @returns {{ok:true,persistent:boolean} | Failure} */
export function saveWorkshopProfile(profile, storage) {
  const result = validateProfile(profile);
  if (!result.ok) return result;
  memoryProfile = result.profile;
  try {
    if (!storage) return { ok: true, persistent: false };
    storage.setItem(WORKSHOP_KEY, JSON.stringify(result.profile));
    return { ok: true, persistent: true };
  } catch { return { ok: true, persistent: false }; }
}
