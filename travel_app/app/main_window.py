"""主窗口。

用 QStackedWidget 承载三个页面：
- 首页：欢迎信息 +「我的行程」入口按钮。
- 行程页：行程列表（查看 / 新建 / 编辑 / 删除 / 切换状态 / 双击进详情）。
- 详情页：单条行程的完整信息 + 编辑入口。
界面文案通过 i18n 取得，支持中英切换。
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAction,
    QDesktopWidget,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import i18n
from app.storage.trip_store import TripStore
from app.views.trip_detail_page import TripDetailPage
from app.views.trips_page import TripsPage


class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self._store = TripStore()
        self._build_ui()
        self._retranslate_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setMinimumSize(480, 360)
        self._center_on_screen()

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # ---- 首页 ----
        self.home_page = QWidget(self)
        home_layout = QVBoxLayout(self.home_page)
        home_layout.setContentsMargins(32, 32, 32, 32)
        home_layout.setSpacing(16)

        self.title_label = QLabel(self.home_page)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 26px; font-weight: 600; color: #1f2937;"
        )
        home_layout.addStretch(1)
        home_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.home_page)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("font-size: 14px; color: #6b7280;")
        home_layout.addWidget(self.subtitle_label)
        home_layout.addStretch(2)

        # “我的行程”主交互按钮
        self.my_trips_btn = QPushButton(self.home_page)
        self.my_trips_btn.setCursor(Qt.PointingHandCursor)
        self.my_trips_btn.setMinimumHeight(56)
        self.my_trips_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
            """
        )
        self.my_trips_btn.clicked.connect(self._on_my_trips_clicked)
        home_layout.addWidget(self.my_trips_btn)
        home_layout.addStretch(1)

        # ---- 行程页 ----
        self.trips_page = TripsPage(self._store, self)
        self.trips_page.back_clicked.connect(self._show_home)
        self.trips_page.view_detail.connect(self._show_detail)

        # ---- 详情页 ----
        self.detail_page = TripDetailPage(self._store, self)
        self.detail_page.back_clicked.connect(self._show_trips)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.trips_page)
        self.stack.addWidget(self.detail_page)
        self.stack.setCurrentWidget(self.home_page)

        # 顶部菜单：语言切换
        menu = self.menuBar().addMenu("☰")
        self.lang_action = QAction("", self)
        self.lang_action.triggered.connect(self._on_toggle_lang)
        menu.addAction(self.lang_action)

        # 状态栏
        self.statusBar().showMessage(i18n.t("status_ready"))

        # 定时器：每分钟自动刷新当前页行程状态（按日期派生）
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(60000)
        self._status_timer.timeout.connect(self._auto_refresh_status)
        self._status_timer.start()

    def _center_on_screen(self) -> None:
        self.resize(720, 540)
        screen = QDesktopWidget().availableGeometry(self)
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    # ------------------------------------------------------------- 页面切换
    def _show_home(self) -> None:
        self.stack.setCurrentWidget(self.home_page)
        self.statusBar().showMessage(i18n.t("status_ready"))

    def _show_trips(self) -> None:
        # 从详情返回时刷新列表（可能发生过编辑/状态变更）
        self.trips_page.refresh()
        self.stack.setCurrentWidget(self.trips_page)

    def _show_detail(self, trip_id: str) -> None:
        self.detail_page.show_trip(trip_id)
        self.stack.setCurrentWidget(self.detail_page)

    def _on_my_trips_clicked(self) -> None:
        """进入行程页并刷新数据。"""
        self.trips_page.refresh()
        self.stack.setCurrentWidget(self.trips_page)

    def _auto_refresh_status(self) -> None:
        """定时刷新当前页的行程状态（随日期自动派生）。"""
        current = self.stack.currentWidget()
        if current is self.trips_page:
            self.trips_page.refresh()
        elif current is self.detail_page:
            self.detail_page.refresh_current()

    # ------------------------------------------------------------- 文案刷新
    def _retranslate_ui(self) -> None:
        """根据当前语言刷新所有界面文案（首页 + 行程页 + 详情页）。"""
        self.setWindowTitle(i18n.t("app_title"))
        self.title_label.setText(i18n.t("greeting"))
        self.subtitle_label.setText(i18n.t("greeting_sub"))
        self.my_trips_btn.setText(i18n.t("btn_my_trips"))
        self.lang_action.setText(i18n.t("action_switch_lang"))
        self.trips_page.retranslate_ui()
        self.detail_page.retranslate_ui()
        if self.stack.currentWidget() is self.home_page:
            self.statusBar().showMessage(i18n.t("status_ready"))

    # ------------------------------------------------------------- 交互回调
    def _on_toggle_lang(self) -> None:
        """切换中英文，并刷新界面。"""
        i18n.toggle_lang()
        self._retranslate_ui()
