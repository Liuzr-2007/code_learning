from logging import root
import math
from multiprocessing import parent_process
import numpy as np
import random

from numpy._core.multiarray import dragon4_scientific

class Node:#先设置节点到时候再更改
    def __init__(self,state,parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.win = 0
        self.visit = 0

    def uct(self,c = 1.414):#设置函数
        if self.visit == 0:return float('inf')
        return self.win/self.visit + c * math.sqrt(math.log(self.parent.visit)/self.visit)

def is_valid(state,r,c,me):
    """假设我下我方颜色 me，对手颜色op = -me

1. 从落子点(r,c)往某个方向走一步，得到nr, nc
2. 如果nr,nc越界 → 这个方向无效，换下一个方向
3. 如果board[nr][nc] != op → 这个方向没有对手棋子，无效
4. 如果是对手棋子：继续沿着同方向一直往前走
   - 碰到我方棋子：这个方向可以翻转，该位置(r,c)是合法点
   - 碰到空位 / 出界：这个方向无效
    只要**任意一个方向满足**，这个位置就是合法落子点。"""
    if board[r][c] != 0:
        return False
    op = -me
    #可以移动的方向，八个方位
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    #是否存在可以翻转的棋子
    has_flip = False
    for dr,dc,in dirs:
        nr = r+dr
        nc = c+dc
        found_opp =False
        while 0<=nr<8 and 0<=nc<8:
            if board[nr][nc] ==op:
                found_opp = True
                nr+=dr
                nc+=dc
            elif board[nr][nc] == me:
                if found_opp:
                    has_filp = True
                break
            else:
                break
    return has_flip

def get_all_valid_step(board):
    """获取所有能下棋的合法位置,
    并用！表示打印把棋盘打印在控制框内"""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_valid(board,r,c):
                moves.append((r,c))
    return moves

def place_and_flip(board,r,c,me):
    op = -me
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    new_board = [row.copy() for row in board]
    new_board[r][c] = me
    for dr,dc in dirs:
        nr = r+dr
        nc = c+dc
        flip_list = []
        while 0 <= nr <8 and 0 <= nc <8:
            if new_board[nr][nc] == op:
                flip_list.append((nr,nc))
                nr += dr
                nc += dc
            elif new_board[nr][nc]==me:
                for fr,fc in flip_list:
                    new_board[fr][fc] = me
                break
            else:
                break
    return new_board

def is_game_over(board):
    black_has_move = len(get_all_valid_step(board, 1)) > 0
    white_has_move = len(get_all_valid_step(board, -1)) > 0
    return not black_has_move and not white_has_move

def rollout(state):
    """模拟棋盘1(目前采用的是随机下棋误差很大"""
    s = state.copy()          # 复制棋盘，不要污染原局面
    turn = 1                  # 当前轮到谁下棋：1玩家，-1AI
    while is_game_over(s)==0:       # 只要游戏还没结束，就循环
        pos = random.choice(get_all_valid_step(s,turn)) # 随机选一个空位
        s[pos] = turn         # 在这个位置落子
        turn *= -1            # 切换玩家（1变-1，-1变1）
    res = is_game_over(s)           # 得到最终对局结果
    return 1 if res==-1 else 0# 如果AI赢返回1，否则返回0

# 模拟的特点
#优点：实现超级简单，不需要写评估函数，不需要搜索，直接随
#机下完一局。
#缺点：纯随机下棋很蠢，模拟结果质量不高；AlphaGo 就是把这个
#随机 rollout 换成神经网络预测，大幅提升效果。

def mcts(root,times=500):#限制循环轮数，防止时间过长
    for _ in range(times):
        n = root
        while n.children and get_all_valid_step(n.state):#n.children当前节点有子节点
            n = max(n.children,key = lambda x:x.uct())#对每个子节点`x`，调用`x.uct()`算出 UCT 值

        if get_all_valid_step(n.state):
            pos = random.choice(get_all_valid_step(n.state))
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
#返回uct值最大的子节点的状态

def print_board(board):
    # board是长度9的一维列表，1=玩家，-1=AI，0=空位
    sym = {1:"X", -1:"O", 0:"·"}
    for i in range(0,9,3):
        print(f"{sym[board[i]]} | {sym[board[i+1]]} | {sym[board[i+2]]}")
        if i != 6:
            print("--+---+--")

if __name__ == "__main__":

    # 8×8 全0棋盘，int类型
    board = np.zeros((8,8), dtype=int)
    # 黑白棋初始4子
    board[3,3] = 1
    board[3,4] = -1
    board[4,3] = -1
    board[4,4] = 1
  
    while True:
        p = int(input("请输入你要下棋的位置（0-8）："))
        if board[p]!=0:
            print("该位置已被占用，请重新输入！")
            continue
        elif p<0 or p>8:
            print("输入位置不合法，请重新输入！")
            continue

        board[p]=1
        res = is_game_over(board)
        if res != 0:
            if res == 1:
                print("🎉 你赢了！")
            elif res == -1:
                print("😥 AI赢了！")
            elif res == 2:
                print("🤝 平局！")
            break

        board = mcts(Node(board),300)
        print("AI落子后：")
        print_board(board)
        if is_game_over(board)!=0:break
