# Base class and race expansion

Expand the starting roster before implementing special-class remort recipes. These are initial design proposals. Verify the current playable roster and class and race IDs against the deployed Round 74B source before assigning identifiers or building any content.

## Proposed base classes

| Class | Role | First distinctive mechanic |
|---|---|---|
| Alchemist | Preparation and party support | Brew a limited batch of field tonics and choose which ones to bring into a dungeon. |
| Warden | Route control and protection | Establish a temporary camp ward that protects resting allies. Placement and timing matter. |
| Runecaller | Deliberate spellcasting | Inscribe a rune on a room or an object, then trigger it later for a ward, light, or detection effect. |

### Additional base-class candidates

| Class | Role | First distinctive mechanic |
|---|---|---|
| Pugilist | Close-range control | Choose one hold at a time to pin, disarm, or shove an opponent. A heavy opponent can break loose. |
| Hexbinder | Reactive spellcasting | Place a hex that triggers when an enemy casts, flees, or strikes an ally. Choosing the right trigger matters. |
| Spiritcaller | Single-companion tactics | Bind one spirit and give it an explicit order such as guard, distract, or scout. It performs one role at a time. |
| Beastkeeper | Combat with a trained animal | Use a living companion that learns commands through play. Choose a companion for pursuit, defense, or support. |
| Siege Engineer | Deployable tools | Set up a brace that holds a doorway or a winch that moves a heavy obstacle. Devices take time to deploy. |
| Spellbreaker | Anti-magic melee | Study an enemy cast and choose whether to interrupt it or briefly shield an ally from its effect. |
| Wayfarer | Party travel and logistics | Mark a safe return point and lead allies back along routes the party has already opened. |

Spiritcaller and Beastkeeper are distinct proposals. Spiritcaller issues short-lived tactical orders to a bound spirit. Beastkeeper invests in training a persistent animal companion. Check for overlap with the current playable roster before selecting either.

### Further base-class candidates

| Class | Role | First distinctive mechanic |
|---|---|---|
| Chronomancer | Timing and turn control | Delay one incoming hit for a round, giving the party time to heal or shield the target before it lands. |
| Standard-Bearer | Party positioning | Plant a banner that supports allies in your room. Move it as the fight shifts to another room. |
| Lancer | Reach and momentum | Build momentum by advancing into a fight, then spend it on a thrust. Getting blocked or pinned breaks momentum. |
| Threadmender | Damage management | Link yourself to an ally and take on part of their damage, then spend actions mending the strain. |
| Gambler | Risk and resource management | Draw a card and choose to take its modest effect or wager a second draw for a stronger payoff with a setback on failure. |
| Monster Scholar | Enemy analysis | Observe a foe to learn a tell, then share it so allies can recognize and exploit the same opening. |
| Relic Hunter | Dungeons and salvage | Salvage a discovered relic for parts or keep it intact and take it to an appraiser to uncover its history and function. |
| Storm Channeler | Terrain-sensitive casting | Choose whether to store a charge for a later fight or spend it now. Rain and exposed terrain change how the charge behaves. |

For an early Monster Scholar playtest, give one creature a readable tell and a short opening the whole party can use. Test the mechanic before expanding it to other monsters.

### Classic fantasy base-class candidates

| Class | First distinctive mechanic |
|---|---|
| Necromancer | Reanimate a defeated monster as an undead pet. Higher-level Necromancers raise more reliably and can command more pets. Successful raises award bonus XP. |
| Warlock | Borrow power from a patron. Cast a stronger spell by spending a limited pact charge. |
| Vampire | Drain health from a foe to build a blood reserve. Spend it to heal yourself or power an ability. |
| Witch | Curse enemies or brew remedies. Switch between curses that weaken a foe's attacks, defenses, or healing. |
| Shaman | Place one totem that heals allies, protects them, or damages enemies in the room. |
| Druid | Shift into a wolf for offense or a bear for defense, then return to your normal form to cast. |
| Sorcerer | Choose an elemental affinity and build a spell list around fire, frost, or lightning. |
| Berserker | Build rage by dealing and taking damage. Spend it on a heavy strike or a burst of attacks. |
| Demon Hunter | Mark a demon or undead enemy to expose a weakness the party can exploit. |
| Death Knight | Strike with a cursed weapon to build power for a self-heal or an unholy strike. |

Proposed Vampire implementation uses a playable base class independent of the character's race. Check for overlap with existing classes such as Barbarian before adding Berserker as a separate class. Review all names against the deployed roster before assigning IDs.

### Starting and rebirth skills

Each class starts with its first skill at level 1. Completing a life in the class and successfully rebirthing earns its second skill once in the Past Lives journal. The earned skill can be equipped in the existing proposed single inherited-skill slot, including on a later return to its original class. Inherited skills use a cooldown when carried into a class that lacks the original resource. Set costs, durations, and damage after a private playtest. Room-wide hostile skills affect only eligible enemies already in combat with the player or their party. Effects from repeated casts of the same aura refresh its duration without stacking.

| Class | Level 1 | Earned on rebirth |
|---|---|---|
| Necromancer | **Raise Corpse** — Reanimate a defeated monster as an undead pet. Raise additional corpses up to your active pet limit. | **Graveburst** — Channel a pulse of grave energy that damages enemies already fighting your party in the room. |
| Warlock | **Pact Bolt** — Fire a bolt and spend an optional pact charge to empower it. | **Pactbrand** — Enchant your weapon so its next landed hit releases a burst of pact damage. |
| Vampire | **Blood Drain** — Drain a foe to fill your blood reserve and spend some of it to heal yourself. | **Crimson Veil** — Surround yourself with a short aura that drains a small amount of health from enemies who strike you. |
| Witch | **Wither** — Curse one foe to weaken its attacks briefly. | **Witchfire** — Enchant an ally’s weapon so its next landed hit reduces the target’s healing received. |
| Shaman | **Healing Totem** — Place one totem that periodically heals allies in the room. | **Spirit Ward** — Project a short aura that reduces elemental damage taken by nearby allies. |
| Druid | **Wolf Form** — Shift into a wolf for faster melee attacks and return to your normal form to cast. | **Briar Ring** — Root enemies already fighting your party in the room without affecting their ability to attack. |
| Sorcerer | **Elemental Bolt** — Fire a bolt attuned to fire, frost, or lightning. | **Elemental Surge** — Release a room-wide burst against engaged foes. Fire burns, frost slows, and lightning can arc to a second target. |
| Berserker | **Rage Strike** — Build rage in combat and spend it on a heavy melee hit. | **War Cry** — Give yourself and nearby allies a brief damage boost. Repeated cries refresh the effect. |
| Demon Hunter | **Hunter’s Mark** — Mark a demon or undead enemy to expose a weakness your party can exploit. | **Silver Edge** — Enchant your weapon so its next few strikes deal bonus damage to demons and undead. |
| Death Knight | **Unholy Strike** — Strike with a cursed weapon and build power you can spend on a small self-heal. | **Grave Guard** — Raise an aura that absorbs part of the next hit you or a nearby ally takes. |

## Proposed races

| Race | Connection to HollowDeep | First racial feature |
|---|---|---|
| Deepkin | Communities near the flooded passages beneath Oceancrest | Recognize submerged routes and currents that other characters can still learn about through exploration. |
| Stoneborn | Settlements in the deep stone halls | Read quarry marks that reveal unstable tunnels and alternate routes. |
| Thornkin | Woodland communities near the old roads | Recognize useful plants and harvest a small supply of ingredients. |

Consider one modest stat adjustment and one clear utility trait per race after reviewing the existing race balance. Keep class and race selection independent unless a specific lore requirement calls for a restriction. Make each base class playable from character creation with a starter kit, a distinctive early command, a clear training path, and help text.

## Proposed first playtest

Start with Alchemist and Deepkin. Build an isolated ELF32 candidate, create characters with the new options, exercise each new mechanic, and verify help, training, save and reload, and legacy-character compatibility. Check existing ID mappings, serialization, class and race bounds, NPCs, equipment restrictions, and display tables before extending the roster. Review the remaining proposals after the first pair is playable. Production deployment requires separate approval.

### First implementation milestone

Necromancer is the first class selected for an isolated playtest. Start with character creation, a visible class title, and save/reload, then playtest Raise Corpse before expanding the toolkit. Reuse the native pet and follower lifecycle where it supports multiple controlled monsters. Graveburst remains a proposed rebirth unlock.

#### Raise Corpse playtest design

- `raise corpse` selects an eligible monster corpse in the room. `raise corpse <monster>` selects a particular corpse when several are present. Each successful cast adds one undead pet up to the active limit.
- The pet keeps the monster's name and basic combat role, such as an undead wolf that bites or an undead troll that hits hard. First-pass pets use capped stats and ordinary attacks. Player corpses, boss corpses, and summoned creatures are excluded. Raised pets earn their own XP from eligible kills and drop loot when killed in combat. Pet-assisted kills use normal owner and party XP credit, with each kill counted once.
- Pet slots unlock at the following Necromancer levels. Reaching the cap rejects the command before a revival roll. Use existing pet orders where possible and support selecting a particular pet for dismissal or orders.

  | Level unlocked | Active pet cap |
  |---:|---:|
  | 1 | 3 |
  | 7 | 4 |
  | 14 | 5 |
  | 20 | 6 |
  | 27 | 7 |
  | 34 | 8 |
  | 40 | 9 |
  | 47 | 10 |
  | 54 | 11 |
  | 60 | 12 |

- Suggested first-pass Raise Corpse bonus is 10% of the monster's ordinary XP value, awarded to the Necromancer once on a successful raise and subject to normal XP limits. Failed raises award zero XP. Track pet XP for the pet's lifetime. Pet ranks and their effects are open for playtesting.
- On combat death a pet drops its own loot once. The original corpse retains its original loot. Dismissal, logout, expiry, and restart do not generate drops. A dead raised pet cannot be raised again.
- Proposed revival chance is 50% + 1 percentage point per Necromancer level above 1 + 5 percentage points per level the Necromancer is above the monster. Monsters above the Necromancer's level subtract 5 points per level. Clamp the result to 10–95%. A level-10 Necromancer gets 59% against a level-10 monster, 84% against a level-5 monster, and 34% against a level-15 monster.
- Give each eligible corpse one actual revival roll so repeated casts cannot guarantee success. A failed roll leaves the corpse lootable but spent for revival. Validation failures, including a full pet roster, do not spend a corpse. Preserve corpse loot and ownership through revival. Pets are temporary and disappear on dismissal, death, logout, or restart.
- In an isolated gameplay replay, exercise qualifying and rejected corpses, chance boundaries, pet cap unlocks, pet XP and normal owner credit on a kill, once-per-corpse raise XP, pet death drops, original loot preservation, and cleanup across movement and logout. Review the corpse lifetime and follower code before wiring it into the private build.

The creation prototype uses the existing Mage combat and training rules and stores a distinct Necromancer identity in the atomic player-save trailer. The current native class number is also used in staff authority comparisons, so the prototype leaves numeric class and race IDs alone. The prototype is opt-in for the private build. Local ELF64 compilation and native persistence checks passed. The ELF32 build and interactive creation replay still require Linode. See [build-and-check.sh](../../tools/necromancer/build-and-check.sh).
