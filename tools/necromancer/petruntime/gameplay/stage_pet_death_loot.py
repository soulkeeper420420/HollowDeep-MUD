"""Drop independent pet loot only after native combat death."""

def stage(source):
    p=source/'creature.c'
    s=p.read_text(encoding='latin-1')

    anchor='        hd_necro_skeleton_death(crt_ptr);'

    assert s.count(anchor)==1

    s=s.replace(anchor,anchor+r'''
        /* Companion state has already been removed durably.
           Do not capture another corpse or copy victim loot. */
        if (crt_ptr->parent_rom) {
            object *reward = NULL;
            long amount = 1 + MAX(0, MIN(60, crt_ptr->level))/10;

            while (crt_ptr->first_obj) {
                object *item = crt_ptr->first_obj->obj;
                if (!item) break;
                del_obj_crt(item, crt_ptr);
                add_obj_rom(item, crt_ptr->parent_rom);
            }

            if (load_obj(0, &reward) >= 0 && reward) {
                reward->value = amount;
                sprintf(reward->name, "%ld gold coins", amount);
                add_obj_rom(reward, crt_ptr->parent_rom);
            }
        }
''',1)

    p.write_text(s,encoding='latin-1')

    print('PASS: Independent combat-death loot staged',flush=True)
