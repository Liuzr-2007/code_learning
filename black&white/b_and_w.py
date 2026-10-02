import math
import numpy as np
import random
import os
# 常量定义，消除魔数
BOARD_SIZE = 8
BLACK = 1
WHITE = -1
EMPTY = 0
UCT_C = 1.414

class Node:#【修改】新增 turn 属性，记录轮到哪个玩家
    def __init__(self,state, turn, parent=None):
        self.state = state
        self.turn = turn
        self.parent = parent
        self.children = []
        self.win = 0
        self.visit = 0
    def uct(self,c = UCT_C):#设置函数
        if self.visit == 0:return float('inf')
        return self.win/self.visit + c * math.sqrt(math.log(self.parent.visit)/self.visit)

def is_valid(state,r,c,me):
    """假设我下我方颜色 me，对手颜色op = -me
1. 从落子点(r,c)往某个方向走一步，得到nr, nc
2. 如果nr,nc越界 → 这个方向无效，换下一个方向
3. 如果state[nr][nc] != op → 这个方向没有对手棋子，无效
4. 如果是对手棋子：继续沿着同方向一直往前走
   - 碰到我方棋子：这个方向可以翻转，该位置(r,c)是合法点
   - 碰到空位 / 出界：这个方向无效
    只要任意一个方向满足，这个位置就是合法落子点"""
    if state[r][c] != 0:
        return False
    op = -me
    #可以移动的方向，八个方位
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    #是否存在可以翻转的棋子
    has_flip = False
    for dr,dc in dirs:
        nr = r+dr
        nc = c+dc
        found_opp =False
        while 0<=nr<8 and 0<=nc<8:
            if state[nr][nc] ==op:
                found_opp = True
                nr+=dr
                nc+=dc
            elif state[nr][nc] == me:
                if found_opp:
                    has_flip = True
                break
            else:
                break
    return has_flip

def get_all_valid_step(board,me):
    """获取所有能下棋的合法位置"""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_valid(board,r,c,me):
                moves.append((r,c))
    return moves

def place_and_flip(board,r,c,me):
    """落子并翻转棋子"""
    op = -me
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    new_board = board.copy()
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
    black_move = len(get_all_valid_step(board, BLACK))
    white_move = len(get_all_valid_step(board, WHITE))
    if black_move==0 and white_move==0:
        cnt_b = np.sum(board == BLACK)
        cnt_w = np.sum(board == WHITE)
        if cnt_b > cnt_w:
            return BLACK
        elif cnt_b < cnt_w:
            return WHITE
        else:
            return 0 #平局
    return None #游戏继续

def rollout(state):
    """模拟棋盘(目前采用的是随机下棋误差很大)"""
    s = state.copy()          # 复制棋盘，不要污染原局面
    turn = BLACK                  # 当前轮到谁下棋：1玩家，-1AI
    while is_game_over(s) is None:       # 只要游戏还没结束，就循环
        moves = get_all_valid_step(s,turn)  # 获取当前玩家所有合法落子位置
        if not moves:
            turn *= -1          # 如果当前玩家没有合法落子位置，轮到对手下棋
            continue
        r,c = random.choice(moves)  # 随机选择一个合法落子位置
        s = place_and_flip(s,r,c,turn)  # 落子并翻转棋子
        turn *= -1            # 切换玩家（1变-1，-1变1）
    final = is_game_over(s)           # 得到最终对局结果
    #AI(WHITE)胜利返回1，平局0.5，输返回0
    if final == WHITE:
        return 1
    elif final == 0:
        return 0.5
    else:
        return 0

def mcts(root,times=500):#【修改】使用节点自带turn，自动切换玩家
    for _ in range(times):
        n = root
        while n.children and get_all_valid_step(n.state, n.turn):
            n = max(n.children,key = lambda x:x.uct())
        valid_moves = get_all_valid_step(n.state, n.turn)
        if valid_moves:
            pos = random.choice(valid_moves)
            ns = place_and_flip(n.state, pos[0], pos[1], n.turn)
            next_turn = -n.turn
            new_node = Node(ns, next_turn, n)
            n.children.append(new_node)
            n = new_node
        r = rollout(n.state)
        while n:
            n.visit +=1
            n.win +=r
            n = n.parent
    return max(root.children, key = lambda x:x.visit).state

def print_board(board):
    print("  A B C D E F G H")
    for row in range(8):
        line = f"{row} "
        for col in range(8):
            val = board[row, col]
            if val == 0:
                line += ". "
            elif val == 1:
                line += "● "
            elif val == -1:
                line += "○ "
        print(line)

def parse_input(s):
    s = s.strip().upper()
    if len(s) != 2:
        raise Exception("输入格式错误，示例：3E")
    row = int(s[0])
    c_char = s[1]
    col = ord(c_char) - ord('A')
    if not (0 <= row <=7 and 0 <= col <=7):
        raise Exception("坐标超出棋盘范围 0~7，A~H")
    return row, col

def clear_screen():
    # Windows用cls，Linux/Mac用clear，跨平台
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    # 8×8 全0棋盘，int类型
    board = np.zeros((8,8), dtype=int)
    # 黑白棋初始4子
    board[3,3] = BLACK
    board[3,4] = WHITE
    board[4,3] = WHITE
    board[4,4] = BLACK

    clear_screen() #开局清屏
    print_board(board)
  
    skip_count = 0 #初始化连续跳过计数器
    while True:
        # ========== 玩家（黑棋）回合 ==========
        black_moves = get_all_valid_step(board, BLACK)
        if not black_moves:
            print("黑棋无棋可下，跳过！")
            skip_count +=1
        else:
            skip_count = 0 # 成功落子，重置跳过计数
            while True:
                user_input = input("请输入你要下棋的位置（如3E）：")
                try:
                    row, col = parse_input(user_input)
                except Exception as e:
                    print(e)
                    continue
                # 判断玩家落子是否合法
                if not is_valid(board, row, col, me=BLACK):
                    print("❌ 这个位置不能落子！请重新输入")
                    continue
                break
            #玩家落子并翻转棋子
            board = place_and_flip(board, row, col, BLACK)
            clear_screen() #【清屏】清除旧画面
            print("你落子后：")
            print_board(board)
        
        # 连续双方都不能下，游戏结束
        if skip_count >=2:
            break
        # ========== AI（白棋）回合 ==========
        ai_moves = get_all_valid_step(board, WHITE)
        if not ai_moves:
            print("AI无棋可下，跳过！")
            skip_count +=1
        else:
            skip_count = 0
            print("AI正在思考...")
            board = mcts(Node(board, WHITE),300)
            clear_screen() #【清屏】AI走完清屏刷新
            print("AI落子后：")
            print_board(board)
        if skip_count >=2:
            break
    
    #游戏结束，统计棋子判定胜负
    clear_screen() #游戏结束清屏，最后显示结果
    cnt_b = np.sum(board == BLACK)
    cnt_w = np.sum(board == WHITE)
    print(f"\n游戏结束！黑棋：{cnt_b} 枚，白棋：{cnt_w} 枚")
    if cnt_b > cnt_w:
        print("🎉 你赢了！")
    elif cnt_b < cnt_w:
        print("😥 AI赢了！")
    else:
        print("🤝 平局！")
