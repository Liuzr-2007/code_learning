#pragma once
#ifndef GAME_H
#define GAME_H

#include "struct.h"

// 全局变量（在 game.c 中定义）
extern Texture2D bgTex;

extern Background backgrounds[BG_COUNT];

extern int currentIndex;

extern Button startButton;
extern Button exitButton;
#endif // GAME_H
