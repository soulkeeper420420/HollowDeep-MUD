/* Round79X: native-independent command grammar and authorized transitions.
 * This module cannot infer a stable from user input and cannot award mounts.
 */
#include "hd79_mount_actions.h"
#include "hd79_mount_wire.h"
#include <string.h>

static int space(unsigned char ch)
{
    return ch==' ' || ch=='\t' || ch=='\n' || ch=='\r';
}
static int parse_id(const char *s,unsigned *id)
{
    if (!s || s[0]<'1' || s[0]>'6' || s[1]!=0) return 0;
    *id=(unsigned)(s[0]-'0');
    return 1;
}
int hd79_mount_parse(const char *verb,const char *args,
                     hd79_mount_request *out)
{
    hd79_mount_request req;
    char buffer[65];
    const char *begin,*end;
    size_t length;
    if (!verb || !args || !out || strlen(verb)>16) return -1;
    begin=args;
    while (*begin && space((unsigned char)*begin)) ++begin;
    end=begin;
    while (*end && (size_t)(end-begin)<64) ++end;
    if (*end) return -1;
    while (end>begin && space((unsigned char)end[-1])) --end;
    length=(size_t)(end-begin);
    if (length>=sizeof buffer) return -1;
    memcpy(buffer,begin,length);
    buffer[length]=0;
    req.action=0;
    req.id=0;
    if (!strcmp(verb,"mount")) {
        if (!strcmp(buffer,"list") || !buffer[0]) req.action=HD79_ACTION_LIST;
        else if (!strcmp(buffer,"status")) req.action=HD79_ACTION_STATUS;
        else if (parse_id(buffer,&req.id)) req.action=HD79_ACTION_BOARD;
    } else if (!strcmp(verb,"dismount")) {
        if (!buffer[0]) req.action=HD79_ACTION_DISMOUNT;
    } else if (!strcmp(verb,"stable")) {
        if (parse_id(buffer,&req.id)) req.action=HD79_ACTION_STABLE;
    } else if (!strcmp(verb,"retrieve")) {
        if (parse_id(buffer,&req.id)) req.action=HD79_ACTION_RETRIEVE;
    }
    if (!req.action) return -1;
    *out=req;
    return 1;
}
int hd79_mount_apply(const hd79_mount_roster *prior,const char *epoch,
                     const hd79_mount_request *request,
                     const hd79_mount_context *context,
                     hd79_mount_roster *next)
{
    if (!prior || !epoch || !request || !context || !next ||
        !hd79_mount_roster_valid(prior) || strcmp(prior->epoch,epoch) ||
        context->room_id>HD79_MOUNT_MAX_STABLE_ROOM ||
        (context->verified_stable!=0 && context->verified_stable!=1) ||
        (context->mount_present!=0 && context->mount_present!=1))
        return -1;
    switch (request->action) {
    case HD79_ACTION_LIST:
    case HD79_ACTION_STATUS:
        return request->id==0 ? HD79_ACTION_READONLY : -1;
    case HD79_ACTION_BOARD:
        if (!request->id) return -1;
        return hd79_mount_board(prior,next,epoch,request->id,
                                context->mount_present);
    case HD79_ACTION_DISMOUNT:
        if (request->id) return -1;
        return hd79_mount_dismount(prior,next,epoch);
    case HD79_ACTION_STABLE:
        if (!request->id || !context->room_id) return -1;
        return hd79_mount_stable(prior,next,epoch,request->id,
                                 context->room_id,context->verified_stable,
                                 context->mount_present);
    case HD79_ACTION_RETRIEVE:
        if (!request->id || !context->room_id) return -1;
        return hd79_mount_retrieve(prior,next,epoch,request->id,
                                   context->room_id,context->verified_stable);
    default:
        return -1;
    }
}
