# -*- coding: utf-8 -*-
"""
桌面宠物 —— 用一张精灵图(sprite sheet)制作。
图中有多个小人，代表不同运动状态。程序自动检测网格、切出每一帧，
按行分组为不同动画状态(idle/walk/happy/sleep)，宠物在不同行为下播放对应动画。

行为：
  - 空闲：播放 idle 行
  - 自动走动 / 拖拽中：播放 walk 行，按方向左右翻转，水平移动
  - 喂食(右键)：播放一次 happy 行，然后回到原状态
  - 休息(右键)：播放 sleep 行，点击宠物可唤醒
  - 松手：受重力下落到屏幕底部并小弹跳
  - 右键菜单 / 双击切换自动走动 / 说话气泡

透明：tkinter -transparentcolor 把“魔色”品红变透明并点击穿透，
所以先把精灵图背景(深色)抠除，背景区域填成魔色。
"""

import os
import sys
import random
import statistics
import ctypes
from ctypes import wintypes
from collections import deque

import tkinter as tk
from PIL import Image, ImageTk, ImageFilter

# ---------------- Win32 窗口检测(ctypes，无需 pywin32) ----------------
_user32 = ctypes.windll.user32
GA_ROOT = 2
_DESKTOP_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd"}  # 桌面/任务栏，不当落脚点

_user32.WindowFromPoint.argtypes = [wintypes.POINT]
_user32.WindowFromPoint.restype = wintypes.HWND
_user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetAncestor.restype = wintypes.HWND
_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetClassNameW.restype = ctypes.c_int
_ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_ENUMPROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL


def _get_rect(hwnd):
    r = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def _get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    _user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _root_at(x, y):
    """屏幕坐标 (x,y) 处最上层可见窗口的顶层句柄。"""
    pt = wintypes.POINT(x, y)
    hwnd = _user32.WindowFromPoint(pt)
    if not hwnd:
        return 0
    root = _user32.GetAncestor(hwnd, GA_ROOT)
    return root or hwnd


def _enum_windows():
    out = []

    def cb(hwnd, _):
        if _user32.IsWindowVisible(hwnd):
            out.append(hwnd)
        return True

    _user32.EnumWindows(_ENUMPROC(cb), 0)
    return out

# ---------------- 配置 ----------------
def _resource_path(name):
    """兼容 PyInstaller 打包：打包后资源在 sys._MEIPASS，否则在脚本目录。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


SOURCE = _resource_path("sprite.png")
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
PET_HEIGHT = 175            # 显示高度
ENHANCE = True              # 是否锐化增强清晰度
ENHANCE_SCALE = 2           # 放大倍数(先放大再缩到显示尺寸，保留更多细节)
SHARPEN_RADIUS = 1.3
SHARPEN_PERCENT = 150
SHARPEN_THRESHOLD = 3
MAGIC = (255, 0, 255)
MAGIC_HEX = "#ff00ff"
TASKBAR_MARGIN = 60

# 动作定义：行号(0起) / 水平移动方向(+1右 -1左 0原地) / 帧间隔(ms)
#   row1 = 向右走动画, row2 = 向左走动画(直接播放对应行，不翻转)
#   row0 已弃用，不再播放；启动默认播放 row3 (act3)
ACTIONS = {
    "walk_right": {"row": 1, "move": 1,  "interval": 90},
    "walk_left":  {"row": 2, "move": -1, "interval": 90},
    "act3":       {"row": 3, "move": 0,  "interval": 300},
    "act4":       {"row": 4, "move": 0,  "interval": 300},
    "act5":       {"row": 5, "move": 0,  "interval": 300},
    "act6":       {"row": 6, "move": 0,  "interval": 300},
    "sleep":      {"row": 7, "move": 0,  "interval": 1500},
    "happy":      {"row": 8, "move": 0,  "interval": 110},
}
DEFAULT_ACTION = "act3"     # 启动默认动作(row3)
# 自主随机切换的动作池(每隔 ACTION_SWITCH_MIN~MAX 秒挑一个)
RANDOM_POOL = ["walk_right", "walk_left", "act3", "act4", "act5", "act6", "happy", "sleep"]
ACTION_SWITCH_MIN = 30    # 秒
ACTION_SWITCH_MAX = 120   # 秒
WALK_SPEED = 5            # 走动时每帧像素

SPEECHES = ["在呢~", "想我啦？", "今天也要加油哦！", "嗷呜~", "陪我玩一会儿嘛",
            "咕咕咕…", "好困哦 zzz", "戳我干嘛(•́ω•̀)", "抱抱~", "你是最棒的！"]
FEED_LINES = ["谢谢投喂！好吃~", "嗝~", "再来一口嘛", "幸福~"]
SLEEP_LINES = ["呼……zZ", "困了，先睡了", "晚安~"]


# ---------------- 精灵图切割 ----------------
def _grid_detect(im, px, bg, tol=22, min_area=6000):
    """检测精灵图网格，返回 (col_centers, row_centers, fg_mask, good_cells)。"""
    w, h = im.size
    isbg = [[True] * w for _ in range(h)]
    for y in range(h):
        row = isbg[y]
        for x in range(w):
            c = px[x, y]
            if not (abs(c[0] - bg[0]) <= tol and abs(c[1] - bg[1]) <= tol
                    and abs(c[2] - bg[2]) <= tol):
                row[x] = False
    # 连通区域
    seen = [[False] * w for _ in range(h)]
    good = []
    for y in range(h):
        for x in range(w):
            if isbg[y][x] or seen[y][x]:
                continue
            dq = deque([(x, y)]); seen[y][x] = True
            mnx = mxx = x; mny = mxy = y; cnt = 0
            while dq:
                cx, cy = dq.popleft(); cnt += 1
                if cx < mnx: mnx = cx
                if cx > mxx: mxx = cx
                if cy < mny: mny = cy
                if cy > mxy: mxy = cy
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not isbg[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True; dq.append((nx, ny))
            bw, bh = mxx - mnx + 1, mxy - mny + 1
            if 70 <= bw <= 120 and 120 <= bh <= 150 and cnt >= min_area:
                good.append((mnx, mny, mxx, mxy))

    def cluster(vals, gap=40):
        vals = sorted(vals); groups = []
        for v in vals:
            if not groups or abs(v - statistics.mean(groups[-1])) > gap:
                groups.append([v])
            else:
                groups[-1].append(v)
        return [int(statistics.mean(g)) for g in groups]

    col_centers = cluster([(c[0] + c[2]) // 2 for c in good])
    row_centers = cluster([(c[1] + c[3]) // 2 for c in good])
    return col_centers, row_centers, isbg, good


def extract_states(path):
    """
    返回 dict: state_name -> list[PIL.Image] (统一画布，魔色背景)。
    同一行的帧 = 一个动画状态。每帧按脚底中心对齐到画布底部中央。
    """
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    border = []
    for x in range(w):
        border.append(px[x, 0]); border.append(px[x, h - 1])
    for y in range(h):
        border.append(px[0, y]); border.append(px[w - 1, y])
    bg = tuple(int(statistics.median(c[i] for c in border)) for i in range(3))

    col_centers, row_centers, isbg, good = _grid_detect(im, px, bg)
    if not good:
        print("未能从精灵图中检测到小人！")
        sys.exit(1)

    # 计算统一画布大小
    maxw = max(c[2] - c[0] + 1 for c in good)
    maxh = max(c[3] - c[1] + 1 for c in good)
    pad = 6
    cw, ch = maxw + pad * 2, maxh + pad * 2

    def nearest(val, centers):
        return min(range(len(centers)), key=lambda i: abs(centers[i] - val))

    # 每行收集帧（保留原图颜色，含原背景；缩放后再抠背景，避免插值产生魔色毛边）
    rows = {ri: [] for ri in range(len(row_centers))}
    for (mnx, mny, mxx, mxy) in good:
        cx = (mnx + mxx) // 2; cy = (mny + mxy) // 2
        ci = nearest(cx, col_centers); ri = nearest(cy, row_centers)
        frame = im.crop((mnx, mny, mxx + 1, mxy + 1))  # 原色裁剪
        rows[ri].append(frame)

    # 每行按列排序，放到统一画布(填原背景色)，脚底对齐
    states = {}
    for ri, frames in rows.items():
        if not frames:
            continue
        canvas_list = []
        for f in frames:
            cv = Image.new("RGB", (cw, ch), bg)
            ox = (cw - f.width) // 2
            oy = ch - f.height - pad  # 脚底贴底
            cv.paste(f, (ox, oy))
            canvas_list.append(cv)
        states[ri] = canvas_list

    return states, bg


def _figure_mask(img, bg, tol=26):
    """在全分辨率下计算角色遮罩('1' 图像：角色=1，背景=0)。
    flood-fill 从四边抠除连通背景(含内部孔洞)，再腐蚀外圈 1 像素抗锯齿环。
    在全分辨率做这一步，抗锯齿只有 1px，腐蚀可完全清除 -> 干净硬边。"""
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()
    bgcand = [[(abs(px[x, y][0] - bg[0]) <= tol and
                abs(px[x, y][1] - bg[1]) <= tol and
                abs(px[x, y][2] - bg[2]) <= tol) for x in range(w)] for y in range(h)]
    remove = [[False] * w for _ in range(h)]
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bgcand[y][x] and not remove[y][x]:
                remove[y][x] = True; dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if bgcand[y][x] and not remove[y][x]:
                remove[y][x] = True; dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and bgcand[ny][nx] and not remove[ny][nx]:
                remove[ny][nx] = True; dq.append((nx, ny))
    # 腐蚀角色外圈 1 像素(抗锯齿过渡色)
    er = [row[:] for row in remove]
    for y in range(h):
        for x in range(w):
            if remove[y][x]:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and remove[ny][nx]:
                    er[y][x] = True
                    break
    mask = Image.new("1", (w, h), 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            if not er[y][x]:
                mp[x, y] = 1
    return mask


def build_photo_states():
    """返回 (action_name->[PhotoImage...], display_size)。每个动作对应精灵图一行。"""
    states, bg = extract_states(SOURCE)
    # 行号 -> 动作名(以 ACTIONS 为准；未列出的行作为 actN 备用)
    name_by_row = {}
    for name, info in ACTIONS.items():
        if info["row"] in states:
            name_by_row[info["row"]] = name
    for ri in states:
        name_by_row.setdefault(ri, "row%d" % ri)

    sample = states[next(iter(states))][0]
    scale = PET_HEIGHT / sample.height
    disp_w = max(1, int(sample.width * scale))
    disp_h = PET_HEIGHT

    photo_states = {}
    for ri, frames in states.items():
        name = name_by_row.get(ri, "row%d" % ri)
        plist = []
        for cv in frames:
            # 1) 全分辨率抠图遮罩(flood-fill + 腐蚀 1px，干净硬边)
            mask_full = _figure_mask(cv, bg)
            # 2) 角色内部：放大+锐化(清晰)；遮罩边缘不参与缩放，避免光晕
            if ENHANCE:
                big = cv.resize((cv.width * ENHANCE_SCALE, cv.height * ENHANCE_SCALE),
                                Image.LANCZOS)
                fig = big.resize((disp_w, disp_h), Image.LANCZOS)
                fig = fig.filter(ImageFilter.UnsharpMask(
                    radius=SHARPEN_RADIUS, percent=SHARPEN_PERCENT,
                    threshold=SHARPEN_THRESHOLD))
            else:
                fig = cv.resize((disp_w, disp_h), Image.LANCZOS)
            # 3) 遮罩用 NEAREST 放大到显示尺寸 -> 保持硬边，无毛边/光晕
            mask_disp = mask_full.resize((disp_w, disp_h), Image.NEAREST)
            # 4) 合成：遮罩外填魔色(透明)
            out = Image.new("RGB", (disp_w, disp_h), MAGIC)
            op = out.load(); fp = fig.load(); mp = mask_disp.load()
            for y in range(disp_h):
                for x in range(disp_w):
                    if mp[x, y]:
                        op[x, y] = fp[x, y]
            plist.append(ImageTk.PhotoImage(out))
        photo_states[name] = plist
    return photo_states, (disp_w, disp_h)


# ---------------- 宠物主类 ----------------
class Pet:
    def __init__(self, root, photo_states, disp_size):
        self.root = root
        self.photos = photo_states
        self.disp_w, self.disp_h = disp_size

        self.action = DEFAULT_ACTION
        self.frame_idx = 0
        self.drag_data = None
        self.falling = False
        self.speech_top = None
        self._timer = None
        self._switch_timer = None
        # 落脚状态：是否站在某窗口上沿，以及该窗口句柄/上沿 y(脚底坐标)
        self.on_window = False
        self.support_hwnd = None
        self.support_feet = 0
        # 只把素材里真实存在的动作加入随机池
        self.pool = [a for a in RANDOM_POOL if a in self.photos]

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.screen_w = sw
        self.screen_h = sh
        self.ground_feet = sh - TASKBAR_MARGIN          # 地面(脚底) y
        self.ground_y = self.ground_feet - self.disp_h   # 地面时宠物顶端 y
        self.x = sw // 2 - self.disp_w // 2
        self.y = self.ground_y
        self.support_feet = self.ground_feet

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.config(bg=MAGIC_HEX)
        root.wm_attributes("-transparentcolor", MAGIC_HEX)
        root.geometry("{}x{}+{}+{}".format(self.disp_w, self.disp_h, self.x, self.y))
        root.update_idletasks()
        # 自身窗口句柄(枚举/可见性判断时排除)
        self.root_hwnd = _user32.GetAncestor(root.winfo_id(), GA_ROOT) or root.winfo_id()

        self.label = tk.Label(root, image=self.photos[self.action][0],
                              bg=MAGIC_HEX, borderwidth=0, highlightthickness=0)
        self.label.pack()

        self.label.bind("<ButtonPress-1>", self.on_press)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        self.label.bind("<Double-Button-1>", self.on_double)
        self.label.bind("<ButtonPress-3>", self.on_right)

        self._tick()
        self._schedule_next_switch()

    # ---- 动作信息 ----
    def _info(self, action):
        return ACTIONS.get(action, {"move": 0, "interval": 400})

    # ---- 显示 ----
    def move_to(self, x, y):
        self.x = int(x); self.y = int(y)
        self.root.geometry("+{}+{}".format(self.x, self.y))

    # ---- 主循环：动画 + 走动 ----
    def _tick(self):
        frames = self.photos[self.action]
        idx = self.frame_idx % len(frames)
        self.label.config(image=frames[idx])
        self.frame_idx += 1

        if not self.drag_data and not self.falling:
            mv = self._info(self.action)["move"]
            if mv != 0:
                nx = self.x + WALK_SPEED * mv
                if nx <= 0 or nx + self.disp_w >= self.screen_w:
                    # 撞到屏幕边：贴边并换一个随机动作
                    self.x = max(0, min(self.screen_w - self.disp_w, nx))
                    self.move_to(self.x, self.y)
                    self.pick_random_action()
                elif self.on_window:
                    foot_x = nx + self.disp_w // 2
                    top, hwnd = self._surface_below(foot_x, self.support_feet)
                    if top == self.support_feet and hwnd == self.support_hwnd:
                        self.move_to(nx, self.y)            # 沿窗口上沿走
                    else:
                        # 走到窗口边缘外 -> 自然掉落
                        self.move_to(nx, self.y)
                        self.on_window = False
                        self._fall()
                else:
                    self.move_to(nx, self.y)
            elif self.on_window:
                # 原地动作时也检查落脚窗口是否还在(可能被关闭/移走)
                foot_x = self.x + self.disp_w // 2
                top, hwnd = self._surface_below(foot_x, self.support_feet)
                if not (top == self.support_feet and hwnd == self.support_hwnd):
                    self.on_window = False
                    self._fall()

        interval = self._info(self.action).get("interval", 400)
        self._timer = self.root.after(interval, self._tick)

    # ---- 窗口上沿检测 ----
    def _surface_below(self, foot_x, feet_y):
        """返回 (落脚脚底 y, hwnd)：foot_x 处、feet_y 之下最近的可见窗口上沿；
        没有则返回 (ground_feet, None)。"""
        best_top = None
        best_hwnd = None
        for hwnd in _enum_windows():
            if hwnd == self.root_hwnd:
                continue
            if _get_class(hwnd) in _DESKTOP_CLASSES:
                continue
            l, t, r, b = _get_rect(hwnd)
            if r <= l or b <= t:
                continue
            if not (l <= foot_x <= r):
                continue
            if t < feet_y - 2:                # 上沿必须在脚底下方
                continue
            probe_y = min(t + 4, b - 1)       # 在上沿稍下方取样，避开自身遮挡
            if _root_at(foot_x, probe_y) != hwnd:
                continue                      # 该位置被别的窗口遮住，不可落脚
            if best_top is None or t < best_top:
                best_top = t
                best_hwnd = hwnd
        if best_top is None:
            return (self.ground_feet, None)
        return (best_top, best_hwnd)

    # ---- 随机动作切换 ----
    def _schedule_next_switch(self):
        delay = random.randint(ACTION_SWITCH_MIN, ACTION_SWITCH_MAX) * 1000
        self._switch_timer = self.root.after(delay, self.pick_random_action)

    def pick_random_action(self):
        if not self.pool:
            return
        choices = [a for a in self.pool if a != self.action] or self.pool
        self.set_action(random.choice(choices))

    def set_action(self, action):
        if action not in self.photos:
            action = DEFAULT_ACTION if DEFAULT_ACTION in self.photos else (self.pool[0] if self.pool else action)
        self.action = action
        self.frame_idx = 0

    # ---- 拖拽 ----
    def on_press(self, e):
        if self.action == "sleep":
            self.set_action(DEFAULT_ACTION)
            self.say("醒啦~")
        self.drag_data = (e.x_root - self.x, e.y_root - self.y)
        self.falling = False
        self.on_window = False        # 被抓起，脱离当前落脚面

    def on_drag(self, e):
        if self.drag_data:
            self.move_to(e.x_root - self.drag_data[0], e.y_root - self.drag_data[1])

    def on_release(self, e):
        self.drag_data = None
        self._fall()

    # ---- 重力下落：落到下方最近的窗口上沿或地面 ----
    def _fall(self):
        if self.falling:
            return
        self.falling = True
        foot_x = self.x + self.disp_w // 2
        start_feet = self.y + self.disp_h
        target_feet, target_hwnd = self._surface_below(foot_x, start_feet)
        vy = [0.0]
        g = 1.4

        def step():
            if not self.falling:
                return
            vy[0] = min(vy[0] + g, 34)
            ny = self.y + vy[0]
            if ny + self.disp_h >= target_feet:
                self.move_to(self.x, target_feet - self.disp_h)
                if vy[0] > 6:                      # 落地反弹
                    vy[0] = -vy[0] * 0.32
                    self.root.after(16, step)
                else:
                    self.falling = False
                    self._land(target_feet, target_hwnd)
                return
            self.move_to(self.x, ny)
            self.root.after(16, step)

        step()

    def _land(self, feet, hwnd):
        if hwnd is None or hwnd == 0:
            self.on_window = False
            self.support_hwnd = None
            self.support_feet = self.ground_feet
        else:
            self.on_window = True
            self.support_hwnd = hwnd
            self.support_feet = feet

    # ---- 双击：立刻换动作 ----
    def on_double(self, e):
        self.pick_random_action()
        self.say("换个动作~")

    # ---- 说话气泡 ----
    def say(self, text):
        if self.speech_top is not None:
            try: self.speech_top.destroy()
            except tk.TclError: pass
        b = tk.Toplevel(self.root)
        b.overrideredirect(True)
        b.attributes("-topmost", True)
        lbl = tk.Label(b, text=text, bg="#fff8c4", fg="#333333",
                       font=("微软雅黑", 10), padx=10, pady=5,
                       borderwidth=1, relief="solid")
        lbl.pack()
        b.update_idletasks()
        bx = self.x + self.disp_w // 2 - b.winfo_width() // 2
        by = self.y - b.winfo_height() - 6
        b.geometry("+{}+{}".format(bx, by))
        self.speech_top = b
        def close():
            try: b.destroy()
            except tk.TclError: pass
            self.speech_top = None
        b.after(2500, close)

    # ---- 菜单行为 ----
    def feed(self):
        self.say(random.choice(FEED_LINES))
        self.set_action("happy")

    def sleep(self):
        self.set_action("sleep")
        self.say(random.choice(SLEEP_LINES))

    # ---- 右键菜单 ----
    def on_right(self, e):
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="🍖 喂食", command=self.feed)
        m.add_command(label="🎲 换个动作", command=self.pick_random_action)
        m.add_command(label="💤 休息", command=self.sleep)
        m.add_command(label="💬 说句话", command=lambda: self.say(random.choice(SPEECHES)))
        m.add_separator()
        m.add_command(label="ℹ️ 关于", command=lambda: self.say("桌面宠物 · 精灵图制作"))
        m.add_command(label="❌ 退出", command=self.quit)
        m.tk_popup(e.x_root, e.y_root)

    def quit(self):
        for t in (self._timer, self._switch_timer):
            if t:
                try: self.root.after_cancel(t)
                except Exception: pass
        self.root.destroy()


def main():
    root = tk.Tk()
    root.title("桌面宠物")
    photo_states, disp_size = build_photo_states()
    if DEFAULT_ACTION not in photo_states:
        # 兜底：默认动作缺失时用第一个可用动作顶替
        first = next(iter(photo_states))
        photo_states[DEFAULT_ACTION] = photo_states[first]
    Pet(root, photo_states, disp_size)
    root.mainloop()


if __name__ == "__main__":
    main()
