#include "Draw.h"
#include "struct.h"
#include <stdio.h>
#include <raylib.h>

// 导入图片
void LoadBackgrounds(Background backgrounds[], int count) {
	for (int i = 0; i < count; i++) {
		backgrounds[i].bgTexture = LoadTexture(backgrounds[i].bgPath);
	}

	if (!IsTextureValid(backgrounds[0].bgTexture)) {
		printf("Failed to load background texture: %s\n", backgrounds[0].bgPath);
		return;
	}
}

void UnLoadBackgrounds(Background backgrounds[], int count) {
	for (int i = 0; i < count; i++) {
		UnloadTexture(backgrounds[i].bgTexture);
	}
}

void DrawButton(Rectangle rect, const char* text, int fontSize, Color normalColor, Color hoverColor, Vector2 mousePos) {
	bool isMouseInRect = CheckCollisionPointRec(mousePos, rect);
	Color buttonColor = isMouseInRect ? hoverColor : normalColor;
	DrawRectangleRec(rect, buttonColor);
	int textWidth = MeasureText(text, fontSize);
	int textX = rect.x + (rect.width - textWidth) / 2;
	int textY = rect.y + (rect.height - fontSize) / 2;
	DrawText(text, textX, textY, fontSize, WHITE);
}

// 简单的分层绘制：先画 bottom，再画 top（top 可缩放并带 tint）
void DrawLayeredTextures(Texture2D bottom, Texture2D top, Vector2 bottomPos, Vector2 topPos, float topScale, Color tint)
{
    // 底图按原始大小绘制（若需缩放可改用 DrawTextureEx / DrawTexturePro）
    DrawTexture(bottom, (int)bottomPos.x, (int)bottomPos.y, WHITE);

    // 顶图使用 DrawTextureEx 支持缩放（顶图若包含 alpha，则底图会透出）
    DrawTextureEx(top, topPos, 0.0f, topScale, tint);
}