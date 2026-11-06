/**
 * Curated, independently written guidance for original Mordor 3.00 and the
 * separately installed Hollowdeep extensions. Original topics are verified
 * against command/spell tables and supplied help; extension topics describe
 * engine/extensions/hollowdeep.c. Original engine:
 * copyright Brett J. Vickers and Brooke Paul; their notices remain in the source.
 * This reference describes capabilities, not the state of a running game host.
 */
export const CODEX_CATEGORIES = ['All', 'Classes', 'Spells', 'Combat', 'Social', 'Progression', 'World', 'Chronicles', 'Staff'];

const classes = [
  ['assassin', 'Assassin', 'A patient ambusher', 'Backstab · hide · peek', 'Assassins approach combat through concealment and an opening strike. Hide before attempting a backstab; it requires a suitable sharp or thrusting weapon and cannot open a fight that is already underway.', 'Use peek to investigate an inventory, then pick your moment. A failed backstab leaves a longer wait before your next attack.', ['hide', 'backstab ', 'peek ']],
  ['barbarian', 'Barbarian', 'The force at the front', 'Bash · circle · endurance', 'Barbarians have the highest base starting health among the playable classes. Their physical skills include bash and circle, which can interrupt an opponent and create time for the group.', 'Balance direct attacks with control skills. Track your health and keep an exit in mind before you commit.', ['bash ', 'circle ', 'score']],
  ['bard', 'Bard', 'A voice that changes a battle', 'Charm · song · magic', 'Bards can attempt to charm a creature through song. Charm has limited daily uses, can fail, and does not work on every creature.', 'Keep your voice: silence prevents the bard’s charm skill. Watch the response from the server before relying on a charmed creature.', ['charm ', 'information', 'score']],
  ['cleric', 'Cleric', 'Piety and restorative magic', 'Pray · turn · healing', 'Clerics combine a strong magic-point progression with prayer and the ability to turn undead. Piety influences important divine abilities.', 'Learn healing spells through the game and use prayer before danger. Turning is reserved for undead enemies; it is not a universal attack.', ['pray', 'turn ', 'cast mend-wounds']],
  ['fighter', 'Fighter', 'A dependable weapon specialist', 'Bash · circle · weapons', 'Fighters have a substantial health progression and access to bash and circle. They are a direct path into weapon combat and group adventuring.', 'Learn your weapon proficiency and use control skills to give allies room to act. Keep equipment in good repair.', ['bash ', 'circle ', 'equipment']],
  ['mage', 'Mage', 'A scholar of the four realms', 'Teach · enchant · spells', 'Mages have the strongest base magic-point progression. They can teach basic spells to other characters and enchant equipment, subject to the spell’s requirements.', 'Study scrolls to expand your spellbook. Carry healing and plan around remaining magic points; a mage’s base health progression is lower than a fighter’s.', ['information', 'teach ', 'cast enchant ']],
  ['monk', 'Monk', 'Discipline of body and mind', 'Meditate · touch · unarmed combat', 'Monks can meditate to recover health. At level 10, an unarmed monk may attempt the touch-of-death skill against a valid target.', 'Meditation can fail and has a cooldown. Touch requires empty hands and does not work on undead monsters.', ['meditate', 'touch ', 'score']],
  ['paladin', 'Paladin', 'A martial path guided by piety', 'Pray · turn · weapons', 'Paladins combine weapon combat with prayer and the ability to turn undead. They share divine skills with clerics while following their own class progression.', 'Know the enemy before choosing a skill. Turn targets undead; ordinary fights still call for weapons and learned spells.', ['pray', 'turn ', 'equipment']],
  ['ranger', 'Ranger', 'A guide through unfamiliar ground', 'Track · haste · hide', 'Rangers can read tracks left by the last creature to leave a room. Haste provides a temporary dexterity boost, and rangers are particularly capable at hiding.', 'Track is a direction clue, not an automatic route. Read each room and use haste when its brief advantage matters.', ['track', 'haste', 'hide']],
  ['thief', 'Thief', 'The quiet route through a locked door', 'Pick · sneak · backstab', 'Thieves specialize in picking locks, stealth, theft, and opening attacks. Sneak attempts to move a hidden character through an exit without being noticed.', 'Hide before sneaking or backstabbing. Failed theft and failed attacks can alert the target; outcomes depend on the character and situation.', ['hide', 'sneak ', 'pick ']],
].map(([id, title, subtitle, skills, overview, tip, commands]) => ({
  id: `class-${id}`, title, category: 'Classes', subtitle, tags: skills.split(' · '),
  paragraphs: [overview, tip], command: 'information', syntax: 'information',
  relatedCommands: commands, source: 'src_3.00/command1.c · global.c · class ability functions',
}));

const spellRows = [
  ['hurt', 'Hurt', 'Wind', 'A basic offensive spell from the wind realm.', 'Add an enemy as the target. This is an attack, so choose the creature deliberately.'],
  ['rumble', 'Rumble', 'Earth', 'A basic offensive spell from the earth realm.', 'Add an enemy as the target. You must know the spell and have enough magic points.'],
  ['burn', 'Burn', 'Fire', 'A basic offensive spell from the fire realm.', 'Use it against a chosen target; casting offensive magic begins or continues combat.'],
  ['blister', 'Blister', 'Water', 'A basic offensive spell from the water realm.', 'Spell damage and success are resolved by the game server.'],
  ['fireball', 'Fireball', 'Fire', 'An offensive fire spell beyond the introductory burn spell.', 'Learn it before casting and watch your magic-point reserve during a fight.'],
  ['waterbolt', 'Waterbolt', 'Water', 'An offensive spell from the water realm.', 'Target the intended creature, using its numeric selector if several share a name.'],
  ['crush', 'Crush', 'Earth', 'An offensive earth spell.', 'Its casting cost and result come from the running server.'],
  ['dustgust', 'Dustgust', 'Wind', 'An offensive wind spell.', 'Learning one realm’s spells does not mean every spell is already known. Check information.'],
  ['shockbolt', 'Shockbolt', 'Wind', 'A stronger offensive wind spell.', 'Reserve enough magic for healing or escape when planning a longer fight.'],
  ['lightning', 'Lightning', 'Wind', 'A high-tier offensive spell in the wind realm.', 'A spell still needs to be learned; its appearance in this library does not grant it to a character.'],
  ['iceblade', 'Iceblade', 'Water', 'The highest-tier offensive water spell in the original realm table.', 'Strong offensive spells consume more magic than introductory spells.'],
  ['immolate', 'Immolate', 'Fire', 'A high-tier offensive fire spell.', 'Choose a target and review the command before sending it.'],
  ['earthquake', 'Earthquake', 'Earth', 'The highest-tier offensive earth spell in the original realm table.', 'This original command uses a target; do not assume that its name means it attacks the entire room.'],
  ['flamefill', 'Flamefill', 'Fire', 'The highest-tier offensive fire spell in the original realm table.', 'Use information to check learned spells and score to check current magic points.'],
];
const utilitySpells = [
  ['light', 'Light', 'Exploration', 'Creates magical illumination around the caster.', 'Read the room after casting. Some exploration problems require equipment or other abilities as well.', false],
  ['curepoison', 'Cure poison', 'Restoration', 'Attempts to remove poison from the target.', 'Use score to review your condition. Leave the target off when casting on yourself.', false],
  ['bless', 'Bless', 'Support', 'Improves the target’s ability to hit in combat.', 'This is a temporary magical effect, not a permanent character-stat increase.', false],
  ['protection', 'Protection', 'Support', 'Improves the target’s armor class.', 'Use it before danger and follow the server’s messages about duration and restrictions.', false],
  ['mend-wounds', 'Mend wounds', 'Restoration', 'A healing spell that restores hit points.', 'Leave off the target to cast on yourself, or name another valid target.', false],
  ['invisibility', 'Invisibility', 'Exploration', 'Makes the target invisible when the spell succeeds.', 'Invisibility is distinct from hiding, and some creatures can see through it.', false],
  ['detect-invisible', 'Detect invisible', 'Exploration', 'Lets the target perceive invisible creatures and items.', 'This is the canonical spell name in the original command table.', false],
  ['detect-magic', 'Detect magic', 'Exploration', 'Helps the target recognize magical creatures and equipment.', 'Use look and the server’s descriptions to interpret what is revealed.', false],
  ['enchant', 'Enchant', 'Craft', 'Allows a mage to place an enchantment on suitable equipment.', 'The original engine restricts this spell to mages. Add the item you intend to enchant.', true],
  ['word-of-recall', 'Word of recall', 'Travel', 'A cleric spell that returns its target to the recall destination.', 'Travel can be restricted by the room or target. Review the server response rather than assuming success.', false],
  ['levitate', 'Levitate', 'Travel', 'Helps with climbing and some traps by lifting the target.', 'The original spell table calls it levitate, even where older help text says levitation.', false],
  ['resist-fire', 'Resist fire', 'Protection', 'Provides protection against fire-related danger.', 'Protection is situational; it does not make the character immune to all attacks.', false],
  ['resist-magic', 'Resist magic', 'Protection', 'Provides resistance to magical attacks.', 'Keep an eye on active effects and the server’s casting restrictions.', false],
  ['summon', 'Summon', 'Travel', 'Attempts to bring a named character to your location.', 'Add a character name and use it with your group’s agreement. Server restrictions still apply.', true],
  ['teleport', 'Teleport', 'Travel', 'Moves its target to an unpredictable destination.', 'Plan for uncertainty: this is not a route to a chosen room.', false],
];
const spells = [...spellRows.map(([id, title, realm, overview, tip]) => ({
  id: `spell-${id}`, title, category: 'Spells', subtitle: `${realm} realm · offensive magic`,
  tags: [realm, 'Offensive'], paragraphs: [overview, tip], command: `cast ${id} `,
  syntax: `cast ${id} <target>`, relatedCommands: ['information', 'score'], source: 'src_3.00/global.c · help/spellfile · help/spell.*',
})), ...utilitySpells.map(([id, title, realm, overview, tip, target]) => ({
  id: `spell-${id}`, title, category: 'Spells', subtitle: `${realm} magic`, tags: [realm, 'Utility'],
  paragraphs: [overview, tip], command: `cast ${id}${target ? ' ' : ''}`,
  syntax: `cast ${id}${target ? ' <target>' : ' [target]'}`, relatedCommands: ['information', 'score'], source: 'src_3.00/global.c · help/spell.*',
}))];

const rows = [
  ['look', 'Look around', 'World', 'Read before you move', 'look [target]', 'look', 'Room descriptions reveal visible exits, creatures, and objects. Look again when the situation changes, and inspect individual objects when clues call for it.', 'Start here on entering unfamiliar ground. The visible exits, not a compass assumption, determine where you can go.', 'help/help.2'],
  ['navigation', 'Find your way', 'World', 'Rooms and their exits', 'north | south | east | west | up | down', 'north', 'Use a direction to take a matching exit. The original engine also understands the first-letter shortcuts for the main directions.', 'Named exits may use go or enter followed by the exit name. Read look before choosing.', 'help/help.1 · help/help.30'],
  ['information', 'Character & spellbook', 'Progression', 'Know your capabilities', 'information', 'information', 'Information gives a detailed character report, including known spells. Score is a shorter report of health, magic, gold, experience, and conditions.', 'Your character’s own report is the authority on what you can currently do.', 'help/help.16 · help/help.38'],
  ['score', 'Health & progress', 'Progression', 'Your next decision starts here', 'score', 'score', 'Check hit points, magic points, gold, experience, and visible conditions. Score and health share the same original command handler.', 'Check before starting another fight, spending magic, or setting out on a difficult route.', 'help/help.15'],
  ['train', 'Train & advance', 'Progression', 'Experience is the beginning', 'train', 'train', 'Level advancement requires sufficient experience and gold, as well as the appropriate training location for your class. A new level increases health, magic, and a character attribute.', 'Find your class’s training room through exploration. The server tells you what is missing when you attempt to train.', 'help/help.46'],
  ['study', 'Learn from scrolls', 'Progression', 'Build your spellbook', 'study <scroll> [number]', 'study ', 'Study a magical scroll to learn its spell. A successfully studied scroll is consumed.', 'Read the item description and identify the intended scroll before using its numeric selector.', 'help/help.39'],
  ['inventory', 'Carry & equip', 'World', 'Prepare before danger', 'inventory', 'inventory', 'Inventory lists the objects you carry. Equipment lists worn and wielded items; use wear, wield, hold, and remove to change them.', 'Object names can be ambiguous. Use a distinctive keyword and the numeric selector when needed.', 'help/help.5 · help/help.10 · src_3.00/global.c'],
  ['search', 'Search for secrets', 'World', 'Look beyond the obvious', 'search', 'search', 'Search investigates the room for hidden things. Descriptions can hint at concealed objects or routes worth a closer look.', 'Discovery is resolved by the server. An unsuccessful search is not proof that a room has no secrets.', 'help/help.24'],
  ['prepare', 'Prepare for traps', 'World', 'One careful step', 'prepare', 'prepare', 'Prepare before entering a room where you expect a trap. The preparation applies to the next room you enter.', 'This is a timed skill and is not guaranteed protection. Dexterity and the trap still matter.', 'help/help.66'],
  ['shops', 'Browse a shop', 'World', 'A place to spend your gold', 'list', 'list', 'In a shop, list displays the goods and their prices. Buy purchases an item from that list.', 'Prefer a distinctive item keyword. When items share a keyword, add a numeric selector to buy the intended one.', 'help/help.41 · help/help.42'],
  ['sell', 'Trade your findings', 'World', 'Turn an item into gold', 'value <item> | sell <item>', 'value ', 'Pawn shops let you value and sell eligible equipment. Selling is a transaction, and the offered price can be lower than an item’s apparent worth.', 'Check value first. You must be in the correct kind of shop; ordinary rooms do not support selling.', 'help/help.43 · help/help.44'],
  ['talk', 'Talk to the world', 'World', 'Ask, listen, investigate', 'talk <creature> [keyword]', 'talk ', 'Some creatures answer questions or respond to specific keywords. Begin a conversation, then follow clues in the reply.', 'Quest clues are part of the world. This guide does not reveal hidden item locations or puzzle answers.', 'help/help.56'],
  ['save', 'Save your character', 'World', 'Keep your progress', 'save', 'save', 'The save command writes character progress through the original game server. Quitting normally also saves your character.', 'The browser’s notes and command profiles are separate from server character saves.', 'help/help.52 · help/help.3'],
  ['attack', 'Fight deliberately', 'Combat', 'Combat needs your attention', 'kill <creature> [number]', 'kill ', 'Choose an enemy in your room to attack. In the original Mordor combat model, you issue further attacks yourself instead of assuming a single command will finish the fight.', 'Watch health, action timing, and enemy responses. A creature can remember you after you attack it.', 'help/help.23'],
  ['flee', 'Leave a dangerous fight', 'Combat', 'Escape has a cost', 'flee', 'flee', 'Flee attempts to escape a room when ordinary movement is blocked by combat. In the original rules, any wielded weapon is dropped in the room you leave.', 'Plan an escape before you need it. Review the server’s result and check your equipment afterward.', 'help/help.37'],
  ['cast', 'Cast learned magic', 'Combat', 'Every class can learn spells', 'cast <spell> [target]', 'cast ', 'Cast a spell your character has learned, using available magic points. Many beneficial spells target you when no other target is named.', 'Some spells have additional class restrictions. Study, information, and the individual spell entries help you plan.', 'help/help.38'],
  ['backstab', 'Strike from hiding', 'Combat', 'Thief & assassin', 'backstab <creature> [number]', 'backstab ', 'A hidden thief or assassin can open combat with a sharp or thrusting weapon for a stronger strike.', 'Backstab does not work as a repeated attack once the target is already fighting you. Failure leaves a longer recovery.', 'help/help.45'],
  ['bash', 'Bash an opponent', 'Combat', 'Fighter & barbarian', 'bash <creature> [number]', 'bash ', 'Bash trades some direct damage for a chance to knock an opponent down and delay its response.', 'Use the resulting opening alongside your group’s actions. The skill is class-restricted.', 'help/help.51'],
  ['circle', 'Create an opening', 'Combat', 'Fighter & barbarian', 'circle <creature> [number]', 'circle ', 'Circle attempts to confuse an opponent and delay its attacks, giving you and your group a brief advantage.', 'Read the result before assuming the enemy is controlled; this is a situational combat skill.', 'help/help.50'],
  ['turn', 'Turn the undead', 'Combat', 'Cleric & paladin', 'turn <undead> [number]', 'turn ', 'Turn attempts to greatly harm or destroy an undead monster. Piety and relative levels affect success.', 'Use it on an undead target. Ordinary living enemies require a different approach.', 'help/help.62'],
  ['haste', 'Ranger’s haste', 'Combat', 'A short burst of speed', 'haste', 'haste', 'Haste temporarily raises a ranger’s dexterity, helping speed and defense.', 'The ability has a cooldown and lasts for a limited time; the game’s messages show when it is available.', 'help/help.64'],
  ['pray', 'Pray for strength', 'Combat', 'Cleric & paladin', 'pray', 'pray', 'Prayer can grant a temporary piety increase to clerics and paladins.', 'It is a timed ability, so use it when the benefit will matter rather than repeating the command continuously.', 'help/help.65'],
  ['meditate', 'Recover through meditation', 'Combat', 'Monk', 'meditate', 'meditate', 'A monk can attempt to recover health through meditation. Success is not guaranteed and the skill cannot be used continuously.', 'Check score afterward. A successful meditation is followed by a longer cooldown than a failed attempt.', 'src_3.00/command12.c'],
  ['touch', 'Touch of death', 'Combat', 'Monk · level 10+', 'touch <creature> [number]', 'touch ', 'An unarmed monk of at least level 10 can attempt a powerful touch against a valid living target.', 'Empty hands are required. It does not work on undead monsters and has a substantial cooldown.', 'src_3.00/command12.c'],
  ['say', 'Speak nearby', 'Social', 'A conversation in the room', 'say <message>', 'say ', 'Say sends your words to other characters in the room. It is useful for introductions and roleplay.', 'For a message to someone elsewhere, use tell with their character name.', 'help/help.4'],
  ['tell', 'Speak to a character', 'Social', 'Direct communication', 'tell <character> <message>', 'tell ', 'Tell addresses a named player directly, without requiring both characters to be in the same room.', 'Use the character name known to the game. The server reports whether delivery is possible.', 'help/help.17'],
  ['follow', 'Travel together', 'Social', 'Start a group adventure', 'follow <character>', 'follow ', 'Follow a character in your room to move with them through the world. The group is built around a shared leader.', 'Agree on a route before following. Movement and access restrictions are still resolved by the server.', 'help/help.18'],
  ['party', 'Review your group', 'Social', 'Know who follows you', 'party', 'party', 'Party and group show the characters following you. The lose command removes a follower from your group.', 'Use follow to join a leader and gtalk to coordinate with the group.', 'help/help.20'],
  ['gtalk', 'Coordinate the party', 'Social', 'Messages for your group', 'gtalk <message>', 'gtalk ', 'Gtalk sends a message to members of the same group. It requires a group formed around a shared leader.', 'Call out your next move, a dangerous enemy, or the need to recover.', 'help/help.57'],
  ['who', 'Find fellow adventurers', 'Social', 'The people in the realm', 'who', 'who', 'Who requests the server’s current player list. Character visibility and other server rules determine what is shown.', 'This codex never invents a player count. Connect to the realm to get current information.', 'src_3.00/global.c'],
  ['emote', 'Bring a scene to life', 'Social', 'Express your character', 'emote <action>', 'emote ', 'Emote describes an action by your character to others nearby. Social commands such as wave and smile are also available.', 'Describe your own character’s actions and leave other players room to respond.', 'src_3.00/global.c'],
  ['pledge', 'Choose an allegiance', 'Social', 'The original organization system', 'pledge <creature>', 'pledge ', 'Pledge joins the organization represented by an eligible creature. The original system changes the consequences of conflict between opposing groups.', 'Read the server’s rules before committing. Leaving with rescind can carry serious penalties.', 'help/help.72 · help/help.73'],
];

const commands = rows.map(([id, title, category, subtitle, syntax, command, overview, tip, source]) => ({
  id: `command-${id}`, title, category, subtitle, syntax, command,
  tags: [category, 'Original engine'], paragraphs: [overview, tip], relatedCommands: [], source,
}));

export const CHRONICLE_QUESTS = [
  { id: 'first-steps', title: 'Beyond the threshold', rooms: 3, level: 1, badge: 'Wayfarer' },
  { id: 'mapmaker', title: 'Ten roads remembered', rooms: 10, level: 1, badge: 'Pathfinder' },
  { id: 'apprentice', title: 'An adventurer’s calling', rooms: 3, level: 3, badge: 'Adept' },
  { id: 'veteran', title: 'A name in the chronicles', rooms: 10, level: 5, badge: 'Veteran' },
];
const chronicles = [
  {
    id: 'extension-hcommands', title: 'Your command companion', subtitle: 'Hollowdeep’s in-game command guide',
    syntax: 'hcommands [mobile|social]', command: 'hcommands', tags: ['Hollowdeep extension', 'Guide'],
    paragraphs: ['Hcommands brings a compact guide into the game terminal: exploration, combat, character progression, group communication, and the new Chronicle commands.', 'Use the original help command for the full rules behind each action. This guide does not grant abilities or change the class requirements of the commands it lists.'],
    relatedCommands: ['hcommands mobile', 'hcommands social', 'hclass', 'hquest', 'help'],
  },
  {
    id: 'extension-hclass', title: 'A calling of your own', subtitle: 'Class guidance inside the realm',
    syntax: 'hclass [class-name|progress]', command: 'hclass', tags: ['Hollowdeep extension', 'Classes'],
    paragraphs: ['Hclass displays guidance for your current character’s class. Name any of the ten original playable classes to read its guide instead, such as hclass mage or hclass ranger.', 'This is a reference command. It does not change your class or grant skills. Gain experience and gold through the original game, then train in the appropriate class training room when ready.'],
    relatedCommands: ['hclass progress', 'hclass mage', 'information', 'train'],
  },
  {
    id: 'extension-hquest', title: 'The Hollowdeep Chronicles', subtitle: 'Four journeys. Four earned honors.',
    syntax: 'hquest [list|status|next|survey|accept <id>|claim <id>]', command: 'hquest', tags: ['Hollowdeep extension', 'Exploration', 'Cosmetic badges'],
    paragraphs: ['Accept a Chronicle with hquest accept <id>, then explore the actual game world. Use hquest survey in each new room to record it. A real room counts only once, and repeating a survey in the same place gives no extra progress.', 'Each Chronicle requires a number of unique surveyed rooms and a real character level. Earlier surveys count toward later accepted Chronicles. When both requirements are met, use hquest claim <id> to earn its badge once.', 'Accepted Chronicles, surveyed places, and claimed badges persist in the game host’s separate Chronicle journal. It holds up to 128 unique rooms. These honors are cosmetic: they do not award gold, experience, or class abilities.'],
    relatedCommands: ['hquest next', 'hquest accept first-steps', 'hquest survey', 'hquest claim first-steps', 'hprofile'],
  },
  {
    id: 'extension-hprofile', title: 'Your place in the chronicles', subtitle: 'Recorded places and earned badges',
    syntax: 'hprofile [status]', command: 'hprofile', tags: ['Hollowdeep extension', 'Character honors'],
    paragraphs: ['Hprofile shows the number of unique places recorded in your Chronicle, your current character level, and the badges you have claimed. The information comes from the game server’s persistent journal.', 'Use hquest to review your active Chronicles and claim a completed goal. A badge can be earned only once. Badges do not replace your original character statistics, title, class, gold, or experience.'],
    relatedCommands: ['hprofile status', 'hclass progress', 'hquest status', 'score'],
  },
].map(entry => ({ ...entry, category: 'Chronicles', extension: true, source: 'engine/extensions/hollowdeep.c' }));

const advanced = [
  {
    id: 'extension-hstance', title: 'Choose your fighting stance', category: 'Combat', subtitle: 'Accuracy, defense, and a growing advantage',
    syntax: 'hstance [balanced|guarded|aggressive]', command: 'hstance', tags: ['Hollowdeep extension', 'Physical combat'],
    paragraphs: ['Aggressive improves physical accuracy and makes you easier to hit. Guarded improves defense and reduces accuracy. Balanced applies neither modifier. The equal tradeoff grows from 1 point at levels 1–4 to 2 at levels 5–9 and 3 from level 10.', 'A stance persists between sessions. Wait 20 seconds after an attack, spell, or stance change before switching. Stances do not change spell damage, base stats, experience, or the original character-file format. Install the native update before using this command.'],
    relatedCommands: ['hstance balanced', 'hstance guarded', 'hstance aggressive', 'hclass progress'], source: 'engine/extensions/hollowdeep_stance.c',
  },
  {
    id: 'extension-hstaff', title: 'Appoint the realm’s staff', category: 'Staff', subtitle: 'Owner, admin, moderator, and player roles',
    syntax: 'hstaff whoami|list|audit|grant <name> <role>|revoke <name>', command: 'hstaff whoami', tags: ['Hollowdeep extension', 'Roles'],
    paragraphs: ['The configured founder starts as owner. Owners may appoint owners, admins, or mods; admins may appoint mods. Players can check their own role. Targets must have a saved character, and nobody can change their own role or demote the protected founder.', 'Roles control these Hollowdeep tools; original Mordor DM/caretaker powers remain separate. Admins and owners can inspect the recent action audit. Install the native update before using this command.'],
    relatedCommands: ['hstaff list', 'hstaff audit', 'help hstaff'], source: 'engine/extensions/hollowdeep_staff.c',
  },
  {
    id: 'extension-hmoderate', title: 'Care for the community', category: 'Staff', subtitle: 'Announcements and measured moderation',
    syntax: 'hmoderate announce <text>|mute <name> [minutes]|unmute <name>|kick <name>', command: 'help hmoderate', tags: ['Hollowdeep extension', 'Moderation'],
    paragraphs: ['Mods, admins, and owners can announce, mute, unmute, or kick lower-role characters. Mutes default to 10 minutes, accept 1–1440 minutes, and survive reconnects. Muted characters can still explore, fight, save, and quit.', 'Kick uses the original disconnect and save path. It does not delete a character or ban reconnecting. Peers, higher roles, and the founder are protected. Install the native update before using these tools.'],
    relatedCommands: ['hstaff whoami', 'hstaff list', 'help hmoderate'], source: 'engine/extensions/hollowdeep_staff.c',
  },
].map(entry => ({ ...entry, extension: true }));

export const CODEX_ENTRIES = [...classes, ...spells, ...commands, ...chronicles, ...advanced];
export const CODEX_CLASS_COUNT = classes.length;
export const CODEX_SPELL_COUNT = spells.length;

/** Search every word across useful content; normalize Unicode and cap work. */
export function searchCodex(query = '', category = 'All') {
  if (!CODEX_CATEGORIES.includes(category)) return [];
  const words = String(query).slice(0, 300).normalize('NFKC').toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  return CODEX_ENTRIES.filter(entry => {
    if (category !== 'All' && entry.category !== category) return false;
    const haystack = [entry.title, entry.subtitle, entry.syntax, ...entry.tags, ...entry.paragraphs].join(' ').normalize('NFKC').toLocaleLowerCase();
    return words.every(word => haystack.includes(word));
  });
}

export function commandHref(command) {
  if (typeof command !== 'string' || !command.trim() || !command.isWellFormed() || new TextEncoder().encode(command).length > 256 || /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/u.test(command)) return '/';
  return `/?command=${encodeURIComponent(command)}`;
}
