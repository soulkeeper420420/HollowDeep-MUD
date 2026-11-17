#!/usr/bin/env bash
# Private Necromancer character-creation prototype for HollowDeep.
# Applies to the two released Round 74B source archives. Builds and runs a
# save-store check in a fresh private directory. Starts no service.
set -Eeuo pipefail
umask 077
dev=/root/hollowdeep-dev
base=${1:-"$dev/round74b-native-source.tar.gz"}
handoff=${2:-"$dev/round74b-codex-handoff-20261116T165302Z.tar.gz"}
printf '%s  %s\n' \
    ac3a6f59e2126ddd344d068976fb89a3501c4c5446ecce49108190a3ca93ca50 "$base" \
    3e52716ee11824283fb76c9c2f9c9ef535e20dd35217820561d7333597afe624 "$handoff" |
    sha256sum -c -
stage=$(mktemp -d "$dev/necromancer-playtest-XXXXXXXX")
mkdir "$stage/src" "$stage/handoff" "$stage/fixture" "$stage/fixture/player"
tar -xzf "$base" -C "$stage/src" --no-same-owner --no-same-permissions
tar -xzf "$handoff" -C "$stage/handoff" --no-same-owner --no-same-permissions
cp "$stage/handoff/changed/"* "$stage/src/"
patch --batch --forward -p1 -d "$stage/src" <<'NECROMANCER_PATCH'
--- a/Makefile
+++ b/Makefile
@@ -7,6 +7,9 @@
 
 # Round 74B test-only native progression (no production or XP migration)
 CFLAGS += -DHD74_PRIVATE_NATIVE
+ifeq ($(NECROMANCER_PLAYTEST),1)
+CFLAGS += -DHD_NECROMANCER_PLAYTEST
+endif
 OBJECTS += hd74_native.o hd74_progression.o hd74_xp.o
 
 # Round 73G private receipt-preserving native save/load candidate
--- a/command1.c
+++ b/command1.c
@@ -16,6 +16,9 @@
 #include "mextern.h"
 #include <ctype.h>
 #include <string.h>
+#ifdef HD_NECROMANCER_PLAYTEST
+#include <strings.h>
+#endif
 #ifdef DMALLOC
   #include "/usr/local/include/dmalloc.h"
 #endif
@@ -221,11 +224,22 @@
 			F_SET(Ply[fd].ply, PMALES);
 		print(fd, "\nAvailable classes:\n");
 		print(fd, "Assassin, Barbarian, Bard, Cleric, Fighter,\n");
-		print(fd, "Mage, Monk, Paladin, Ranger, Thief\n");
+#ifdef HD_NECROMANCER_PLAYTEST
+        print(fd, "Mage, Monk, Necromancer, Paladin, Ranger, Thief\n");
+#else
+        print(fd, "Mage, Monk, Paladin, Ranger, Thief\n");
+#endif
 		print(fd, "Choose one: ");
 		RETURN(fd, create_ply, 3);
-	case 3:
-		switch(low(str[0])) {
+    case 3:
+#ifdef HD_NECROMANCER_PLAYTEST
+        Ply[fd].extr->tempstr[1][0] = 0;
+        if (!strcasecmp(str, "necromancer")) {
+            Ply[fd].ply->class = MAGE;
+            Ply[fd].extr->tempstr[1][0] = 'n';
+        } else
+#endif
+        switch(low(str[0])) {
 			case 'a': Ply[fd].ply->class = ASSASSIN; break;
 			case 'b': switch(low(str[3])) {
 				case 'b':Ply[fd].ply->class = BARBARIAN; break;
@@ -447,7 +461,13 @@
 		strcpy(Ply[fd].ply->name, Ply[fd].extr->tempstr[0]);
 		up_level(Ply[fd].ply);
                 Ply[fd].ply->fd = -1;
+#ifdef HD_NECROMANCER_PLAYTEST
+                if ((Ply[fd].extr->tempstr[1][0] == 'n'
+                     ? hd_store_create_necromancer(Ply[fd].ply->name, Ply[fd].ply)
+                     : hd_store_create_player(Ply[fd].ply->name, Ply[fd].ply)) != 0) {
+#else
                 if (hd_store_create_player(Ply[fd].ply->name, Ply[fd].ply) != 0) {
+#endif
                         print(fd, "Character creation could not be saved. Reconnect before retrying.\n");
                         output_buf();
                         disconnect(fd);
--- a/hd_player_store.c
+++ b/hd_player_store.c
@@ -29,6 +29,17 @@
 static const char first_life[] =
     "a74b000000000000000000000000000000000000000000000000000000000000";
 
+static const char necromancer_id[] = "ffffffffffffffffffffffffffffff75";
+#ifdef HD_NECROMANCER_PLAYTEST
+static const char necromancer_identity[] =
+    "a74c000000000000000000000000000000000000000000000000000000000001";
+#endif
+
+static int reserved_receipt(const char *claim)
+{
+    return !strcmp(claim, life_id) || !strcmp(claim, necromancer_id);
+}
+
 static int life_remorts(const hd_receipt_set *set)
 {
     size_t i, j;
@@ -182,7 +193,7 @@
     int rc, result=-1;
     raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
     if (!raw) return -1;
-    if (!claim_id || !strcmp(claim_id, life_id)) { free(raw); return -1; }
+    if (!claim_id || reserved_receipt(claim_id)) { free(raw); return -1; }
     rc=read_record(name,raw,&size,&used,&receipts);
     if (rc==0) result=hd_receipt_lookup(&receipts,claim_id,digest);
     free(raw);
@@ -227,8 +238,27 @@
     return remorts;
 }
 
+#ifdef HD_NECROMANCER_PLAYTEST
+int hd_store_is_necromancer(const char *name)
+{
+    unsigned char *raw = malloc(HD_RAW_CAPACITY);
+    size_t size = 0, used = 0;
+    hd_receipt_set receipts;
+    int is_necromancer = 0;
+    if (!raw) return 0;
+    if (read_record(name, raw, &size, &used, &receipts) == 0 &&
+        ((const creature *)raw)->class == MAGE)
+        is_necromancer = hd_receipt_lookup(&receipts, necromancer_id,
+                                         necromancer_identity) == 1;
+    free(raw);
+    return is_necromancer;
+}
+#endif
+
+enum player_write { PLAYER_SAVE, PLAYER_CREATE, PLAYER_CREATE_NECROMANCER };
+
 static int store_internal(const char *name, creature *crt,
-                          const char *claim, const char *digest, int create) {
+                          const char *claim, const char *digest, enum player_write action) {
     unsigned char *raw=NULL, *packed=NULL;
     hd_receipt_set receipts;
     size_t old_len=0, old_native=0, expected=0, raw_total=0;
@@ -243,12 +273,17 @@
     lock_fd=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
     if (lock_fd<0 || flock(lock_fd,LOCK_EX)<0) goto done;
     old=read_record(name,raw,&old_len,&old_native,&receipts);
-    if (old < 0 || (create && old != 1)) goto done;
+    if (old < 0 || (action != PLAYER_SAVE && old != 1)) goto done;
     if (old == 1) memset(&receipts,0,sizeof receipts);
-    if (create && hd_receipt_add(&receipts, life_id, first_life)) goto done;
+    if (action != PLAYER_SAVE && hd_receipt_add(&receipts, life_id, first_life)) goto done;
+#ifdef HD_NECROMANCER_PLAYTEST
+    if (action == PLAYER_CREATE_NECROMANCER &&
+        (crt->class != MAGE || hd_receipt_add(&receipts, necromancer_id,
+                                            necromancer_identity))) goto done;
+#endif
     if (claim || digest) {
         int seen;
-        if (!claim || !digest || !strcmp(claim, life_id)) goto done;
+        if (!claim || !digest || reserved_receipt(claim)) goto done;
         seen=hd_receipt_lookup(&receipts,claim,digest);
         if (seen<0) goto done;
         if (seen==1) { result=HD_STORE_ALREADY_CLAIMED; goto done; }
@@ -271,11 +306,17 @@
     return result;
 }
 int hd_store_save_player(const char *name,creature *player) {
-    return store_internal(name,player,NULL,NULL,0);
+    return store_internal(name,player,NULL,NULL,PLAYER_SAVE);
 }
 int hd_store_create_player(const char *name, creature *player) {
-    return store_internal(name,player,NULL,NULL,1);
+    return store_internal(name,player,NULL,NULL,PLAYER_CREATE);
+}
+#ifdef HD_NECROMANCER_PLAYTEST
+int hd_store_create_necromancer(const char *name, creature *player)
+{
+    return store_internal(name, player, NULL, NULL, PLAYER_CREATE_NECROMANCER);
 }
+#endif
 /* Match disconnect's native normalization without mutating worn items or lists. */
 int hd_store_save_live_player(const char *name, creature *player)
 {
@@ -295,5 +336,5 @@
 }
 int hd_store_save_claim(const char *name,creature *staged,
                         const char *claim_id,const char *digest) {
-    return store_internal(name,staged,claim_id,digest,0);
+    return store_internal(name,staged,claim_id,digest,PLAYER_SAVE);
 }
--- a/hd_player_store.h
+++ b/hd_player_store.h
@@ -12,6 +12,10 @@
 
 #define HD_STORE_ABSENT (-3)
 int hd_store_create_player(const char *name, creature *player);
+#ifdef HD_NECROMANCER_PLAYTEST
+int hd_store_create_necromancer(const char *name, creature *player);
+int hd_store_is_necromancer(const char *name);
+#endif
 int hd_store_save_live_player(const char *name, creature *player);
 int hd_store_verified_remorts(const char *name);
 int hd_store_load_player(const char *name, creature **out);
--- a/player.c
+++ b/player.c
@@ -9,6 +9,9 @@
 #include <math.h>
 #include "mstruct.h"
 #include "mextern.h"
+#ifdef HD_NECROMANCER_PLAYTEST
+extern int hd_store_is_necromancer(const char *name);
+#endif
 #ifdef HD74_PRIVATE_NATIVE
 #include "hd74_xp.h"
 #endif
@@ -1242,7 +1245,13 @@
 {
 	int	titlnum;
 
-	titlnum = (ply_ptr->level-1)/3;
+#ifdef HD_NECROMANCER_PLAYTEST
+    static char necromancer_title[] = "Necromancer";
+    if (ply_ptr->type == PLAYER && ply_ptr->class == MAGE &&
+        hd_store_is_necromancer(ply_ptr->name))
+        return necromancer_title;
+#endif
+    titlnum = (ply_ptr->level-1)/3;
 	if(titlnum > 7)
 		titlnum = 7;
 	return(lev_title[ply_ptr->class][titlnum]);
NECROMANCER_PATCH
cat > "$stage/check.c" <<'NECROMANCER_CHECK'
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hd_player_store.h"

static const char reserved[] = "ffffffffffffffffffffffffffffff75";
static const char digest[] = "a74c000000000000000000000000000000000000000000000000000000000001";

void merror(const char *reason, int severity)
{
    fprintf(stderr, "%s (%d)\n", reason, severity);
    abort();
}

int main(void)
{
    creature player = {0};
    creature *loaded = NULL;
    strcpy(player.name, "Hdnecromancer");
    player.type = PLAYER;
    player.class = MAGE;
    player.level = 1;

    assert(!hd_store_is_necromancer(player.name));
    assert(hd_store_create_necromancer(player.name, &player) == HD_STORE_OK);
    assert(hd_store_create_necromancer(player.name, &player) == HD_STORE_FAILURE);
    assert(hd_store_verified_remorts(player.name) == 0);
    assert(hd_store_is_necromancer(player.name));
    assert(hd_store_load_player(player.name, &loaded) == HD_STORE_OK);
    assert(loaded->class == MAGE && loaded->class < CARETAKER);
    loaded->gold = 127;
    assert(hd_store_save_live_player(loaded->name, loaded) == HD_STORE_OK);
    assert(hd_store_is_necromancer(loaded->name));
    assert(hd_store_verified_remorts(loaded->name) == 0);
    assert(hd_store_read_claim(loaded->name, reserved, digest) == -1);
    free(loaded);

    strcpy(player.name, "Hdmage");
    assert(hd_store_create_player(player.name, &player) == HD_STORE_OK);
    assert(!hd_store_is_necromancer(player.name));
    assert(hd_store_save_claim(player.name, &player, reserved, digest) == HD_STORE_FAILURE);
    assert(!hd_store_is_necromancer(player.name));
    strcpy(player.name, "Hdfighter");
    player.class = FIGHTER;
    assert(hd_store_create_necromancer(player.name, &player) == HD_STORE_FAILURE);
    assert(hd_store_load_player(player.name, &loaded) == HD_STORE_ABSENT);
    puts("PASS: Necromancer identity, native player role, first-life metadata, resave and reserved marker");
    return 0;
}
NECROMANCER_CHECK
src="$stage/src"
cc -m32 -std=gnu89 -DHD_NECROMANCER_PLAYTEST -DCOMPRESS -fcommon \
    -ffunction-sections -fdata-sections -Wl,--gc-sections \
    -Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types \
    -I "$src" "$stage/check.c" "$src/"{files1,files3,compress,hd_player_store,treasure_receipt,atomic_player_snapshot}.c -o "$stage/check"
(cd "$stage/fixture" && "$stage/check")
if ! make -s -j2 -C "$src" NECROMANCER_PLAYTEST=1 >"$stage/build.log" 2>&1; then
    tail -40 "$stage/build.log"
    exit 1
fi
file "$src/frp.new"
printf 'HOLLOWDEEP NECROMANCER PRIVATE ELF32 BUILD PASS: %s\n' "$src/frp.new"
