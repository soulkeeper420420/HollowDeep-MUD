# HollowDeep Gameplay and Wilderness Vision

AtlasMUD screenshots are design references, not content to copy.

## Wilderness
- An original, interconnected overland world
- Readable terrain maps and recognizable landmarks
- Forests, mountains, rivers, swamps, deserts and coastlines
- Roaming encounters, hidden routes and dangerous regions
- Weather, day/night, resources and wilderness exploration
- Connected settlements, dungeons, guilds and quest locations

## Character and Gameplay Systems
- Detailed attributes, proficiencies and magical realms
- Expansive spells, abilities, skills and passive skills
- Equipment slots, visible equipment and meaningful item bonuses
- Colored inventory and detailed item identification
- Clans, ranks, banks, halls, permissions and wars
- Secure DM help, administration and building commands

## World Expansion
- Target at least 9,000 playable rooms
- Audit native room capacity before increasing room IDs
- Preserve existing rooms, exits, monsters and inventories
- Build regions in validated batches
- Verify high-numbered rooms in isolated native gameplay
- Never change production without explicit authorization

## Future Treasure Maps

Players find treasure maps, follow wilderness clues, locate hidden chests and defeat their guardians. Each chest instance will use a unique claim ID and bind its unlock to a verified guardian defeat. Decide eligibility and contribution rules before implementing group claims.

A server-authoritative claim will commit the claim ID and exact randomized reward together with delivery state. A resumed or retried claim must reuse the reward and recognize a delivery already committed to the recipient. Replays, restarts and concurrent claims must never generate a second reward. Test crash recovery between unlock, reward selection, character persistence and claim completion before enabling rewards.

Reward pools may include enchanted weapons, armor, magical items, gems, crafting materials and rare artifacts. Treasure combat and loot delivery are planned for a later round.
