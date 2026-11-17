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
allowed class entries are symbolic keys for review. Actual reference
resolution, importing native entries and generation against the pinned
engine tables belong to the next integration step.
