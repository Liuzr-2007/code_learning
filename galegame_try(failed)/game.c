#include "raylib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Draw.h"
#include "struct.h"
#include"checkfunction.h"


// 全局当前显示的背景纹理
Texture2D bgTex;


Background backgrounds[BG_COUNT] = {
	{"gate.png", {0}, 0, 0},
	{"test.png", {0}, 0, 0},
};

int currentIndex = 0; // 用于跟踪当前背景索引，改为 int
// 在创建主循环前声明按钮（放在 bool showRect = true; 之后）   
Button startButton = { .rect = {350, 400, 200, 100}, .mousePos = {0,0} };
Button exitButton = { .rect = {10, 10, 100, 50}, .mousePos = {0,0} };

int main(int argc,char* argv[])
{
	bool showRect = true;

	InitWindow(900, 600, u8"game");
	SetTargetFPS(60);

	LoadBackgrounds(backgrounds, BG_COUNT);
	bgTex = backgrounds[0].bgTexture;

	Vector2 mouse = GetMousePosition();

	while (!WindowShouldClose()){
        // 每帧更新鼠标位置
        Vector2 mouse = GetMousePosition();
        exitButton.mousePos = mouse;
        bool isMouseInRect2 = CheckCollisionPointRec(exitButton.mousePos, exitButton.rect);

        // 绘制与界面处理（确保 startinterface 签名与调用一致）
        startinterface(&showRect);

        // 退出按钮检测：使用每帧更新的 mouse 和即时按键状态
        if (isMouseInRect2 && IsMouseButtonPressed(MOUSE_LEFT_BUTTON)) {
            break; // 退出主循环 
        }

        EndDrawing();
	}

	UnLoadBackgrounds(backgrounds, BG_COUNT);
	CloseWindow();
	getchar();
	return 0;
}