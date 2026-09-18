#include "checkfunction.h"

void CheckKeyPress(int* i, Background backgrounds[], Texture2D* bgTex) {
	int idx = *i;
	switch (GetKeyPressed()) {
	case KEY_UP:
		idx++;
		break;
	case KEY_DOWN:
		idx--;
		break;
	default:
		break;
	}

	if (idx < 0) idx = 0;
	if (idx >= BG_COUNT) idx = BG_COUNT - 1;

	*i = idx;
	*bgTex = backgrounds[idx].bgTexture;
}

void Check_if_click(int* i, int isMouseInRect, Background backgrounds[], Texture2D* bgTex, bool* showRect) {
	if (isMouseInRect && IsMouseButtonPressed(MOUSE_LEFT_BUTTON) && showRect) {
		int idx = *i;
		idx++; // 切换到下一个背景，或根据需求设置固定索引
		if (idx >= BG_COUNT) idx = BG_COUNT - 1; // 或者 idx = 0 实现循环
		*i = idx;
		*bgTex = backgrounds[idx].bgTexture;
	}
}//问题在于应该把背景放在各个游戏状态内，而不是专门用函数切换