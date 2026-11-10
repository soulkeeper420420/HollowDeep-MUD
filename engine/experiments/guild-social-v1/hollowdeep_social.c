/*
 * HollowDeep experimental guild/social batch 1.
 * ORIGINAL IMPLEMENTATION. No Atlas MUD source code copied.
 * Requires Mordor mstruct.h and existing HollowDeep staff authorization.
 *
 * IMPORTANT: HD_GUILD_STAGING_FREE_CREATE permits deed-free guild creation
 * ONLY in an isolated test game. Never deploy that test flag to production.
 * Production clan creation stays disabled until native deed validation
 * and atomic inventory+registry handling are implemented and tested.
 */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_social.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>

extern void print(int fd, const char *format, ...);
extern creature *find_who(char *name);
extern int Tablesize;
extern plystruct Ply[PMAX];

#ifndef O_NOFOLLOW
#define O_NOFOLLOW 0
#endif
#ifndef HOLLOWDEEP_DATA_DIR
#define HOLLOWDEEP_DATA_DIR "hollowdeep-data"
#endif
#define HD_GUILD_FILE HOLLOWDEEP_DATA_DIR "/player-guilds.v1"
#define HD_GUILD_TEMP HOLLOWDEEP_DATA_DIR "/.player-guilds-XXXXXX"
#define HD_MAX_GUILDS 32
#define HD_MAX_MEMBERS 256
#define HD_MAX_INVITES 256
#define HD_MAX_GUILD_FILE 65536
#define HD_MAX_CHAT_USERS 128

struct hd_guild { char name[25]; };
struct hd_member { char guild[25], name[20]; int rank; };
struct hd_invitation { char guild[25], name[20]; };
struct hd_guild_state {
    int guild_count, member_count, invite_count;
    struct hd_guild guilds[HD_MAX_GUILDS];
    struct hd_member members[HD_MAX_MEMBERS];
    struct hd_invitation invites[HD_MAX_INVITES];
};
struct hd_chat_user { char name[20]; time_t last_chat; int global_off; };
static struct hd_chat_user chat_users[HD_MAX_CHAT_USERS];

/* Only letters are allowed for guild and character identifiers in V1.
 * This deliberately rules out path, delimiter, ANSI and whitespace injection. */
static int identifier(const char *value, size_t max)
{
    size_t i, len;
    if (!value) return 0;
    len = strnlen(value, max);
    if (len < 3 || len >= max) return 0;
    for (i = 0; i < len; i++)
        if (!isalpha((unsigned char)value[i]) || (unsigned char)value[i] > 127)
            return 0;
    return 1;
}
static void normalized(const char *src, char *out, size_t size)
{
    size_t i;
    for (i = 0; i + 1 < size && src[i]; i++)
        out[i] = (char)(i ? tolower((unsigned char)src[i]) :
                           toupper((unsigned char)src[i]));
    out[i] = 0;
}
static int guild_index(const struct hd_guild_state *s, const char *name)
{
    int i;
    for (i = 0; i < s->guild_count; i++)
        if (!strcasecmp(s->guilds[i].name, name)) return i;
    return -1;
}
static int member_index(const struct hd_guild_state *s, const char *name)
{
    int i;
    for (i = 0; i < s->member_count; i++)
        if (!strcasecmp(s->members[i].name, name)) return i;
    return -1;
}
static int invitation_index(const struct hd_guild_state *s,
                            const char *guild, const char *name)
{
    int i;
    for (i = 0; i < s->invite_count; i++)
        if (!strcasecmp(s->invites[i].guild, guild) &&
            !strcasecmp(s->invites[i].name, name)) return i;
    return -1;
}
static int secure_data_dir(void)
{
    struct stat st;
    if (lstat(HOLLOWDEEP_DATA_DIR, &st)) return 0;
    return S_ISDIR(st.st_mode) && st.st_uid == geteuid() &&
           !(st.st_mode & (S_IWGRP | S_IWOTH));
}
static int load_guilds(struct hd_guild_state *s)
{
    struct stat st;
    char line[160], name[25], guild[25], extra;
    int fd, rank, i, j, leader_count;
    FILE *fp;
    if (!secure_data_dir()) return 0;
    fd = open(HD_GUILD_FILE, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return errno == ENOENT;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) ||
        st.st_uid != geteuid() || st.st_size > HD_MAX_GUILD_FILE ||
        (st.st_mode & (S_IWGRP | S_IWOTH))) {
        close(fd); return 0;
    }
    fp = fdopen(fd, "r");
    if (!fp) { close(fd); return 0; }
    if (!fgets(line, sizeof(line), fp) || strcmp(line, "HDGUILD1\n"))
        goto invalid;
    while (fgets(line, sizeof(line), fp)) {
        if (!strchr(line, '\n')) goto invalid;
        if (line[0] == 'G' && line[1] == ' ') {
            if (sscanf(line, "G %24s %c", guild, &extra) != 1 ||
                !identifier(guild, sizeof(guild)) ||
                s->guild_count == HD_MAX_GUILDS || guild_index(s, guild) >= 0)
                goto invalid;
            strcpy(s->guilds[s->guild_count++].name, guild);
        } else if (line[0] == 'M' && line[1] == ' ') {
            if (sscanf(line, "M %24s %24s %d %c",
                       guild, name, &rank, &extra) != 3 ||
                !identifier(name, 20) || !identifier(guild, 25) ||
                guild_index(s, guild) < 0 || member_index(s, name) >= 0 ||
                s->member_count == HD_MAX_MEMBERS || rank < 0 || rank > 2)
                goto invalid;
            strcpy(s->members[s->member_count].name, name);
            strcpy(s->members[s->member_count].guild, guild);
            s->members[s->member_count++].rank = rank;
        } else if (line[0] == 'I' && line[1] == ' ') {
            if (sscanf(line, "I %24s %24s %c",
                       guild, name, &extra) != 2 ||
                !identifier(name, 20) || !identifier(guild, 25) ||
                guild_index(s, guild) < 0 ||
                invitation_index(s, guild, name) >= 0 ||
                s->invite_count == HD_MAX_INVITES)
                goto invalid;
            strcpy(s->invites[s->invite_count].name, name);
            strcpy(s->invites[s->invite_count++].guild, guild);
        } else goto invalid;
    }
    if (ferror(fp)) goto invalid;
    for (i = 0; i < s->guild_count; i++) {
        leader_count = 0;
        for (j = 0; j < s->member_count; j++)
            if (!strcasecmp(s->guilds[i].name, s->members[j].guild) &&
                s->members[j].rank == 2) leader_count++;
        if (leader_count != 1) goto invalid;
    }
    if (fclose(fp)) return 0;
    return 1;
invalid:
    fclose(fp);
    return 0;
}
static int save_guilds(const struct hd_guild_state *s)
{
    char temp[] = HD_GUILD_TEMP;
    int fd, dirfd, i, ok;
    FILE *fp;
    if (!secure_data_dir()) return 0;
    fd = mkstemp(temp);
    if (fd < 0) return 0;
    if (fchmod(fd, 0600)) { close(fd); unlink(temp); return 0; }
    fp = fdopen(fd, "w");
    if (!fp) { close(fd); unlink(temp); return 0; }
    ok = fprintf(fp, "HDGUILD1\n") > 0;
    for (i = 0; ok && i < s->guild_count; i++)
        ok = fprintf(fp, "G %s\n", s->guilds[i].name) > 0;
    for (i = 0; ok && i < s->member_count; i++)
        ok = fprintf(fp, "M %s %s %d\n", s->members[i].guild,
                     s->members[i].name, s->members[i].rank) > 0;
    for (i = 0; ok && i < s->invite_count; i++)
        ok = fprintf(fp, "I %s %s\n", s->invites[i].guild,
                     s->invites[i].name) > 0;
    if (fflush(fp) || fsync(fd)) ok = 0;
    if (fclose(fp)) ok = 0;
    if (ok) ok = rename(temp, HD_GUILD_FILE) == 0;
    if (!ok) unlink(temp);
    if (ok) {
        dirfd = open(HOLLOWDEEP_DATA_DIR, O_RDONLY | O_DIRECTORY);
        if (dirfd >= 0) { fsync(dirfd); close(dirfd); }
    }
    return ok;
}
static void remove_invitation(struct hd_guild_state *s, int ix)
{
    memmove(&s->invites[ix], &s->invites[ix + 1],
            (s->invite_count - ix - 1) * sizeof(s->invites[0]));
    s->invite_count--;
}
static void remove_member(struct hd_guild_state *s, int ix)
{
    memmove(&s->members[ix], &s->members[ix + 1],
            (s->member_count - ix - 1) * sizeof(s->members[0]));
    s->member_count--;
}
static struct hd_chat_user *chat_user(const char *name)
{
    int i, empty = -1;
    for (i = 0; i < HD_MAX_CHAT_USERS; i++) {
        if (chat_users[i].name[0] && !strcasecmp(chat_users[i].name, name))
            return &chat_users[i];
        if (!chat_users[i].name[0] && empty < 0) empty = i;
    }
    if (empty < 0) return NULL;
    snprintf(chat_users[empty].name, sizeof(chat_users[empty].name), "%.19s", name);
    return &chat_users[empty];
}
static const char *message_body(cmd *command)
{
    const char *p = command->fullstr;
    while (*p && *p != ' ') p++;
    while (*p == ' ') p++;
    return p;
}
static int message_valid(const char *p)
{
    size_t n = strlen(p);
    if (n < 1 || n > 160) return 0;
    for (; *p; p++)
        if ((unsigned char)*p < 32 || (unsigned char)*p > 126) return 0;
    return 1;
}
static int check_chat(creature *player)
{
    struct hd_chat_user *u;
    time_t now = time(NULL);
    if (F_ISSET(player, PSILNC)) {
        print(player->fd, "You are silenced.\n"); return 0;
    }
    if (!hd_staff_can_chat(player)) return 0;
    if (now <= 0) { print(player->fd, "Chat clock is unavailable.\n"); return 0; }
    u = chat_user(player->name);
    if (!u) { print(player->fd, "Chat is temporarily full.\n"); return 0; }
    if (u->last_chat && now >= u->last_chat && now - u->last_chat < 3) {
        print(player->fd, "Please wait a few seconds before chatting again.\n");
        return 0;
    }
    u->last_chat = now;
    return 1;
}
int hd_global_chat(creature *player, cmd *command)
{
    struct hd_chat_user *u, *recipient_pref;
    const char *message = message_body(command);
    int fd;
    u = chat_user(player->name);
    if (!u) return 0;
    if (!strcasecmp(message, "off")) {
        u->global_off = 1;
        print(player->fd, "Global chat turned off for this game process.\n");
        return 0;
    }
    if (!strcasecmp(message, "on")) {
        u->global_off = 0;
        print(player->fd, "Global chat turned on.\n");
        return 0;
    }
    if (!*message || !strcasecmp(message, "status")) {
        print(player->fd, "chat <message> | chat on | chat off\n");
        print(player->fd, "Global chat is %s. Cyan channel, not broadcast.\n",
              u->global_off ? "off" : "on");
        return 0;
    }
    if (!message_valid(message)) {
        print(player->fd, "Global chat requires 1-160 printable characters.\n");
        return 0;
    }
    if (u->global_off) {
        print(player->fd, "Turn global chat on before sending.\n"); return 0;
    }
    if (F_ISSET(player, PDMINV)) {
        print(player->fd, "Global chat is unavailable while invisible.\n"); return 0;
    }
    if (!check_chat(player)) return 0;
    for (fd = 0; fd < Tablesize; fd++) {
        if (!Ply[fd].ply || Ply[fd].ply->fd != fd) continue;
        if (F_ISSET(Ply[fd].ply, PIGNOR) && Ply[fd].ply != player) continue;
        recipient_pref = chat_user(Ply[fd].ply->name);
        if (recipient_pref && recipient_pref->global_off) continue;
        ANSI(fd, CYAN);
        print(fd, "[Global] %s: %s\n", player->name, message);
        ANSI(fd, NORMAL);
    }
    return 0;
}
static void clan_help(creature *player)
{
    print(player->fd, "CLANS: clan list | info <name> | roster | invites\n");
    print(player->fd, "clan create <name> | invite <player> | accept <name> | decline <name>\n");
    print(player->fd, "clan promote <player> | demote <player> | kick <player>\n");
    print(player->fd, "clan transfer <player> | leave | clanchat <message>\n");
#ifdef HD_GUILD_STAGING_FREE_CREATE
    print(player->fd, "TEST SERVER ONLY: create is deed-free in this staging build.\n");
#else
    print(player->fd, "Founding disabled until physical charter deed validation is installed.\n");
#endif
}
int hd_player_clan(creature *player, cmd *command)
{
    struct hd_guild_state *s;
    struct hd_member *self, *other;
    creature *target;
    char verb[25] = "", action[25] = "", arg[25] = "", extra;
    char guildname[25], targetname[20];
    int tokens, mine, other_ix, gid, ix, j, total;
    int dirty = 0, result = 0;
    s = calloc(1, sizeof(*s));
    if (!s) { print(player->fd, "Guild memory unavailable.\n"); return 0; }
    if (!load_guilds(s)) {
        print(player->fd, "Guild records unavailable or invalid. No change made.\n");
        goto done;
    }
    tokens = sscanf(command->fullstr, "%24s %24s %24s %c",
                    verb, action, arg, &extra);
    mine = member_index(s, player->name);
    self = mine < 0 ? NULL : &s->members[mine];
    if (tokens == 1 || (tokens == 2 && !strcmp(action, "help"))) {
        clan_help(player);
    } else if (tokens == 2 && !strcmp(action, "list")) {
        print(player->fd, "PLAYER GUILDS (%d):\n", s->guild_count);
        for (j = 0; j < s->guild_count; j++)
            print(player->fd, "  %s\n", s->guilds[j].name);
    } else if (tokens == 3 && !strcmp(action, "info")) {
        gid = guild_index(s, arg);
        if (gid < 0) print(player->fd, "No such guild.\n");
        else {
            total = 0;
            for (j = 0; j < s->member_count; j++)
                if (!strcasecmp(s->members[j].guild, s->guilds[gid].name))
                    total++;
            print(player->fd, "Guild: %s | Members: %d\n", s->guilds[gid].name, total);
        }
    } else if (tokens == 2 && !strcmp(action, "roster")) {
        if (!self) print(player->fd, "You are not in a guild.\n");
        else {
            print(player->fd, "GUILD ROSTER: %s\n", self->guild);
            for (j = 0; j < s->member_count; j++)
                if (!strcasecmp(s->members[j].guild, self->guild))
                    print(player->fd, "  %s - %s\n", s->members[j].name,
                         s->members[j].rank == 2 ? "Leader" :
                         s->members[j].rank == 1 ? "Officer" : "Member");
        }
    } else if (tokens == 2 && !strcmp(action, "invites")) {
        print(player->fd, "Pending invitations:\n");
        for (j = 0; j < s->invite_count; j++)
            if (!strcasecmp(s->invites[j].name, player->name))
                print(player->fd, "  %s\n", s->invites[j].guild);
    } else if (tokens == 3 && !strcmp(action, "create")) {
#ifndef HD_GUILD_STAGING_FREE_CREATE
        print(player->fd, "Clan creation requires a physical clan deed; not enabled.\n");
#else
        if (self) print(player->fd, "Leave your existing guild first.\n");
        else if (!identifier(arg, sizeof(guildname)) || s->guild_count == HD_MAX_GUILDS ||
                 s->member_count == HD_MAX_MEMBERS || guild_index(s, arg) >= 0)
            print(player->fd, "Invalid, duplicate or unavailable guild name.\n");
        else {
            normalized(arg, guildname, sizeof(guildname));
            strcpy(s->guilds[s->guild_count++].name, guildname);
            strcpy(s->members[s->member_count].guild, guildname);
            snprintf(s->members[s->member_count].name, 20, "%.19s", player->name);
            s->members[s->member_count++].rank = 2;
            dirty = 1;
        }
#endif
    } else if (tokens == 3 && !strcmp(action, "invite")) {
        target = find_who(arg);
        if (!self || self->rank < 1) print(player->fd, "Officer rank required.\n");
        else if (!target || !identifier(target->name, 20))
            print(player->fd, "Invite an online player by exact name.\n");
        else if (member_index(s, target->name) >= 0)
            print(player->fd, "That player already belongs to a guild.\n");
        else if (s->invite_count == HD_MAX_INVITES ||
                 invitation_index(s, self->guild, target->name) >= 0)
            print(player->fd, "Invitation limit reached or already invited.\n");
        else {
            strcpy(s->invites[s->invite_count].guild, self->guild);
            strcpy(s->invites[s->invite_count++].name, target->name);
            dirty = 1;
        }
    } else if (tokens == 3 && (!strcmp(action, "accept") || !strcmp(action, "decline"))) {
        ix = invitation_index(s, arg, player->name);
        if (ix < 0) print(player->fd, "No such invitation.\n");
        else if (!strcmp(action, "accept") &&
                 (self || s->member_count == HD_MAX_MEMBERS))
            print(player->fd, "Unable to join another guild.\n");
        else {
            if (!strcmp(action, "accept")) {
                strcpy(s->members[s->member_count].guild, s->invites[ix].guild);
                snprintf(s->members[s->member_count].name, 20, "%.19s", player->name);
                s->members[s->member_count++].rank = 0;
            }
            remove_invitation(s, ix);
            for (j = s->invite_count - 1; j >= 0; j--)
                if (!strcasecmp(s->invites[j].name, player->name))
                    remove_invitation(s, j);
            dirty = 1;
        }
    } else if (tokens == 3 && (!strcmp(action, "promote") ||
                               !strcmp(action, "demote") ||
                               !strcmp(action, "transfer") ||
                               !strcmp(action, "kick"))) {
        other_ix = member_index(s, arg);
        other = other_ix < 0 ? NULL : &s->members[other_ix];
        if (!self || !other || strcasecmp(self->guild, other->guild))
            print(player->fd, "That player is not in your guild.\n");
        else if (!strcmp(action, "kick")) {
            if (self->rank < 1 || self->rank <= other->rank)
                print(player->fd, "Insufficient rank to remove this member.\n");
            else { remove_member(s, other_ix); dirty = 1; }
        } else if (self->rank != 2)
            print(player->fd, "Only the guild leader can change ranks.\n");
        else if (mine == other_ix)
            print(player->fd, "You cannot alter your own rank this way.\n");
        else if (!strcmp(action, "promote")) {
            if (other->rank != 0) print(player->fd, "Already an officer.\n");
            else { other->rank = 1; dirty = 1; }
        } else if (!strcmp(action, "demote")) {
            if (other->rank != 1) print(player->fd, "Not an officer.\n");
            else { other->rank = 0; dirty = 1; }
        } else if (!strcmp(action, "transfer")) {
            self->rank = 0; other->rank = 2; dirty = 1;
        }
    } else if (tokens == 2 && !strcmp(action, "leave")) {
        if (!self) print(player->fd, "You are not in a guild.\n");
        else {
            strcpy(guildname, self->guild);
            total = 0;
            for (j = 0; j < s->member_count; j++)
                if (!strcasecmp(s->members[j].guild, guildname)) total++;
            if (self->rank == 2 && total > 1)
                print(player->fd, "Transfer leadership before leaving.\n");
            else {
                remove_member(s, mine);
                if (total == 1) {
                    gid = guild_index(s, guildname);
                    if (gid >= 0) {
                        memmove(&s->guilds[gid], &s->guilds[gid + 1],
                                (s->guild_count - gid - 1) * sizeof(s->guilds[0]));
                        s->guild_count--;
                    }
                    for (j = s->invite_count - 1; j >= 0; j--)
                        if (!strcasecmp(s->invites[j].guild, guildname))
                            remove_invitation(s, j);
                }
                dirty = 1;
            }
        }
    } else {
        clan_help(player);
    }
    if (dirty) {
        result = save_guilds(s);
        print(player->fd, result ? "Guild records updated.\n" :
              "Guild storage failed; change was not committed.\n");
    }
done:
    free(s);
    return 0;
}
int hd_clan_chat(creature *player, cmd *command)
{
    struct hd_guild_state *s;
    const char *message = message_body(command);
    int ix, j, fd, delivered = 0;
    if (!message_valid(message)) {
        print(player->fd, "clanchat <1-160 printable characters>\n"); return 0;
    }
    s = calloc(1, sizeof(*s));
    if (!s) return 0;
    if (!load_guilds(s)) {
        print(player->fd, "Guild records unavailable.\n"); goto done;
    }
    ix = member_index(s, player->name);
    if (ix < 0) { print(player->fd, "You are not in a guild.\n"); goto done; }
    if (F_ISSET(player, PDMINV)) {
        print(player->fd, "Guild chat unavailable while invisible.\n"); goto done;
    }
    if (!check_chat(player)) goto done;
    for (fd = 0; fd < Tablesize; fd++) {
        if (!Ply[fd].ply || Ply[fd].ply->fd != fd) continue;
        j = member_index(s, Ply[fd].ply->name);
        if (j < 0 || strcasecmp(s->members[ix].guild, s->members[j].guild))
            continue;
        if (F_ISSET(Ply[fd].ply, PIGNOR) && Ply[fd].ply != player) continue;
        ANSI(fd, MAGENTA);
        print(fd, "[Guild: %s] %s: %s\n",
              s->members[ix].guild, player->name, message);
        ANSI(fd, NORMAL);
        delivered++;
    }
    if (!delivered) print(player->fd, "No online guild recipient was available.\n");
done:
    free(s);
    return 0;
}
int hd_staff_hub(creature *player, cmd *command)
{
    int role = hd_staff_role(player), level;
    (void)command;
    level = hd_staff_rank(role);
    if (level < 1) {
        print(player->fd, "Staff tools are restricted to assigned staff roles.\n");
        return 0;
    }
    print(player->fd, "HOLLOWDEEP STAFF HUB - %s\n", hd_staff_role_badge(role));
    print(player->fd, "Read: dmcommands | hstaff whoami | hstaff list | staffclan who\n");
    print(player->fd, "Moderation: hmoderate mute | unmute | kick | announce\n");
    if (level >= 2)
        print(player->fd, "Admin: hbuild info | hdm | staff role management (per policy)\n");
    if (level >= 3)
        print(player->fd, "Owner: highest HollowDeep permissions, always audited.\n");
    print(player->fd, "Atlas-inspired navigation only; no new privileges assigned.\n");
    return 0;
}
