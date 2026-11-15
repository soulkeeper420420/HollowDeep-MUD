# Round 70 — Quick Room Creation

The private World Builder now offers **Create & Connect Room** inside
**Create a new room**. Select a source room, enter an unused ID in the
8900–8999 range and a name, choose a standard exit direction, then click
once to create the room and its reverse exit. The UI selects the new
room, clears the name input and advances to the next candidate ID.

The entire proposed plan is validated by the same server endpoint as the
other building controls; invalid IDs, conflicting exits, or stale edits
cannot partially mutate the draft. Existing rooms, placements, saved
drafts and custom templates are preserved. The new action participates
in the existing unsaved-edit confirmation and recovery system.

`round59/browser.cjs` covers success, duplicate ID rejection, conflicting
exit rejection, unsaved edit cancellation, and downloaded ZIP export.
`round59/replay.py` verifies exported binary records and makes a player
navigate up into the new room and back down in a disposable native world,
then continues the existing Round 59–69 regression suite.

Production source, rooms, template banks and the service are read-only;
`round59/private.sh` hashes them and confirms the server has not restarted.
