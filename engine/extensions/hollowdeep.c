/*
 * Hollowdeep additions for the original Mordor 3.00 engine.
 * Original engine by Brett Vickers and Brooke Paul; see its copyright notices.
 * Original notices and distribution terms remain with the source package.
 *
 * These commands add a persistent exploration journal and class guidance.
 * Achievement rewards are cosmetic badges, not gold or experience. This
 * avoids changing legacy player structs or creating a second currency ledger.
 * Edit QUESTS below to extend the realm. Keep existing IDs and bit positions
 * stable once characters have earned them. Maximum 16 quests, 128 rooms.
 */
#include "mstruct.h"
#include "hollowdeep.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

extern void print(int fd, const char *format, ...);
extern long needed_exp[MAXALVL];
/* Match Mordor's spell registry in global.c; spell IDs need not be indexes. */
extern struct {
    char *splstr;
    int splno;
    int (*splfn)();
} spllist[];

#ifndef HOLLOWDEEP_DATA_DIR
#define HOLLOWDEEP_DATA_DIR "hollowdeep-data"
#endif
#define HD_MAX_ROOMS 128
#define HD_PATH_BYTES 512
#define HD_QUEST_COUNT 4
#define HD_ALL_QUESTS ((1U << HD_QUEST_COUNT) - 1)

struct hd_quest {
    const char *id;
    const char *title;
    unsigned int rooms;
    unsigned int level;
    const char *badge;
};

static const struct hd_quest QUESTS[HD_QUEST_COUNT] = {
    {"first-steps", "Beyond the threshold", 3, 1, "Wayfarer"},
    {"mapmaker", "Ten roads remembered", 10, 1, "Pathfinder"},
    {"apprentice", "An adventurer's calling", 3, 3, "Adept"},
    {"veteran", "A name in the chronicles", 10, 5, "Veteran"}
};

struct hd_state {
    unsigned int accepted;
    unsigned int claimed;
    unsigned int room_count;
    unsigned int rooms[HD_MAX_ROOMS];
};

static const char *CLASSES[] = {
    "None", "Assassin", "Barbarian", "Cleric", "Fighter", "Mage",
    "Paladin", "Ranger", "Thief", "Bard", "Monk"
};
static const char *CLASS_GUIDES[] = {
    "Choose a playable class when creating your character.",
    "Work from hiding and choose your opening carefully. Read help backstab and help hide.",
    "A durable melee adventurer. Read help bash and help wield before your next fight.",
    "Faith and healing magic support your journey. Read help cast, help study, and help turn.",
    "A weapon-focused melee adventurer. Read help circle, help bash, and help equipment.",
    "Study magic and manage your mana. Read help cast and help study; choose spells you know.",
    "Combine martial skill and faith. Read help cast, help pray, and help turn.",
    "Read the trail and move with care. Read help track, help sneak, and help search.",
    "Use stealth and a careful opening. Read help hide, help backstab, and help sneak.",
    "An agile adventurer with the original bard charm ability. Read help charm and help cast.",
    "Follow the original martial path. Read help meditate and help touch for your class abilities."
};

/* Character names are an engine field, but still validate before using a path. */
static int state_path(creature *player, char *path, size_t size)
{
    size_t i, length = 0;
    char name[81];
    while (length < sizeof(player->name) && player->name[length]) length++;
    if (length < 2 || length >= sizeof(player->name)) return 0;
    for (i = 0; i < length; i++) {
        unsigned char c = (unsigned char)player->name[i];
        if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'))) return 0;
        name[i] = (char)tolower(c);
    }
    name[length] = '\0';
    return snprintf(path, size, "%s/%s.journal", HOLLOWDEEP_DATA_DIR, name) < (int)size;
}

static int ensure_directory(void)
{
    struct stat st;
    if (lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) {
        if (errno != ENOENT || mkdir(HOLLOWDEEP_DATA_DIR, 0700) < 0) return 0;
        if (lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) return 0;
    }
    return S_ISDIR(st.st_mode) && !S_ISLNK(st.st_mode);
}

/* Return 1 on a valid/new journal; corrupt files are never silently overwritten. */
static int load_state(creature *player, struct hd_state *state)
{
    char path[HD_PATH_BYTES], magic[16], extra;
    unsigned int version, i, j, room_number;
    struct stat st;
    FILE *file;
    int fd;
    memset(state, 0, sizeof(*state));
    if (!state_path(player, path, sizeof(path)) || !ensure_directory()) return 0;
    fd = open(path, O_RDONLY | O_NOFOLLOW);
    if (fd < 0) return errno == ENOENT;
    if (fstat(fd, &st) < 0 || !S_ISREG(st.st_mode) || st.st_size > 4096) { close(fd); return 0; }
    file = fdopen(fd, "r");
    if (!file) { close(fd); return 0; }
    if (fscanf(file, "%15s %u %u %u %u", magic, &version, &state->accepted,
               &state->claimed, &state->room_count) != 5 || strcmp(magic, "HOLLOWDEEP") || version != 1 ||
        state->room_count > HD_MAX_ROOMS || (state->accepted & ~HD_ALL_QUESTS) ||
        (state->claimed & ~HD_ALL_QUESTS) || (state->claimed & ~state->accepted)) { fclose(file); return 0; }
    for (i = 0; i < state->room_count; i++) {
        if (fscanf(file, "%u", &room_number) != 1 || room_number < 1 || room_number > 32767) { fclose(file); return 0; }
        for (j = 0; j < i; j++) if (state->rooms[j] == room_number) { fclose(file); return 0; }
        state->rooms[i] = room_number;
    }
    if (fscanf(file, " %c", &extra) != EOF || ferror(file)) { fclose(file); return 0; }
    return fclose(file) == 0;
}

/* mkstemp + fsync + rename publishes the complete journal in one operation. */
static int save_state(creature *player, const struct hd_state *state)
{
    char path[HD_PATH_BYTES], temporary[HD_PATH_BYTES];
    FILE *file;
    unsigned int i;
    int fd, ok;
    if (!state_path(player, path, sizeof(path)) || !ensure_directory() ||
        snprintf(temporary, sizeof(temporary), "%s/.journal-XXXXXX", HOLLOWDEEP_DATA_DIR) >= (int)sizeof(temporary)) return 0;
    fd = mkstemp(temporary);
    if (fd < 0) return 0;
    file = fdopen(fd, "w");
    if (!file) { close(fd); unlink(temporary); return 0; }
    ok = fprintf(file, "HOLLOWDEEP 1 %u %u %u\n", state->accepted, state->claimed, state->room_count) >= 0;
    for (i = 0; ok && i < state->room_count; i++) ok = fprintf(file, "%u\n", state->rooms[i]) >= 0;
    if (fflush(file) != 0 || fsync(fd) != 0) ok = 0;
    if (fclose(file) != 0) ok = 0;
    if (!ok || rename(temporary, path) != 0) { unlink(temporary); return 0; }
    return 1;
}

static void storage_error(creature *player)
{
    print(player->fd, "Your chronicle could not be read or saved. Ask the game host to check hollowdeep-data. No achievement was granted.\n");
}

static int quest_index(const char *id)
{
    int i;
    for (i = 0; i < HD_QUEST_COUNT; i++) if (!strcmp(id, QUESTS[i].id)) return i;
    return -1;
}

static int spell_name_order(const void *left, const void *right)
{
    return strcmp(*(const char *const *)left, *(const char *const *)right);
}

int spells(creature *player, cmd *command)
{
    const char *known[sizeof(player->spells) * 8];
    size_t count = 0, i;
    int id;
    if (command->num > 1) {
        print(player->fd, "Usage: spells (or spell). To cast, use cast <spell> [target].\n");
        return 0;
    }
    for (i = 0; spllist[i].splno != -1; i++) {
        id = spllist[i].splno;
        if (id < 0 || (size_t)id >= sizeof(player->spells) * 8) continue;
        if (S_ISSET(player, id) && count < sizeof(known) / sizeof(known[0]))
            known[count++] = spllist[i].splstr;
    }
    qsort(known, count, sizeof(known[0]), spell_name_order);
    print(player->fd, "YOUR KNOWN SPELLS\n");
    print(player->fd, "Spells known: %u | Mana: %d/%d\n", (unsigned int)count,
          player->mpcur, player->mpmax);
    if (!count) {
        print(player->fd, "You have not learned any spells. See help study for learning from scrolls.\n");
        return 0;
    }
    for (i = 0; i < count; i++) print(player->fd, "  %s\n", known[i]);
    print(player->fd, "Cast: cast <spell> [target] | Details: help <spell>\n");
    print(player->fd, "Known spells still require the mana, class, level and conditions needed to cast.\n");
    return 0;
}

int hcommands(creature *player, cmd *command)
{
    const char *topic = command->num > 1 ? command->str[1] : "all";
    if (!strcmp(topic, "mobile")) {
        print(player->fd, "HOLLOWDEEP MOBILE COMMANDS\n");
        print(player->fd, "Look: l | Inventory: i | Score: sc\n");
        print(player->fd, "Move: n s e w ne nw se sw u d\n");
        print(player->fd, "Attack: k <creature> | Cast: c <spell> [target]\n");
        print(player->fd, "Help: ? <command> | Save: save | Leave: quit\n");
        print(player->fd, "If quit asks you to wait, wait and enter quit again.\n");
        print(player->fd, "Compact status: hprofile status\n");
        print(player->fd, "Known spells: spells (or spell)\n");
        print(player->fd, "Training: hclass progress | Next goal: hquest next\n");
        return 0;
    }
    if (!strcmp(topic, "social")) {
        print(player->fd, "HOLLOWDEEP SOCIAL COMMANDS\n");
        print(player->fd, "who - see online adventurers\n");
        print(player->fd, "say <message> - speak in your room\n");
        print(player->fd, "tell <name> <message> - send a private message\n");
        print(player->fd, "follow <name> - follow someone in the same room\n");
        print(player->fd, "group - list the people following you\n");
        print(player->fd, "gtalk <message> - speak to your leader and group\n");
        print(player->fd, "lose - stop following your leader\n");
        print(player->fd, "lose <name> - remove one of your followers\n");
        print(player->fd, "emote <action> - describe an action in your room\n");
        return 0;
    }
    if (strcmp(topic, "all")) {
        print(player->fd, "Usage: hcommands [all|mobile|social]\n");
        return 0;
    }
    print(player->fd, "HOLLOWDEEP COMMANDS\n");
    print(player->fd, "Explore: look, search, north/south/east/west, up/down, prepare\n");
    print(player->fd, "Fight: kill <creature>, cast <spell> [target], flee\n");
    print(player->fd, "Warning: original Mordor's flee can drop your wielded weapon.\n");
    print(player->fd, "Character: score, equipment, inventory, train, study <scroll>\n");
    print(player->fd, "Known magic: spells (or spell); help <spell> for its rules\n");
    print(player->fd, "Staff world tools: hbuild | Role-based DM powers: hdm\n");
    print(player->fd, "Timed monster XP/gold events: hbonus\n");
    print(player->fd, "Together: who, say <message>, tell <name> <message>, follow <name>, group, gtalk <message>\n");
    print(player->fd, "Chronicles: hquest, hquest accept <id>, hquest survey, hquest claim <id>, hprofile\n");
    print(player->fd, "Class guide: hclass [class-name]. Original rules: help <command>.\n");
    print(player->fd, "Quick views: hprofile status, hclass progress, hquest next\n");
    print(player->fd, "Find commands: help commands | help search <text> | skills [all] | dmcommands\n");
    print(player->fd, "Staff channel: staffclan who | staffclan say <message>\n");
    print(player->fd, "Focused guides: hcommands mobile | hcommands social\n");
    return 0;
}

static int training_room_matches(creature *player)
{
    unsigned int i, class_number = (unsigned char)player->class;
    if (!player->parent_rom) return 0;
    /* Match original train(): class bit 0 maps to RTRAIN+3. */
    for (i = 0; i < 4; i++) {
        int class_bit = (class_number & (1U << i)) != 0;
        int room_bit = F_ISSET(player->parent_rom, RTRAIN + 3 - i) != 0;
        if (class_bit != room_bit) return 0;
    }
    return 1;
}

static int training_progress(creature *player)
{
    unsigned int level = (unsigned char)player->level;
    unsigned int class_number = (unsigned char)player->class;
    long required, price, missing_exp, missing_gold;
    int correct_room, ready;
    if (class_number < 1 || class_number > 10 || level < 1) {
        print(player->fd, "Training progress is available for playable classes at level 1 or above.\n");
        return 0;
    }
    if (level < MAXALVL) {
        required = needed_exp[level - 1];
    } else {
        /* The original on-disk ABI uses signed 32-bit long values. */
        if (needed_exp[MAXALVL - 1] < 0 ||
            needed_exp[MAXALVL - 1] > 2147483647L / (long)level) {
            print(player->fd, "Training requirements exceed the original engine's supported range.\n");
            return 0;
        }
        required = needed_exp[MAXALVL - 1] * (long)level;
    }
    if (required < 0 || required > 2147483647L ||
        player->experience < 0 || player->gold < 0) {
        print(player->fd, "Training progress is unavailable for these character values.\n");
        return 0;
    }
    price = required / 2L;
    missing_exp = player->experience < required ? required - player->experience : 0;
    missing_gold = player->gold < price ? price - player->gold : 0;
    correct_room = training_room_matches(player);
    ready = !missing_exp && !missing_gold && correct_room &&
            !F_ISSET(player, PBLIND) && F_ISSET(player, PSECOK);
    print(player->fd, "TRAINING PROGRESS - %s level %u\n", CLASSES[class_number], level);
    print(player->fd, "XP: %ld / %ld required; %ld more needed.\n",
          player->experience, required, missing_exp);
    print(player->fd, "Gold: %ld / %ld cost; %ld more needed.\n",
          player->gold, price, missing_gold);
    print(player->fd, "Training room: %s.\n", correct_room ? "matches your class" : "find your class's training room");
    if (F_ISSET(player, PBLIND)) print(player->fd, "Training is blocked while you are blind.\n");
    if (!F_ISSET(player, PSECOK)) print(player->fd, "Training approval is pending. Try again shortly.\n");
    if (ready) print(player->fd, "Ready: use train here to advance one level.\n");
    else print(player->fd, "Meet the requirements above, then use train.\n");
    print(player->fd, "Training spends gold. Your accumulated XP is retained.\n");
    return 0;
}

int hclass(creature *player, cmd *command)
{
    int i, selected = (unsigned char)player->class;
    if (command->num > 1 && !strcmp(command->str[1], "progress"))
        return training_progress(player);
    if (command->num > 1) {
        char lower[20]; size_t j;
        selected = -1;
        for (i = 1; i <= 10; i++) {
            for (j = 0; CLASSES[i][j] && j < sizeof(lower)-1; j++) lower[j] = (char)tolower((unsigned char)CLASSES[i][j]);
            lower[j] = '\0';
            if (!strcmp(lower, command->str[1])) selected = i;
        }
    }
    print(player->fd, "Original Mordor classes: assassin, barbarian, cleric, fighter, mage, paladin, ranger, thief, bard, monk.\n");
    if (selected < 1 || selected > 10) { print(player->fd, "Use hclass <class-name> for a playable class guide.\n"); return 0; }
    print(player->fd, "%s: %s\n", CLASSES[selected], CLASS_GUIDES[selected]);
    print(player->fd, "Train in your class's training room when you have enough experience and gold. Class and level restrictions still apply.\n");
    return 0;
}

int hprofile(creature *player, cmd *command)
{
    struct hd_state state;
    int i, badges = 0, compact = 0;
    unsigned int class_number = (unsigned char)player->class;
    if (command->num > 1) {
        if (strcmp(command->str[1], "status")) {
            print(player->fd, "Usage: hprofile [status]\n");
            return 0;
        }
        compact = 1;
    }
    if (!load_state(player, &state)) { storage_error(player); return 0; }
    if (compact) {
        print(player->fd, "STATUS - %s | Level %u | %s\n", player->name,
              (unsigned int)(unsigned char)player->level,
              class_number >= 1 && class_number <= 10 ? CLASSES[class_number] : "Other class");
        print(player->fd, "HP %d/%d | MP %d/%d\n", player->hpcur, player->hpmax, player->mpcur, player->mpmax);
        print(player->fd, "XP %ld | Gold %ld\n", player->experience, player->gold);
        for (i = 0; i < HD_QUEST_COUNT; i++) if (state.claimed & (1U << i)) badges++;
        print(player->fd, "Chronicle: %u/%u places | %d/%d badges\n",
              state.room_count, (unsigned int)HD_MAX_ROOMS, badges, HD_QUEST_COUNT);
        print(player->fd, "Training: hclass progress | Next goal: hquest next\n");
        return 0;
    }
    print(player->fd, "HOLLOWDEEP CHRONICLE - %s\n", player->name);
    print(player->fd, "Recorded places: %u. Current character level: %u.\n", state.room_count, (unsigned char)player->level);
    for (i = 0; i < HD_QUEST_COUNT; i++) if (state.claimed & (1U << i)) { print(player->fd, "Badge: %s\n", QUESTS[i].badge); badges++; }
    if (!badges) print(player->fd, "No badges yet. Start with hquest accept first-steps.\n");
    print(player->fd, "Badges are cosmetic journal honors. They do not modify your class, title, gold, or experience.\n");
    return 0;
}

static int next_quest(creature *player, const struct hd_state *state)
{
    int i, first_active = -1, first_available = -1;
    unsigned int bit, missing_rooms, missing_levels;
    unsigned int level = (unsigned char)player->level;
    for (i = 0; i < HD_QUEST_COUNT; i++) {
        bit = 1U << i;
        if (state->claimed & bit) continue;
        if (!(state->accepted & bit)) {
            if (first_available < 0) first_available = i;
            continue;
        }
        if (state->room_count >= QUESTS[i].rooms && level >= QUESTS[i].level) {
            print(player->fd, "Ready to claim: %s.\n", QUESTS[i].title);
            print(player->fd, "Use hquest claim %s for the %s badge.\n", QUESTS[i].id, QUESTS[i].badge);
            return 0;
        }
        if (first_active < 0) first_active = i;
    }
    if (first_active >= 0) {
        i = first_active;
        missing_rooms = state->room_count < QUESTS[i].rooms ? QUESTS[i].rooms - state->room_count : 0;
        missing_levels = level < QUESTS[i].level ? QUESTS[i].level - level : 0;
        print(player->fd, "Next active chronicle: %s (%s).\n", QUESTS[i].title, QUESTS[i].id);
        print(player->fd, "Remaining: %u places; %u levels.\n", missing_rooms, missing_levels);
        if (missing_rooms) print(player->fd, "Explore new rooms and use hquest survey.\n");
        if (missing_levels) print(player->fd, "Use hclass progress to plan your next training.\n");
        return 0;
    }
    if (first_available >= 0) {
        print(player->fd, "Next available chronicle: %s.\n", QUESTS[first_available].title);
        print(player->fd, "Start with hquest accept %s.\n", QUESTS[first_available].id);
        return 0;
    }
    print(player->fd, "All chronicles are complete. Use hprofile to review your badges.\n");
    return 0;
}

int hquest(creature *player, cmd *command)
{
    struct hd_state state;
    int index, i;
    unsigned int bit, room_number;
    const char *action = command->num > 1 ? command->str[1] : "list";
    if (!load_state(player, &state)) { storage_error(player); return 0; }
    if (!strcmp(action, "next")) return next_quest(player, &state);
    if (!strcmp(action, "survey")) {
        if (!state.accepted) { print(player->fd, "Accept a chronicle first: hquest accept first-steps.\n"); return 0; }
        if (!player->parent_rom || player->parent_rom->rom_num < 1) { print(player->fd, "You cannot survey this location.\n"); return 0; }
        room_number = (unsigned short)player->parent_rom->rom_num;
        for (i = 0; i < (int)state.room_count; i++) if (state.rooms[i] == room_number) { print(player->fd, "This place is already in your chronicle. Explore a new room.\n"); return 0; }
        if (state.room_count == HD_MAX_ROOMS) { print(player->fd, "Your chronicle has recorded its maximum of 128 places.\n"); return 0; }
        state.rooms[state.room_count++] = room_number;
        if (!save_state(player, &state)) { storage_error(player); return 0; }
        print(player->fd, "You record this place in your chronicle. Unique places: %u.\n", state.room_count);
        return 0;
    }
    if (!strcmp(action, "accept") || !strcmp(action, "claim")) {
        if (command->num < 3 || (index = quest_index(command->str[2])) < 0) { print(player->fd, "Choose a quest ID shown by hquest. Example: hquest accept first-steps.\n"); return 0; }
        bit = 1U << index;
        if (!strcmp(action, "accept")) {
            if (state.accepted & bit) { print(player->fd, "That chronicle is already accepted. Use hquest to check it.\n"); return 0; }
            state.accepted |= bit;
            if (!save_state(player, &state)) { storage_error(player); return 0; }
            print(player->fd, "Accepted: %s. Survey %u unique rooms and reach level %u. Earlier surveys count.\n", QUESTS[index].title, QUESTS[index].rooms, QUESTS[index].level);
            return 0;
        }
        if (!(state.accepted & bit)) { print(player->fd, "Accept this chronicle before claiming its badge.\n"); return 0; }
        if (state.claimed & bit) { print(player->fd, "You already earned that badge. Use hprofile to see your honors.\n"); return 0; }
        if (state.room_count < QUESTS[index].rooms || (unsigned char)player->level < QUESTS[index].level) {
            print(player->fd, "Not complete: %u/%u places; level %u/%u.\n", state.room_count, QUESTS[index].rooms, (unsigned char)player->level, QUESTS[index].level); return 0;
        }
        state.claimed |= bit;
        if (!save_state(player, &state)) { storage_error(player); return 0; }
        print(player->fd, "Chronicle complete: %s. You earned the %s badge!\n", QUESTS[index].title, QUESTS[index].badge);
        return 0;
    }
    if (strcmp(action, "list") && strcmp(action, "status")) {
        print(player->fd, "Usage: hquest [list|status|next|survey|accept <id>|claim <id>]\n"); return 0;
    }
    print(player->fd, "THE HOLLOWDEEP CHRONICLES\nRecord real places with hquest survey. Each room counts once.\n");
    for (i = 0; i < HD_QUEST_COUNT; i++) {
        bit = 1U << i;
        print(player->fd, "%s - %s [%s]\n", QUESTS[i].id, QUESTS[i].title,
              (state.claimed & bit) ? "claimed" : (state.accepted & bit) ? "active" : "available");
        print(player->fd, "  Places %u/%u; level %u/%u. Badge: %s.\n", state.room_count, QUESTS[i].rooms,
              (unsigned char)player->level, QUESTS[i].level, QUESTS[i].badge);
    }
    print(player->fd, "hquest accept <id> | hquest survey | hquest claim <id> | hprofile\n");
    return 0;
}
