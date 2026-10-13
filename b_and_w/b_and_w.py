import math
import numpy as np
import random
import os
import time
# 常量定义，消除魔数
BOARD_SIZE = 8
BLACK = 1
WHITE = -1
EMPTY = 0
UCT_C = 1.0
STEP_TIME_LIMIT = 60  # 每步限时（秒）
#**调整 UCT 探索常数 UCT_C**
# UCT_C越大：AI 越喜欢探索冷门分支；
# UCT_C越小：越贪心，优先选历史赢率高的走法

def format_duration(seconds):
    """把秒数格式化为 M:SS 形式，用于显示对局总时间"""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


class Node:
    def __init__(self,state, turn, parent=None):
        self.state = state
        self.turn = turn   # 当前节点轮到谁下棋
        self.parent = parent
        self.children = []
        self.win = 0.0
        self.visit = 0
        self.is_expanded = False
    def uct(self,c = UCT_C):#设置函数
        if self.visit == 0:
            return float('inf')
        return self.win/self.visit + c * math.sqrt(math.log(self.parent.visit)/self.visit)

    def expand(self):
        """一次性生成全部合法子节点，包含pass"""
        if self.is_expanded:
            return
        current_player = self.turn
        valid_moves = get_all_valid_step(self.state, current_player)
        for move in valid_moves:
            new_state = self.state.copy()
            if move is not None:
                r, c = move
                new_state = place_and_flip(new_state, r, c, current_player)
            # move=None 代表pass，棋盘不变，轮到对手
            child_turn = -current_player
            # =========修复：增加turn参数传给子节点=========
            child = Node(state=new_state, turn=child_turn, parent=self)
            self.children.append(child)
        self.is_expanded = True

# 黑白棋基础工具函数
def get_move_score(r, c):
    """启发式打分，rollout优先选高分位置"""
    if (r in [0,7]) and (c in [0,7]):
        return 100
    if (r in [0,7] and c in [1,6]) or (c in [0,7] and r in [1,6]):
        return -50
    if r in [0,7] or c in [0,7]:
        return 20
    return 10

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

def get_all_valid_step(board,player):
    """获取所有能下棋的合法位置"""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_valid(board,r,c,player):
                moves.append((r,c))
    return moves

def place_and_flip(board,r,c,player):
    """落子并翻转棋子"""
    op = -player
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    new_board = board.copy()
    new_board[r][c] = player        
    for dr,dc in dirs:
        nr = r+dr
        nc = c+dc
        flip_list = []
        while 0 <= nr <8 and 0 <= nc <8:
            if new_board[nr][nc] == op:
                flip_list.append((nr,nc))
                nr += dr
                nc += dc
            elif new_board[nr][nc]==player:
                for fr,fc in flip_list:
                    new_board[fr][fc] = player
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

def is_game_end(state, last_pass, current_player):
    """判断游戏结束：连续两次pass"""
    moves = get_all_valid_step(state, current_player)
    if not moves:
        if last_pass:
            return True
    return False

def select(root):
    """选择阶段：向下搜索，遇到未扩展节点就expand"""
    node = root
    while True:
        if not node.is_expanded:
            node.expand()
            return node
        if len(node.children) == 0:
            return node
        node = max(node.children , key = lambda x:x.uct())

def rollout_ez(state):
    """模拟棋盘(采用的是随机下棋误差很大)"""
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

def rollout_hard(state,player):
    """启发式模拟，不再纯随机"""
    sim_state = state.copy()
    sim_player = player
    last_pass = False
    while True:
        if is_game_end(sim_state,last_pass,sim_player):
            break
        moves = get_all_valid_step(sim_state,sim_player)
        if not moves:
            last_pass = True
            sim_player = -sim_player
            continue
        last_pass = False
        # 启发式选择落子位置，优先选高分位置
        scored = [(get_move_score(r,c), (r,c)) for r,c in moves]
        scores, positions = zip(*scored)
        score_vals = [s for s,_ in scored]
        #最小分数偏移，防止负数
        min_s = min(score_vals)
        weights = [s - min_s + 1 for s in score_vals]
        total = sum(weights)
        probs = [w/total for w in weights]
        idx = np.random.choice(len(moves), p=probs)
        r,c = positions[idx]
        sim_state = place_and_flip(sim_state, r,c, sim_player)
        sim_player = -sim_player
    # 计算回报：棋子差值 [-1, 1]
    black = np.sum(sim_state == BLACK)
    white = np.sum(sim_state == WHITE)
    reward = (black - white) / 64
    return reward

def backprop(node, reward):
    """反向传播，注意视角翻转"""
    cur = node
    while cur is not None:
        cur.visit += 1
        cur.win += reward
        reward = -reward
        cur = cur.parent

# =========重写mcts函数，使用完整4阶段MCTS：选择→扩展→模拟→回溯=========
def mcts_hard(root,times=500):
    for _ in range(times):
        leaf = select(root)
        # 模拟，使用启发式rollout
        reward = rollout_hard(leaf.state, leaf.turn)
        backprop(leaf, reward)
    # 访问次数最多的子节点就是AI选的走法
    best_child = max(root.children, key = lambda x:x.visit)
    return best_child.state

# ========== 简单AI：旧版MCTS算法 ==========
# 采用的是获得所有的下棋位置然后随机下棋
def mcts_easy(root,times=200):# 使用节点自带turn，自动切换玩家
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
        r = rollout_ez(n.state)
        while n:
            n.visit +=1
            n.win +=r
            n = n.parent
    return max(root.children, key = lambda x:x.visit).state

# 打印棋盘（CMD对齐版本 X/O）
# hints:合法落子位置集合（如 {(r,c), ...}），这些空位显示为 *
def print_board(board, hints=None):
    print("  A B C D E F G H")
    for row in range(8):
        line = f"{row}"
        for col in range(8):
            val = board[row, col]
            if val == 0:
                c = "*" if hints and (row, col) in hints else "."
            elif val == 1:
                c = "X"
            elif val == -1:
                c = "O"
            line += f"{c:>2}"
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
    # =========难度选择菜单=========
    clear_screen()
    print("===== 黑白棋 =====")
    print("你是X")
    print("1 - 简单AI（旧算法，随机rollout）")
    print("2 - 困难AI（新版完整MCTS，启发式rollout）")
    while True:
        choice = input("请选择难度(1/2): ")
        if choice == "1":
            use_hard = False
            break
        elif choice == "2":
            use_hard = True
            break
        else:
            print("输入错误，请输入1或者2！")

    # 8×8 全0棋盘，int类型
    board = np.zeros((8,8), dtype=int)
    # 黑白棋初始4子
    board[3,3] = BLACK
    board[3,4] = WHITE
    board[4,3] = WHITE
    board[4,4] = BLACK
    clear_screen() #开局清屏
    print_board(board)

    game_start = time.time()  # 对局总时间起点
    skip_count = 0 #初始化连续跳过计数器
    while True:
        # ========== 玩家（黑棋）回合 ==========
        black_moves = get_all_valid_step(board, BLACK)
        if not black_moves:
            print("黑棋无棋可下，跳过！")
            skip_count +=1
        else:
            skip_count = 0 # 成功落子，重置跳过计数
            clear_screen() # 清掉上一回合画面，只显示带*提示的棋盘
            print(f"⏱ 本回合限时 {STEP_TIME_LIMIT} 秒，请尽快落子！")
            print("你可以落子的位置已用 * 标出：")
            print_board(board, hints=set(black_moves))
            turn_start = time.time()  # 本步计时起点
            timed_out = False
            while True:
                user_input = input("请输入你要下棋的位置（如3E）：")
                # 输入本身已耗时，超时则直接判定本回合跳过
                if time.time() - turn_start > STEP_TIME_LIMIT:
                    timed_out = True
                    break
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
            turn_elapsed = time.time() - turn_start
            if timed_out:
                print(f"⏰ 超时！本步用时 {turn_elapsed:.1f}s，超过 {STEP_TIME_LIMIT}s 限制，本回合被迫跳过。")
                skip_count += 1
            else:
                #玩家落子并翻转棋子
                board = place_and_flip(board, row, col, BLACK)
                clear_screen() #【清屏】清除旧画面
                print(f"你落子后（本步用时 {turn_elapsed:.1f}s）：")
                print_board(board)

        # 显示对局总时间
        print(f"⏱ 对局总时间：{format_duration(time.time() - game_start)}")

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
            ai_start = time.time()  # AI思考计时起点
            root = Node(board, WHITE)
            # 根据难度选择调用对应MCTS
            if use_hard:
                board = mcts_hard(root,500)
            else:
                board = mcts_easy(root,200)
            ai_elapsed = time.time() - ai_start
            clear_screen() #【清屏】AI走完清屏刷新
            print(f"AI落子后（思考用时 {ai_elapsed:.1f}s）：")
            print_board(board)

        # 显示对局总时间
        print(f"⏱ 对局总时间：{format_duration(time.time() - game_start)}")

        if skip_count >=2:
            break

    #游戏结束，统计棋子判定胜负
    total_time = time.time() - game_start
    clear_screen() #游戏结束清屏，最后显示结果
    cnt_b = np.sum(board == BLACK)
    cnt_w = np.sum(board == WHITE)
    print(f"\n游戏结束！黑棋：{cnt_b} 枚，白棋：{cnt_w} 枚")
    print(f"⏱ 对局总时间：{format_duration(total_time)}")
    if cnt_b > cnt_w:
        print("🎉 你赢了！")
    elif cnt_b < cnt_w:
        print("😥 AI赢了！")
    else:
        print("🤝 平局！")
