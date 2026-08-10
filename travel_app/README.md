# 行程助手 / Travel Assistant

一个用 PyQt5 实现的行程管理应用。当前版本仅包含主界面与一个“我的行程”交互按钮，其余功能待开发。界面支持中英双语切换。

## 目录结构

```
travel_app/
├── main.py              # 程序入口
├── requirements.txt     # 依赖
├── README.md
└── app/
    ├── __init__.py
    ├── i18n.py          # 中英双语文案集中管理
    └── main_window.py   # 主界面（含“我的行程”按钮）
```

## 安装与运行

```bash
pip install -r requirements.txt
python main.py
```

## 使用说明

- 主界面中央为“我的行程”按钮，点击后弹出占位提示（功能开发中）。
- 顶部菜单 ☰ 中的语言项可在中文 / English 之间切换，界面文案实时刷新。

## 后续扩展指引

- **新增文案**：在 `app/i18n.py` 的 `_STRINGS` 字典中增加 `key -> {zh, en}` 条目，控件处调用 `i18n.t("key")` 取值。
- **接入“我的行程”真实功能**：在 `main_window.py` 的 `_on_my_trips_clicked` 中替换占位逻辑，或跳转到新的行程列表页（建议新建 `app/views/trips_view.py`）。
- **新增主界面按钮**：在 `_build_ui` 中仿照 `my_trips_btn` 增加按钮，并在 `_retranslate_ui` 中补充文案刷新。
