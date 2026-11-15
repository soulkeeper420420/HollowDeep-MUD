# Round 71 — Native World Capacity and Wilderness Foundation

## Goal and scope

Make HollowDeep capable of building the first connected wilderness region in a **disposable world**, while retaining Round 59–70 editor features. A 16,000-ID native engine candidate is prepared privately from the Linode's existing Mordor 3.00 source with `RMAX` changed from 9000 to 16000. This candidate is **not** installed in production.

## World IDs and safety

- Existing: room IDs found in the baseline, including the older 8900–8999 private-creation range, remain valid.
- Extended region creation: IDs **10000–15999** only when `HD_ROUND71_EXTENDED_ROOMS=1`; native room IDs must remain below the private 16,000-ID engine limit.
- IDs 9000–9999 remain reserved pending investigation of legacy r09000 and r09999 files.
- Default World Builder behavior retains the 50-room cap and former new-room range; private expanded mode allows 200 rooms per plan.
- No generation or export is a production deployment. It is a validated ZIP candidate only.
- `wilderness_grid.grid()` takes an existing validated plan, deep-copies it, rejects collisions, and creates up to a 10×10 grid connected by cardinal reciprocal exits; the anchor connects up/down to the first cell. Existing rooms, exits, inventories, native templates, and drafts are preserved.

## Browser editor

The private World Builder has **Generate wilderness region**. Select an existing anchor, the first unused 10000–15999 ID, grid dimensions, a short region name, and an up/down entrance. The new API `/api/wilderness-grid` validates the entire candidate and returns it atomically. Unsaved edits are protected by the existing dirty-state confirmation and browser undo/recovery behavior.

## Verification

`private.sh` runs existing Python and Chromium regressions, a 100-room generation and rejection test, a browser-created 4×4 wilderness ZIP export, and a 16,000-ID native engine run that moves through the new region and back. Uses a disposable copy of the previously verified Round 59 native world; no old player saves or private logs are published. The script records production hashes and service identity, and commits only explicitly approved source files after every test passes.

## Next direction

The 4×4 generator uses coordinate-based room names and basic terrain descriptions. Further wilderness work will add distinctive terrain tiles, an ASCII map with player location, encounters, geography, resource gathering, weather, day/night changes and quests. AtlasMUD screenshots inform design goals, but HollowDeep uses original worldbuilding and assets.
