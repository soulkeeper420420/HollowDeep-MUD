#ifndef HD_PLAYER_STORE_MOCK_Z_H
#define HD_PLAYER_STORE_MOCK_Z_H
#define PLAYER 1
#define CARETAKER 10
typedef struct room {int rom_num;} room;
typedef struct creature {
 int type,class,fd,rom_num,hpcur;
 room *parent_rom;
 char name[80];
} creature;
#endif
