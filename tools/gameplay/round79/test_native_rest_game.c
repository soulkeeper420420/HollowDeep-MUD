/* Round79P private native ELF32 Breath recovery fixture.
 * First rerun the already passing Round79K atomic room+Breath tests,
 * then exercise rest->+15, command-interruption->+5 and lifecycle reset.
 * Uses only synthetic players, private files and the existing fixture.
 */
/* Private runner materializes the previously tested Round79K fixture
 * as travel_base.c with only its outer main() renamed. Its nested
 * synthetic player fixture retains its own legacy_main alias.
 */
#include "travel_base.c"
#include "hd79_rest_game.h"

int main(void)
{
    const char *name="Hdrestqa";
    room town={0};
    creature player,*live=NULL;
    hd_breath_record before,after;
    unsigned i;
    uint32_t start;
    int result;

    assert(hd79_previous_travel_main()==0);
    town.rom_num=2;
    initial(&player,name);
    player.class=FIGHTER;
    player.level=40;
    player.rom_num=2;
    player.hpmax=player.hpcur=200;
    assert(hd_store_create_player(name,&player)==HD_STORE_OK);
    assert(hd_store_load_player(name,&live)==HD_STORE_OK);
    assert(live);
    live->parent_rom=&town;

    result=-1;
    assert(hd79_breath_status(live,&result)==0 && result==100);
    assert(hd_breath_store_read(name,&before)==HD_BREATH_STORE_OK);
    start=before.last_recover;

    /* Spend 20 synthetic Breath via the tested atomic receipt API.
     * No real wilderness movement occurs in this private fixture.
     */
    for(i=0;i<10;i++) {
        assert(hd_breath_store_step(name,&before,
            HD_BREATH_OP_TRAVEL,1,0,start+1+i,&after)==HD_BREATH_STORE_OK);
        before=after;
    }
    expect_disk(name,2,80);

    /* Resting only becomes eligible at >=45 uninterrupted seconds.
     * Read-only skills/look/help cannot disrupt session status.
     */
    assert(hd79_rest_begin_at_for_test(live,start)==0);
    assert(hd79_rest_begin_at_for_test(live,start+17)==0);
    hd79_rest_before_command(live,"skills");
    hd79_rest_before_command(live,"look");
    assert(hd79_rest_bonus_eligible(live,start+44,start)==0);
    assert(hd79_rest_bonus_eligible(live,start+45,start)==1);
    assert(hd79_breath_pulse(live,(long)start+45)==0);
    expect_disk(name,2,95);
    assert(hd79_breath_pulse(live,(long)start+45)==0);
    expect_disk(name,2,95);
    puts("PASS: real native Breath atomically grants +15 after verified rest tick once");

    /* Combat and real movement interrupt before native callback.
     * The subsequent normal recovery remains +5 and must not reuse
     * the previous rest state's accelerated rate.
     */
    hd79_rest_before_command(live,"attack");
    assert(hd79_rest_bonus_eligible(live,start+90,start+45)==0);
    assert(hd79_breath_pulse(live,(long)start+90)==0);
    expect_disk(name,2,100);
    puts("PASS: attack interruption restores normal +5 recovery");

    /* Damage, even from non-command monster combat, invalidates rest. */
    assert(hd79_rest_begin_at_for_test(live,start+100)==0);
    live->hpcur-=20;
    assert(hd79_rest_bonus_eligible(live,start+160,start+90)==0);
    assert(hd79_rest_bonus_eligible(live,start+161,start+90)==0);
    live->hpcur+=20;
    puts("PASS: observed health damage revokes accelerated resting");

    /* Unexpected relocation must revoke before a +15 receipt.
     * Also prove the social sleep/sit/stand verbs never begin rest.
     */
    assert(hd79_rest_begin_at_for_test(live,start+200)==0);
    live->rom_num=3;
    assert(!hd79_rest_bonus_eligible(live,start+250,start+90));
    live->rom_num=2;
    hd79_rest_before_command(live,"sleep");
    hd79_rest_before_command(live,"sit");
    hd79_rest_before_command(live,"stand");
    assert(!hd79_rest_bonus_eligible(live,start+250,start+90));
    puts("PASS: relocation and legacy emote verbs cannot retain REST");

    /* Free/death hooks call hd79_rest_forget in native runtime. The
     * deterministic function is also checked directly here.
     */
    assert(hd79_rest_begin_at_for_test(live,start+300)==0);
    hd79_rest_forget(live);
    assert(!hd79_rest_bonus_eligible(live,start+400,start+90));
    free_crt(live);
    puts("PASS: logout/death cleanup forgets transient rest session");

    puts("ROUND79P: NATIVE ELF32 RESTING +15 ATOMIC CONTRACT PASS");
    puts("REAL SOCKET REST COMMAND AND TIME-BASED PULSE: STILL REQUIRE TEST");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
