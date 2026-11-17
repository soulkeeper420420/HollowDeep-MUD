# HollowDeep race and class definitions

Use these editable JSON drafts to plan and review character content. The
same commands support a new definition and edits to an existing JSON
definition. They leave the MUD source, native IDs, and game saves alone.

```sh
python3 content.py new race deep-dwarf 'Deep Dwarf' deep-dwarf.json
python3 content.py new class spellblade 'Spellblade' spellblade.json
python3 content.py check deep-dwarf.json
python3 content.py preview spellblade.json
```

To edit, copy the accepted JSON to a draft, keep its kind and key, and
change the desired fields. Review it with
`python3 content.py preview draft.json --against accepted.json`.
Definitions start with `selectable: false`. Ability, trait, equipment and
allowed class entries are symbolic keys for review. Reference resolution and generating brand-new native entries belong to
the next integration step.

## Import and preview an existing native entry

Use a development source directory containing `mtype.h`, `global.c` and
`command1.c`.

```sh
python3 native.py export ./src race dwarf dwarf.json
python3 native.py export ./src class mage mage.json
python3 native.py preview ./src dwarf.json
```

Permitted native edits currently include display labels, starting racial
attribute offsets, and class HP/MP gained per level. Keep the exported key
when renaming a display label. The existing creation menu text, input
selectors, adjectival race names, and saved numeric IDs remain the same.
Class growth edits apply to future level gains and preserve existing saved
HP/MP. Unsupported field changes and new native keys are rejected.
The preview prints a unified diff and leaves the source directory alone.
