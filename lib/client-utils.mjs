/** Client-only helpers. No game credentials or game state are persisted here. */
export { createAnsiParser } from './ansi-parser.mjs';
export const COMMAND_CATALOG = [
  { id: 'hquest', command: 'hquest', label: 'Hollowdeep chronicles', category: 'Chronicles', description: 'List exploration quests and progress. Requires the Hollowdeep server kit to be installed.' },
  { id: 'hquest-survey', command: 'hquest survey', label: 'Record this place', category: 'Chronicles', description: 'Record your actual room for an accepted chronicle. Each room counts once; requires the server kit.' },
  { id: 'hquest-accept', command: 'hquest accept first-steps', label: 'Begin your first chronicle', category: 'Chronicles', description: 'Accept the first exploration quest: survey three unique places to earn a cosmetic Wayfarer badge. Requires the server kit.' },
  { id: 'hquest-claim', command: 'hquest claim ', label: 'Claim a chronicle badge', category: 'Chronicles', description: 'Add a completed quest ID. Badges reward exploration and level milestones; they do not grant gold or experience. Requires the server kit.', template: true },
  { id: 'hprofile', command: 'hprofile', label: 'Your chronicle profile', category: 'Chronicles', description: 'See recorded places and earned cosmetic badges. Requires the Hollowdeep server kit.' },
  { id: 'hclass', command: 'hclass', label: 'Your class guide', category: 'Chronicles', description: 'Read guidance for your current class and original abilities. Requires the Hollowdeep server kit.' },
  { id: 'hcommands', command: 'hcommands', label: 'Hollowdeep command help', category: 'Chronicles', description: 'See the added chronicle commands and common original commands. Requires the Hollowdeep server kit.' },
  { id: 'look', command: 'look', label: 'Look around', category: 'Information', description: 'Read the room description, visible creatures, objects, and exits.' },
  { id: 'north', command: 'north', label: 'Go north', category: 'Navigation', description: 'Take the northern exit, if the room has one.' },
  { id: 'south', command: 'south', label: 'Go south', category: 'Navigation', description: 'Take the southern exit, if the room has one.' },
  { id: 'east', command: 'east', label: 'Go east', category: 'Navigation', description: 'Take the eastern exit, if the room has one.' },
  { id: 'west', command: 'west', label: 'Go west', category: 'Navigation', description: 'Take the western exit, if the room has one.' },
  { id: 'up', command: 'up', label: 'Go up', category: 'Navigation', description: 'Use an upward exit, if one is available.' },
  { id: 'down', command: 'down', label: 'Go down', category: 'Navigation', description: 'Use a downward exit, if one is available.' },
  { id: 'score', command: 'score', label: 'Character score', category: 'Information', description: 'Review your character statistics and progress.' },
  { id: 'who', command: 'who', label: 'Who is playing', category: 'Social', description: 'See the adventurers currently in the world.' },
  { id: 'help', command: 'help', label: 'Original game help', category: 'Information', description: 'Read the original server’s authoritative command help.' },
  { id: 'say', command: 'say ', label: 'Speak to the room', category: 'Social', description: 'Add your message after “say” to speak to nearby adventurers.', template: true },
  { id: 'tell', command: 'tell ', label: 'Tell an adventurer', category: 'Social', description: 'Add a player name and message to speak directly to them.', template: true },
  { id: 'kill', command: 'kill ', label: 'Attack a creature', category: 'Combat', description: 'Add the creature’s name. This starts combat when you send it.', template: true, caution: true },
  { id: 'cast', command: 'cast ', label: 'Cast a spell', category: 'Combat', description: 'Add a spell and any target required by the original game.', template: true, caution: true },
  { id: 'inventory', command: 'inventory', label: 'Check inventory', category: 'Items', description: 'List the objects your character is carrying.' },
  { id: 'get', command: 'get ', label: 'Pick up an object', category: 'Items', description: 'Add the name of an object in your room.', template: true },
  { id: 'drop', command: 'drop ', label: 'Drop an object', category: 'Items', description: 'Add the name of an object you want to leave behind.', template: true, caution: true },
  { id: 'wear', command: 'wear ', label: 'Wear equipment', category: 'Items', description: 'Add the name of a wearable object from your inventory.', template: true },
  { id: 'wield', command: 'wield ', label: 'Wield a weapon', category: 'Items', description: 'Add the name of a weapon from your inventory.', template: true },
  // Verified against Mordor 3.00 src_3.00/global.c and the matching help files.
  { id: 'equipment', command: 'equipment', label: 'Equipped items', category: 'Items', description: 'Review the equipment your character is wearing and wielding.' },
  { id: 'remove', command: 'remove ', label: 'Remove equipment', category: 'Items', description: 'Add the name of an equipped object to remove it.', template: true },
  { id: 'give', command: 'give ', label: 'Give an object', category: 'Items', description: 'Add an object and recipient. Check the item and destination before sending.', template: true, caution: true },
  { id: 'list', command: 'list', label: 'Browse a shop', category: 'Items', description: 'List the merchandise available in your current shop.' },
  { id: 'buy', command: 'buy ', label: 'Buy an item', category: 'Items', description: 'Add an item sold by this shop. Buying spends your gold.', template: true, caution: true },
  { id: 'sell', command: 'sell ', label: 'Sell an item', category: 'Items', description: 'Add an inventory item to sell at a suitable shop.', template: true, caution: true },
  { id: 'value', command: 'value ', label: 'Value an item', category: 'Items', description: 'Add an item to ask its value before selling.', template: true },
  { id: 'repair', command: 'repair ', label: 'Repair equipment', category: 'Items', description: 'Add the item to repair at an appropriate repair shop.', template: true, caution: true },
  { id: 'follow', command: 'follow ', label: 'Follow an adventurer', category: 'Social', description: 'Add a player name to follow them into a group.', template: true },
  { id: 'lose', command: 'lose ', label: 'Remove a follower', category: 'Social', description: 'Add the name of someone following you to remove them from your group.', template: true, caution: true },
  { id: 'group', command: 'group', label: 'View your followers', category: 'Social', description: 'List the players who are currently following you.' },
  { id: 'gtalk', command: 'gtalk ', label: 'Talk to your group', category: 'Social', description: 'Add a message for your group. You must be in a group to use this.', template: true },
  { id: 'emote', command: 'emote ', label: 'Roleplay an action', category: 'Social', description: 'Add an action to display after your character’s name.', template: true },
  { id: 'search', command: 'search', label: 'Search your surroundings', category: 'Navigation', description: 'Search the current room for things that are not immediately visible.' },
  { id: 'track', command: 'track', label: 'Follow tracks', category: 'Navigation', description: 'Rangers can try to discover the direction last taken out of a room.' },
  { id: 'prepare', command: 'prepare', label: 'Prepare for a trap', category: 'Navigation', description: 'Prepare before entering the next room to improve your chance of avoiding its trap.' },
  { id: 'sneak', command: 'sneak ', label: 'Sneak through an exit', category: 'Navigation', description: 'Hidden thieves can add a direction and attempt to move unseen.', template: true },
  { id: 'hide', command: 'hide', label: 'Hide from sight', category: 'Combat', description: 'Attempt to hide. Success and restrictions are decided by the server.', caution: true },
  { id: 'backstab', command: 'backstab ', label: 'Backstab a target', category: 'Combat', description: 'Hidden thieves and assassins can initiate combat with a backstab. Add a target.', template: true, caution: true },
  { id: 'circle', command: 'circle ', label: 'Circle an opponent', category: 'Combat', description: 'Fighters and barbarians can attempt to confuse and delay an opponent.', template: true, caution: true },
  { id: 'bash', command: 'bash ', label: 'Bash an opponent', category: 'Combat', description: 'Fighters and barbarians can bash a target to cause damage and delay it.', template: true, caution: true },
  { id: 'flee', command: 'flee', label: 'Flee from danger', category: 'Combat', description: 'Escape the room when trapped in combat. Mordor drops your wielded weapon when you flee.', caution: true },
  { id: 'train', command: 'train', label: 'Train for your next level', category: 'Progression', description: 'Train at your class’s training location when you have enough experience and gold.', caution: true },
  { id: 'study', command: 'study ', label: 'Learn from a scroll', category: 'Progression', description: 'Add a magical scroll to learn its spell. The scroll is consumed after studying.', template: true, caution: true },
  { id: 'pray', command: 'pray', label: 'Pray for divine favor', category: 'Progression', description: 'Clerics and paladins can pray for a temporary increase in piety.' },
  { id: 'save', command: 'save', label: 'Save your character', category: 'Progression', description: 'Ask the original game server to save your character.' },

];

export function validateCommand(value, maxBytes = 256) {
  if (typeof value !== 'string') return { ok: false, error: 'Enter a text command.' };
  if (!value.isWellFormed()) return { ok: false, error: 'Your command contains an incomplete character.' };
  if (/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/u.test(value)) return { ok: false, error: 'Commands must be a single line without control characters.' };
  if (new TextEncoder().encode(value).length > maxBytes) return { ok: false, error: `Commands can contain at most ${maxBytes} UTF-8 bytes.` };
  return { ok: true };
}

export function filterCommands(query, category = 'All', favorites = []) {
  const terms = String(query ?? '').trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const starred = new Set(favorites);
  return COMMAND_CATALOG.filter(item => {
    if (category === 'Favorites' && !starred.has(item.id)) return false;
    if (category !== 'All' && category !== 'Favorites' && item.category !== category) return false;
    const haystack = `${item.command} ${item.label} ${item.category} ${item.description}`.toLocaleLowerCase();
    return terms.every(term => haystack.includes(term));
  });
}

export function readFavorites(raw) {
  try {
    const value = JSON.parse(raw ?? '[]');
    if (!Array.isArray(value)) return [];
    const known = new Set(COMMAND_CATALOG.map(item => item.id));
    return [...new Set(value.filter(id => typeof id === 'string' && known.has(id)))];
  } catch { return []; }
}

export function readJournal(raw) {
  try {
    const value = JSON.parse(raw ?? '[]');
    if (!Array.isArray(value)) return [];
    const ids = new Set();
    return value.filter(note => {
      if (!note || typeof note.id !== 'string' || !note.id.trim() || note.id.length > 80 || ids.has(note.id) ||
          typeof note.text !== 'string' || !note.text.trim() || note.text.length > 4000 ||
          typeof note.createdAt !== 'string' || !Number.isFinite(Date.parse(note.createdAt))) return false;
      ids.add(note.id); return true;
    }).slice(0, 100).map(({ id, text, createdAt }) => ({ id, text, createdAt }));
  } catch { return []; }
}

export function journalText(notes) {
  return ['HOLLOWDEEP — ADVENTURE JOURNAL', 'Personal notes saved in this browser.', '', ...notes.flatMap(note => [new Date(note.createdAt).toISOString(), note.text, ''])].join('\n');
}

export function connectionText(host, port) {
  let validHost = typeof host === 'string' && host.length <= 253;
  if (validHost && host.startsWith('[')) {
    try { validHost = new URL(`http://${host}/`).hostname === host; } catch { validHost = false; }
  } else if (validHost) {
    validHost = host.split('.').every(label => /^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/.test(label));
  }
  if (!validHost || !Number.isInteger(port) || port < 1 || port > 65535) throw new Error('A valid published MUD hostname and port are required.');
  return `HOLLOWDEEP — MORDOR 3.00\n\nHostname: ${host}\nPort: ${port}\nProtocol: Telnet\nDisplay: ANSI colors\n\nCreate a new connection in Mudlet, MUSHclient, or another telnet MUD client.\nEnter the hostname and port above, then connect.\nFollow Mordor’s prompts to create or log into your character.\n\nNative clients use your Mordor character password, not ChatGPT sign-in.\nTelnet is unencrypted. Use a password unique to this game.\n`;
}

/** Cache non-sensitive preferences for this tab if persistent storage is denied or full. */
export function createPreferenceStore(key) {
  let latest;
  return {
    read(storage, decode) {
      if (latest !== undefined) return decode(latest);
      try { return decode(storage?.getItem(key) ?? null); } catch { return decode(null); }
    },
    write(storage, value) {
      latest = JSON.stringify(value);
      try { if (!storage) return false; storage.setItem(key, latest); return true; } catch { return false; }
    },
  };
}

export function composeSocial(channel, target, message) {
  if (!['say', 'tell', 'gtalk', 'emote'].includes(channel)) return { ok: false, error: 'Choose room speech, a direct message, group chat, or an emote.' };
  if (typeof message !== 'string' || !message.trim()) return { ok: false, error: 'Write a message first.' };
  if (channel === 'tell' && (typeof target !== 'string' || !/^[A-Za-z][A-Za-z'-]{0,29}$/.test(target))) return { ok: false, error: 'Enter a single character name using letters, apostrophes, or hyphens.' };
  const command = channel === 'tell' ? `tell ${target} ${message.trim()}` : `${channel} ${message.trim()}`;
  const validation = validateCommand(message);
  if (!validation.ok) return validation;
  const result = validateCommand(command);
  return result.ok ? { ok: true, command } : result;
}

export function composeCombat(action, target) {
  if (!['kill', 'cast'].includes(action)) return { ok: false, error: 'Choose attack or cast.' };
  if (typeof target !== 'string' || !target.trim()) return { ok: false, error: action === 'kill' ? 'Name a creature first.' : 'Enter the spell and its target.' };
  const validation = validateCommand(target);
  if (!validation.ok) return validation;
  const command = `${action} ${target.trim()}`;
  const result = validateCommand(command);
  return result.ok ? { ok: true, command } : result;
}
