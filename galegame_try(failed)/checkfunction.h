// 头文件保护宏，防止重复包含（核心作用）
#ifndef CHECKFUNCTION_H
#define CHECKFUNCTION_H

// 引入自定义结构体头文件（你代码中已有的）
#include "struct.h"

// 为C++编译器提供extern "C"链接说明，确保C++中能正确调用C函数
#ifdef __cplusplus
extern "C" {
#endif

void CheckKeyPress(int* i, Background backgrounds[], Texture2D* bgTex);

void Check_if_click(int* i, int isMouseInRect, Background backgrounds[], Texture2D* bgTex, bool* showRect);

#ifdef __cplusplus
} // 闭合extern "C"
#endif

#endif // CHECKFUNCTION_H