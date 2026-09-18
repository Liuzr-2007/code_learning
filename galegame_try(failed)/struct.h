#pragma once
#ifndef STRUCT_H
#define STRUCT_H

#include <raylib.h>

#define BG_COUNT 2   // 定义：一共有 BG_COUNT 张背景图，确保与各处初始化数组数量一致

typedef struct {
	const char* bgPath;  // 背景图路径
	Texture2D bgTexture; // 背景贴图（使用前需 LoadTexture，退出时 UnloadTexture）
	int x;               // 绘制X坐标
	int y;               // 绘制Y坐标
} Background;

typedef struct {
	const char* name;    // 角色名称
	Texture2D texture;   // 角色贴图（使用前需 LoadTexture）
	int x;               // 绘制X坐标
	int y;               // 绘制Y坐标
} Character;

typedef struct {
	Rectangle rect;     // 矩形区域
	Vector2 velocity;   // 速度向量
} GameObject;

// 用于表示按钮：只保存矩形区域（鼠标位置按需在每帧获取）
typedef struct {
	Rectangle rect;
	Vector2 mousePos;   // 可选：若你想把每帧的鼠标位置关联到按钮，可保留；否则可删除此成员
} Button;

#endif // STRUCT_H
