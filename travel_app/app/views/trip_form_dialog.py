"""行程表单对话框。

同时支持「新建」与「编辑」两种模式：
- 新建：不传 trip，字段为空。
- 编辑：传入已有 Trip，字段预填充，标题为「编辑行程」。

出发地与目的地均带地名自动补全（共享同一候选模型）。
行程状态由起止日期相对今天自动派生，故表单不收集状态字段；
保存时由 TripStore 按日期重算。
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QDate, QStringListModel, Qt, QTimer
from PyQt5.QtWidgets import (
    QCompleter,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
)

from app import i18n
from app.data.places import places_for
from app.models.trip import Trip
from app.views.map_view import MapViewWindow


class TripFormDialog(QDialog):
    """行程输入表单（新建 / 编辑）。"""

    def __init__(self, parent=None, trip: Optional[Trip] = None) -> None:
        super().__init__(parent)
        self._is_edit = trip is not None
        self._build_ui()
        self._map_preview = MapViewWindow("", "", self)
        self._map_preview.setMinimumHeight(230)
        layout = self.layout()
        layout.addWidget(self._map_preview, 1)
        self._map_update_timer = QTimer(self)
        self._map_update_timer.setSingleShot(True)
        self._map_update_timer.setInterval(500)
        self._map_update_timer.timeout.connect(self._refresh_map_preview)
        self.origin_edit.textChanged.connect(self._schedule_map_update)
        self.destination_edit.textChanged.connect(self._schedule_map_update)
        self.transport_combo.currentIndexChanged.connect(self._schedule_map_update)
        self.start_edit.dateChanged.connect(self._schedule_map_update)
        self.end_edit.dateChanged.connect(self._schedule_map_update)
        if trip is not None:
            self._prefill(trip)
        self._retranslate_ui()

    def _schedule_map_update(self, _text: str = "") -> None:
        self._map_update_timer.start()

    def _refresh_map_preview(self) -> None:
        self._map_preview.update_places(
            self.origin_edit.text().strip(), self.destination_edit.text().strip(),
            ("car", "plane", "rail")[self.transport_combo.currentIndex()],
            self.start_edit.date().toString("yyyy-MM-dd"),
            self.end_edit.date().toString("yyyy-MM-dd"),
        )

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)

        # 出发地 / 目的地共享同一个候选模型
        self._place_model = QStringListModel(self)

        self.title_label = QLabel(self)
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.title_edit = QLineEdit(self)
        self.form_layout.addRow(self.title_label, self.title_edit)

        self.origin_label = QLabel(self)
        self.origin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.origin_edit = QLineEdit(self)
        self._attach_place_completer(self.origin_edit)
        self.form_layout.addRow(self.origin_label, self.origin_edit)

        self.destination_label = QLabel(self)
        self.destination_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.destination_edit = QLineEdit(self)
        self._attach_place_completer(self.destination_edit)
        self.form_layout.addRow(self.destination_label, self.destination_edit)

        self.transport_label = QLabel(self)
        self.transport_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.transport_combo = QComboBox(self)
        self.transport_combo.addItems(["car", "plane", "rail"])
        self.form_layout.addRow(self.transport_label, self.transport_combo)

        today = QDate.currentDate()
        self.start_label = QLabel(self)
        self.start_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.start_edit = QDateEdit(today, self)
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("yyyy-MM-dd")
        self.form_layout.addRow(self.start_label, self.start_edit)

        self.end_label = QLabel(self)
        self.end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.end_edit = QDateEdit(today, self)
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_edit.setMinimumDate(today)
        self.form_layout.addRow(self.end_label, self.end_edit)

        # 约束：结束日期不早于出发日期
        self.start_edit.dateChanged.connect(self._on_start_changed)

        layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _attach_place_completer(self, edit: QLineEdit) -> None:
        """为输入框配置地名自动补全（多个输入框共享同一候选模型）。"""
        completer = QCompleter(self._place_model, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        popup = completer.popup()
        popup.setStyleSheet(
            "QListView { background-color: #ffffff; border: 1px solid #d1d5db;"
            " selection-background-color: #2563eb; selection-color: #ffffff;"
            " font-size: 14px; }"
            "QListView::item { padding: 4px 8px; }"
        )
        edit.setCompleter(completer)

    def _on_start_changed(self, new_start: QDate) -> None:
        self.end_edit.setMinimumDate(new_start)
        if self.end_edit.date() < new_start:
            self.end_edit.setDate(new_start)

    def _prefill(self, trip: Trip) -> None:
        self.title_edit.setText(trip.title)
        self.origin_edit.setText(trip.origin)
        self.destination_edit.setText(trip.destination)
        index = self.transport_combo.findData(trip.transport)
        if index < 0:
            index = self.transport_combo.findText(trip.transport)
        if index >= 0:
            self.transport_combo.setCurrentIndex(index)
        start = QDate.fromString(trip.start_date, "yyyy-MM-dd")
        end = QDate.fromString(trip.end_date, "yyyy-MM-dd")
        if start.isValid():
            self.start_edit.setDate(start)
        if end.isValid():
            self.end_edit.setMinimumDate(self.start_edit.date())
            self.end_edit.setDate(end)

    # ------------------------------------------------------------- 文案刷新
    def _retranslate_ui(self) -> None:
        self.title_label.setText(i18n.t("form_title"))
        self.origin_label.setText(i18n.t("form_origin"))
        self.destination_label.setText(i18n.t("form_destination"))
        self.transport_label.setText(i18n.t("form_transport"))
        transport_keys = ("transport_car", "transport_plane", "transport_rail")
        current = self.transport_combo.currentIndex()
        for index, key in enumerate(transport_keys):
            self.transport_combo.setItemText(index, i18n.t(key))
        self.transport_combo.setCurrentIndex(current)
        self.origin_edit.setPlaceholderText(i18n.t("form_destination_placeholder"))
        self.destination_edit.setPlaceholderText(i18n.t("form_destination_placeholder"))
        self.start_label.setText(i18n.t("form_start"))
        self.end_label.setText(i18n.t("form_end"))
        title_key = "form_dialog_title_edit" if self._is_edit else "form_dialog_title_new"
        self.setWindowTitle(i18n.t(title_key))
        self.button_box.button(QDialogButtonBox.Ok).setText(i18n.t("btn_confirm"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(i18n.t("btn_cancel"))
        self._populate_completer()

    def _populate_completer(self) -> None:
        """按当前语言填充补全候选地名（出发地/目的地共享）。"""
        self._place_model.setStringList(places_for(i18n.get_lang()))

    # ------------------------------------------------------------- 校验与取值
    def _on_accept(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(
                self,
                i18n.t("form_validation_title"),
                i18n.t("form_title_required"),
            )
            return
        if self.end_edit.date() < self.start_edit.date():
            QMessageBox.warning(
                self,
                i18n.t("form_validation_title"),
                i18n.t("form_end_before_start"),
            )
            return
        self.accept()

    def get_data(self) -> dict:
        """返回表单填写的行程字段（仅在 accept 后调用）。不含 status。"""
        return {
            "title": self.title_edit.text().strip(),
            "origin": self.origin_edit.text().strip(),
            "destination": self.destination_edit.text().strip(),
            "transport": ("car", "plane", "rail")[self.transport_combo.currentIndex()],
            "start_date": self.start_edit.date().toString("yyyy-MM-dd"),
            "end_date": self.end_edit.date().toString("yyyy-MM-dd"),
        }
