#!/usr/bin/env python3
"""HollowDeep private pet runtime integration. No production file or process changes."""
from pathlib import Path
import hashlib, os, shutil, subprocess, sys, tempfile, runpy, resource
ROOT=Path('/root/hollowdeep-dev')
EXPECTED={'Makefile': '00fd4b67459f439ebf46b4bdf800a2bb13c23331c8d27d6dc57d61afe81731dc',
 'atomic_player_snapshot.c': '20f570c93e84de1f5fb57d80556accd690ef1c23600641e4df25f69e5bf9bfa2',
 'atomic_player_snapshot.h': '6762d2f547d11e427defa2fb170fab147019448d65fae549db2b1432bb5201e2',
 'combat.c': 'fd5c63641329e4bca9ee431a5a2adf0152450f3f155d71de2e01bfc677861287',
 'command1.c': '01d250cd576b13898a83401b01410973c424b53182bbcd664249d072a4ddf8d5',
 'command2.c': 'd084e5aee544013b48e18b584c5315b1d698e32397c5c3434112c4583e6ddd52',
 'command5.c': 'e8d12345154e70051185445dd7e4ec38278c2a0294210e2b5d15ba652dffe477',
 'compress.c': 'b906eb9ae5e4319fde4693142d0189c4b8e47985eb7357d3042774dfe12dd9b9',
 'creature.c': '3fdd4c14e56e1e84a512bd78b71f95ffd360d54279787129be6775ce8ca511d9',
 'files1.c': 'd54386bd9d0c57ab6e947c06afa49e7847ace2beff6f88c826cb4ff32c465799',
 'files2.c': 'b72e78e3ce0e59f8a543ec9020aaafc440ff03e823ce5886258312e83f7d51c5',
 'files3.c': '6961a6439c3d561d02a0c7ea4a7b1c4a4d9368b87f60f808c1ec72d868d51b8f',
 'global.c': '55d7891e1d8766e4dc23b5d24cb3d0655f8ae7f33a39a8f649b7dcc72f97c894',
 'hd74_xp.c': 'c4045eaea261f93e6f874ceb5e79afd90a97492d6b31e63680594a0abcce0cd0',
 'hd74_xp.h': '788a262b1b1fa6e08a6bc1fba8c2cc6d524af63ded2b34c77e20ea131d418265',
 'hd_corpse.c': '8fa9fde462ee588838d50c60d82de9fd4f34ad0e85a648839bf752208829cb09',
 'hd_corpse.h': 'fa3f15ba1ef23b7bda9d1014c67882807a14a6f4d1c5b0575b49a49e79581ffd',
 'hd_deity.c': '5fcd61ce961336d182702a55f4cee92aa5b9d544447147f2cfd8297cf75a80c7',
 'hd_deity.h': '475669181260f3d2eb157a29799e31ebd17761c96dfb7c5d4ae814a19fe63450',
 'hd_necro_skeleton.c': '74083ff5e5d7171f5b22217173b766904fe0a39dad6e196ac9744fe71064efe3',
 'hd_necro_skeleton.h': '4ef4a33e61595cbd6061e4e2072e80efcc15a4d709f04afded534aba1e5385b2',
 'hd_pet_store.h': '91afd3bfad4f968f07050b5f18f5ecba591ec04ded617cc7ea243eae6f7a3f5a',
 'hd_pet_store.inc': '504b9500752b0d9eaf5b462638871faa46880eb272cc86dc4fb7d9c49938a59e',
 'hd_player_store.c': '36be86735ec7061977c385c0a419e568ad4ec4daa3d639cff5da11278546acc4',
 'hd_player_store.h': '9efea61baf56f09cf727d032636efaefe17ebc61226323113c83c3c7361d4c3a',
 'hollowdeep_bonus.c': 'd38cb97a2195458d7dc84f78c4d69624e17c7ee4b16688663635ed00240c6cba',
 'hollowdeep_bonus.h': '617bfb34aef37ddd2fa3567046dfcb90237aff194c7f15e1d7f55ccb7f9cd8b8',
 'hollowdeep_help.c': '30aa4a6d0482cfd16a1625bf439c4058a4aa03d917849d6f90da724a1c75f3f8',
 'hollowdeep_help.h': '5e7f6f0a13bed3e650702552b98c55bfcab89cbb241a8dc561d518e34cb47499',
 'hollowdeep_staff.c': 'dd861f148274acbe0e4056c8c4e10749f08499300d00b602aaa4e53daf833b9b',
 'hollowdeep_staff.h': '925a2c31a35e9c8823ecf32956441c3d232ca6b35e008c45673bf3a924b7578b',
 'io.c': '3204f844be57da19b72a05ab435fe30bd236384e5f2dec7c5a55bed067574500',
 'logic.c': 'a59bfcf3522417b213d0af5285df112162d3af8bb96a80862de9ef7a1cac6e9c',
 'magic1.c': 'd700418d55c68dade72dbf20fe85ace17501a0a604c12670683223d3e8eed5cd',
 'magic2.c': '43cca287e410ca2cc089edab5353075e29ab3c3c53c5603b73c780140f7e1c06',
 'magic3.c': 'e29d922ca2755e16b8205aa2082c3d05516b448f709426f0e769cecfb29cca6b',
 'main.c': '06c3a68e5c814b3c78c7cb17693708deda50353d5b0d119adf30079fb345ea73',
 'mextern.h': '07645128e860e80dd6e9037e7f5274a578f3b111d22ef10ad08425ea5368d9f9',
 'misc.c': '499264198e908479375c7407bd4fc3b2933bd748cf635d11ad78ac7fb5a89802',
 'mstruct.h': '0b88d8b0510692c6839fd24226251f09b1f612cb7a3433a5a8eba915886bcfda',
 'mtype.h': '0b8e511e6a545c9bed6ad27233dd4036733b115081d8bb0aeca1915527c56771',
 'object.c': '6801cf3240fd0c4907668a6e566cfe7276dc4bbcfbccb9c35ea40678c119db0b',
 'player.c': 'c8a375038b565a597061a7624740b9a471497c7cbe6b6a3349deb64645d2483b',
 'room.c': 'd81050b5a2f6ff66b6561557ddf6e4af88195e17ef7faa4e5828f469ea3b8aed',
 'treasure_receipt.c': 'aa6fe16fe2d789b39d0e15c195c201f197c72e831004700bbea4a8e4c92ea805',
 'treasure_receipt.h': 'c36fcfa5f5240f69e1b2772fbd2fc7373b18c8c02da14581f18c1b9832909dec',
 'update.c': 'e0fcf9c0f7597440d0202d2676111abd121f5529f22d7bbc3b841f083876c573'}
AFTER={'Makefile': 'f160205a5fba30ffec1ddba80fdff3ef017c547e80ef132766bcbcc64e6c3692',
 'command1.c': '82f453ce78280ab0dc16a8ba3f22aeb4ceda4e36f708eab2ec0a266a61e27708',
 'creature.c': '1d7f9629f7117f1711708ca01cd17350a0673d9ba8521e319ed39fb171d93837',
 'hd_necro_skeleton.c': 'f544877d682bebebb747c244631b18cb1e0ea8192914515463aaa28c6ce58a41',
 'hd_necro_skeleton.h': '77dcb6d5e06ed23eeef1954a9421db8c265ff9cd3a2a241435e2803a0f4068fb',
 'update.c': '07fc8b00cd065762de1940d1d46ec86c6137ba14f334b94f2f3603d3a2c340b7'}
PAYLOAD={'help/corpses': 'MONSTER CORPSES - PRIVATE PLAYTEST\n'
                 'When a normal monster is slain, its corpse is visible in the room. Its\n'
                 'ordinary drops and gold remain held until consumed. Look to see corpse IDs.\n'
                 '  loot corpse [id]       Anyone; release loot without raising the monster.\n'
                 '  sacrifice corpse [id] Requires a deity assigned by a DM; releases loot.\n'
                 '  raise corpse [id]     Necromancer only; costs 8 mana and releases loot.\n'
                 'If multiple corpses are present, give the exact displayed ID. All three\n'
                 'choices consume the same corpse once. Use normal get commands for the loot.\n'
                 'A failed action does not consume the corpse. Merchant stock is not loot,\n'
                 'and killed summoned skeletons create no corpses, loot, XP or deity favor.\n'
                 'Corpses remain in their numbered room across cache eviction in this process.\n'
                 'They are not inventory objects. A full server restart still loses them. No\n'
                 'favor award is implemented yet. See help raise skeleton and help deity.\n'
                 '\n'
                 'Private pet restore: living skeletons are saved on their owner. Corpse and\n'
                 'released floor loot are still transient across a full server restart.\n',
 'help/deity-corpses': 'DEITIES AND CORPSE SACRIFICE - PRIVATE PLAYTEST\n'
                       'An authorized DM may assign a numeric deity to a saved character. Characters\n'
                       'with a valid deity may use sacrifice corpse [id] to consume a monster corpse\n'
                       'and release its held loot and gold into the room. No favor reward yet.\n'
                       'Characters without a valid deity may use loot corpse [id] instead.\n'
                       'Corpses are one-use. If more than one is present, look and select its ID.\n'
                       'See help corpse and help sacrifice. Contact a DM for allegiance changes.\n',
 'help/help.151': 'DEITY ASSIGNMENT - DM/STAFF ADMIN (PRIVATE PLAYTEST)\n'
                  'Syntax:\n'
                  '  *deity list\n'
                  '  *deity <player>\n'
                  '  *deity <player> <1-16>\n'
                  '  *deity <player> 0\n'
                  '\n'
                  'List valid slots, inspect allegiance, assign a deity, or clear allegiance.\n'
                  'Example: *deity Playername 3\n'
                  'Requires native DM class and staff administrator authority. Target must\n'
                  'be an existing saved character (online or offline). Changes are audited\n'
                  'and recorded in the protected deity database. Invalid or corrupt records\n'
                  'fail closed. Names of deities and favor rewards are not yet configured.\n'
                  'See also: help deity | help corpse\n',
 'help/help.152': 'MONSTER CORPSES - PRIVATE PLAYTEST\n'
                  'When a normal monster is slain, its corpse is visible in the room. Its\n'
                  'ordinary drops and gold remain held until consumed. Look to see corpse IDs.\n'
                  '  loot corpse [id]       Anyone; release loot without raising the monster.\n'
                  '  sacrifice corpse [id] Requires a deity assigned by a DM; releases loot.\n'
                  '  raise corpse [id]     Necromancer only; costs 8 mana and releases loot.\n'
                  'If multiple corpses are present, give the exact displayed ID. All three\n'
                  'choices consume the same corpse once. Use normal get commands for the loot.\n'
                  'A failed action does not consume the corpse. Merchant stock is not loot,\n'
                  'and killed summoned skeletons create no corpses, loot, XP or deity favor.\n'
                  'Corpses remain in their numbered room across cache eviction in this process.\n'
                  'They are not inventory objects. A full server restart still loses them. No\n'
                  'favor award is implemented yet. See help raise skeleton and help deity.\n'
                  '\n'
                  'Private pet restore: living skeletons are saved on their owner. Corpse and\n'
                  'released floor loot are still transient across a full server restart.\n',
 'help/help.153': 'MONSTER CORPSES - PRIVATE PLAYTEST\n'
                  'When a normal monster is slain, its corpse is visible in the room. Its\n'
                  'ordinary drops and gold remain held until consumed. Look to see corpse IDs.\n'
                  '  loot corpse [id]       Anyone; release loot without raising the monster.\n'
                  '  sacrifice corpse [id] Requires a deity assigned by a DM; releases loot.\n'
                  '  raise corpse [id]     Necromancer only; costs 8 mana and releases loot.\n'
                  'If multiple corpses are present, give the exact displayed ID. All three\n'
                  'choices consume the same corpse once. Use normal get commands for the loot.\n'
                  'A failed action does not consume the corpse. Merchant stock is not loot,\n'
                  'and killed summoned skeletons create no corpses, loot, XP or deity favor.\n'
                  'Corpses remain in their numbered room across cache eviction in this process.\n'
                  'They are not inventory objects. A full server restart still loses them. No\n'
                  'favor award is implemented yet. See help raise skeleton and help deity.\n'
                  '\n'
                  'Private pet restore: living skeletons are saved on their owner. Corpse and\n'
                  'released floor loot are still transient across a full server restart.\n',
 'help/necromancer-corpses': 'NECROMANCER - PRIVATE CLASS PLAYTEST\n'
                             'The Necromancer uses the native Mage training and combat rules with a\n'
                             'verified separate identity. Its first skill is Raise Skeleton (8 MP).\n'
                             'Use raise corpse [id] to animate a slain monster; its loot drops and its\n'
                             "maximum HP/MP become the skeleton's starting stats. One living summon,\n"
                             'no expiration timer. Heal with Vigor, Mend, Restore or compatible items.\n'
                             'Your saved skeleton returns upon verified login, including a full game\n'
                             'process restart. A recorded death ends that summon. See help raise skeleton.\n'
                             'Corpse/floor loot restart durability and crash recovery remain unfinished.\n'
                             'This is a private playtest, not a live release.\n',
 'help/raise-corpse': 'RAISE SKELETON - NECROMANCER (PRIVATE PLAYTEST)\n'
                      '  raise corpse [id]     Look for corpse IDs when several are present.\n'
                      '  raise skeleton [id]   Equivalent. Alias: raiseskeleton (one corpse only).\n'
                      'Costs 8 mana, one living skeleton. The selected corpse releases its loot;\n'
                      "its maximum HP/MP become the skeleton's full starting stats. The summon\n"
                      'has no expiration timer. Heal it with Vigor, Mend, Restore or compatible\n'
                      'healing items: drink <healing-potion> on skeleton.\n'
                      'In this private build your saved skeleton returns on your verified login,\n'
                      'including after a game-process restart. It is restored with saved current\n'
                      'HP/MP and follows you. Restoring does not charge mana. A recorded death\n'
                      'prevents restoration. Ordinary room saves exclude summoned pets.\n'
                      'Failed raises leave the corpse and mana intact. A killed skeleton yields\n'
                      'no new corpse or loot. Unconsumed corpses and released floor loot are\n'
                      'still transient on restart. Full crash recovery remains under development.\n'
                      'See help corpse and help necromancer.\n',
 'patch.py': 'from pathlib import Path\n'
             'import sys\n'
             '\n'
             'def patch(src):\n'
             "    out={n:(src/n).read_text('latin-1') for n in "
             "('hd_necro_skeleton.c','hd_necro_skeleton.h','Makefile','command1.c','update.c','creature.c')}\n"
             '    def rep(n,a,b):\n'
             "        if out[n].count(a)!=1: raise RuntimeError('Anchor mismatch: '+n+': '+a[:80])\n"
             '        out[n]=out[n].replace(a,b)\n'
             "    n='hd_necro_skeleton.c'\n"
             "    rep(n,'#include <time.h>','#include <time.h>\\n#ifdef HD_PET_RUNTIME_PLAYTEST\\n#include "
             '"hd_pet_store.h"\\n#include <unistd.h>\\n#endif\')\n'
             "    rep(n,'    long last_hit;','    long last_hit;\\n#ifdef HD_PET_RUNTIME_PLAYTEST\\n    "
             "hd_pet_state durable;\\n#endif')\n"
             '    # Never resolve an offline pet by character name in gameplay. Only the\n'
             '    # authenticated reconnect path can bind that pet after checking its epoch.\n'
             "    rep(n, '        if (!pets[i].owner && pets[i].owner_name[0] &&\\n            "
             "!strcmp(pets[i].owner_name, owner->name)) return &pets[i];', '#ifndef "
             'HD_PET_RUNTIME_PLAYTEST\\n        if (!pets[i].owner && pets[i].owner_name[0] &&\\n            '
             "!strcmp(pets[i].owner_name, owner->name)) return &pets[i];\\n#endif')\n"
             '    # Private process halts rather than continuing with uncertain or conflicting disk state.\n'
             "    rep(n,'static void forget_pet(necro_pet_slot *slot)', '''#ifdef HD_PET_RUNTIME_PLAYTEST\n"
             'static void pet_storage_stop(const char *where, int status)\n'
             '{\n'
             '    fprintf(stderr, "PETRUNTIME: storage divergence at %s (%d); private process stopped\\\\n", '
             'where, status);\n'
             '    fflush(stderr);\n'
             '    _exit(73);\n'
             '}\n'
             'static int same_state(const hd_pet_state *a, const hd_pet_state *b)\n'
             '{\n'
             '    return !strcmp(a->epoch,b->epoch) && a->revision==b->revision &&\n'
             '        a->level==b->level && a->room==b->room && a->hpmax==b->hpmax &&\n'
             '        a->hpcur==b->hpcur && a->mpmax==b->mpmax && a->mpcur==b->mpcur;\n'
             '}\n'
             'static int stored_state(creature *owner, hd_pet_state *state)\n'
             '{\n'
             '    int rc = hd_pet_store_read(owner->name,state);\n'
             '    if (rc == HD_PET_ABSENT) rc=hd_pet_store_init(owner->name,state);\n'
             '    if (rc == HD_PET_UNCERTAIN || rc == HD_PET_CONFLICT)\n'
             '        pet_storage_stop("identity initialization",rc);\n'
             '    return rc == HD_PET_OK;\n'
             '}\n'
             'static void checkpoint_slot(necro_pet_slot *slot)\n'
             '{\n'
             '    hd_pet_state next, written;\n'
             '    creature *pet=slot->pet;\n'
             '    int rc;\n'
             '    if (!pet) return;\n'
             '    if (!slot->durable.hpcur) pet_storage_stop("missing durable pet",-1);\n'
             '    next=slot->durable;\n'
             '    if (pet->hpcur < 1) {\n'
             '        /* Native die/free normally records this before the command returns. */\n'
             '        pet_storage_stop("unhandled zero HP",-1);\n'
             '    }\n'
             '    next.room=pet->parent_rom ? pet->parent_rom->rom_num : slot->dormant_room;\n'
             '    next.hpcur=pet->hpcur; next.mpcur=pet->mpcur;\n'
             '    if (pet->hpmax!=(int)next.hpmax || pet->mpmax!=(int)next.mpmax ||\n'
             '        pet->level!=(int)next.level) pet_storage_stop("unexpected max stat mutation",-1);\n'
             '    if (same_state(&next,&slot->durable)) return;\n'
             '    rc=hd_pet_store_commit(slot->owner_name,&slot->durable,&next,NULL,&written);\n'
             '    if (rc != HD_PET_OK) pet_storage_stop("checkpoint",rc);\n'
             '    slot->durable=written;\n'
             '}\n'
             'void hd_necro_skeleton_checkpoint_all(void)\n'
             '{\n'
             '    int i;\n'
             '    for (i=0;i<PMAX;i++) if (pets[i].pet) checkpoint_slot(&pets[i]);\n'
             '}\n'
             'static void tombstone(necro_pet_slot *slot)\n'
             '{\n'
             '    hd_pet_state next=slot->durable,written;\n'
             '    int rc;\n'
             '    if (!next.hpcur) pet_storage_stop("missing live death record",-1);\n'
             '    next.level=next.room=next.hpmax=next.hpcur=next.mpmax=next.mpcur=0;\n'
             '    rc=hd_pet_store_commit(slot->owner_name,&slot->durable,&next,NULL,&written);\n'
             '    if (rc!=HD_PET_OK) pet_storage_stop("death tombstone",rc);\n'
             '    slot->durable=written;\n'
             '}\n'
             'void hd_necro_skeleton_death(creature *pet)\n'
             '{\n'
             '    int i;\n'
             '    for (i=0;i<PMAX;i++) if (pets[i].pet==pet && pet) {\n'
             '        tombstone(&pets[i]); return;\n'
             '    }\n'
             '    pet_storage_stop("death missing slot",HD_PET_ERROR);\n'
             '}\n'
             "/* Restore only in the verified owner's login session. The owner room is\n"
             ' * authoritative on login, matching the existing follower behavior. */\n'
             'static creature *restore_pet(const hd_pet_state *saved)\n'
             '{\n'
             '    creature *pet=calloc(1,sizeof *pet);\n'
             '    if (!pet) return NULL;\n'
             '    strcpy(pet->name,"skeleton servant");\n'
             '    strcpy(pet->description,"A skeletal servant raised from a fallen monster.");\n'
             '    pet->type=MONSTER; pet->class=FIGHTER; pet->fd=-1;\n'
             '    pet->level=(char)saved->level;\n'
             '    pet->hpmax=(short)saved->hpmax; pet->hpcur=(short)saved->hpcur;\n'
             '    pet->mpmax=(short)saved->mpmax; pet->mpcur=(short)saved->mpcur;\n'
             '    pet->strength=pet->dexterity=10; pet->ndice=1; pet->sdice=2;\n'
             '    F_SET(pet,MNRGLD);\n'
             '    return pet;\n'
             '}\n'
             '#endif\n'
             "static void forget_pet(necro_pet_slot *slot)''')\n"
             "    rep(n,'    creature *pet;\\n    if (!owner || owner->type != PLAYER', '''    creature "
             '*pet;\n'
             '#ifdef HD_PET_RUNTIME_PLAYTEST\n'
             '    hd_pet_state old,next,written;\n'
             '    int rc;\n'
             '#endif\n'
             "    if (!owner || owner->type != PLAYER''')\n"
             '    rep(n,\'    pet = calloc(1, sizeof *pet);\\n    if (!pet) { print(owner->fd, "Your magic '
             'falters.\\\\n"); return 0; }\\n    strcpy(pet->name, "skeleton servant");\\n    '
             'strcpy(pet->description, "A skeletal servant raised from a fallen monster.");\\n    pet->type '
             "= MONSTER;\\n    pet->class = FIGHTER;\\n    pet->fd = -1;\\n    pet->level = (char)level;', "
             "'''#ifdef HD_PET_RUNTIME_PLAYTEST\n"
             '    if (!stored_state(owner,&old)) {\n'
             '        print(owner->fd,"Your skeleton storage is unavailable. The corpse is '
             'untouched.\\\\n"); return 0;\n'
             '    }\n'
             '    if (old.hpcur) { print(owner->fd,"You already command a saved skeleton.\\\\n"); return 0; '
             '}\n'
             '#endif\n'
             '    pet = calloc(1, sizeof *pet);\n'
             '    if (!pet) { print(owner->fd, "Your magic falters.\\\\n"); return 0; }\n'
             '    strcpy(pet->name, "skeleton servant");\n'
             '    strcpy(pet->description, "A skeletal servant raised from a fallen monster.");\n'
             '    pet->type = MONSTER;\n'
             '    pet->class = FIGHTER;\n'
             '    pet->fd = -1;\n'
             "    pet->level = (char)level;''')\n"
             "    rep(n,'    F_SET(pet, MNRGLD);\\n    slot->owner = owner;\\n    strcpy(slot->owner_name, "
             "owner->name);', '''    F_SET(pet, MNRGLD);\n"
             '#ifdef HD_PET_RUNTIME_PLAYTEST\n'
             '    next=old; next.room=owner->parent_rom->rom_num; next.level=level;\n'
             '    next.hpmax=next.hpcur=hp; next.mpmax=next.mpcur=mp;\n'
             '    rc=hd_pet_store_commit(owner->name,&old,&next,owner,&written);\n'
             '    if (rc != HD_PET_OK) {\n'
             '        free(pet);\n'
             '        if (rc==HD_PET_UNCERTAIN || rc==HD_PET_CONFLICT) pet_storage_stop("raise",rc);\n'
             '        print(owner->fd,"Your skeleton storage is unavailable. The corpse is '
             'untouched.\\\\n"); return 0;\n'
             '    }\n'
             '    slot->durable=written;\n'
             '    slot->dormant_room=next.room;\n'
             '#endif\n'
             '    slot->owner = owner;\n'
             "    strcpy(slot->owner_name, owner->name);''')\n"
             "    rep(n,'    add_crt_rom(slot->pet, new_room, 1);','    add_crt_rom(slot->pet, new_room, "
             "1);\\n#ifdef HD_PET_RUNTIME_PLAYTEST\\n    checkpoint_slot(slot);\\n#endif')\n"
             "    rep(n,'            pets[i].dormant_room=where->rom_num;','            "
             'pets[i].dormant_room=where->rom_num;\\n#ifdef HD_PET_RUNTIME_PLAYTEST\\n            '
             "checkpoint_slot(&pets[i]);\\n#endif')\n"
             "    rep(n,'    if (slot) slot->owner = NULL;','    if (slot) {\\n#ifdef "
             'HD_PET_RUNTIME_PLAYTEST\\n        if (slot->pet) checkpoint_slot(slot);\\n#endif\\n        '
             "slot->owner = NULL;\\n    }')\n"
             "    rep(n,'    if (!slot || !slot->owner_name[0] || !owner ||\\n        "
             "!hd_store_is_necromancer(owner->name)) return;','''#ifdef HD_PET_RUNTIME_PLAYTEST\n"
             '    hd_pet_state saved;\n'
             '    creature *restored;\n'
             '    int i;\n'
             '    if (!owner || owner->type!=PLAYER || owner->class!=MAGE ||\n'
             '        !hd_store_is_necromancer(owner->name)) return;\n'
             '    if (!stored_state(owner,&saved)) pet_storage_stop("login read",HD_PET_ERROR);\n'
             '    if (!slot) for (i=0;i<PMAX;i++) if (!pets[i].owner && pets[i].pet &&\n'
             '        !strcmp(pets[i].owner_name,owner->name)) { slot=&pets[i]; break; }\n'
             '    if (slot && slot->pet) {\n'
             '        if (!same_state(&slot->durable,&saved)) pet_storage_stop("login identity/state '
             'mismatch",HD_PET_CONFLICT);\n'
             '    } else {\n'
             '        if (!saved.hpcur) return;\n'
             '        if (!owner->parent_rom) pet_storage_stop("restore room missing",HD_PET_ERROR);\n'
             '        if (!slot) slot=free_slot();\n'
             '        if (!slot || !(restored=restore_pet(&saved))) pet_storage_stop("restore '
             'allocation",HD_PET_ERROR);\n'
             '        memset(slot,0,sizeof *slot);\n'
             '        slot->owner=owner; strcpy(slot->owner_name,owner->name);\n'
             '        slot->durable=saved; slot->pet=restored; slot->dormant_room=saved.room;\n'
             '        add_crt_rom(restored,owner->parent_rom,0);\n'
             '        checkpoint_slot(slot);\n'
             '        print(owner->fd,"Your saved skeleton returns (%d HP / %d '
             'MP).\\\\n",restored->hpcur,restored->mpcur);\n'
             '        return;\n'
             '    }\n'
             '#else\n'
             '    if (!slot || !slot->owner_name[0] || !owner ||\n'
             '        !hd_store_is_necromancer(owner->name)) return;\n'
             "#endif''')\n"
             "    rep(n,'        if (slot->pet == who) { forget_pet(slot); return; }','''        if "
             '(slot->pet == who) {\n'
             '#ifdef HD_PET_RUNTIME_PLAYTEST\n'
             '            if (slot->durable.hpcur) {\n'
             '                if (who->hpcur>0) pet_storage_stop("unexpected live pet free",HD_PET_ERROR);\n'
             '                tombstone(slot);\n'
             '            }\n'
             '#endif\n'
             '            forget_pet(slot); return;\n'
             "        }''')\n"
             "    n='hd_necro_skeleton.h';rep(n,'struct creature *hd_necro_skeleton_probe(struct creature "
             "*owner);','struct creature *hd_necro_skeleton_probe(struct creature *owner);\\n#ifdef "
             'HD_PET_RUNTIME_PLAYTEST\\nvoid hd_necro_skeleton_checkpoint_all(void);\\nvoid '
             "hd_necro_skeleton_death(struct creature *);\\n#endif')\n"
             "    n='command1.c';rep(n,'\\t\\tif(n == DISCONNECT) {\\n\\t\\t\\tscwrite(fd, "
             '"Goodbye!\',\'\\n#ifdef HD_PET_RUNTIME_PLAYTEST\\n        '
             'hd_necro_skeleton_checkpoint_all();\\n#endif\\n\\t\\tif(n == DISCONNECT) '
             '{\\n\\t\\t\\tscwrite(fd, "Goodbye!\')\n'
             "    n='update.c';rep(n,'    if(t - last_action_update >= Action_update_interval)         "
             "\\n\\tupdate_action(t);','    if(t - last_action_update >= Action_update_interval)         "
             '\\n\\tupdate_action(t);\\n#ifdef HD_PET_RUNTIME_PLAYTEST\\n    '
             "hd_necro_skeleton_checkpoint_all();\\n#endif')\n"
             "    n='creature.c';rep(n,'    if (hd_necro_skeleton_is_pet(crt_ptr)) {\\n        if "
             "(crt_ptr->parent_rom)', '    if (hd_necro_skeleton_is_pet(crt_ptr)) {\\n#ifdef "
             'HD_PET_RUNTIME_PLAYTEST\\n        hd_necro_skeleton_death(crt_ptr);\\n#endif\\n        if '
             "(crt_ptr->parent_rom)')\n"
             "    n='update.c'\n"
             "    rep(n,'\\tif(F_ISSET(crt_ptr, MMOBIL) && !F_ISSET(crt_ptr, MPERMT) && !F_ISSET(crt_ptr, "
             "MDMFOL)){','#ifdef HD_PET_RUNTIME_PLAYTEST\\n    if "
             '(!hd_necro_skeleton_is_pet(crt_ptr))\\n#endif\\n    if(F_ISSET(crt_ptr, MMOBIL) && '
             "!F_ISSET(crt_ptr, MPERMT) && !F_ISSET(crt_ptr, MDMFOL)){')\n"
             "    rep(n,'        if(!F_ISSET(crt_ptr, MHASSC) && !F_ISSET(crt_ptr, MPERMT) && "
             "!F_ISSET(crt_ptr, MDMFOL)) {','#ifdef HD_PET_RUNTIME_PLAYTEST\\n        if "
             '(!hd_necro_skeleton_is_pet(crt_ptr))\\n#endif\\n        if(!F_ISSET(crt_ptr, MHASSC) && '
             "!F_ISSET(crt_ptr, MPERMT) && !F_ISSET(crt_ptr, MDMFOL)) {')\n"
             "    rep(n,'            crt_ptr->hpcur += MAX(1,crt_ptr->hpmax/10);\\n            "
             'if(crt_ptr->hpcur > crt_ptr->hpmax)\\n                crt_ptr->hpcur = '
             'crt_ptr->hpmax;\\n            crt_ptr->mpcur += MAX(1,crt_ptr->mpmax/6);\\n            '
             'if(crt_ptr->mpcur > crt_ptr->mpmax)\\n                crt_ptr->mpcur = '
             "crt_ptr->mpmax;','#ifdef HD_PET_RUNTIME_PLAYTEST\\n            if "
             '(hd_necro_skeleton_is_pet(crt_ptr)) {\\n                crt_ptr->hpcur = '
             '(short)MIN((int)crt_ptr->hpmax,(int)crt_ptr->hpcur+MAX(1,crt_ptr->hpmax/10));\\n                '
             'crt_ptr->mpcur = '
             '(short)MIN((int)crt_ptr->mpmax,(int)crt_ptr->mpcur+MAX(1,crt_ptr->mpmax/6));\\n            } '
             'else\\n#endif\\n            {\\n            crt_ptr->hpcur += '
             'MAX(1,crt_ptr->hpmax/10);\\n            if(crt_ptr->hpcur > crt_ptr->hpmax)\\n                '
             'crt_ptr->hpcur = crt_ptr->hpmax;\\n            crt_ptr->mpcur += '
             'MAX(1,crt_ptr->mpmax/6);\\n            if(crt_ptr->mpcur > crt_ptr->mpmax)\\n                '
             "crt_ptr->mpcur = crt_ptr->mpmax;\\n            }')\n"
             "    n='Makefile';rep(n,'frp.new: $(OBJECTS)','# Private gameplay integration; not a production "
             'option.\\nifeq ($(PET_RUNTIME_PLAYTEST),1)\\nifneq ($(PET_STORE_PLAYTEST),1)\\n$(error '
             'PET_RUNTIME_PLAYTEST requires PET_STORE_PLAYTEST=1)\\nendif\\nCFLAGS += '
             "-DHD_PET_RUNTIME_PLAYTEST\\nendif\\n\\nfrp.new: $(OBJECTS)')\n"
             "    for n,body in out.items(): (src/n).write_text(body,'latin-1')\n",
 'runtime_gameplay.py': ('"""Private real listener restart replay. Called only by guarded onepass runner."""\n'
 'import os\n'
 'import re\n'
 'import runpy\n'
 'import shutil\n'
 'import socket\n'
 'import subprocess\n'
 'import tempfile\n'
 'import time\n'
 'from pathlib import Path\n'
 '\n'
 '\n'
 'def replay(src, help_pages, prior_gameplay, cache_gameplay, work):\n'
 "    if os.geteuid()!=0 or os.readlink('/proc/self/ns/net')==os.readlink('/proc/1/ns/net'):\n"
 "        raise RuntimeError('Separate network namespace and root required')\n"
 "    if not work.is_relative_to(Path('/root/hollowdeep-dev')) or not "
 "work.name.startswith('necromancer-playtest-runtime-') or src!=work/'src':\n"
 "        raise RuntimeError('Refusing non-disposable gameplay root')\n"
 '    old=runpy.run_path(str(prior_gameplay))\n'
 '    cache=runpy.run_path(str(cache_gameplay))\n'
 "    stage=work/'socket-world';stage.mkdir(mode=0o700)\n"
 "    print('PETRUNTIME: PRIVATE SOCKET WORLD: '+str(stage),flush=True)\n"
 "    for name in ('rooms','player','log','objmon','post','help','bin','hollowdeep-data'):\n"
 '        (stage/name).mkdir(mode=0o700)\n'
 '    for name,body in help_pages.items():\n'
 "        if '/' in name or not name: raise RuntimeError('Invalid help page')\n"
 "        (stage/'help'/name).write_text(body,encoding='ascii')\n"
 "    (stage/'hollowdeep-data/deities.db').write_text('HOLLOWDEEP_DEITIES 1 1\\nHdfaithqa 3\\n')\n"
 "    compile_fixture=old['compile_fixture']\n"
 "    compile_fixture.__globals__['SOURCE']=cache['fixture_source'](old['SOURCE'])\n"
 "    fixture=compile_fixture(src,stage,'-m32')\n"
 '    subprocess.run([str(fixture)],cwd=stage,check=True)\n'
 "    chroot=shutil.which('chroot',path='/usr/sbin:/usr/bin:/sbin:/bin')\n"
 "    if not chroot:raise RuntimeError('Required chroot missing')\n"
 "    exe=src/'frp.new'\n"
 "    interpreter=old['prepare_chroot'](exe,stage)\n"
 "    launcher=[chroot,'--userspec=65534:65534','--groups=65534',str(stage)]\n"
 "    env={'PATH':'/usr/bin:/bin','HOLLOWDEEP_BIND':'127.0.0.1'}\n"
 '    '
 "subprocess.run(launcher+[interpreter,'--list','/bin/hollowdeep'],cwd=stage,env=env,check=True,timeout=15)\n"
 '    '
 "connect=old['connect_game'];command=old['command'];require=old['require'];view=old['room_view'];collect=old['collect'];quit_game=old['quit_with_cooldown'];kill=old['kill_and_find']\n"
 '    def start(label):\n'
 '        with socket.socket() as probe:\n'
 "            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]\n"
 "        logpath=work/(label+'.log')\n"
 "        with logpath.open('wb') as log:\n"
 '            '
 "process=subprocess.Popen(launcher+['/bin/hollowdeep',str(port)],cwd=stage,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)\n"
 "        print(f'PETRUNTIME: private listener {label} PID {process.pid}',flush=True)\n"
 '        return process,port,logpath\n'
 '    def stop(process, abrupt=False):\n'
 '        if process is None:return\n'
 '        if process.poll() is None:\n'
 '            if abrupt:process.kill()\n'
 '            else:process.terminate()\n'
 '            try:process.wait(timeout=5)\n'
 '            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)\n'
 '    def login(client,name,room_name,restored=False):\n'
 "        old['recv_until'](client,b'Please enter name:');old['send'](client,name)\n"
 "        old['recv_until'](client,b'Please enter password:');old['send'](client,'Fixturepass')\n"
 "        wanted=b'Your saved skeleton returns (147 HP / 51 MP).' if restored else "
 "(room_name.encode('ascii') if room_name else b'Obvious exits:')\n"
 '        '
 "reply=old['recv_until'](client,wanted,seconds=15).decode('latin-1',errors='replace')+collect(client,quiet=0.4,limit=2)\n"
 "        print('LOGIN: '+name+'\\n'+reply,flush=True)\n"
 "        if not restored and 'Your saved skeleton returns' in reply:\n"
 "            raise RuntimeError('Unexpected saved skeleton restoration')\n"
 '        location=view(client)\n'
 '        if room_name:\n'
 '            require(location,room_name)\n'
 "        elif 'necromancer grave trial' in location:\n"
 "            room_name='Necromancer Grave Trial'\n"
 "        elif 'necromancer trial annex' in location:\n"
 "            room_name='Necromancer Trial Annex'\n"
 '        else:\n'
 "            raise RuntimeError('Unexpected native login room')\n"
 '        return room_name\n'
 '\n'
 '    def move(client,direction,destination):\n'
 '        deadline=time.monotonic()+60\n'
 '        for attempt in range(12):\n'
 '            if time.monotonic()>=deadline:\n'
 '                break\n'
 '            reply=command(client,direction)\n'
 '            delay=re.search(\n'
 "                r'Please wait\\s+(\\d+)\\s+more seconds?',\n"
 '                reply,re.I\n'
 '            )\n'
 '            if delay:\n'
 '                time.sleep(int(delay.group(1))+1)\n'
 '                continue\n'
 '            require(view(client),destination)\n'
 "            print('PASS: Native movement to '+destination,\n"
 '                  flush=True)\n'
 '            return\n'
 "        raise RuntimeError('Movement cooldown deadline exceeded')\n"
 '\n'
 '    def one_pet(client,room_name):\n'
 '        text=view(client);require(text,room_name)\n'
 "        rows=[x for x in text.splitlines() if x.strip().startswith('you see') and 'skeleton servant' "
 'in x]\n'
 "        if len(rows)!=1 or not re.search(r'\\ba skeleton servant\\b',rows[0]) or "
 "re.search(r'\\b[2-9]\\d* skeleton servants?\\b',rows[0]):\n"
 "            raise RuntimeError('Expected exactly one visible skeleton: '+repr(text[-1500:]))\n"
 '    def absent_pet(client):\n'
 '        text=view(client)\n'
 "        if any('skeleton servant' in x for x in text.splitlines() if x.strip().startswith('you see')) "
 "or 'corpse of skeleton servant' in text:\n"
 "            raise RuntimeError('Unexpected skeleton or corpse: '+repr(text[-1500:]))\n"
 '    def defeat_pet(client):\n'
 '        death=False;deadline=time.monotonic()+150\n'
 '        while time.monotonic()<deadline:\n'
 "            text=command(client,'attack skeleton');death=death or bool(re.search(r'you killed "
 "(?:the|a) skeleton servant',text,re.I))\n"
 '            time.sleep(3.2)\n'
 "            text=view(client);death=death or bool(re.search(r'you killed (?:the|a) skeleton "
 "servant',text,re.I))\n"
 '            if death:\n'
 '                absent_pet(client);return\n'
 "        raise RuntimeError('Native pet death not confirmed within combat deadline')\n"
 '\n'
 "    probe_root=work/'logout-probe'\n"
 '    probe_root.mkdir(mode=0o700)\n'
 "    (probe_root/'player').mkdir(mode=0o700)\n"
 "    probe_source=probe_root/'probe.c'\n"
 '    probe_source.write_text(\'\\n#define main original_test_main\\n#include "test_runtime.c"\\n#undef '
 'main\\n\\nint main(int argc, char **argv)\\n{\\n    creature *p = NULL;\\n    otag *tag;\\n    '
 'hd_pet_state pet;\\n    int ruby = 0;\\n\\n    if (argc != 2) return 2;\\n    if '
 '(hd_store_load_player("Hdnecroqa", &p) != 0 || !p)\\n        return 3;\\n\\n    for '
 '(tag=p->first_obj; tag; tag=tag->next_tag)\\n        if (tag->obj &&\\n            '
 '!strcmp(tag->obj->name,"rubyfixture"))\\n            ruby++;\\n\\n    if '
 '(hd_pet_store_read("Hdnecroqa", &pet) != 0)\\n        return 4;\\n\\n    printf("DURABLE SAVE: '
 'gold=%ld ruby=%d room=%d petHP=%u petMP=%u\\\\n",\\n           (long)p->gold, ruby, '
 '(int)p->rom_num,\\n           (unsigned)pet.hpcur, (unsigned)pet.mpcur);\\n\\n    if (p->gold != 1013 '
 '|| ruby != 1) return 5;\\n\\n    if (atoi(argv[1])) {\\n        if (pet.hpcur != 147 || pet.mpcur != '
 '51)\\n            return 6;\\n    } else if (pet.hpcur != 0) {\\n        return 7;\\n    }\\n\\n    '
 "return 0;\\n}\\n',encoding='ascii')\n"
 "    probe=probe_root/'probe'\n"
 "    components=('files1','files3','compress','hd_player_store',\n"
 "                'treasure_receipt','atomic_player_snapshot',\n"
 "                'hd_necro_skeleton','hd_corpse','room')\n"
 '    flags=[\n'
 "        '-DHD_NECROMANCER_PLAYTEST',\n"
 "        '-DHD_DEITY_PLAYTEST',\n"
 "        '-DHD_CORPSE_PLAYTEST',\n"
 "        '-DHD_PET_STORE_PLAYTEST',\n"
 "        '-DHD_PET_RUNTIME_PLAYTEST',\n"
 "        '-DHD_ATOMIC_TESTING'\n"
 '    ]\n'
 '    subprocess.run([\n'
 "        os.environ.get('CC','cc'),'-m32','-std=gnu89',\n"
 "        '-O1','-g','-fcommon','-DCOMPRESS',\n"
 "        '-ffunction-sections','-fdata-sections',\n"
 "        '-Wl,--gc-sections','-Wl,--wrap=load_obj',\n"
 "        '-I',str(src),'-I',str(work/'pkg')\n"
 '    ]+flags+[str(probe_source)]+[\n'
 "        str(src/(n+'.c')) for n in components\n"
 "    ]+['-o',str(probe)],check=True)\n"
 '\n'
 '    def durable_logout(process,port,alive):\n'
 '        # EOF alone does not prove disconnect/save has finished.\n'
 '        # Wait for a subsequent native listener response.\n'
 '        with connect(port,process) as barrier:\n'
 "            old['recv_until'](barrier,b'Please enter name:',seconds=15)\n"
 '\n'
 '        assert process.poll() is None\n'
 "        saved=stage/'player'/'Hdnecroqa'\n"
 '        assert saved.is_file() and not saved.is_symlink()\n'
 "        shutil.copyfile(saved,probe_root/'player'/'Hdnecroqa')\n"
 '        subprocess.run(\n'
 "            [str(probe),'1' if alive else '0'],\n"
 '            cwd=probe_root,check=True\n'
 '        )\n'
 "        print('PETRUNTIME: durable logout inventory, gold and pet state PASS',\n"
 '              flush=True)\n'
 '\n'
 '    process=None;logpath=None\n'
 '    try:\n'
 "        process,port,logpath=start('listener-1')\n"
 '        with connect(port,process) as owner:\n'
 "            login(owner,'Hdnecroqa','Necromancer Grave Trial')\n"
 "            require(command(owner,'help raise skeleton'),'saved skeleton')\n"
 "            cid=kill(owner,'trialwretch','rubyfixture')\n"
 "            result=command(owner,f'raise corpse {cid}')\n"
 "            require(result,'You raise a skeleton (147 HP / 51 MP).');require(result,'loot falls to "
 "the ground')\n"
 "            old['after_release'](owner,cid,'rubyfixture')\n"
 "            require(command(owner,'get rubyfixture'),'You get');require(command(owner,'get "
 "gold'),'You now have 1013 gold pieces.')\n"
 "            move(owner,'north','Necromancer Trial Annex');one_pet(owner,'Necromancer Trial Annex')\n"
 "            require(command(owner,'inventory'),'rubyfixture')\n"
 '            quit_game(owner,process)\n'
 '        durable_logout(process,port,True)\n'
 "        print('PETRUNTIME: native raise, loot pickup, follow and saved logout PASS',flush=True)\n"
 '        # Kill ONLY the stopped-from-play private process after a completed logout.\n'
 '        # This tests a process restart, not a disk power-loss/rename crash window.\n'
 '        stop(process,abrupt=True);oldpid=process.pid\n'
 "        process,port,logpath=start('listener-2')\n"
 "        if process.pid==oldpid:raise RuntimeError('Expected distinct private listener PID')\n"
 '        with connect(port,process) as owner:\n'
 "            login(owner,'Hdnecroqa','Necromancer Trial Annex',restored=True)\n"
 "            one_pet(owner,'Necromancer Trial Annex')\n"
 "            require(command(owner,'inventory'),'rubyfixture')\n"
 "            print('PETRUNTIME: real fresh game process restored one saved pet and collected item "
 "PASS',flush=True)\n"
 '            with connect(port,process) as faithful:\n'
 "                login(faithful,'Hdfaithqa','Necromancer Grave Trial')\n"
 "                move(faithful,'north','Necromancer Trial Annex');one_pet(faithful,'Necromancer Trial "
 "Annex')\n"
 '                defeat_pet(faithful);absent_pet(owner)\n'
 "                print('PETRUNTIME: native combat killed restored pet; no pet corpse "
 "PASS',flush=True)\n"
 '                quit_game(faithful,process)\n'
 '            quit_game(owner,process)\n'
 '        durable_logout(process,port,False)\n'
 '        stop(process,abrupt=True);oldpid=process.pid\n'
 "        process,port,logpath=start('listener-3')\n"
 "        if process.pid==oldpid:raise RuntimeError('Expected distinct private listener PID')\n"
 '        with connect(port,process) as owner:\n'
 "            login(owner,'Hdnecroqa','Necromancer Trial Annex')\n"
 '            absent_pet(owner)\n'
 "            move(owner,'south','Necromancer Grave Trial')\n"
 '            absent_pet(owner)\n'
 "            require(command(owner,'inventory'),'rubyfixture')\n"
 '            quit_game(owner,process)\n'
 '        durable_logout(process,port,False)\n'
 "        print('PETRUNTIME: REAL NATIVE SOCKET RESTART/DEATH PASS',flush=True)\n"
 '    except Exception:\n'
 "        if logpath and logpath.exists():print('PRIVATE LISTENER "
 "LOG:\\n'+logpath.read_text(errors='replace')[-5000:],flush=True)\n"
 '        raise\n'
 '    finally:\n'
 '        stop(process)\n'),
 'test_pet_store.c': '#define _GNU_SOURCE\n'
                     '#include "hd_player_store.h"\n'
                     '#include "hd_pet_store.h"\n'
                     '#include <assert.h>\n'
                     '#include <stdio.h>\n'
                     '#include <stdlib.h>\n'
                     '#include <string.h>\n'
                     '#include <unistd.h>\n'
                     '#include <sys/wait.h>\n'
                     '#include <sys/stat.h>\n'
                     '#include <fcntl.h>\n'
                     '#include <errno.h>\n'
                     '\n'
                     'static const char *name="Hdnecroqa";\n'
                     'static const char *claim="11111111111111111111111111111111";\n'
                     'static const char '
                     '*digest="2222222222222222222222222222222222222222222222222222222222222222";\n'
                     'static const char *petid="ffffffffffffffffffffffffffffff76";\n'
                     'void merror(const char *message,int severity){fprintf(stderr,"native error %s '
                     '%d\\n",message,severity);abort();}\n'
                     'void hd_necro_skeleton_on_free(creature *p){(void)p;}\n'
                     'void del_active(creature *p){assert(p->type==PLAYER);}\n'
                     'static void zero_pet(hd_pet_state '
                     '*s){s->hpcur=s->hpmax=s->mpcur=s->mpmax=s->level=s->room=0;}\n'
                     'static void initial(creature *p,const char *n){memset(p,0,sizeof '
                     '*p);strcpy(p->name,n);p->type=PLAYER;p->class=MAGE;p->race=HUMAN;p->hpmax=p->hpcur=200;p->mpmax=p->mpcur=110;p->rom_num=1;p->gold=1013;}\n'
                     'static void want(hd_pet_state '
                     '*s){s->level=2;s->room=1;s->hpmax=s->hpcur=147;s->mpmax=s->mpcur=51;}\n'
                     'static void state(const hd_pet_state *s,unsigned rev,unsigned hp,unsigned mp,unsigned '
                     'room){assert(s->revision==rev && strlen(s->epoch)==24 && s->hpcur==hp && s->mpcur==mp '
                     '&& s->room==room);}\n'
                     'static void native_player(int mp){creature '
                     '*p=NULL;assert(hd_store_load_player(name,&p)==0);assert(p->mpcur==mp&&p->gold==1013&&p->first_obj&&p->first_obj->obj&&!strcmp(p->first_obj->obj->name,"rubyfixture"));assert(p->first_obj->obj->first_obj&&!strcmp(p->first_obj->obj->first_obj->obj->name,"nestedfixture"));free_crt(p);}\n'
                     'static void competing_writers(const char *self){\n'
                     '    pid_t left,right;int '
                     'a,b;left=fork();assert(left>=0);if(left==0){execl(self,self,"race",(char*)0);_exit(127);}\n'
                     '    '
                     'right=fork();assert(right>=0);if(right==0){execl(self,self,"race",(char*)0);_exit(127);}\n'
                     '    assert(waitpid(left,&a,0)==left&&waitpid(right,&b,0)==right);\n'
                     '    '
                     'assert(WIFEXITED(a)&&WIFEXITED(b));assert((WEXITSTATUS(a)==0&&WEXITSTATUS(b)==10)||(WEXITSTATUS(b)==0&&WEXITSTATUS(a)==10));\n'
                     '    puts("PETSTORE: competing processes CAS allows exactly one mutation PASS");\n'
                     '}\n'
                     'static void phase(const char *self,const char *step){pid_t pid=fork();int '
                     'status;assert(pid>=0);if(!pid){execl(self,self,step,(char*)0);_exit(127);}assert(waitpid(pid,&status,0)==pid&&WIFEXITED(status)&&WEXITSTATUS(status)==0);}\n'
                     'int main(int argc,char **argv){\n'
                     '    hd_pet_state a,b,c,stale; creature p,*loaded=NULL; object bag={0},gem={0};otag '
                     't={0},nested={0};\n'
                     '    '
                     'if(argc==1){phase(argv[0],"seed");phase(argv[0],"raise");phase(argv[0],"checkpoint");competing_writers(argv[0]);phase(argv[0],"death");phase(argv[0],"recreate");puts("PETSTORE: '
                     'native multi-process atomic mana + state, nested inventory, checkpoints, tombstone, '
                     'stale epoch, injected write failures PASS");return 0;}\n'
                     '    if(!strcmp(argv[1],"seed")){\n'
                     '        '
                     'initial(&p,name);strcpy(bag.name,"rubyfixture");strcpy(gem.name,"nestedfixture");nested.obj=&gem;bag.first_obj=&nested;t.obj=&bag;p.first_obj=&t;\n'
                     '        assert(hd_store_create_necromancer(name,&p)==HD_STORE_OK);\n'
                     '        assert(hd_store_save_claim(name,&p,claim,digest)==HD_STORE_OK);\n'
                     '        assert(hd_store_read_claim(name,claim,digest)==1);\n'
                     '        assert(hd_pet_store_read(name,&a)==HD_PET_ABSENT);\n'
                     '        assert(hd_store_save_claim(name,&p,petid,digest)==HD_STORE_FAILURE);\n'
                     '        assert(hd_store_read_claim(name,petid,digest)==-1);\n'
                     '        assert(hd_pet_store_init(name,&a)==HD_PET_OK);state(&a,1,0,0,0);\n'
                     '        '
                     'assert(hd_pet_store_init(name,&b)==HD_PET_CONFLICT&&!strcmp(a.epoch,b.epoch));\n'
                     '        initial(&p,"Hdmageqa");assert(hd_store_create_player(p.name,&p)==0);\n'
                     '        '
                     'assert(hd_pet_store_init(p.name,&b)==HD_PET_ERROR&&hd_pet_store_read(p.name,&b)==HD_PET_ERROR);\n'
                     '        native_player(110);puts("PETSTORE: initialize unique saved epoch; reserved '
                     'claim and ordinary Mage denied PASS");\n'
                     '    }else if(!strcmp(argv[1],"raise")){\n'
                     '        assert(hd_pet_store_read(name,&a)==0);state(&a,1,0,0,0);\n'
                     '        assert(hd_store_load_player(name,&loaded)==0); b=a;want(&b);\n'
                     '        '
                     'loaded->mpcur=7;assert(hd_pet_store_commit(name,&a,&b,loaded,&c)==HD_PET_ERROR);loaded->mpcur=110;\n'
                     '        assert(hd_pet_store_commit(name,&a,&b,NULL,&c)==HD_PET_ERROR);\n'
                     '        '
                     'b.room=2;assert(hd_pet_store_commit(name,&a,&b,loaded,&c)==HD_PET_ERROR);b.room=1;\n'
                     '        '
                     'setenv("HD_ATOMIC_FAIL","write",1);assert(hd_pet_store_commit(name,&a,&b,loaded,&c)==HD_PET_ERROR);unsetenv("HD_ATOMIC_FAIL");native_player(110);\n'
                     '        '
                     'setenv("HD_ATOMIC_FAIL","before_rename",1);assert(hd_pet_store_commit(name,&a,&b,loaded,&c)==HD_PET_ERROR);unsetenv("HD_ATOMIC_FAIL");\n'
                     '        assert(hd_pet_store_read(name,&c)==0);state(&c,1,0,0,0);native_player(110);\n'
                     '        '
                     'assert(hd_pet_store_commit(name,&a,&b,loaded,&c)==HD_PET_OK);state(&c,2,147,51,1);assert(loaded->mpcur==110);native_player(102);\n'
                     '        '
                     'assert(hd_pet_store_commit(name,&a,&b,loaded,&c)==HD_PET_CONFLICT);native_player(102);free_crt(loaded);puts("PETSTORE: '
                     'one atomic raise and exact 8 MP debit; failed/stale writes unchanged PASS");\n'
                     '    }else if(!strcmp(argv[1],"checkpoint")){\n'
                     '        '
                     'assert(hd_pet_store_read(name,&a)==0);state(&a,2,147,51,1);native_player(102);\n'
                     '        b=a;b.hpcur=91;b.mpcur=17;b.room=2;\n'
                     '        '
                     'c=b;c.hpmax++;assert(hd_pet_store_commit(name,&a,&c,NULL,&stale)==HD_PET_ERROR);\n'
                     '        '
                     'c=b;c.hpcur=999;assert(hd_pet_store_commit(name,&a,&c,NULL,&stale)==HD_PET_ERROR);\n'
                     '        '
                     'setenv("HD_ATOMIC_FAIL","after_rename",1);assert(hd_pet_store_commit(name,&a,&b,NULL,&c)==HD_PET_UNCERTAIN);unsetenv("HD_ATOMIC_FAIL");state(&c,3,91,17,2);\n'
                     '        '
                     'assert(hd_pet_store_read(name,&stale)==0);state(&stale,3,91,17,2);assert(hd_pet_store_commit(name,&a,&b,NULL,&c)==HD_PET_CONFLICT);\n'
                     '        '
                     'assert(hd_store_load_player(name,&loaded)==0);loaded->mpcur=109;assert(hd_store_save_live_player(name,loaded)==0);free_crt(loaded);native_player(109);\n'
                     '        '
                     'assert(hd_pet_store_read(name,&stale)==0);state(&stale,3,91,17,2);assert(hd_store_read_claim(name,claim,digest)==1);puts("PETSTORE: '
                     'exact HP/MP checkpoint, uncertain rename reconciliation, ordinary save preserves state '
                     'and reward receipt PASS");\n'
                     '    }else if(!strcmp(argv[1],"race")){\n'
                     '        int rc;assert(hd_pet_store_read(name,&a)==0);if(a.revision==4)return '
                     '10;state(&a,3,91,17,2);b=a;b.hpcur=90;\n'
                     '        '
                     'rc=hd_pet_store_commit(name,&a,&b,NULL,&c);assert(rc==HD_PET_OK||rc==HD_PET_CONFLICT);return '
                     'rc==HD_PET_OK?0:10;\n'
                     '    }else if(!strcmp(argv[1],"death")){\n'
                     '        assert(hd_pet_store_read(name,&a)==0);state(&a,4,90,17,2);b=a;zero_pet(&b);\n'
                     '        '
                     'assert(hd_pet_store_commit(name,&a,&b,NULL,&c)==0);state(&c,5,0,0,0);native_player(109);\n'
                     '        '
                     'assert(hd_pet_store_commit(name,&a,&a,NULL,&c)==HD_PET_CONFLICT);assert(hd_pet_store_read(name,&c)==0);state(&c,5,0,0,0);\n'
                     '        puts("PETSTORE: durable death tombstone rejects stale live checkpoint PASS");\n'
                     '    }else if(!strcmp(argv[1],"recreate")){\n'
                     '        '
                     'assert(hd_pet_store_read(name,&a)==0);state(&a,5,0,0,0);assert(unlink("player/Hdnecroqa")==0);initial(&p,name);assert(hd_store_create_necromancer(name,&p)==0);\n'
                     '        '
                     'assert(hd_pet_store_read(name,&b)==HD_PET_ABSENT);assert(hd_pet_store_init(name,&b)==0);state(&b,1,0,0,0);assert(strcmp(a.epoch,b.epoch));\n'
                     '        '
                     'c=a;want(&c);assert(hd_pet_store_commit(name,&a,&c,&p,&stale)==HD_PET_CONFLICT);\n'
                     '        puts("PETSTORE: recreated name receives distinct epoch; stale old character '
                     'transaction denied PASS");\n'
                     '        '
                     'assert(rename("player/Hdnecroqa","player/Hdbackup")==0);assert(symlink("Hdbackup","player/Hdnecroqa")==0);\n'
                     '        '
                     'assert(hd_pet_store_read(name,&a)==HD_PET_ERROR&&hd_pet_store_init(name,&a)==HD_PET_ERROR);\n'
                     '        '
                     'assert(unlink("player/Hdnecroqa")==0);assert(rename("player/Hdbackup","player/Hdnecroqa")==0);\n'
                     '        assert(hd_pet_store_read(name,&a)==0);state(&a,1,0,0,0);\n'
                     '        {int '
                     'fd=open("player/Hdnecroqa",O_WRONLY|O_TRUNC);assert(fd>=0);assert(write(fd,"bad",3)==3);assert(close(fd)==0);}\n'
                     '        '
                     'assert(hd_pet_store_read(name,&a)==HD_PET_ERROR&&hd_pet_store_init(name,&a)==HD_PET_ERROR);\n'
                     '        puts("PETSTORE: symlinked and corrupt save refused PASS");\n'
                     '    }else return 2;\n'
                     '    return 0;\n'
                     '}\n',
 'test_runtime.c': '#define _GNU_SOURCE\n'
                   '#include "hd_player_store.h"\n'
                   '#include "hd_pet_store.h"\n'
                   '#include "hd_necro_skeleton.h"\n'
                   '#include "hd_corpse.h"\n'
                   '#include <assert.h>\n'
                   '#include <fcntl.h>\n'
                   '#include <stdarg.h>\n'
                   '#include <stdio.h>\n'
                   '#include <stdlib.h>\n'
                   '#include <string.h>\n'
                   '#include <sys/wait.h>\n'
                   '#include <unistd.h>\n'
                   'static const char *name="Hdpetruntime";\n'
                   'static char output[8192];\n'
                   'void merror(const char *what,int sev){fprintf(stderr,"native error %s '
                   '%d\\n",what,sev);abort();}\n'
                   'void print(int fd,char *fmt,...){va_list ap;size_t '
                   'len=strlen(output);(void)fd;va_start(ap,fmt);vsnprintf(output+len,sizeof '
                   'output-len,fmt,ap);va_end(ap);}\n'
                   'void broadcast_rom(int fd,int n,char *fmt,...){(void)fd;(void)n;(void)fmt;}\n'
                   'void del_active(creature *p){(void)p;}\n'
                   'int hd_deity_get(const char *n){(void)n;return 1;}\n'
                   'long hd_bonus_gold(long n){return n;}\n'
                   'int __wrap_load_obj(int n,object **o){assert(n==0);*o=calloc(1,sizeof '
                   '**o);assert(*o);return 0;}\n'
                   'static void attach(creature *p,room *r){p->fd=4;p->parent_rom=r;p->rom_num=r->rom_num;}\n'
                   'static int count(room *r){int n=0;ctag *t;for(t=r->first_mon;t;t=t->next_tag)++n;return '
                   'n;}\n'
                   'static void corpse(room *r){creature *m=calloc(1,sizeof *m);otag *t=calloc(1,sizeof '
                   '*t);assert(m&&t);t->obj=calloc(1,sizeof '
                   '*t->obj);assert(t->obj);strcpy(t->obj->name,"runtimegem");t->obj->parent_crt=m;m->first_obj=t;m->gold=13;m->type=MONSTER;m->fd=-1;m->level=8;m->hpmax=147;m->mpmax=51;strcpy(m->name,"runtime '
                   'rat");add_crt_rom(m,r,0);assert(hd_corpse_capture(m));del_crt_rom(m,r);free_crt(m);}\n'
                   'static void cmd_raise(creature *p){cmd c={0};strcpy(c.fullstr,"raise corpse '
                   '1");output[0]=0;hd_corpse_raise(p,&c);}\n'
                   'static int phase(const char *self,const char *step,int expect){pid_t p=fork();int '
                   'st;assert(p>=0);if(!p){execl(self,self,step,(char*)0);_exit(127);}assert(waitpid(p,&st,0)==p&&WIFEXITED(st)&&WEXITSTATUS(st)==expect);return '
                   '0;}\n'
                   'int main(int argc,char **argv){\n'
                   ' creature seed={0},*p=NULL,*pet;room a={0},b={0};hd_pet_state saved,old;\n'
                   ' a.rom_num=400;b.rom_num=401;\n'
                   ' '
                   'if(argc==1){phase(argv[0],"raise",0);phase(argv[0],"restore",0);phase(argv[0],"uncertain",73);phase(argv[0],"unexpected-free",73);phase(argv[0],"death",0);phase(argv[0],"dead",0);puts("PETRUNTIME: '
                   'native corpse raise, fresh-process restore, movement/stats, uncertain commit stop, '
                   'native death cleanup and non-resurrection PASS");return 0;}\n'
                   ' if(!strcmp(argv[1],"raise")){\n'
                   '  '
                   'strcpy(seed.name,name);seed.type=PLAYER;seed.class=MAGE;seed.level=8;seed.hpmax=seed.hpcur=1000;seed.mpmax=seed.mpcur=110;seed.rom_num=400;seed.gold=1000;\n'
                   '  '
                   'assert(hd_store_create_necromancer(name,&seed)==0);assert(hd_store_load_player(name,&p)==0);attach(p,&a);hd_necro_skeleton_reconnect(p);assert(!hd_necro_skeleton_probe(p));corpse(&a);\n'
                   '  '
                   'setenv("HD_ATOMIC_FAIL","before_rename",1);cmd_raise(p);unsetenv("HD_ATOMIC_FAIL");assert(!hd_necro_skeleton_probe(p)&&p->mpcur==110&&!a.first_obj);output[0]=0;hd_corpse_display(p,&a);assert(strstr(output,"corpse '
                   '1"));\n'
                   '  '
                   'cmd_raise(p);pet=hd_necro_skeleton_probe(p);assert(pet&&pet->hpcur==147&&pet->mpcur==51&&p->mpcur==102&&count(&a)==1);assert(a.first_obj&&a.first_obj->next_tag);assert(hd_pet_store_read(name,&saved)==0&&saved.hpcur==147&&saved.mpcur==51);cmd_raise(p);assert(strstr(output,"No '
                   'such corpse")&&p->mpcur==102);\n'
                   '  puts("PETRUNTIME: actual capture/raise release and committed 8 MP; failed write leaves '
                   'corpse untouched PASS");\n'
                   ' } else {\n'
                   '  '
                   'assert(hd_store_load_player(name,&p)==0);assert(hd_pet_store_read(name,&old)==0);attach(p,&a);hd_necro_skeleton_reconnect(p);pet=hd_necro_skeleton_probe(p);\n'
                   '  if(!strcmp(argv[1],"restore")){\n'
                   '   '
                   'assert(pet&&count(&a)==1&&p->mpcur==102&&pet->hpcur==147&&pet->mpcur==51);assert(strstr(output,"Your '
                   'saved skeleton '
                   'returns"));hd_necro_skeleton_reconnect(p);assert(count(&a)==1&&hd_necro_skeleton_probe(p)==pet);\n'
                   '   '
                   'pet->hpcur=71;pet->mpcur=12;hd_necro_skeleton_checkpoint_all();assert(hd_pet_store_read(name,&saved)==0&&saved.hpcur==71&&saved.mpcur==12);assert(saved.revision==old.revision+1);hd_necro_skeleton_checkpoint_all();assert(hd_pet_store_read(name,&old)==0&&old.revision==saved.revision);\n'
                   '   '
                   'attach(p,&b);hd_necro_skeleton_follow(p,&a,&b);assert(count(&a)==0&&count(&b)==1&&pet->parent_rom==&b);assert(hd_pet_store_read(name,&saved)==0&&saved.room==401&&saved.hpcur==71);assert(hd_store_save_live_player(name,p)==0);hd_necro_skeleton_logout(p);hd_necro_skeleton_room_unload(&b);assert(!pet->parent_rom&&count(&b)==0);hd_necro_skeleton_room_load(&b);assert(count(&b)==1&&pet->hpcur==71);assert(!hd_necro_skeleton_probe(p));hd_necro_skeleton_reconnect(p);assert(hd_necro_skeleton_probe(p)==pet&&count(&b)==1);puts("PETRUNTIME: '
                   'fresh process restore, no second charge, changed stats, no redundant write, native '
                   'follow and room unload PASS");\n'
                   '  }else if(!strcmp(argv[1],"uncertain")){\n'
                   '   '
                   'assert(pet&&pet->hpcur==71&&pet->mpcur==12);pet->hpcur=70;setenv("HD_ATOMIC_FAIL","after_rename",1);hd_necro_skeleton_checkpoint_all();assert(!"uncertain '
                   'checkpoint must stop private process");\n'
                   '  }else if(!strcmp(argv[1],"unexpected-free")){\n'
                   '   assert(pet&&pet->hpcur==70);del_crt_rom(pet,&a);free_crt(pet);assert(!"unexpected '
                   'live free must stop, not tombstone");\n'
                   '  }else if(!strcmp(argv[1],"death")){\n'
                   '   '
                   'assert(pet&&pet->hpcur==70&&pet->mpcur==12&&p->mpcur==102);pet->hpcur=0;hd_necro_skeleton_death(pet);assert(hd_pet_store_read(name,&saved)==0&&!saved.hpcur);del_crt_rom(pet,&a);free_crt(pet);assert(!hd_necro_skeleton_probe(p)&&!count(&a));assert(hd_pet_store_read(name,&saved)==0&&!saved.hpcur&&saved.revision>old.revision);puts("PETRUNTIME: '
                   'native free death tombstone before slot erased PASS");\n'
                   '  }else if(!strcmp(argv[1],"dead")){\n'
                   '   '
                   'assert(!pet&&!count(&a)&&!old.hpcur&&p->mpcur==102);corpse(&a);cmd_raise(p);assert(hd_necro_skeleton_probe(p)&&count(&a)==1&&p->mpcur==94);puts("PETRUNTIME: '
                   'dead pet not resurrected; new corpse raises one new pet PASS");\n'
                   '  }else return 2;\n'
                   ' }\n'
                   ' /* Deliberate process boundary: do not run an in-memory cleanup that would\n'
                   '  * destroy the pet. The saved record is the only cross-process pet state. */\n'
                   ' fflush(stdout);return 0;\n'
                   '}\n'}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile(src,after=False):
    expected=dict(EXPECTED)
    if after:expected.update(AFTER)
    for n,h in expected.items():
        f=src/n
        if not f.is_file() or f.is_symlink() or digest(f)!=h:raise RuntimeError('Exact source fingerprint mismatch: '+n)

def stage(src,pkg):
    profile(src)
    runpy.run_path(str(pkg/'patch.py'))['patch'](src)
    profile(src,True)
    print('PETRUNTIME: 47 exact source and six output fingerprints PASS',flush=True)

def checks(src,pkg,qa,abi,extra_include=None):
    qa.mkdir();fixture=qa/'runtime';fixture.mkdir();(fixture/'player').mkdir();storage=qa/'storage';storage.mkdir();(storage/'player').mkdir();(fixture/'help').mkdir()
    for f in (pkg/'help').iterdir():shutil.copyfile(f,fixture/'help'/f.name)
    assert len(list((fixture/'help').iterdir()))==7
    print('PETRUNTIME: seven ASCII native help pages staged privately',flush=True)
    def run(argv,label,cwd):
        path=qa/(label+'.log')
        with path.open('wb') as log: result=subprocess.run(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            print(path.read_text(errors='replace')[-7000:],flush=True)
            raise RuntimeError(label+' failed; '+str(path))
    cc=os.environ.get('CC','cc');base=[cc,abi,'-std=gnu89','-O1','-g','-fcommon','-DCOMPRESS','-Wno-return-type','-Wno-implicit-function-declaration','-Wno-int-conversion','-Wno-incompatible-pointer-types','-I',str(src)]
    if extra_include:base.extend(['-I',str(extra_include)])
    defs=['-DHD_NECROMANCER_PLAYTEST','-DHD_DEITY_PLAYTEST','-DHD_CORPSE_PLAYTEST','-DHD_PET_STORE_PLAYTEST','-DHD_PET_RUNTIME_PLAYTEST']
    for mode,flags in [('legacy',[]),('runtime',defs+(['-DHD74_PRIVATE_NATIVE'] if abi=='-m32' else []))]:
        for n in ('command1.c','update.c','creature.c'):
            run(base+flags+['-fsyntax-only',str(src/n)],mode+'-'+n,qa)
        print('PETRUNTIME: '+mode+' native syntax PASS',flush=True)
    components=['files1','files3','compress','hd_player_store','treasure_receipt','atomic_player_snapshot']
    linking=['-DHD_ATOMIC_TESTING','-ffunction-sections','-fdata-sections','-Wl,--gc-sections']
    run(base+defs[:4]+linking+[str(pkg/'test_pet_store.c')]+[str(src/(n+'.c')) for n in components]+['-o',str(qa/'test-store')],'storage-compile',qa)
    run(base+defs+linking+['-Wl,--wrap=load_obj',str(pkg/'test_runtime.c')]+[str(src/(n+'.c')) for n in components+['hd_necro_skeleton','hd_corpse','room']]+['-o',str(qa/'test-runtime')],'runtime-compile',qa)
    env=dict(os.environ);env.pop('HD_ATOMIC_FAIL',None)
    subprocess.run([str(qa/'test-store')],cwd=storage,env=env,check=True)
    subprocess.run([str(qa/'test-runtime')],cwd=fixture,env=env,check=True)
    if abi=='-m32':
        run(['make','-s','-B','-j2','NECROMANCER_PLAYTEST=1','DEITY_PLAYTEST=1','CORPSE_PLAYTEST=1','PET_STORE_PLAYTEST=1','PET_RUNTIME_PLAYTEST=1','frp.new'],'full-build',src)
        if (src/'frp.new').open('rb').read(5)!=b'\x7fELF\x01':raise RuntimeError('Expected ELF32 game')
        print('PETRUNTIME: PRIVATE RUNTIME PERSISTENCE ELF32 PASS',flush=True)
    else:print('PETRUNTIME: EXACT LOCAL NATIVE64 FOCUSED REPLAY PASS',flush=True)

def pid():
    p=subprocess.check_output(['systemctl','show','hollowdeep.service','-p','MainPID','--value'],text=True).strip()
    if not p.isdigit() or int(p)<1:raise RuntimeError('Expected an active production service')
    return p

def main():
    os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    if len(sys.argv)!=4:raise SystemExit('Usage: onepass_linode.py VERIFIED_PRIVATE_PETSTORE_SRC PRIOR_SOCKET_PY CACHE_SOCKET_PY')
    if os.geteuid()!=0 or os.readlink('/proc/self/ns/net')==os.readlink('/proc/1/ns/net'):raise SystemExit('Root and separate network namespace required')
    raw=Path(sys.argv[1]);src=raw.resolve(strict=True)
    if raw.is_symlink() or src!=ROOT/'necromancer-playtest-petstore-7i1sb1i8'/'src' or any(x.is_symlink() for x in src.rglob('*')):raise SystemExit('Refusing unapproved private source')
    profile(src);exe=src/'frp.new'
    if exe.open('rb').read(5)!=b'\x7fELF\x01':raise RuntimeError('Expected accepted ELF32 input')
    original=digest(exe);before=pid();work=Path(tempfile.mkdtemp(prefix='necromancer-playtest-runtime-',dir=ROOT));pkg=work/'pkg';pkg.mkdir()
    print('PRIVATE PET RUNTIME BUILD: '+str(work),flush=True)
    print('ACCEPTED INPUT BINARY SHA256: '+original,flush=True)
    try:
        for n,body in PAYLOAD.items():
            dest=pkg/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body,encoding='ascii')
        shutil.copytree(src,work/'src');stage(work/'src',pkg);checks(work/'src',pkg,work/'qa','-m32')
        print('PRIVATE SOURCE: '+str(work/'src'),flush=True)
        print('RUNTIME BINARY SHA256: '+digest(work/'src'/'frp.new'),flush=True)
        runpy.run_path(str(pkg/'runtime_gameplay.py'))['replay'](work/'src',{n[5:]:body for n,body in PAYLOAD.items() if n.startswith('help/')},Path(sys.argv[2]).resolve(strict=True),Path(sys.argv[3]).resolve(strict=True),work)
    finally:
        profile(src)
        if digest(exe)!=original:raise RuntimeError('Original private executable changed')
        if pid()!=before:raise RuntimeError('Production service PID changed; inspect immediately')
        print('PRODUCTION SERVICE PID: UNCHANGED',flush=True)
        print('PRODUCTION DEPLOYMENT: NONE',flush=True)
        print('PRIVATE RESULTS: '+str(work),flush=True)

if __name__=='__main__':main()
