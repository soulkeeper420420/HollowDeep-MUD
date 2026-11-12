#include <stddef.h>
#include <stdio.h>
#include "mstruct.h"

int main(void)
{
    room native_room;
    printf("{\"header\":%zu,\"exits\":%zu,\"table\":%zu,\"slots\":%zu,"
           "\"slot\":%zu,\"interval\":%zu,\"time\":%zu,\"id\":%zu,"
           "\"creature\":%zu,\"type\":%zu,\"name\":%zu,\"name_size\":%zu,"
           "\"monster\":%d,\"maximum\":%d,\"per_file\":%d}\n",
           sizeof(room), sizeof(exit_), offsetof(room, perm_mon),
           sizeof(native_room.perm_mon) / sizeof(lasttime), sizeof(lasttime),
           offsetof(lasttime, interval), offsetof(lasttime, ltime),
           offsetof(lasttime, misc), sizeof(creature), offsetof(creature, type),
           offsetof(creature, name), sizeof(((creature *)0)->name),
           MONSTER, CMAX, MFILESIZE);
    return sizeof(long) != 4 || sizeof(short) != 2;
}
