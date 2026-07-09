#include<stdio.h>
#include<stdlib.h>
#include<stdbool.h>
#include<string.h> // 添加此行以声明memcpy

typedef int ElemType; // 定义元素类型	
#define OVERFLOW -2
#define ERROR -3
#define errV -4

typedef struct {
	ElemType* elem; // 存储空间基址
	int length; // 当前长度
	int size; // 当前分配的存储容量
	int inc; // inc(rement)存储空间分配增量
}*SqList,*List;
SqList L;//被声明为顺序表指针变量，需初始化才能使用

//初始化顺序表
SqList InitList(int size,int inc) {
	SqList L;
	if (!(L = (SqList)malloc(sizeof(*L)))) exit(OVERFLOW);	//分配结构体的空间
	L->elem = (ElemType*)malloc(size * sizeof(ElemType));	//分配元素储存的空间，用指针与结构体链接

	if (!L->elem) exit(OVERFLOW);
	L->length = 0;
	L->size = size;	
	L->inc = inc;
	return L;
}
//释放顺序表空间
SqList FreeList(SqList L) {
	if (!L) exit(ERROR);
	if (L) {
		free(L->elem);
		free(L);
	}
	return NULL;
}
SqList Clearlilst(SqList L) {
	if (!L) exit(ERROR);
	L->length = 0;
}
bool ListEmpty(SqList L) {
	if (!L) exit(ERROR);
	if (L->length == 0) return true;
	return false;
}
ElemType ListLen(SqList L){
	if (!L) exit(ERROR);
	return L->length;
}
ElemType GetElem(SqList L, int i) {
	if (!L) exit(ERROR);
	if (i<1 || i>L->length) return errV;
	else return L->elem[i];
}
void PutElem(SqList L, ElemType e, int i) {
	if (!L) exit(ERROR);
	if (i < 1) exit(errV);
	L->elem[i] = e;
	return;
}
ElemType LocateElem(SqList L,ElemType e,bool(*Equal)(ElemType, ElemType)) {
	if (!L) exit(ERROR);
	int i = 1;
	while (i <= L->length && !Equal(e, L->elem[i])) i++;
	if (i <= L->length) return i;
	else return 0;
}
ElemType prevElem(SqList L, ElemType e, bool(*Equal)(ElemType, ElemType)) {
	if (!L) exit(ERROR);
	int i = 1;
	while (i <= L->length && !Equal(e, L->elem[i])) i++;
	if (i <= L->length) return L->elem[i - 1];
	else return errV;
}
ElemType nextElem(SqList L, ElemType e, bool(*Equal)(ElemType, ElemType)) {
	if (!L) exit(ERROR);
	int i = 1;
	while (i <= L->length && !Equal(e, L->elem[i])) i++;
	if (i <= L->length) return L->elem[i + 1];
	else return errV;
}
SqList ListInsert(SqList L, int i, ElemType e) {
	if (!L) exit(ERROR);
	if (i < 1 || i > L->length + 1) exit(errV);
	if (L->length >= L->size) {
		ElemType* newbase = (ElemType*)realloc(L->elem, (L->size + L->inc) * sizeof(ElemType));
		if (!newbase) exit(OVERFLOW);
		L->elem = newbase;
		L->size += L->inc;
	}
	for (int j = L->length; j >= i; j--) L->elem[j + 1] = L->elem[j];
	L->elem[i] = e;
	L->length++;
	return L;
}
SqList ListDelete(SqList L, int i) {
	if (!L) exit(ERROR);
	if (i < 1 || i > L->length) exit(errV);
	for (int j = i; j < L->length; j++) L->elem[j] = L->elem[j + 1];
	L->length--;
	return L;
}
SqList MergeList(SqList La, SqList Lb) {
	SqList Lc;
	ElemType* pa, * pb, * pc, * pa_end, * pb_end;
	if (!La || !Lb) return NULL;
	pa = La->elem; pb = Lb->elem;
	Lc = InitList(La->length + Lb->length, La->inc);
	Lc->length = Lc->size;
	pc = Lc->elem;
	pa_end = La->elem + La->length - 1;
	pb_end = Lb->elem + Lb->length - 1;
	while (pa <= pa_end && pb <= pb_end) {
		if (*pa <= *pb) *pc++ = *pa++;
		else *pc++ = *pb++;
	}
	if (pa <= pa_end) memcpy(pc, pa, (pa_end - pa + 1) * sizeof(ElemType));
	if (pb <= pb_end) memcpy(pc, pb, (pb_end - pb + 1) * sizeof(ElemType));
	return Lc;
}


//STACK
typedef struct {
	ElemType* base;
	ElemType* top;
	int size;
}*SqStack;

SqStack Initstack(int size) {
	SqStack S;
	if(!(S=(SqStack)malloc(sizeof(*S)))) exit(OVERFLOW);
	if (!(S->base = (ElemType*)calloc(size, sizeof(ElemType)))) exit(OVERFLOW);
	S->top = S->base;
	S->size = size;
	return S;
}

SqStack FreeStack(SqStack S) {
	if (!S) exit(ERROR);
	S->top = S->base;
	free(S->base);
	free(S);
	return NULL;
}

SqStack ClearStack(SqStack S) {
	if (!S) exit(ERROR);
	S->top = S->base;
	return S;
}

bool StackEmpty(SqStack S) {
	if (!S) exit(ERROR);
	return S->top == S->base;
}
//attention!
int StackLen(SqStack S) {
	if (!S) exit(ERROR);
	return S->top - S->base;
}

ElemType GetTop(SqStack S) {
	if (!S) exit(ERROR);
	return *(S->top - 1);
}

void Push(SqStack S, ElemType e) {
	if (!S) exit(ERROR);
	if (S->top - S->base >= S->size) {
		ElemType* newbase = (ElemType*)realloc(S->base, (S->size + 10) * sizeof(ElemType));
		if (!newbase) exit(OVERFLOW);
		S->base = newbase;
		S->top = S->base + S->size;
		S->size += 10;
	}
	*S->top++ = e;
}

ElemType Pop(SqStack S) {
	if (!S) exit(ERROR);
	if (StackEmpty(S)) exit(errV);
	return *--S->top;
}

void StackTrav(SqStack S, void(*Visit)(ElemType)) {
	if (!S) exit(ERROR);
	ElemType* p = S->base;
	while (p < S->top) Visit(*p++);
}

//string locat
typedef char* SStr;
typedef struct {
	char *sv;
	int len;
	int size;
}*LStr;
int Index(SStr S, SStr T, int pos) {
	int i = pos, j = 1;
	if (!S || !T || T[0] <= 0 || pos < 1) return 0;
	while (i <= S[0] && j <= T[0]) {
		if (S[i] == T[j]) { ++i; ++j; }
		else { i = i - j + 2; j = 1; }
	}
	if(j>T[0]) return i - T[0];
	else return 0;
}
//Tree
#include <iostream>
#define _for(i, a, b) for (int i=(a); i<=(b); i++)
using namespace std;

const int MAXN = 1e6 + 10;

struct node {
	int left, right;
};
node tree[MAXN];//存储结构定义

int n, ans;

void dfs(int id, int deep) {
	if (id == 0) return;//到达叶子节点时返回
	ans = max(ans, deep);//更新答案
	dfs(tree[id].left, deep + 1);//向左遍历
	dfs(tree[id].right, deep + 1);//向右遍历
}

int main() {
	cin >> n;
	_for(i, 1, n) cin >> tree[i].left >> tree[i].right;//读入+建树
	dfs(1, 1);//从1号节点出发，当前深度为1
	cout << ans << endl;//输出答案
	return 0;//完结撒花！
}
/*
 给出一棵二叉树的中序与后序排列。求出它的先序排列。（约定树结点用不同的大写字母表示，且二叉树的节点个数 ≤8）。

输入格式
共两行，均为大写字母组成的字符串，表示一棵二叉树的中序与后序排列。

输出格式
共一行一个字符串，表示一棵二叉树的先序。
输入 
BADC
BDCA
输出 
ABCD

首先，一点基本常识，给你一个后序遍历，那么最后一个就是根（如ABCD，则根为D）。
因为题目求先序，意味着要不断找根。
那么我们来看这道题方法：（示例）
中序ACGDBHZKX，后序CDGAHXKZB，首先可找到主根B；
那么我们找到中序遍历中的B，由这种遍历的性质，可将中序遍历分为ACGD和HZKX两棵子树，
那么对应可找到后序遍历CDGA和HXKZ（从头找即可）
从而问题就变成求1.中序遍历ACGD，后序遍历CDGA的树 2.中序遍历HZKX，后序遍历HXKZ的树；
接着递归，按照原先方法，找到1.子根A，再分为两棵子树2.子根Z，再分为两棵子树。
就按这样一直做下去（先输出根，再递归）；
模板概括为step1:找到根并输出
step2:将中序，后序各分为左右两棵子树；
step3:递归，重复step1,2；
*/
#include<cstdio>
#include<iostream>
#include<cstring>
using namespace std;
void beford(string in, string after) {
	if (in.size() > 0) {
		char ch = after[after.size() - 1];
		cout << ch;//找根输出
		int k = in.find(ch);
		beford(in.substr(0, k), after.substr(0, k));
		beford(in.substr(k + 1), after.substr(k, in.size() - k - 1));//递归左右子树；
	}
}
int main() {
	string inord, aftord;
	cin >> inord; cin >> aftord;//读入
	beford(inord, aftord); cout << endl;
	return 0;
}
