# HollowDeep Round 73 — Treasure encounter foundation (not yet playable)

**Base:** Round 72 `34f3b95fc51afd701ece16b514409c1ba8d56d32` on branch `round72-wilderness`.

## What this milestone enables

World Builder drafts may include a top-level `treasure_sites` list. Each site is attached to a **mapped wilderness room**, names one to five valid monster **templates**, declares a chest label and rarity tier, and contains a clue for a future physical treasure-map item. Existing native templates, rooms and exits remain untouched.

```json
{
  "treasure_sites": [
    {
      "site_id": "copper-cache",
      "room_id": 10002,
      "guardians": [7, 9],
      "chest_label": "Copperbound Chest",
      "tier": "rare",
      "clue": "Beyond the cairn, seek the eastern shadow."
    }
  ]
}
```

The site list is placed alongside the existing `rooms` and optional `custom_templates` keys in the World Builder plan, not inside individual room records. Use the existing validated JSON editing functionality until a visual treasure-editor UI is implemented. The guardian numbers are template IDs; a native encounter must create **unique spawned guardian instance IDs** before unlocking loot. Do **not** add an ordinary pickupable chest as a permanent object placement. A versioned `rooms/treasure_sites.json` asset is included in the candidate ZIP with SHA-256 in `manifest.json`.

The independent `claim_ledger.py` is a **private, non-networked state-machine prototype**: map ownership binds an encounter, only the specific spawned guardians can clear the lock, a single claim ID and exact server-authored reward snapshot survive retries/reopens, and the same claim is returned under concurrent requests. An item reward may contain a bounded enchantment descriptor, but this module does **not** create native items or make them appear in inventory.

## Critical security/integration boundary

**Do not enable real rewards from this code alone.** The current Mordor 3.00-derived engine has not yet been wired to the ledger. Before a guardian-protected chest can appear in live gameplay, the native engine must:

1. Create unique encounter, map-item and spawned guardian **instance IDs**; verify the player's possession of the bound map.
2. Call the private ledger **only for trusted completed combat kills** (not for claimed kills or template IDs from players).
3. Intercept **all** native `get`, `take`, `open` and equivalent chest/loot paths, rejecting them while the encounter remains locked. Do not allow normal room object placement to bypass this check.
4. Generate only server-chosen, ABI-valid reward templates and enchantment modifiers, enforcing wear slots, item ranges, inventory capacity and balancing. Clients must never choose reward data.
5. Persist player inventory/save **idempotently using the exact claim ID** before acknowledging delivery. SQLite's single pending claim prevents multiple reward *decisions*, but it cannot by itself guarantee exactly-once delivery across an external native save and a process crash. A replay must see the claim ID already recorded in the player save and must not recreate an item. Test crash/restart in every interval between combat, claim, native save and acknowledgement.
6. Decide party/assist credit and timeout/reset policy; Round 73 currently binds claims to one map owner and has no group distribution.

## Validation and publication

`test_treasure.py` covers blueprint rejection, metadata determinism, guardian ownership, kill-event replay, early-claim denial, identical concurrent claims, exact reward persistence, and replayed receipts. Run it locally with:

```bash
cd tools/world-builder/round73
PYTHONPATH=../round57 python3 -m unittest -v test_treasure
```

The supplied isolated continuation script adds the new module to Round 72's disposable Linode test runner, reruns all existing browser and native gameplay checks, compares protected production hashes, and **commits/pushes only if everything passes**. Native guardian/chest interception remains a future implementation gate even after the suite passes.

No production deployment, production server restart, or live-world modification is permitted.

## Next executable milestone

Round 73B: inspect native C combat/get/open/save code; implement actual instanced encounter + map reading + chest lock in isolated engine; use a disposable test world to prove guardians block pickup, each death unlocks progressively, loot cannot be duplicated by replays, and enchanted gear equips after durable character save. Follow with browser map clue UI and optional party logic.

## Discord announcement draft (development preview, not a playable release)

**HollowDeep development — Treasure hunts (Round 73 foundation)**
We're developing original treasure maps for the wilderness: follow location clues, challenge guardian encounters, and eventually unlock chests containing gold, materials and enchanted gear. The private foundation now validates treasure sites and tests durable one-time claim records. Native guardian combat, chest interaction and actual reward delivery are still being built and **are not live**. Production remains unchanged.
