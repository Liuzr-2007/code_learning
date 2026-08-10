"""行程列表页。

展示已保存的行程，支持新建、编辑、删除、切换状态，以及双击进入详情页。
通过 back_clicked 信号通知主窗口返回首页，view_detail(trip_id) 信号请求打开详情页。
"""

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import i18n
from app.models.trip import Trip
from app.storage.trip_store import TripStore
from app.views.trip_form_dialog import TripFormDialog


class TripsPage(QWidget):
    """「我的行程」列表页。"""

    back_clicked = pyqtSignal()
    view_detail = pyqtSignal(str)  # 请求打开某条行程的详情页

    def __init__(self, store: TripStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._trips: List[Trip] = []
        self._build_ui()
        self.retranslate_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # 顶栏：返回 + 标题
        top = QHBoxLayout()
        top.setSpacing(10)
        self.back_btn = QPushButton(self)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(
            "QPushButton { border: none; color: #2563eb; font-size: 15px; }"
            "QPushButton:hover { color: #1d4ed8; }"
        )
        self.back_btn.clicked.connect(self.back_clicked)
        top.addWidget(self.back_btn)

        self.title_label = QLabel(self)
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #1f2937;"
        )
        top.addWidget(self.title_label)
        top.addStretch(1)
        root.addLayout(top)

        # 工具栏：新建 / 编辑 / 切换状态 / 删除
        toolbar = QHBoxLayout()
        toolbar.addStretch(1)
        self.new_btn = self._make_primary_btn()
        self.new_btn.clicked.connect(self._on_new)
        toolbar.addWidget(self.new_btn)

        self.edit_btn = self._make_ghost_btn()
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = self._make_danger_btn()
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)
        root.addLayout(toolbar)

        # 列表
        self.list_widget = QListWidget(self)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet(
            "QListWidget { border: 1px solid #e5e7eb; border-radius: 8px;"
            " font-size: 15px; }"
            "QListWidget::item { padding: 10px 12px; }"
            "QListWidget::item:alternate { background-color: #f9fafb; }"
        )
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        root.addWidget(self.list_widget, 1)

        # 空状态提示
        self.empty_label = QLabel(self)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #9ca3af; font-size: 14px;")
        root.addWidget(self.empty_label)

    def _make_primary_btn(self) -> QPushButton:
        btn = QPushButton(self)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: #fff; padding: 6px 16px;"
            " border: none; border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        return btn

    def _make_ghost_btn(self) -> QPushButton:
        btn = QPushButton(self)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: #f3f4f6; color: #374151; padding: 6px 16px;"
            " border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #e5e7eb; }"
        )
        return btn

    def _make_danger_btn(self) -> QPushButton:
        btn = QPushButton(self)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: #f3f4f6; color: #b91c1c; padding: 6px 16px;"
            " border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #fee2e2; }"
        )
        return btn

    # ------------------------------------------------------------- 数据刷新
    def refresh(self) -> None:
        """从 store 重新加载行程并刷新列表显示。保留当前选中项。"""
        selected_id = None
        current = self.list_widget.currentItem()
        if current is not None:
            selected_id = current.data(Qt.UserRole)

        self._trips = self._store.load_all()
        self.list_widget.clear()
        for trip in self._trips:
            item = QListWidgetItem(self._format_trip(trip))
            item.setData(Qt.UserRole, trip.id)
            self.list_widget.addItem(item)
            if trip.id == selected_id:
                self.list_widget.setCurrentItem(item)
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        empty = len(self._trips) == 0
        self.empty_label.setVisible(empty)
        self.list_widget.setVisible(not empty)

    def _format_trip(self, trip: Trip) -> str:
        date_range = i18n.t("list_date_range").format(
            start=trip.start_date, end=trip.end_date
        )
        dest_label = i18n.t("list_destination_label")
        dest = trip.destination or "—"
        status_label = i18n.t("status_" + trip.status)
        return f"{trip.title}  [{status_label}]\n{dest_label}: {dest}  ·  {date_range}"

    def _selected_trip(self) -> Optional[Trip]:
        current = self.list_widget.currentItem()
        if current is None:
            return None
        trip_id = current.data(Qt.UserRole)
        return next((t for t in self._trips if t.id == trip_id), None)

    # ------------------------------------------------------------- 文案刷新
    def retranslate_ui(self) -> None:
        self.back_btn.setText(i18n.t("btn_back"))
        self.title_label.setText(i18n.t("page_trips_title"))
        self.new_btn.setText(i18n.t("btn_new_trip"))
        self.edit_btn.setText(i18n.t("btn_edit"))
        self.delete_btn.setText(i18n.t("btn_delete"))
        self.empty_label.setText(i18n.t("empty_trips"))
        # 列表项文案依赖语言（状态/日期格式），需重绘
        for i, trip in enumerate(self._trips):
            item = self.list_widget.item(i)
            if item is not None:
                item.setText(self._format_trip(trip))

    # ------------------------------------------------------------- 交互回调
    def _on_new(self) -> None:
        dialog = TripFormDialog(self)
        if dialog.exec_() == TripFormDialog.Accepted:
            trip = Trip(**dialog.get_data())
            self._store.add(trip)
            self.refresh()
            self._notify_status(i18n.t("status_trip_added"))

    def _on_edit(self) -> None:
        trip = self._selected_trip()
        if trip is None:
            self._notify_status(i18n.t("status_no_trip_selected"))
            return
        dialog = TripFormDialog(self, trip=trip)
        if dialog.exec_() == TripFormDialog.Accepted:
            updated = Trip(id=trip.id, **dialog.get_data())
            self._store.update(updated)
            self.refresh()
            self._notify_status(i18n.t("status_trip_updated"))

    def _on_delete(self) -> None:
        current = self.list_widget.currentItem()
        if current is None:
            self._notify_status(i18n.t("status_select_to_delete"))
            return
        trip_id = current.data(Qt.UserRole)
        confirm = QMessageBox.question(
            self,
            i18n.t("confirm_delete_title"),
            i18n.t("confirm_delete_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self._store.delete(trip_id)
            self.refresh()
            self._notify_status(i18n.t("status_trip_deleted"))

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        trip_id = item.data(Qt.UserRole)
        if trip_id:
            self.view_detail.emit(trip_id)

    def _notify_status(self, message: str) -> None:
        """通过窗口状态栏提示操作结果。"""
        window = self.window()
        status_bar = getattr(window, "statusBar", None)
        if callable(status_bar):
            status_bar().showMessage(message)
