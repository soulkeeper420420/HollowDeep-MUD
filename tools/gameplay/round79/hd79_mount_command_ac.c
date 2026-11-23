/* Round79Y: feature-gated native player command adapter.
 * Source is only installed into a NEW disposable ELF32 game candidate.
 * No mount NPCs, stable-room markers, movement hooks, or awards are made.
 * Physical mount presence and stable authenticity CANNOT be inferred from
 * the persisted roster. Therefore BOARD/STABLE/RETRIEVE FAIL CLOSED.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_mount_actions.h"
#include "hd79_mount_action_store.h"
#include "hd79_mount_store.h"
#ifdef HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST
#include "hd79_mount_presence_store.h"
#include "hd79_presence_dismount_store.h"
#endif
#include "hd79_mount_wire.h"
#include "hd_mount_travel.h"
#include <stdio.h>
#include <string.h>

/* cmd.fullstr is the native 256-byte input, while cmd.val[] can turn
 * numeric tokens into an implicit value of 1. Never parse cmd.val[] for
 * mount IDs: bare 'mount' and 'mount 1' can otherwise be confused.
 */
static int hd79_mount_command_parse(const cmd *command,hd79_mount_request *req)
{
    const char *input,*start,*p;
    char verb[17];
    size_t len=0,verb_len;
    if (!command || !req) return -1;
    while (len<sizeof command->fullstr && command->fullstr[len]) ++len;
    if (!len || len==sizeof command->fullstr) return -1;
    input=command->fullstr;
    while (*input==' ' || *input=='\t') ++input;
    start=input;
    p=input;
    while (*p && *p!=' ' && *p!='\t' && *p!='\r' && *p!='\n') {
        if ((size_t)(p-start)>=sizeof verb-1) return -1;
        ++p;
    }
    verb_len=(size_t)(p-start);
    if (!verb_len) return -1;
    memcpy(verb,start,verb_len);
    verb[verb_len]=0;
    /* No hidden aliases, abbreviations, or ambiguous input rewrites. */
    if (strcmp(verb,command->str[0])) return -1;
    if (hd79_mount_parse(verb,p,req)!=1) return -1;
    return 1;
}

static void hd79_show_mounts(creature *player,const hd79_mount_roster *state,
                             int status_only)
{
    char line[200];
    unsigned i;
    if (!state->count) {
        print(player->fd,"You do not own any mounts yet.\n");
        return;
    }
    if (status_only && !state->active_id) {
        print(player->fd,"You are traveling on foot.\n");
        return;
    }
    if (status_only) {
        i=state->active_id-1;
        if (i>=state->count) return;
        {
            const hd79_owned_mount *m=&state->entries[i];
            const hd_mount_profile *profile=hd_mount_get(m->species);
            if (!profile) return;
            snprintf(line,sizeof line,"Riding #%u %s, Endurance %u/%u.\n",
                     m->id,profile->name,m->endurance,profile->endurance_max);
            print(player->fd,line);
        }
        return;
    }
    print(player->fd,"Owned mounts:\n");
    for (i=0;i<state->count;i++) {
        const hd79_owned_mount *m=&state->entries[i];
        const hd_mount_profile *profile=hd_mount_get(m->species);
        if (!profile) continue;
        snprintf(line,sizeof line,"#%u %s - Endurance %u/%u%s%s\n",
                 m->id,profile->name,m->endurance,profile->endurance_max,
                 m->stabled?" [stabled]":"",
                 state->active_id==m->id?" [riding]":"");
        print(player->fd,line);
    }
}

int hd79_mount_command(creature *player,cmd *command)
{
    hd79_mount_request request;
#ifndef HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST
    hd79_mount_context context;
#else
    hd79_mount_presence positions;
#endif
    hd79_mount_roster state;
    int rc;
    if (!player || player->type!=PLAYER || player->class>=CARETAKER ||
        !player->name[0] || !player->parent_rom || player->hpcur<=0) {
        if (player) print(player->fd,"Mount actions are unavailable.\n");
        return 0;
    }
    if (hd79_mount_command_parse(command,&request)<0) {
        print(player->fd,"Usage: mount [list|status|1..6], dismount, stable ID, retrieve ID.\n");
        return 0;
    }
    if (player->rom_num<0 ||
        (unsigned)player->rom_num>HD79_MOUNT_MAX_STABLE_ROOM) {
        print(player->fd,"Mount location could not be verified.\n");
        return 0;
    }
#ifdef HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST
    rc=hd79_presence_store_read(player->name,&state,&positions);
    if (rc==HD79_PRESENCE_STORE_ABSENT) {
#else
    rc=hd79_mount_store_read(player->name,&state);
    if (rc==HD79_MOUNT_STORE_ABSENT) {
#endif
        print(player->fd,"No mounts registered for this character yet.\n");
        return 0;
    }
#ifdef HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST
    if (rc!=HD79_PRESENCE_STORE_OK || !hd79_presence_valid(&state,&positions)) {
#else
    if (rc!=HD79_MOUNT_STORE_OK) {
#endif
        print(player->fd,"Your mount record is unavailable. Action denied.\n");
        return 0;
    }
    if (request.action==HD79_ACTION_LIST ||
        request.action==HD79_ACTION_STATUS) {
        hd79_show_mounts(player,&state,
                         request.action==HD79_ACTION_STATUS);
        return 0;
    }
    /* No world-verified mount entity or stable-room authority is installed.
     * Never take present/stable context from client text or roster flags.
     */
    if (request.action==HD79_ACTION_BOARD ||
        request.action==HD79_ACTION_STABLE ||
        request.action==HD79_ACTION_RETRIEVE) {
        print(player->fd,
              "This mount action requires native presence/stable verification; not available yet.\n");
        return 0;
    }
    if (request.action!=HD79_ACTION_DISMOUNT) {
        print(player->fd,"Mount action denied.\n");
        return 0;
    }
    if (!state.active_id) {
        print(player->fd,"You are already on foot.\n");
        return 0;
    }
#ifdef HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST
    rc=hd79_presence_dismount_store(player->name,
                                   (unsigned)player->rom_num,&state);
    if (rc==HD79_DISMOUNT_SUCCESS)
#else
    memset(&context,0,sizeof context);
    context.room_id=(unsigned)player->rom_num;
    rc=hd79_mount_action_store(player->name,&request,&context,&state);
    if (rc==HD79_ACTION_STORE_OK)
#endif
        print(player->fd,"You dismount. Your mount Endurance is preserved.\n");
#ifdef HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST
    else if (rc==HD79_DISMOUNT_CONFLICT ||
             rc==HD79_DISMOUNT_UNCERTAIN)
#else
    else if (rc==HD79_ACTION_STORE_CONFLICT ||
             rc==HD79_ACTION_STORE_UNCERTAIN)
#endif
        print(player->fd,"Mount save state changed. Reconnect and retry.\n");
    else
        print(player->fd,"Dismount could not be saved. No action confirmed.\n");
    return 0;
}
