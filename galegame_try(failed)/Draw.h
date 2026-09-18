#ifndef DRAW_H
#define DRAW_H

#include "struct.h"

#ifdef __cplusplus
extern "C" {
#endif

void LoadBackgrounds(Background backgrounds[], int count);

void UnLoadBackgrounds(Background backgrounds[], int count);

void DrawLayeredTextures(Texture2D bottom, Texture2D top, Vector2 bottomPos, Vector2 topPos, float topScale, Color tint);

void DrawButton(Rectangle rect, const char* text, int fontSize, Color normalColor, Color hoverColor, Vector2 mousePos);

#ifdef __cplusplus
}
#endif

#endif // DRAW_H