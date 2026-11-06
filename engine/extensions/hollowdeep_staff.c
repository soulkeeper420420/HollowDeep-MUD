/* Hollowdeep staff roles and moderation for original Mordor 3.00.
 * Original engine copyright notices remain applicable. Roles grant only the
 * capabilities below and role-scoped builder/DM tools, never native classes.
 * One atomic sidecar stores roles, timed mutes and a bounded metadata audit.
 */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>

extern void print(int fd, const char *format, ...);
extern void broadcast(const char *format, ...);
extern creature *find_who(char *name);
extern void disconnect(int fd);
extern void output_buf(void);

#ifndef HOLLOWDEEP_DATA_DIR
#define HOLLOWDEEP_DATA_DIR "hollowdeep-data"
#endif
#define HD_STAFF_FILE HOLLOWDEEP_DATA_DIR "/staff.db"
#define HD_STAFF_MAX 128
#define HD_AUDIT_MAX 64
#define HD_STAFF_BYTES 32768
#define HD_NAME_BYTES 20 /* Original login accepts 3-19 alphabetic characters. */
#define HD_TIME_MAX 2147483647UL

struct staff_entry { char name[HD_NAME_BYTES]; int role; unsigned long muted_until; };
struct audit_entry {
    unsigned long when;
    char actor[HD_NAME_BYTES], action[12], target[HD_NAME_BYTES], value[16];
};
struct staff_state {
    unsigned int count, audit_count;
    struct staff_entry entries[HD_STAFF_MAX];
    struct audit_entry audit[HD_AUDIT_MAX];
};
static const char *ROLE_NAMES[] = {"player", "mod", "admin", "owner", "implementor"};

/* Keep original on-disk IDs 0-3 unchanged; Implementor is a Moderator peer. */
int hd_staff_rank(int role)
{
    switch (role) {
    case HD_ROLE_PLAYER: return 0;
    case HD_ROLE_MOD: case HD_ROLE_IMPLEMENTOR: return 1;
    case HD_ROLE_ADMIN: return 2;
    case HD_ROLE_OWNER: return 3;
    default: return -1;
    }
}

const char *hd_staff_role_badge(int role)
{
    static const char *badges[] = {"", "[MOD]", "[ADMIN]", "[OWNER]", "[IMPLEMENTOR]"};
    return role >= 0 && role < HD_ROLE_COUNT ? badges[role] : "";
}

const char *hd_staff_badge(creature *player)
{
    return hd_staff_role_badge(hd_staff_role(player));
}

static int canonical_name(const char *input, char *output)
{
    size_t i, length = strnlen(input, HD_NAME_BYTES);
    if (length < 3 || length >= HD_NAME_BYTES) return 0;
    for (i = 0; i < length; i++) {
        unsigned char c = (unsigned char)input[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) return 0;
        output[i] = (char)(i ? tolower(c) : toupper(c));
    }
    output[length] = 0;
    return 1;
}

static int valid_saved_name(const char *input)
{
    char canonical[HD_NAME_BYTES];
    return canonical_name(input, canonical) && !strcmp(input, canonical);
}

static int is_bootstrap(creature *player)
{
    return player && player->class == DM && valid_saved_name(player->name)
           && !strcmp(player->name, DMNAME);
}

static int data_directory(void)
{
    struct stat st;
    if (lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) {
        if (errno != ENOENT || mkdir(HOLLOWDEEP_DATA_DIR, 0700) < 0) return 0;
        if (lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) return 0;
    }
    return S_ISDIR(st.st_mode) && st.st_uid == geteuid()
           && !(st.st_mode & (S_IWGRP | S_IWOTH));
}

static int valid_audit(struct audit_entry *entry)
{
    static const char *actions[] = {"grant", "revoke", "mute", "unmute", "kick", "announce"};
    unsigned int i;
    char *end;
    unsigned long number;
    if (!valid_saved_name(entry->actor) || entry->when > HD_TIME_MAX) return 0;
    if (!strcmp(entry->action, "buildtry") || !strcmp(entry->action, "powertry")
            || !strcmp(entry->action, "rangetry") || !strcmp(entry->action, "eventtry")) {
        if (!valid_saved_name(entry->target) || !entry->value[0]) return 0;
        for (i = 0; entry->value[i]; i++)
            if (!((entry->value[i] >= 'a' && entry->value[i] <= 'z') ||
                  (entry->value[i] >= '0' && entry->value[i] <= '9') || entry->value[i] == ':')) return 0;
        return 1;
    }
    for (i = 0; i < sizeof(actions)/sizeof(actions[0]); i++)
        if (!strcmp(entry->action, actions[i])) break;
    if (i == sizeof(actions)/sizeof(actions[0])) return 0;
    if (!strcmp(entry->action, "announce"))
        return !strcmp(entry->target, "-") && !strcmp(entry->value, "-");
    if (!valid_saved_name(entry->target)) return 0;
    if (!strcmp(entry->action, "grant")) {
        for (i = 0; i < HD_ROLE_COUNT; i++) if (!strcmp(entry->value, ROLE_NAMES[i])) return 1;
        return 0;
    }
    if (!strcmp(entry->action, "mute")) {
        errno = 0;
        number = strtoul(entry->value, &end, 10);
        return !errno && *entry->value && !*end && number >= 1 && number <= 1440;
    }
    return !strcmp(entry->value, "-");
}

static int load_staff(struct staff_state *state)
{
    FILE *file;
    int fd, version;
    char magic[24], extra;
    struct stat st;
    unsigned int i, j;
    memset(state, 0, sizeof(*state));
    if (!data_directory()) return 0;
    fd = open(HD_STAFF_FILE, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return errno == ENOENT;
    if (fstat(fd, &st) < 0 || !S_ISREG(st.st_mode) || st.st_uid != geteuid()
            || st.st_size > HD_STAFF_BYTES || (st.st_mode & (S_IWGRP | S_IWOTH))) {
        close(fd); return 0;
    }
    file = fdopen(fd, "r");
    if (!file) { close(fd); return 0; }
    if (fscanf(file, "%23s %d %u %u", magic, &version, &state->count, &state->audit_count) != 4
            || strcmp(magic, "HOLLOWDEEP_STAFF") || version != 1
            || state->count > HD_STAFF_MAX || state->audit_count > HD_AUDIT_MAX) goto bad;
    for (i = 0; i < state->count; i++) {
        struct staff_entry *entry = &state->entries[i];
        if (fscanf(file, "%19s %d %lu", entry->name, &entry->role, &entry->muted_until) != 3
                || !valid_saved_name(entry->name) || !strcmp(entry->name, DMNAME)
                || hd_staff_rank(entry->role) < 0 || entry->muted_until > HD_TIME_MAX
                || (!entry->role && !entry->muted_until)) goto bad;
        for (j = 0; j < i; j++) if (!strcmp(entry->name, state->entries[j].name)) goto bad;
    }
    for (i = 0; i < state->audit_count; i++) {
        struct audit_entry *entry = &state->audit[i];
        if (fscanf(file, "%lu %19s %11s %19s %15s", &entry->when, entry->actor,
                   entry->action, entry->target, entry->value) != 5 || !valid_audit(entry)) goto bad;
    }
    if (fscanf(file, " %c", &extra) != EOF || ferror(file)) goto bad;
    return fclose(file) == 0;
bad:
    fclose(file); return 0;
}

static int save_staff(const struct staff_state *state)
{
    char temporary[] = HOLLOWDEEP_DATA_DIR "/.staff-XXXXXX";
    FILE *file;
    int fd, ok;
    unsigned int i;
    if (!data_directory()) return 0;
    fd = mkstemp(temporary);
    if (fd < 0) return 0;
    file = fdopen(fd, "w");
    if (!file) { close(fd); unlink(temporary); return 0; }
    ok = fprintf(file, "HOLLOWDEEP_STAFF 1 %u %u\n", state->count, state->audit_count) >= 0;
    for (i = 0; ok && i < state->count; i++) {
        const struct staff_entry *entry = &state->entries[i];
        ok = fprintf(file, "%s %d %lu\n", entry->name, entry->role, entry->muted_until) >= 0;
    }
    for (i = 0; ok && i < state->audit_count; i++) {
        const struct audit_entry *entry = &state->audit[i];
        ok = fprintf(file, "%lu %s %s %s %s\n", entry->when, entry->actor,
                     entry->action, entry->target, entry->value) >= 0;
    }
    if (fflush(file) != 0 || fsync(fd) != 0) ok = 0;
    if (fclose(file) != 0) ok = 0;
    if (!ok || rename(temporary, HD_STAFF_FILE) != 0) { unlink(temporary); return 0; }
    return 1;
}

static void storage_error(creature *player)
{
    print(player->fd, "Staff data is unavailable. No staff change was made; ask the host to inspect hollowdeep-data/staff.db.\n");
}

static int entry_index(const struct staff_state *state, const char *name)
{
    unsigned int i;
    for (i = 0; i < state->count; i++) if (!strcmp(state->entries[i].name, name)) return (int)i;
    return -1;
}

static int named_role(const struct staff_state *state, const char *name)
{
    int index;
    if (!strcmp(name, DMNAME)) return HD_ROLE_OWNER;
    index = entry_index(state, name);
    return index < 0 ? HD_ROLE_PLAYER : state->entries[index].role;
}

static int actor_role(const struct staff_state *state, creature *player)
{
    if (!player || player->type != PLAYER || !valid_saved_name(player->name) || player->fd < 0) return -1;
    if (!strcmp(player->name, DMNAME)) return is_bootstrap(player) ? HD_ROLE_OWNER : -1;
    return named_role(state, player->name);
}

int hd_staff_role(creature *player)
{
    struct staff_state state;
    if (!load_staff(&state)) return -1;
    return actor_role(&state, player);
}

/* Staff clan membership is derived from the validated role database. It has
 * no separate membership cache, invite path, dues or permission escalation. */
int staffclan(creature *player, cmd *command)
{
    struct staff_state state;
    creature *recipient;
    char verb[25], action[25], extra;
    const char *message, *cursor;
    int role, words, delivered = 0;
    unsigned int i;
    if (!load_staff(&state) || (role = actor_role(&state, player)) < 0) {
        storage_error(player); return 0;
    }
    if (hd_staff_rank(role) < hd_staff_rank(HD_ROLE_MOD)) {
        print(player->fd, "HollowDeep Staff is a staff-only clan. An assigned staff role is required.\n"); return 0;
    }
    if (strnlen(command->fullstr, sizeof(command->fullstr)) == sizeof(command->fullstr)) return 0;
    words = sscanf(command->fullstr, "%24s %24s %c", verb, action, &extra);
    if (words == 1 || (words == 2 && !strcmp(action, "status"))) {
        print(player->fd, "HOLLOWDEEP STAFF CLAN\nYour role: %s %s.\n", hd_staff_role_badge(role), ROLE_NAMES[role]);
        print(player->fd, "Membership follows your current staff role. No invitations or fees.\nstaffclan who | staffclan say <message>\n");
        return 0;
    }
    if (words == 2 && (!strcmp(action, "who") || !strcmp(action, "list"))) {
        print(player->fd, "HOLLOWDEEP STAFF ROSTER\n[OWNER] %s (configured founder)\n", DMNAME);
        for (i = 0; i < state.count; i++) if (hd_staff_rank(state.entries[i].role) >= hd_staff_rank(HD_ROLE_MOD))
            print(player->fd, "%s %s\n", hd_staff_role_badge(state.entries[i].role), state.entries[i].name);
        print(player->fd, "This roster includes offline members. Private chat reaches online staff only.\n");
        return 0;
    }
    if (words >= 2 && !strcmp(action, "say")) {
        cursor = command->fullstr;
        for (i = 0; i < 2; i++) {
            while (*cursor == ' ') cursor++;
            while (*cursor && *cursor != ' ') cursor++;
        }
        while (*cursor == ' ') cursor++;
        message = cursor;
        if (!*message || strlen(message) > 160) goto usage;
        for (; *cursor; cursor++) if ((unsigned char)*cursor < 32 || (unsigned char)*cursor > 126) goto usage;
        if (!hd_staff_can_chat(player)) return 0;
        /* The configured founder is not stored as a mutable staff entry. */
        for (i = 0; i <= state.count; i++) {
            recipient = find_who(i == state.count ? DMNAME : state.entries[i].name);
            if (!recipient || recipient->fd < 0 || hd_staff_rank(actor_role(&state, recipient)) < hd_staff_rank(HD_ROLE_MOD)) continue;
            print(recipient->fd, "[HollowDeep Staff] %s %s: %s\n", hd_staff_role_badge(role), player->name, message);
            delivered++;
        }
        if (!delivered) print(player->fd, "No online staff recipients were available.\n");
        return 0;
    }
usage:
    print(player->fd, "staffclan [status] | who | say <1-160 printable ASCII characters>\n");
    return 0;
}

static unsigned long now_seconds(void)
{
#ifdef HOLLOWDEEP_STAFF_TEST_TIME
    extern long hd_staff_test_now(void);
    time_t now = hd_staff_test_now();
#else
    time_t now = time(NULL);
#endif
    return now < 0 || (unsigned long)now > HD_TIME_MAX ? 0 : (unsigned long)now;
}

static void prune_expired(struct staff_state *state, unsigned long now)
{
    unsigned int i = 0;
    while (i < state->count) {
        struct staff_entry *entry = &state->entries[i];
        if (entry->muted_until <= now) entry->muted_until = 0;
        if (!entry->role && !entry->muted_until) {
            memmove(entry, entry + 1, (state->count - i - 1) * sizeof(*entry));
            state->count--;
        } else i++;
    }
}

static struct staff_entry *editable_entry(struct staff_state *state, const char *name)
{
    int index = entry_index(state, name);
    struct staff_entry *entry;
    if (index >= 0) return &state->entries[index];
    if (state->count == HD_STAFF_MAX) return NULL;
    entry = &state->entries[state->count++];
    memset(entry, 0, sizeof(*entry));
    strcpy(entry->name, name);
    return entry;
}

static int account_exists(const char *name)
{
    char path[512];
    struct stat st;
    int fd, ok;
    if (!valid_saved_name(name) || snprintf(path, sizeof(path), "%s/%s", PLAYERPATH, name) >= (int)sizeof(path)) return 0;
    if (lstat(PLAYERPATH, &st) < 0 || !S_ISDIR(st.st_mode)) return 0;
    fd = open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return 0;
    ok = fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_size > 0;
    close(fd);
    return ok;
}

static int audit_action(struct staff_state *state, creature *actor, const char *action,
                        const char *target, const char *value, unsigned long now)
{
    struct audit_entry *entry;
    if (!now || !valid_saved_name(actor->name)) return 0;
    if (state->audit_count == HD_AUDIT_MAX) {
        memmove(state->audit, state->audit + 1, (HD_AUDIT_MAX - 1) * sizeof(*state->audit));
        state->audit_count--;
    }
    entry = &state->audit[state->audit_count++];
    memset(entry, 0, sizeof(*entry));
    entry->when = now;
    snprintf(entry->actor, sizeof(entry->actor), "%.19s", actor->name);
    snprintf(entry->action, sizeof(entry->action), "%s", action);
    snprintf(entry->target, sizeof(entry->target), "%s", target);
    snprintf(entry->value, sizeof(entry->value), "%s", value);
    return valid_audit(entry) && save_staff(state);
}

int hd_staff_saved_name(const char *input, char *canonical)
{
    return canonical_name(input, canonical) && account_exists(canonical);
}

int hd_staff_open_data(const char *name)
{
    char path[256];
    struct stat st;
    int fd;
    if ((strcmp(name, "builders.db") && strcmp(name, "bonus.db")) || !data_directory()) return -2;
    snprintf(path, sizeof(path), "%s/%s", HOLLOWDEEP_DATA_DIR, name);
    fd = open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return errno == ENOENT ? -1 : -2;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_uid != geteuid()
            || st.st_size > HD_STAFF_BYTES || (st.st_mode & (S_IWGRP | S_IWOTH))) {
        close(fd); return -2;
    }
    return fd;
}

int hd_staff_write_data(const char *name, const char *data, unsigned long size)
{
    char path[256], temporary[] = HOLLOWDEEP_DATA_DIR "/.powers-XXXXXX";
    int existing = hd_staff_open_data(name), fd, ok;
    unsigned long written = 0;
    ssize_t count;
    if (existing == -2 || size > HD_STAFF_BYTES) return 0;
    if (existing >= 0) close(existing);
    snprintf(path, sizeof(path), "%s/%s", HOLLOWDEEP_DATA_DIR, name);
    fd = mkstemp(temporary);
    if (fd < 0) return 0;
    while (written < size) {
        count = write(fd, data + written, size - written);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) break;
        written += (unsigned long)count;
    }
    ok = written == size && fsync(fd) == 0;
    if (close(fd)) ok = 0;
    if (ok) ok = rename(temporary, path) == 0;
    unlink(temporary);
    return ok;
}

int hd_staff_authorize_action(creature *player, int required, const char *action,
                              const char *target, const char *value)
{
    struct staff_state state;
    if (hd_staff_rank(required) < 0
            || (strcmp(action, "buildtry") && strcmp(action, "powertry") && strcmp(action, "rangetry") && strcmp(action, "eventtry"))
            || strlen(target) >= HD_NAME_BYTES || strlen(value) >= 16
            || !load_staff(&state) || hd_staff_rank(actor_role(&state, player)) < hd_staff_rank(required)
            || !audit_action(&state, player, action, target, value, now_seconds())) {
        print(player->fd, "The required role and audit storage could not be verified; no world or DM change was made.\n");
        return 0;
    }
    return 1;
}

int hd_staff_can_chat(creature *player)
{
    struct staff_state state;
    int index;
    unsigned long now = now_seconds();
    if (!now || !load_staff(&state) || actor_role(&state, player) < 0) {
        print(player->fd, "Chat is unavailable while staff data is checked. Movement, help and saving remain available.\n");
        return 0;
    }
    index = entry_index(&state, player->name);
    if (index >= 0 && state.entries[index].muted_until > now) {
        unsigned long minutes = (state.entries[index].muted_until - now + 59) / 60;
        print(player->fd, "You are muted for up to %lu more minute(s).\n", minutes);
        return 0;
    }
    return 1;
}

int hd_staff_blocks_command(creature *player, int command_number)
{
    switch (command_number) {
    case 4: case 17: case 25: case 29: case 53: case 57: case 59:
        return !hd_staff_can_chat(player);
    default: return 0;
    }
}

/* Mordor's parser treats a numeric argument as a selector on the preceding
 * word. Staff syntax instead needs literal duration tokens and exact arity. */
static int staff_words(const cmd *original, cmd *parsed)
{
    const char *cursor = original->fullstr, *start;
    size_t length, i;
    if (strnlen(cursor, sizeof(original->fullstr)) == sizeof(original->fullstr)) return 0;
    memset(parsed, 0, sizeof(*parsed));
    strcpy(parsed->fullstr, original->fullstr);
    while (*cursor) {
        while (*cursor == ' ') cursor++;
        if (!*cursor) break;
        if (parsed->num == COMMANDMAX) return 0;
        start = cursor;
        while (*cursor && *cursor != ' ') cursor++;
        length = (size_t)(cursor - start);
        if (!length || length >= sizeof(parsed->str[0])) return 0;
        for (i = 0; i < length; i++) parsed->str[parsed->num][i] = (char)tolower((unsigned char)start[i]);
        parsed->num++;
    }
    return 1;
}

int hstaff(creature *player, cmd *command)
{
    struct staff_state state;
    struct staff_entry *entry;
    cmd literal;
    const char *action;
    int role, target_role, desired = -1, index;
    unsigned int i;
    unsigned long now = now_seconds();
    char target[HD_NAME_BYTES];
    if (!staff_words(command, &literal)) { print(player->fd, "Use help hstaff for staff command syntax.\n"); return 0; }
    command = &literal;
    action = command->num > 1 ? command->str[1] : "whoami";
    if (!now || !load_staff(&state) || (role = actor_role(&state, player)) < 0) { storage_error(player); return 0; }
    if (!strcmp(action, "whoami") && command->num <= 2) {
        print(player->fd, "Hollowdeep role: %s. Role powers: help hbuild and help hdm. Character class is unchanged.\n", ROLE_NAMES[role]);
        return 0;
    }
    if (!strcmp(action, "list") && command->num == 2) {
        if (hd_staff_rank(role) < hd_staff_rank(HD_ROLE_MOD)) { print(player->fd, "Staff permission required.\n"); return 0; }
        print(player->fd, "STAFF ROSTER\n%s: owner [OWNER] (configured founder)\n", DMNAME);
        for (i = 0; i < state.count; i++) if (state.entries[i].role)
            print(player->fd, "%s: %s %s\n", state.entries[i].name, ROLE_NAMES[state.entries[i].role], hd_staff_role_badge(state.entries[i].role));
        return 0;
    }
    if (!strcmp(action, "audit") && command->num == 2) {
        if (hd_staff_rank(role) < hd_staff_rank(HD_ROLE_ADMIN)) { print(player->fd, "Admin permission required.\n"); return 0; }
        print(player->fd, "RECENT STAFF ACTIONS (UTC epoch seconds)\n");
        for (i = state.audit_count > 10 ? state.audit_count - 10 : 0; i < state.audit_count; i++) {
            struct audit_entry *row = &state.audit[i];
            print(player->fd, "%lu %s %s %s %s\n", row->when, row->actor, row->action, row->target, row->value);
        }
        if (!state.audit_count) print(player->fd, "No recorded staff actions.\n");
        return 0;
    }
    if ((!strcmp(action, "grant") && command->num == 4) || (!strcmp(action, "revoke") && command->num == 3)) {
        if (hd_staff_rank(role) < hd_staff_rank(HD_ROLE_ADMIN)) { print(player->fd, "Admin or owner permission required.\n"); return 0; }
        if (!canonical_name(command->str[2], target) || !account_exists(target)) {
            print(player->fd, "Choose an existing saved character (3-19 letters). Have that player save first.\n"); return 0;
        }
        if (!strcmp(target, DMNAME)) { print(player->fd, "The configured founder's owner role is protected.\n"); return 0; }
        if (!strcmp(action, "revoke")) desired = HD_ROLE_PLAYER;
        else for (i = 0; i < HD_ROLE_COUNT; i++) if (!strcmp(command->str[3], ROLE_NAMES[i])) desired = (int)i;
        if (desired < 0) { print(player->fd, "Roles: player, mod, implementor, admin, owner.\n"); return 0; }
        target_role = named_role(&state, target);
        if (hd_staff_rank(role) < hd_staff_rank(HD_ROLE_OWNER) && (hd_staff_rank(target_role) >= hd_staff_rank(role) || hd_staff_rank(desired) >= hd_staff_rank(role))) {
            print(player->fd, "Only an owner can assign or change admins and owners.\n"); return 0;
        }
        if (!strcmp(target, player->name)) { print(player->fd, "Ask another owner to change your own role.\n"); return 0; }
        if (target_role == desired) { print(player->fd, "%s already has the %s role.\n", target, ROLE_NAMES[desired]); return 0; }
        prune_expired(&state, now);
        index = entry_index(&state, target);
        if (desired == HD_ROLE_PLAYER && index >= 0) {
            memmove(&state.entries[index], &state.entries[index + 1], (state.count - index - 1) * sizeof(*entry));
            state.count--;
        } else if (desired > HD_ROLE_PLAYER) {
            entry = editable_entry(&state, target);
            if (!entry) { print(player->fd, "Staff roster is full. Revoke an unused role first.\n"); return 0; }
            entry->role = desired;
            /* A promotion/demotion clears an old mute; the new hierarchy applies. */
            entry->muted_until = 0;
        }
        if (!audit_action(&state, player, action, target,
                          !strcmp(action, "grant") ? ROLE_NAMES[desired] : "-", now)) { storage_error(player); return 0; }
        print(player->fd, "%s now has the %s role. Native class and abilities are unchanged.\n", target, ROLE_NAMES[desired]);
        return 0;
    }
    print(player->fd, "hstaff whoami | list | audit\nhstaff grant <name> <player|mod|implementor|admin|owner>\nhstaff revoke <name>\n");
    return 0;
}

static const char *announcement_text(const cmd *command)
{
    const char *text = command->fullstr;
    size_t length;
    int words;
    if (strnlen(text, sizeof(command->fullstr)) == sizeof(command->fullstr)) return NULL;
    for (words = 0; words < 2; words++) {
        while (*text == ' ') text++;
        if (!*text) return NULL;
        while (*text && *text != ' ') text++;
    }
    while (*text == ' ') text++;
    length = strlen(text);
    if (!length || length > 180) return NULL;
    for (length = 0; text[length]; length++)
        if ((unsigned char)text[length] < 32 || (unsigned char)text[length] > 126) return NULL;
    return text;
}

int hmoderate(creature *player, cmd *command)
{
    struct staff_state state;
    struct staff_entry *entry;
    creature *online;
    cmd literal;
    const char *action = command->num > 1 ? command->str[1] : "help";
    const char *message;
    int role, index, target_role;
    unsigned long now = now_seconds(), minutes = 10;
    char target[HD_NAME_BYTES], number[16], *end;
    if (strcmp(action, "announce")) {
        if (!staff_words(command, &literal)) { print(player->fd, "Use help hmoderate for moderation syntax.\n"); return 0; }
        command = &literal;
        action = command->num > 1 ? command->str[1] : "help";
    }
    if (!now || !load_staff(&state) || (role = actor_role(&state, player)) < 0) { storage_error(player); return 0; }
    if (hd_staff_rank(role) < hd_staff_rank(HD_ROLE_MOD)) { print(player->fd, "Moderator permission required.\n"); return 0; }
    if (!strcmp(action, "announce")) {
        message = announcement_text(command);
        if (!message) { print(player->fd, "Use hmoderate announce <1-180 printable ASCII characters>.\n"); return 0; }
        if (!hd_staff_can_chat(player)) return 0;
        if (!audit_action(&state, player, "announce", "-", "-", now)) { storage_error(player); return 0; }
        broadcast("### %s %s: %s", hd_staff_role_badge(role), player->name, message);
        return 0;
    }
    if ((!strcmp(action, "mute") && (command->num == 3 || command->num == 4))
            || ((!strcmp(action, "unmute") || !strcmp(action, "kick")) && command->num == 3)) {
        if (!canonical_name(command->str[2], target) || !account_exists(target)) {
            print(player->fd, "Choose an existing saved character (3-19 letters).\n"); return 0;
        }
        target_role = named_role(&state, target);
        if (!strcmp(target, player->name) || hd_staff_rank(target_role) >= hd_staff_rank(role)) {
            print(player->fd, "You can moderate only characters below your own staff role.\n"); return 0;
        }
        online = find_who(target);
        if ((!strcmp(action, "mute") || !strcmp(action, "kick")) && !online) {
            print(player->fd, "That character must be online for this action.\n"); return 0;
        }
        if (online && online->class >= CARETAKER && hd_staff_rank(role) < hd_staff_rank(HD_ROLE_OWNER)) {
            print(player->fd, "Only an owner may moderate a native caretaker.\n"); return 0;
        }
        if (!strcmp(action, "kick")) {
            if (!audit_action(&state, player, "kick", target, "-", now)) { storage_error(player); return 0; }
            print(online->fd, "A staff member has disconnected this session.\n");
            output_buf();
            disconnect(online->fd);
            print(player->fd, "%s disconnected through the engine's normal save/logout routine.\n", target);
            return 0;
        }
        if (!strcmp(action, "mute") && command->num == 4) {
            errno = 0;
            minutes = strtoul(command->str[3], &end, 10);
            if (errno || !*command->str[3] || *end || minutes < 1 || minutes > 1440) {
                print(player->fd, "Mute duration must be 1-1440 minutes. Default: 10.\n"); return 0;
            }
        }
        prune_expired(&state, now);
        index = entry_index(&state, target);
        if (!strcmp(action, "unmute")) {
            if (index < 0 || !state.entries[index].muted_until) { print(player->fd, "That character is not muted.\n"); return 0; }
            state.entries[index].muted_until = 0;
            prune_expired(&state, now);
            if (!audit_action(&state, player, "unmute", target, "-", now)) { storage_error(player); return 0; }
            print(player->fd, "%s may chat again.\n", target);
            return 0;
        }
        if (minutes * 60 > HD_TIME_MAX - now) { print(player->fd, "Mute expiry cannot be represented on this host.\n"); return 0; }
        entry = editable_entry(&state, target);
        if (!entry) { print(player->fd, "Staff records are full; clear expired or unused records first.\n"); return 0; }
        entry->muted_until = now + minutes * 60;
        snprintf(number, sizeof(number), "%lu", minutes);
        if (!audit_action(&state, player, "mute", target, number, now)) { storage_error(player); return 0; }
        print(player->fd, "%s muted for %lu minute(s). Movement, saving and combat remain available.\n", target, minutes);
        print(online->fd, "A staff member muted your chat for %lu minute(s).\n", minutes);
        return 0;
    }
    print(player->fd, "hmoderate announce <message>\nhmoderate mute <name> [minutes]\nhmoderate unmute <name> | kick <name>\n");
    return 0;
}
