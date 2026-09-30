from logging import root
import math
from multiprocessing import parent_process
import numpy as np
import random

class Node:
    def __init__(self,state,parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.win = 0
        self.visit = 0

    def uct(self,c = 1.414):
        if self.visit == 0:return float('inf')
        return self.win/self.visit + c * math.sqrt(math.log(self.parent.visit)/self.visit)

def get_empty(state):#作用：遍历序列，**同时拿到下标和对应的值**
    return [i for i,v in enumerate(state) if v == 0]

def is_end(state):
    win = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in win:
        if state[a]==state[b]==state[c] and state[a]!=0:
            return state[a]
    return 0 if 0 in state else 2 #2平局

def rollout(state):
    "模拟棋盘，目前采用的是随机下棋误差很大"
    s = state.copy()          # 复制棋盘，不要污染原局面
    turn = 1                  # 当前轮到谁下棋：1玩家，-1AI
    while is_end(s)==0:       # 只要游戏还没结束，就循环
        pos = random.choice(get_empty(s)) # 随机选一个空位
        s[pos] = turn         # 在这个位置落子
        turn *= -1            # 切换玩家（1变-1，-1变1）
    res = is_end(s)           # 得到最终对局结果
    return 1 if res==-1 else 0# 如果AI赢返回1，否则返回0

# 模拟的特点
#优点：实现超级简单，不需要写评估函数，不需要搜索，直接随
#机下完一局。
#缺点：纯随机下棋很蠢，模拟结果质量不高；AlphaGo 就是把这个
#随机 rollout 换成神经网络预测，大幅提升效果。

def mcts(root,times=500):
    for _ in range(times):
        n = root
        while n.children and get_empty(n.state):
            n = max(n.children,k = lambda x:x.uct())

        if get_empty(n.state):
            pos = random.choice(get_empty(n.state))
            ns = n.state.copy()
            ns[pos] = -1
            new_node = Node(ns,n)
            n.children.append(new_node)
            n = new_node

        r = rollout(n.state)

        while n:
            n.visit +=1
            n.win +=r
            n = n.parent
    return max(root.children, key = lambda x:x.visit).state

if __name__ == "__main__":
