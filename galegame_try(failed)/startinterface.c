#include "raylib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Draw.h"
#include "struct.h"
#include"checkfunction.h"
#include"game.h"


void startinterface(bool* showRect) {
	// 在 while (!WindowShouldClose()) 循环内，用单一鼠标位置更新两个按钮并检测
	Vector2 mouse = GetMousePosition();
	startButton.mousePos = mouse;
	bool isMouseInRectstart = CheckCollisionPointRec(startButton.mousePos, startButton.rect);

	BeginDrawing();
	DrawTexture(bgTex, 0, 0, WHITE);

	DrawButton(exitButton.rect, "Exit", 30, GRAY, GRAY, exitButton.mousePos);
	// 传入 currentIndex 的地址以允许函数修改当前索引
	Check_if_click(&currentIndex, isMouseInRectstart, backgrounds, &bgTex, &showRect);
	if (isMouseInRectstart && IsMouseButtonPressed(MOUSE_LEFT_BUTTON)) {
		*showRect = false;
	}
	if (showRect) {
		DrawButton(startButton.rect, "start", 20, SKYBLUE, RED, startButton.mousePos);
	}
	CheckKeyPress(&currentIndex, backgrounds, &bgTex);
}