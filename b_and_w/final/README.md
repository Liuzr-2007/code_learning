# 黑白棋（Reversi）

这是一个使用 Python 和 Tkinter 编写的图形界面黑白棋游戏。玩家执黑棋，电脑执白棋。游戏采用标准 8×8 黑白棋规则，并提供合法落子提示、自动跳过无棋可下的回合、胜负统计和重新开始功能。

## 运行方式

### 运行 Python 源码

需要安装 Python 3。Tkinter 通常随 Python 一起提供，不需要额外安装第三方 Python 库。

在项目文件夹打开终端，运行：

```bash
python b_and_w_game.py
```

### 运行 Windows 程序

已打包好的程序位于：

```text
dist/b_and_w_game.exe
```

双击 `b_and_w_game.exe` 即可启动。该 exe 是单文件程序，不需要另外安装 Python。

## 游戏操作

- 点击棋盘上的绿色提示点落子。提示点只显示当前玩家的合法位置。
- 玩家执黑棋，电脑执白棋。
- 落子必须夹住至少一枚对方棋子；被夹住的棋子会翻转为当前玩家的颜色。
- 如果一方没有合法落点，游戏会自动跳过该方回合。
- 双方都没有合法落点时游戏结束，棋子较多的一方获胜。
- 点击“重新开始”可以开始新的一局。

## 电脑 AI

电脑使用快速启发式评分选择落点，逻辑位于 `b_and_w_game.py` 的 `computer_move(board)` 函数中：

1. 先列出白棋所有合法落点。
2. 根据棋盘位置表评分，优先选择角落和边缘等有利位置。
3. 对每枚能翻转的棋子加少量分数。
4. 如果角落仍为空，对紧邻该角落的位置扣分，降低把角落机会让给玩家的风险。
5. 选择总分最高的合法落点；分数相同或接近时加入很小的随机值，让走法略有变化。

这是轻量级启发式 AI，不是 MCTS 或深度搜索，因此响应很快，但不会提前模拟多回合棋局。

## 重新打包 exe

需要安装 PyInstaller：

```bash
python -m pip install pyinstaller
```

然后在项目文件夹运行：

```bash
python -m PyInstaller --noconfirm --clean --onefile --windowed --name b_and_w_game b_and_w_game.py
```

生成的程序会放在 `dist/b_and_w_game.exe`。

## 项目文件

- `b_and_w_game.py`：图形界面游戏源码。
- `dist/b_and_w_game.exe`：已打包的 Windows 可执行程序。
- `b_and_w.py`：原有的命令行版本源码。
- `b_and_w.sln`、`b_and_w.pyproj`：原有 Visual Studio Python 项目文件。
