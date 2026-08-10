"""国际化（i18n）：中英双语文本支持。

通过一个统一的字典表管理所有界面文案，切换语言时只需修改当前语言标识，
所有控件即可重新取值刷新。后续新增功能时，把新文案加进 _STRINGS 即可。
"""

from __future__ import annotations

# 支持的语言
LANG_ZH = "zh"
LANG_EN = "en"
SUPPORTED_LANGS = (LANG_ZH, LANG_EN)

# 所有界面文案集中在此维护：key -> {语言: 文案}
_STRINGS: dict[str, dict[str, str]] = {
    "app_title": {
        LANG_ZH: "行程助手",
        LANG_EN: "Travel Assistant",
    },
    "greeting": {
        LANG_ZH: "欢迎来到行程助手",
        LANG_EN: "Welcome to Travel Assistant",
    },
    "greeting_sub": {
        LANG_ZH: "更多功能即将上线，敬请期待",
        LANG_EN: "More features coming soon, stay tuned",
    },
    "btn_my_trips": {
        LANG_ZH: "我的行程",
        LANG_EN: "My Trips",
    },
    "coming_soon_title": {
        LANG_ZH: "功能开发中",
        LANG_EN: "Coming Soon",
    },
    "coming_soon_msg": {
        LANG_ZH: "“我的行程”功能正在开发中，敬请期待。",
        LANG_EN: "The “My Trips” feature is under development. Stay tuned.",
    },
    "btn_ok": {
        LANG_ZH: "好的",
        LANG_EN: "OK",
    },
    "action_switch_lang": {
        LANG_ZH: "EN",
        LANG_EN: "中",
    },
    "status_ready": {
        LANG_ZH: "就绪",
        LANG_EN: "Ready",
    },
    # ---- 行程列表页 ----
    "page_trips_title": {
        LANG_ZH: "我的行程",
        LANG_EN: "My Trips",
    },
    "btn_back": {
        LANG_ZH: "← 返回",
        LANG_EN: "← Back",
    },
    "btn_new_trip": {
        LANG_ZH: "新建行程",
        LANG_EN: "New Trip",
    },
    "btn_delete": {
        LANG_ZH: "删除",
        LANG_EN: "Delete",
    },
    "empty_trips": {
        LANG_ZH: "还没有行程，点击「新建行程」开始记录吧",
        LANG_EN: "No trips yet. Click “New Trip” to start planning.",
    },
    "confirm_delete_title": {
        LANG_ZH: "删除行程",
        LANG_EN: "Delete Trip",
    },
    "confirm_delete_msg": {
        LANG_ZH: "确定要删除这条行程吗？此操作不可撤销。",
        LANG_EN: "Are you sure you want to delete this trip? This cannot be undone.",
    },
    "status_trip_added": {
        LANG_ZH: "已添加行程",
        LANG_EN: "Trip added",
    },
    "status_trip_deleted": {
        LANG_ZH: "已删除行程",
        LANG_EN: "Trip deleted",
    },
    "status_select_to_delete": {
        LANG_ZH: "请先选中要删除的行程",
        LANG_EN: "Select a trip to delete first",
    },
    "status_no_trip_selected": {
        LANG_ZH: "未选中行程",
        LANG_EN: "No trip selected",
    },
    "list_date_range": {
        LANG_ZH: "{start} 至 {end}",
        LANG_EN: "{start} – {end}",
    },
    "list_destination_label": {
        LANG_ZH: "目的地",
        LANG_EN: "Destination",
    },
    # ---- 新建行程表单 ----
    "form_dialog_title_new": {
        LANG_ZH: "新建行程",
        LANG_EN: "New Trip",
    },
    "form_title": {
        LANG_ZH: "行程标题",
        LANG_EN: "Trip Title",
    },
    "form_destination": {
        LANG_ZH: "目的地",
        LANG_EN: "Destination",
    },
    "form_destination_placeholder": {
        LANG_ZH: "输入城市名自动匹配，如“长沙”",
        LANG_EN: "Type a city to auto-match, e.g. “Changsha”",
    },
    "form_start": {
        LANG_ZH: "出发日期",
        LANG_EN: "Start Date",
    },
    "form_end": {
        LANG_ZH: "结束日期",
        LANG_EN: "End Date",
    },
    "form_title_required": {
        LANG_ZH: "请填写行程标题",
        LANG_EN: "Please enter a trip title",
    },
    "form_end_before_start": {
        LANG_ZH: "结束日期不能早于出发日期",
        LANG_EN: "End date must not be earlier than start date",
    },
    "form_validation_title": {
        LANG_ZH: "输入有误",
        LANG_EN: "Invalid Input",
    },
    "btn_confirm": {
        LANG_ZH: "确定",
        LANG_EN: "OK",
    },
    "btn_cancel": {
        LANG_ZH: "取消",
        LANG_EN: "Cancel",
    },
    # ---- 行程状态 ----
    "status_planned": {
        LANG_ZH: "未开始",
        LANG_EN: "Planned",
    },
    "status_ongoing": {
        LANG_ZH: "进行中",
        LANG_EN: "Ongoing",
    },
    "status_completed": {
        LANG_ZH: "已完成",
        LANG_EN: "Completed",
    },
    "btn_edit": {
        LANG_ZH: "编辑",
        LANG_EN: "Edit",
    },
    "form_dialog_title_edit": {
        LANG_ZH: "编辑行程",
        LANG_EN: "Edit Trip",
    },
    "status_trip_updated": {
        LANG_ZH: "已更新行程",
        LANG_EN: "Trip updated",
    },
    # ---- 行程详情页 ----
    "page_detail_title": {
        LANG_ZH: "行程详情",
        LANG_EN: "Trip Details",
    },
    "detail_title": {
        LANG_ZH: "标题",
        LANG_EN: "Title",
    },
    "detail_destination": {
        LANG_ZH: "目的地",
        LANG_EN: "Destination",
    },
    "detail_start": {
        LANG_ZH: "出发日期",
        LANG_EN: "Start Date",
    },
    "detail_end": {
        LANG_ZH: "结束日期",
        LANG_EN: "End Date",
    },
    "detail_status": {
        LANG_ZH: "状态",
        LANG_EN: "Status",
    },
    "detail_not_found": {
        LANG_ZH: "未找到该行程",
        LANG_EN: "Trip not found",
    },
}

# 当前语言（运行时可切换）
_current_lang: str = LANG_ZH


def get_lang() -> str:
    """返回当前语言。"""
    return _current_lang


def set_lang(lang: str) -> None:
    """切换当前语言。"""
    if lang not in SUPPORTED_LANGS:
        raise ValueError(f"不支持的语言: {lang}")
    global _current_lang
    _current_lang = lang


def toggle_lang() -> str:
    """在中文/英文之间切换，返回切换后的语言。"""
    set_lang(LANG_EN if _current_lang == LANG_ZH else LANG_ZH)
    return _current_lang


def t(key: str) -> str:
    """根据 key 和当前语言取文案。key 不存在时原样返回。"""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_current_lang, entry.get(LANG_ZH, key))
