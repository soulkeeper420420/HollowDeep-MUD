#ifndef HD_PLAYER_STORE_MOCK_H
#define HD_PLAYER_STORE_MOCK_H
#define PLAYER 1
#define CARETAKER 10
typedef struct creature {
    int type,class,fd,rom_num,hpcur;
    void *parent_rom;
    char name[80];
} creature;
#endif
