"""行程详情页。

展示单条行程的完整信息，提供返回与编辑入口。
通过 back_clicked 信号通知主窗口返回行程列表。
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import i18n
from app.models.trip import Trip
from app.storage.trip_store import TripStore
from app.views.trip_form_dialog import TripFormDialog


class TripDetailPage(QWidget):
    """行程详情页。"""

    back_clicked = pyqtSignal()

    def __init__(self, store: TripStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._trip: Optional[Trip] = None
        self._build_ui()
        self.retranslate_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # 顶栏：返回 + 标题 + 编辑
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

        self.edit_btn = QPushButton(self)
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: #fff; padding: 6px 16px;"
            " border: none; border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        self.edit_btn.clicked.connect(self._on_edit)
        top.addWidget(self.edit_btn)
        root.addLayout(top)

        # 详情卡片
        self.trip_title_value = QLabel(self)
        self.destination_value = QLabel(self)
        self.start_value = QLabel(self)
        self.end_value = QLabel(self)
        self.status_value = QLabel(self)
        self._field_labels = []  # 由 retranslate 填充左侧标签

        self.card = QWidget(self)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        self.card.setStyleSheet(
            "QWidget#card { background-color: #f9fafb; border: 1px solid #e5e7eb;"
            " border-radius: 10px; }"
        )
        self.card.setObjectName("card")

        self.rows = []
        for value_label in (
            self.trip_title_value,
            self.destination_value,
            self.start_value,
            self.end_value,
            self.status_value,
        ):
            row = QHBoxLayout()
            key_label = QLabel(self)
            key_label.setMinimumWidth(90)
            key_label.setStyleSheet("color: #6b7280; font-size: 14px;")
            value_label.setStyleSheet("color: #1f2937; font-size: 15px;")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row.addWidget(key_label)
            row.addWidget(value_label, 1)
            card_layout.addLayout(row)
            self.rows.append((key_label, value_label))

        root.addWidget(self.card)
        root.addStretch(1)

        self.not_found_label = QLabel(self)
        self.not_found_label.setAlignment(Qt.AlignCenter)
        self.not_found_label.setStyleSheet("color: #b91c1c; font-size: 15px;")
        root.addWidget(self.not_found_label)

    # ------------------------------------------------------------- 数据展示
    def show_trip(self, trip_id: str) -> None:
        """加载指定 id 的行程并展示。"""
        self._trip = self._store.get(trip_id)
        self._refresh_values()

    def refresh_current(self) -> None:
        """重新加载当前展示的行程（供定时器自动刷新状态用）。"""
        if self._trip is not None:
            self._trip = self._store.get(self._trip.id)
            self._refresh_values()
            self.retranslate_ui()

    def _refresh_values(self) -> None:
        found = self._trip is not None
        self.card.setVisible(found)
        self.not_found_label.setVisible(not found)
        if not found:
            return
        trip = self._trip
        self.trip_title_value.setText(trip.title)
        self.destination_value.setText(trip.destination or "—")
        self.start_value.setText(trip.start_date)
        self.end_value.setText(trip.end_date)
        self.status_value.setText(i18n.t("status_" + trip.status))

    # ------------------------------------------------------------- 文案刷新
    def retranslate_ui(self) -> None:
        self.back_btn.setText(i18n.t("btn_back"))
        self.title_label.setText(i18n.t("page_detail_title"))
        self.edit_btn.setText(i18n.t("btn_edit"))
        self.not_found_label.setText(i18n.t("detail_not_found"))
        keys = (
            "detail_title",
            "detail_destination",
            "detail_start",
            "detail_end",
            "detail_status",
        )
        for (key_label, _), key in zip(self.rows, keys):
            key_label.setText(i18n.t(key))
        if self._trip is not None:
            self.status_value.setText(i18n.t("status_" + self._trip.status))

    # ------------------------------------------------------------- 交互回调
    def _on_edit(self) -> None:
        if self._trip is None:
            return
        dialog = TripFormDialog(self, trip=self._trip)
        if dialog.exec_() == TripFormDialog.Accepted:
            updated = Trip(id=self._trip.id, **dialog.get_data())
            self._store.update(updated)
            self._trip = updated
            self._refresh_values()
            self._notify_status(i18n.t("status_trip_updated"))

    def _notify_status(self, message: str) -> None:
        window = self.window()
        status_bar = getattr(window, "statusBar", None)
        if callable(status_bar):
            status_bar().showMessage(message)
