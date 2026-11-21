# Round 72 · Wilderness terrain and exploration

Generate a region in the private World Builder from an editable native entrance room and an unused contiguous block of IDs in 10000–15999. Enter a seed from 0 through 2147483647 to generate terrain. A blank seed retains the Round 71 grid. The first column forms a road. Rivers and mountains interrupt some north/south paths. East/west paths connect each row to the road.

Select a mapped room to edit its terrain and landmark or preview its region. Apply the map edits before exporting the draft or Native Area ZIP. Changing a tile label keeps the authored exits and room descriptions. Coordinates follow column east and row south, beginning at (1,1).

Use `map` when standing in a mapped native room. It shows the region, current coordinates, a seven-by-seven map, the terrain legend, and the current landmark. The map reveals terrain for adjacent tiles with native exits and marks other nearby tiles as unscouted. The view reflects the current room on each use. Native ANSI preferences control color. The map derives visibility from the current room each time. It stores no exploration history.

## Native compatibility

Review and apply `patch_native.py` to a disposable copy of the private Mordor 3.00 source. It records the 16000-entry room capacity, five-digit native builder input, reserved range rules, staff teleport boundary, and legacy random spell destination range. The loader and cache keep their existing array bounds and the room ABI stays unchanged. Existing random teleport destinations remain within 1–8999. The builder prevents new allocation in 9000–9999.

The ZIP carries `rooms/wilderness.map` with its own manifest SHA-256. Each line after `HDW1` contains the room ID, column, row, terrain symbol, region and landmark separated by tabs. This asset describes the entire mapped draft included in that ZIP. Assembling multiple exports into one world would require validating their combined map before staging it. The private tests use a single export.

## Changelog

- Added deterministic forests, plains, mountains, swamps, rivers, roads and ruins.
- Added map metadata editing, an area preview and export validation.
- Added the native player map and version-controlled changes to build the expanded engine.
- Added seed, topology, metadata, browser export and native navigation checks.

## Isolated validation

Run `bash tools/world-builder/round72/private.sh` from the documented Round 71 fixture environment and a disposable Linode checkout. The harness recompiles the private engine and runs browser and native gameplay tests in disposable roots. It compares protected live source, room and object/monster file hashes, the active executable hash, and service identity before and after, then reports the result. Raw fixtures and logs remain private.

## Discord announcement draft

**HollowDeep development update — Wilderness maps**

Round 72 adds seeded wilderness regions with roads, forests, mountains, swamps, rivers, plains and ruins. In the private test world, typing `map` during a journey shows your position, nearby terrain, coordinates and landmarks. Builders can preview and edit the region before exporting it for testing.

A future update will let players discover treasure maps, follow wilderness clues and defeat guardians to claim hidden rewards. Round 72 is a development milestone.
