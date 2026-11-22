/* Round79Z: informational only, no mount writes or context trust.
 * Requires an existing room pointer and exact native room ID agreement.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_stable_registry.h"
#include <string.h>

int hd79_stablecheck(creature *player,cmd *command)
{
    int rc;
    if(!player || !command || player->type!=PLAYER ||
       player->class>=CARETAKER || !player->parent_rom ||
       player->hpcur<=0 || player->rom_num<1 ||
       player->rom_num!=player->parent_rom->rom_num ||
       strcmp(command->fullstr,"stablecheck") ||
       strcmp(command->str[0],"stablecheck")) {
        if(player) print(player->fd,"Stable verification unavailable.\n");
        return 0;
    }
    rc=hd79_stable_registry_check("hollowdeep-data","mount-stables.hds",
                                  (unsigned)player->rom_num);
    if(rc==1) print(player->fd,"This room is a verified stable.\n");
    else if(rc==0) print(player->fd,"There is no registered stable in this room.\n");
    else print(player->fd,"Stable registry unavailable. No stable actions allowed.\n");
    return 0;
}
