"""黑白棋：标准规则，Tkinter 图形界面，玩家执黑对战电脑白棋。"""
import random
import tkinter as tk
from tkinter import messagebox

N = 8
DIRECTIONS = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
EMPTY, BLACK, WHITE = 0, 1, -1
CELL = 68
MARGIN = 34
COLORS = {BLACK: "#17191d", WHITE: "#f6f4ec"}
POSITION = [
    [100, -25, 15, 8, 8, 15, -25, 100],
    [-25, -45, -5, -3, -3, -5, -45, -25],
    [15, -5, 10, 4, 4, 10, -5, 15],
    [8, -3, 4, 2, 2, 4, -3, 8],
    [8, -3, 4, 2, 2, 4, -3, 8],
    [15, -5, 10, 4, 4, 10, -5, 15],
    [-25, -45, -5, -3, -3, -5, -45, -25],
    [100, -25, 15, 8, 8, 15, -25, 100],
]


def flips(board, r, c, player):
    if board[r][c] != EMPTY:
        return []
    found = []
    for dr, dc in DIRECTIONS:
        line, rr, cc = [], r + dr, c + dc
        while 0 <= rr < N and 0 <= cc < N and board[rr][cc] == -player:
            line.append((rr, cc))
            rr, cc = rr + dr, cc + dc
        if line and 0 <= rr < N and 0 <= cc < N and board[rr][cc] == player:
            found.extend(line)
    return found


def moves(board, player):
    return [(r, c, flips(board, r, c, player)) for r in range(N) for c in range(N)
            if board[r][c] == EMPTY and flips(board, r, c, player)]


def play(board, move, player):
    r, c, changed = move
    result = [row[:] for row in board]
    result[r][c] = player
    for rr, cc in changed:
        result[rr][cc] = player
    return result


def initial_board():
    board = [[EMPTY] * N for _ in range(N)]
    board[3][3], board[4][4] = WHITE, WHITE
    board[3][4], board[4][3] = BLACK, BLACK
    return board


def computer_move(board):
    """快速启发式对手：优先角落、边线，避开容易送角的位置。"""
    options = moves(board, WHITE)
    if not options:
        return None
    def score(move):
        r, c, changed = move
        value = POSITION[r][c] + len(changed) * 0.15
        # 角旁空格在角落尚未占据时通常危险
        if (r, c) in ((0, 1), (1, 0), (1, 1)) and board[0][0] == EMPTY:
            value -= 35
        if (r, c) in ((0, 6), (1, 7), (1, 6)) and board[0][7] == EMPTY:
            value -= 35
        if (r, c) in ((7, 1), (6, 0), (6, 1)) and board[7][0] == EMPTY:
            value -= 35
        if (r, c) in ((7, 6), (6, 7), (6, 6)) and board[7][7] == EMPTY:
            value -= 35
        return value + random.random() * 0.01
    return max(options, key=score)


class Reversi:
    def __init__(self, root):
        self.root = root
        root.title("黑白棋 · Reversi")
        root.resizable(False, False)
        root.configure(bg="#17231d")
        self.board = initial_board()
        self.turn = BLACK
        self.passes = 0
        self.thinking = False
        self.canvas = tk.Canvas(root, width=MARGIN * 2 + CELL * N,
                                height=MARGIN * 2 + CELL * N,
                                bg="#176b48", highlightthickness=0)
        self.canvas.pack(padx=18, pady=(18, 8))
        self.canvas.bind("<Button-1>", self.on_click)
        bar = tk.Frame(root, bg="#17231d")
        bar.pack(fill="x", padx=20, pady=(0, 18))
        self.status = tk.Label(bar, text="", font=("Microsoft YaHei UI", 13, "bold"),
                               fg="white", bg="#17231d", anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        tk.Button(bar, text="重新开始", command=self.restart,
                  font=("Microsoft YaHei UI", 10), padx=12).pack(side="right")
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for i in range(N + 1):
            x = MARGIN + i * CELL
            y = MARGIN + i * CELL
            self.canvas.create_line(x, MARGIN, x, MARGIN + N * CELL, fill="#0d5538", width=2)
            self.canvas.create_line(MARGIN, y, MARGIN + N * CELL, y, fill="#0d5538", width=2)
        for c in range(N):
            self.canvas.create_text(MARGIN + c * CELL + CELL / 2, 17, text=chr(65 + c),
                                    fill="#e6eee7", font=("Segoe UI", 10, "bold"))
        for r in range(N):
            self.canvas.create_text(17, MARGIN + r * CELL + CELL / 2, text=str(r + 1),
                                    fill="#e6eee7", font=("Segoe UI", 10, "bold"))
        valid = {(r, c) for r, c, _ in moves(self.board, self.turn)} if self.turn == BLACK and not self.thinking else set()
        for r in range(N):
            for c in range(N):
                x, y = MARGIN + c * CELL + CELL / 2, MARGIN + r * CELL + CELL / 2
                value = self.board[r][c]
                if value:
                    self.canvas.create_oval(x - 25, y - 25, x + 25, y + 25,
                                            fill=COLORS[value], outline="#101914", width=2)
                    if value == WHITE:
                        self.canvas.create_oval(x - 19, y - 19, x + 19, y + 19,
                                                outline="#d5d1c7", width=1)
                elif (r, c) in valid:
                    self.canvas.create_oval(x - 6, y - 6, x + 6, y + 6,
                                            fill="#b8e3a8", outline="")
        black, white = self.counts()
        turn_text = "电脑正在思考…" if self.thinking else ("轮到你（黑棋）" if self.turn == BLACK else "电脑回合（白棋）")
        self.status.config(text=f"{turn_text}     ● {black}   ○ {white}")

    def counts(self):
        return sum(v == BLACK for row in self.board for v in row), sum(v == WHITE for row in self.board for v in row)

    def on_click(self, event):
        if self.turn != BLACK or self.thinking:
            return
        c = (event.x - MARGIN) // CELL
        r = (event.y - MARGIN) // CELL
        if not (0 <= r < N and 0 <= c < N):
            return
        changed = flips(self.board, r, c, BLACK)
        if not changed:
            return
        self.board = play(self.board, (r, c, changed), BLACK)
        self.passes = 0
        self.turn = WHITE
        self.advance()

    def advance(self):
        if not moves(self.board, self.turn):
            self.passes += 1
            if self.passes >= 2:
                self.finish()
                return
            skipped = "你没有合法位置，自动跳过。" if self.turn == BLACK else "电脑没有合法位置，自动跳过。"
            self.turn = -self.turn
            self.draw()
            self.status.config(text=skipped + "  " + self.status.cget("text").split("     ")[-1])
        if self.turn == WHITE:
            self.thinking = True
            self.draw()
            self.root.after(350, self.do_computer_turn)
        else:
            self.draw()

    def do_computer_turn(self):
        move = computer_move(self.board)
        self.thinking = False
        if move:
            self.board = play(self.board, move, WHITE)
            self.passes = 0
        self.turn = BLACK
        self.advance()

    def finish(self):
        self.thinking = False
        self.draw()
        black, white = self.counts()
        result = "你赢了！" if black > white else "电脑赢了！" if white > black else "平局！"
        self.status.config(text=f"对局结束：{result}     ● {black}   ○ {white}")
        messagebox.showinfo("对局结束", f"{result}\n\n黑棋：{black} 枚    白棋：{white} 枚", parent=self.root)

    def restart(self):
        self.board = initial_board()
        self.turn = BLACK
        self.passes = 0
        self.thinking = False
        self.draw()


if __name__ == "__main__":
    window = tk.Tk()
    Reversi(window)
    window.mainloop()
