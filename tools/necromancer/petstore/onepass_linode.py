#!/usr/bin/env python3
"""Private storage-only replay. No live game or source edits."""
from pathlib import Path
import hashlib, os, shutil, subprocess, sys, tempfile

ROOT=Path('/root/hollowdeep-dev')
BINARY_SHA='791ca5f9d456308e4334a1819195e280b044923751c13fc854d4776730bf7d21'
EXPECTED={'Makefile': '1e14e4009e6aa35cdd4aac4da91eee296805b9b7c1eb8d9e6d8eedf8c727ac61',
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
 'hd_player_store.c': '03a86ce18dd4677b96134fe8121d99372e18202c33706ffcf1146a696ace41f5',
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
AFTER={'hd_player_store.c': '36be86735ec7061977c385c0a419e568ad4ec4daa3d639cff5da11278546acc4', 'Makefile': '00fd4b67459f439ebf46b4bdf800a2bb13c23331c8d27d6dc57d61afe81731dc'}
MAKE_INSERT='# Private persistent pet storage API only; no gameplay hooks.\nifeq ($(PET_STORE_PLAYTEST),1)\nifneq ($(NECROMANCER_PLAYTEST)$(DEITY_PLAYTEST)$(CORPSE_PLAYTEST),111)\n$(error PET_STORE_PLAYTEST requires all three prior private flags)\nendif\nCFLAGS += -DHD_PET_STORE_PLAYTEST\nendif\n\nfrp.new: $(OBJECTS)'
PAYLOAD={'hd_pet_store.h': '#ifndef HD_PET_STORE_H\n'
                   '#define HD_PET_STORE_H\n'
                   '/* Private storage foundation only. No live gameplay hook. */\n'
                   '#include <stdint.h>\n'
                   'struct creature;\n'
                   '#define HD_PET_ABSENT 1\n'
                   '#define HD_PET_CONFLICT 2\n'
                   '#define HD_PET_ERROR (-1)\n'
                   '#define HD_PET_UNCERTAIN (-2)\n'
                   '#define HD_PET_OK 0\n'
                   "/* All-zero stats = dead/no pet. Epoch identifies this character's save;\n"
                   ' * revision is monotonically increased for every successful change. */\n'
                   'typedef struct {\n'
                   '    char epoch[25];\n'
                   '    uint32_t revision;\n'
                   '    unsigned level, room, hpmax, hpcur, mpmax, mpcur;\n'
                   '} hd_pet_state;\n'
                   'int hd_pet_store_read(const char *name, hd_pet_state *out);\n'
                   '/* Initialize an absent record for a verified existing Necromancer only. */\n'
                   'int hd_pet_store_init(const char *name, hd_pet_state *out);\n'
                   '/* Compare AND replace the complete expected state. requested must retain\n'
                   ' * epoch/revision. Dead -> alive requires live_owner, and atomically saves\n'
                   ' * its normalized inventory and mana minus eight. Other changes preserve\n'
                   ' * existing native player bytes; live_owner must be NULL. Never mutates live\n'
                   ' * memory. On UNCERTAIN, freeze/reconcile before any retry or acknowledgement. */\n'
                   'int hd_pet_store_commit(const char *name, const hd_pet_state *expected,\n'
                   '                        const hd_pet_state *requested, struct creature *live_owner,\n'
                   '                        hd_pet_state *committed);\n'
                   '#endif\n',
 'hd_pet_store.inc': '/* Included by hd_player_store.c under the private storage flag, so this\n'
                     ' * reuses the exact locked, bounded native player reader and atomic writer.\n'
                     ' * No standalone sidecar, pointer serialization, or live game hook. */\n'
                     '#include "hd_pet_store.h"\n'
                     '#include <stdio.h>\n'
                     '\n'
                     'static int pet_hex(const char *s, size_t n)\n'
                     '{\n'
                     '    size_t i;\n'
                     '    for (i=0;i<n;i++) if (!s[i] || !strchr("0123456789abcdef",s[i])) return 0;\n'
                     '    return s[n]==0;\n'
                     '}\n'
                     'static int pet_valid(const hd_pet_state *s)\n'
                     '{\n'
                     '    if (!s || !pet_hex(s->epoch,24) || !strcmp(s->epoch,"000000000000000000000000") || '
                     '!s->revision) return 0;\n'
                     '    if (!s->hpcur) return !(s->level || s->room || s->hpmax || s->mpmax || s->mpcur);\n'
                     '    return s->level>=1 && s->level<=60 && s->room<RMAX && s->hpmax<=32767 &&\n'
                     '        s->hpcur<=s->hpmax && s->mpmax<=32767 && s->mpcur<=s->mpmax;\n'
                     '}\n'
                     '/* 64 lowercase hex chars: version/magic 8, epoch 24, revision 8,\n'
                     ' * 6 fixed 4-digit fields = 24. All values checked before encoding. */\n'
                     'static int pet_encode(const hd_pet_state *s, char out[65])\n'
                     '{\n'
                     '    if (!pet_valid(s)) return -1;\n'
                     '    return snprintf(out,65,"a74d0001%s%08lx%04x%04x%04x%04x%04x%04x",\n'
                     '        s->epoch,(unsigned '
                     'long)s->revision,s->level,s->room,s->hpmax,s->hpcur,s->mpmax,s->mpcur)==64?0:-1;\n'
                     '}\n'
                     'static unsigned long pet_num(const char *s, size_t n)\n'
                     '{\n'
                     '    unsigned long v=0; size_t i;\n'
                     "    for(i=0;i<n;i++) v=(v<<4) | (unsigned long)(s[i]<='9'?s[i]-'0':s[i]-'a'+10);\n"
                     '    return v;\n'
                     '}\n'
                     'static int pet_decode(const char *wire, hd_pet_state *out)\n'
                     '{\n'
                     '    hd_pet_state s;\n'
                     '    if(!pet_hex(wire,64) || memcmp(wire,"a74d0001",8)) return -1;\n'
                     '    memset(&s,0,sizeof s); memcpy(s.epoch,wire+8,24);\n'
                     '    s.revision=(uint32_t)pet_num(wire+32,8);\n'
                     '    s.level=(unsigned)pet_num(wire+40,4); s.room=(unsigned)pet_num(wire+44,4);\n'
                     '    s.hpmax=(unsigned)pet_num(wire+48,4); s.hpcur=(unsigned)pet_num(wire+52,4);\n'
                     '    s.mpmax=(unsigned)pet_num(wire+56,4); s.mpcur=(unsigned)pet_num(wire+60,4);\n'
                     '    if(!pet_valid(&s)) return -1;\n'
                     '    *out=s; return 0;\n'
                     '}\n'
                     'static int pet_entry(hd_receipt_set *set)\n'
                     '{\n'
                     '    size_t i;\n'
                     '    for(i=0;i<set->count;i++) if(!strcmp(set->entries[i].claim_id,pet_id)) return '
                     '(int)i;\n'
                     '    return -1;\n'
                     '}\n'
                     'static int pet_check_owner(const unsigned char *raw, hd_receipt_set *set)\n'
                     '{\n'
                     '    return ((const creature*)raw)->type==PLAYER && ((const creature*)raw)->class==MAGE '
                     '&&\n'
                     '        hd_receipt_lookup(set,necromancer_id,necromancer_identity)==1;\n'
                     '}\n'
                     'static int pet_epoch(char out[25])\n'
                     '{\n'
                     '    unsigned char b[12]; size_t off=0,i; ssize_t n;\n'
                     '    const char *hex="0123456789abcdef";\n'
                     '    int fd=open("/dev/urandom",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);\n'
                     '    if(fd<0) return -1;\n'
                     '    while(off<sizeof b) {\n'
                     '        n=read(fd,b+off,sizeof b-off);\n'
                     '        if(n<0 && errno==EINTR) continue;\n'
                     '        if(n<=0) {close(fd);return -1;}\n'
                     '        off+=(size_t)n;\n'
                     '    }\n'
                     '    close(fd);\n'
                     '    for(i=0;i<sizeof b;i++){out[i*2]=hex[b[i]>>4];out[i*2+1]=hex[b[i]&15];}\n'
                     '    out[24]=0; return 0;\n'
                     '}\n'
                     'int hd_pet_store_read(const char *name, hd_pet_state *out)\n'
                     '{\n'
                     '    unsigned char *raw; hd_receipt_set set; size_t size=0,native=0; int '
                     'i,rc=HD_PET_ERROR;\n'
                     '    if(!out) return rc;\n'
                     '    memset(out,0,sizeof *out);\n'
                     '    raw=malloc(HD_RAW_CAPACITY); if(!raw) return rc;\n'
                     '    if(read_record(name,raw,&size,&native,&set)==0 && pet_check_owner(raw,&set)){\n'
                     '        i=pet_entry(&set);\n'
                     '        rc=i<0?HD_PET_ABSENT:pet_decode(set.entries[i].manifest_sha256,out);\n'
                     '    }\n'
                     '    free(raw); return rc;\n'
                     '}\n'
                     '/* One transaction. Init and non-raise operations preserve the entire native\n'
                     ' * payload byte-for-byte. Only a raise replaces it with a normalized trusted\n'
                     ' * snapshot and debit. Ordinary saves retain the reserved receipt. */\n'
                     'static int pet_transaction(const char *name,const hd_pet_state *expected,\n'
                     '                           const hd_pet_state *requested,creature *live,\n'
                     '                           hd_pet_state *out,int init)\n'
                     '{\n'
                     '    unsigned char *raw=NULL,*packed=NULL; hd_receipt_set set;\n'
                     '    hd_pet_state old,next; creature snapshot; otag worn[MAXWEAR];\n'
                     '    char a[65],b[65],wire[65];\n'
                     '    size_t size=0,native=0,total=0,expected_size=0;\n'
                     '    int lock=-1,idx,rc=HD_PET_ERROR,n,slot;\n'
                     '    if(!out || !valid_name(name)) return rc;\n'
                     '    if(!init && (!expected || !requested || pet_encode(expected,a) || '
                     'pet_encode(requested,b))) return rc;\n'
                     '    raw=malloc(HD_RAW_CAPACITY); packed=malloc(HD_PLAYER_COMPRESSED_LIMIT);\n'
                     '    if(!raw || !packed) goto done;\n'
                     '    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);\n'
                     '    if(lock<0 || flock(lock,LOCK_EX)<0) goto done;\n'
                     '    if(read_record(name,raw,&size,&native,&set) || !pet_check_owner(raw,&set)) goto '
                     'done;\n'
                     '    idx=pet_entry(&set);\n'
                     '    if(init){\n'
                     '        if(idx>=0){\n'
                     '            '
                     'if(!pet_decode(set.entries[idx].manifest_sha256,&next)){*out=next;rc=HD_PET_CONFLICT;}\n'
                     '            goto done;\n'
                     '        }\n'
                     '        memset(&next,0,sizeof next); next.revision=1;\n'
                     '        if(pet_epoch(next.epoch)) goto done;\n'
                     '    }else{\n'
                     '        if(idx<0){rc=HD_PET_CONFLICT;goto done;}\n'
                     '        if(pet_decode(set.entries[idx].manifest_sha256,&old)) goto done;\n'
                     '        if(strcmp(set.entries[idx].manifest_sha256,a)){rc=HD_PET_CONFLICT;goto done;}\n'
                     '        if(strcmp(expected->epoch,requested->epoch) || '
                     'expected->revision!=requested->revision || old.revision==UINT32_MAX) goto done;\n'
                     '        next=*requested; next.revision=old.revision+1;\n'
                     '        if(!old.hpcur && next.hpcur){\n'
                     '            /* Live owner must be from this trusted game process; never a\n'
                     '             * client-supplied struct. Caller must prohibit concurrent saves. */\n'
                     '            if(!live || live->type!=PLAYER || live->class!=MAGE || '
                     '!native_name(live->name,name) ||\n'
                     '               live->mpcur<8 || live->mpcur>live->mpmax || '
                     'next.room!=(unsigned)live->rom_num ||\n'
                     '               next.hpcur!=next.hpmax || next.mpcur!=next.mpmax) goto done;\n'
                     '            snapshot=*live; snapshot.mpcur-=8;\n'
                     '            for(slot=0;slot<MAXWEAR;slot++) if(snapshot.ready[slot]){\n'
                     '                worn[slot].obj=snapshot.ready[slot]; '
                     'worn[slot].next_tag=snapshot.first_obj;\n'
                     '                snapshot.first_obj=&worn[slot]; snapshot.ready[slot]=NULL;\n'
                     '            }\n'
                     '            if(native_size(&snapshot,&expected_size)) goto done;\n'
                     '            n=write_crt_to_mem((char*)raw,&snapshot,0);\n'
                     '            if(n<0 || (size_t)n!=expected_size) goto done;\n'
                     '            native=expected_size;\n'
                     '        }else{\n'
                     '            if(live || !old.hpcur) goto done;\n'
                     '            if(next.hpcur && (old.hpmax!=next.hpmax || old.mpmax!=next.mpmax || '
                     'old.level!=next.level)) goto done;\n'
                     '        }\n'
                     '    }\n'
                     '    if(pet_encode(&next,wire)) goto done;\n'
                     '    if(idx<0){if(hd_receipt_add(&set,pet_id,wire)) goto done;}\n'
                     '    else memcpy(set.entries[idx].manifest_sha256,wire,sizeof wire);\n'
                     '    if(hd_receipt_encode(raw,HD_RAW_CAPACITY,native,&set,&total)) goto done;\n'
                     '    '
                     'n=hd_compress_bounded((char*)raw,(char*)packed,(int)total,HD_PLAYER_COMPRESSED_LIMIT);\n'
                     '    if(n<1 || n>(int)HD_PLAYER_COMPRESSED_LIMIT) goto done;\n'
                     '    n=hd_atomic_player_snapshot(PLAYERPATH,name,packed,(size_t)n);\n'
                     '    if(n==HD_SNAPSHOT_OK || n==HD_SNAPSHOT_UNCERTAIN){\n'
                     '        *out=next; rc=n==HD_SNAPSHOT_OK?HD_PET_OK:HD_PET_UNCERTAIN;\n'
                     '    }\n'
                     'done:\n'
                     '    if(lock>=0){flock(lock,LOCK_UN);close(lock);}\n'
                     '    free(raw);free(packed);return rc;\n'
                     '}\n'
                     'int hd_pet_store_init(const char *name,hd_pet_state *out)\n'
                     '{ return pet_transaction(name,NULL,NULL,NULL,out,1); }\n'
                     'int hd_pet_store_commit(const char *name,const hd_pet_state *expected,\n'
                     '                        const hd_pet_state *requested,creature '
                     '*live_owner,hd_pet_state *out)\n'
                     '{ return pet_transaction(name,expected,requested,live_owner,out,0); }\n',
 'help/corpses': 'MONSTER CORPSES - PRIVATE PLAYTEST\n'
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
                 'Private development note: the saved-pet record is being tested separately.\n'
                 'No in-game restart restore is enabled by the storage-foundation build.\n',
 'help/necromancer-corpses': 'NECROMANCER - PRIVATE CLASS PLAYTEST\n'
                             'The Necromancer has a protected class identity using the native Mage rules\n'
                             'for training and combat. Its first skill is Raise Skeleton (8 MP).\n'
                             "Use raise corpse [id] to animate a slain monster; the corpse's ordinary\n"
                             "loot drops and its maximum HP/MP become the skeleton's full starting stats.\n"
                             'One living summon, no expiration timer. Heal with Vigor, Mend, Restore or\n'
                             'compatible healing items. See help raise skeleton and help corpse.\n'
                             'The summon survives logout and room-cache eviction within one game process.\n'
                             'Full server restart durability remains pending. Nothing here is live yet.\n'
                             '\n'
                             'Private development note: the saved-pet record is being tested separately.\n'
                             'No in-game restart restore is enabled by the storage-foundation build.\n',
 'help/raise-corpse': 'RAISE SKELETON - NECROMANCER (PRIVATE PLAYTEST)\n'
                      '  raise corpse [id]     Look for corpse IDs when several are present.\n'
                      '  raise skeleton [id]   Equivalent. Alias: raiseskeleton (one corpse only).\n'
                      'Costs 8 mana, one active skeleton. The selected eligible corpse is consumed,\n'
                      "its loot drops to the floor, and the monster's maximum HP/MP become the\n"
                      "summon's starting HP/MP. The summon does not expire; death destroys it.\n"
                      'Vigor, Mend, Restore and compatible healing items can heal it. For potions:\n'
                      '  drink <healing-potion> on skeleton\n'
                      'Failed raises do not spend mana or consume loot. A killed summoned skeleton\n'
                      'creates no corpse or loot. Living pets survive room-cache eviction; full\n'
                      'server restart durability is not yet implemented. See help corpse and\n'
                      'help necromancer.\n'
                      '\n'
                      'Private development note: the saved-pet record is being tested separately.\n'
                      'No in-game restart restore is enabled by the storage-foundation build.\n',
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
                     '}\n'}


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def profile(src):
    for name,h in EXPECTED.items():
        path=src/name
        if path.is_symlink() or not path.is_file() or digest(path)!=h:
            raise RuntimeError('Private baseline mismatch: '+name)
    if any((src/n).exists() for n in ('hd_pet_store.h','hd_pet_store.inc')):
        raise RuntimeError('Already staged')

def replace(s,a,b):
    if s.count(a)!=1: raise RuntimeError('Unexpected patch anchor: '+a)
    return s.replace(a,b)

def stage(src,pkg):
    profile(src)
    s=(src/'hd_player_store.c').read_text()
    s=replace(s,'static int reserved_receipt(const char *claim)', 'static const char pet_id[] = "ffffffffffffffffffffffffffffff76";\n\nstatic int reserved_receipt(const char *claim)')
    s=replace(s,'return !strcmp(claim, life_id) || !strcmp(claim, necromancer_id);','return !strcmp(claim, life_id) || !strcmp(claim, necromancer_id) || !strcmp(claim, pet_id);')
    s+='\n#ifdef HD_PET_STORE_PLAYTEST\n#ifndef HD_NECROMANCER_PLAYTEST\n#error "Pet store requires verified Necromancer identity"\n#endif\n#include "hd_pet_store.inc"\n#endif\n'
    m=replace((src/'Makefile').read_text(),'frp.new: $(OBJECTS)',MAKE_INSERT)
    m=replace(m,'clean:\n','hd_player_store.o: $(wildcard hd_pet_store.h hd_pet_store.inc)\nclean:\n')
    for n,body in [('hd_player_store.c',s),('Makefile',m)]:
        if hashlib.sha256(body.encode()).hexdigest()!=AFTER[n]:raise RuntimeError('Unexpected output SHA: '+n)
    for n,body in [('hd_player_store.c',s),('Makefile',m)]: (src/n).write_text(body)
    for n in ('hd_pet_store.h','hd_pet_store.inc'): shutil.copyfile(pkg/n,src/n)
    print('PETSTORE: all exact input and patched source fingerprints PASS',flush=True)

def checks(src,pkg,qa,abi):
    qa.mkdir(); fixture=qa/'fixture';fixture.mkdir();(fixture/'player').mkdir();(fixture/'help').mkdir()
    for n in ('corpses','raise-corpse','necromancer-corpses'):
        shutil.copyfile(pkg/'help'/n,fixture/'help'/n)
        assert 'No in-game restart restore is enabled' in (fixture/'help'/n).read_text('ascii')
    print('PETSTORE: three native ASCII help pages staged privately; restart warning retained',flush=True)
    def run(argv,label,cwd):
        path=qa/(label+'.log')
        with path.open('wb') as log: p=subprocess.run(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
        if p.returncode: print(path.read_text(errors='replace')[-6000:]);raise RuntimeError(label+' failed; see '+str(path))
    cc=os.environ.get('CC','cc')
    base=[cc,abi,'-std=gnu89','-O1','-g','-fcommon','-DCOMPRESS','-Wno-implicit-function-declaration','-Wno-int-conversion','-Wno-incompatible-pointer-types','-I',str(src)]
    for flags in ([],['-DHD_NECROMANCER_PLAYTEST'],['-DHD_NECROMANCER_PLAYTEST','-DHD_PET_STORE_PLAYTEST']):
        run(base+flags+['-fsyntax-only',str(src/'hd_player_store.c')],'syntax-'+str(len(flags)),qa)
    exe=qa/'test-pet'
    run(base+['-DHD_NECROMANCER_PLAYTEST','-DHD_PET_STORE_PLAYTEST','-DHD_ATOMIC_TESTING','-ffunction-sections','-fdata-sections','-Wl,--gc-sections',str(pkg/'test_pet_store.c')]+[str(src/(n+'.c')) for n in ('files1','files3','compress','hd_player_store','treasure_receipt','atomic_player_snapshot')]+['-o',str(exe)],'native-test-compile',qa)
    if abi=='-m32' and exe.open('rb').read(5)!=b'\x7fELF\x01':raise RuntimeError('Expected ELF32 test')
    env=dict(os.environ);env.pop('HD_ATOMIC_FAIL',None)
    subprocess.run([str(exe)],cwd=fixture,env=env,check=True)
    if abi=='-m32':
        run(['make','-s','-B','-j2','NECROMANCER_PLAYTEST=1','DEITY_PLAYTEST=1','CORPSE_PLAYTEST=1','PET_STORE_PLAYTEST=1','frp.new'],'full-build',src)
        if (src/'frp.new').open('rb').read(5)!=b'\x7fELF\x01':raise RuntimeError('Expected ELF32 game')
        print('PETSTORE: PRIVATE DISK STORAGE FOUNDATION ELF32 PASS',flush=True)
    else: print('PETSTORE: EXACT ARCHIVE LOCAL NATIVE64 FOUNDATION PASS',flush=True)

def pid():
    value=subprocess.check_output(['systemctl','show','hollowdeep.service','-p','MainPID','--value'],text=True).strip()
    if not value.isdigit() or int(value)<1:raise RuntimeError('Expected active live service')
    return value

def main():
    os.umask(0o077)
    if len(sys.argv)!=2:raise SystemExit('Usage: onepass_linode.py VERIFIED_PRIVATE_CACHE_SRC')
    raw=Path(sys.argv[1]);src=raw.resolve(strict=True)
    if raw.is_symlink() or src!=ROOT/'necromancer-playtest-cache-jyf14lkl'/'src' or any(x.is_symlink() for x in src.rglob('*')):raise SystemExit('Refusing unapproved private source')
    profile(src)
    if digest(src/'frp.new')!=BINARY_SHA:raise SystemExit('Accepted executable mismatch')
    before=pid();work=Path(tempfile.mkdtemp(prefix='necromancer-playtest-petstore-',dir=ROOT));pkg=work/'pkg';pkg.mkdir()
    print('PRIVATE PET STORE BUILD: '+str(work),flush=True)
    try:
        for n,body in PAYLOAD.items():
            target=pkg/n;target.parent.mkdir(exist_ok=True,parents=True);target.write_text(body,encoding='ascii')
        shutil.copytree(src,work/'src')
        stage(work/'src',pkg)
        checks(work/'src',pkg,work/'qa','-m32')
        if digest(src/'frp.new')!=BINARY_SHA:raise RuntimeError('Original private binary changed')
        profile(src)
    finally:
        if pid()!=before:raise RuntimeError('Protected live service PID changed')
        print('PRODUCTION SERVICE PID: UNCHANGED',flush=True)
    print('PRODUCTION DEPLOYMENT: NONE',flush=True)
    print('PRIVATE SOURCE: '+str(work/'src'),flush=True)
    print('PRIVATE RESULTS: '+str(work/'qa'),flush=True)

if __name__=='__main__':main()
