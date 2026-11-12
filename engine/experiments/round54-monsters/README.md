# Round 54 monster placement

This stage extends the existing Round 53 area builder. Put this directory beside `round53-area-builder` under the private world-forge directory. Compile `layout.c` with `gcc -m32 -I<verified-native-source> layout.c -o layout` and run `./layout > layout.json`. Populate `templates/` with private copies of the world's `objmon/mNN` monster records. Run `python3 app.py --test`, then start `python3 app.py` for the loopback builder on port 8782.

Each placement uses one native permanent slot per creature, with ten slots per room. Omitted placement data preserves the baseline. An explicit empty list removes all permanent placements. Unchanged slots retain their timing data. Embedded creature, inventory, object, exit and description records are verified by the inherited native exporter and a second native serializer round trip.

Linode verification passed the three Round 53 reciprocal exports, validated 747 native templates, tested add/count/remove and invalid IDs, and downloaded and verified a two-room ZIP through the HTTP endpoint. The initial HTTP export exposed a missing export directory, which was created and added to startup. Native gameplay spawning and the remaining playable-area sections are pending.
