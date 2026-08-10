"""行程表单对话框。

同时支持「新建」与「编辑」两种模式：
- 新建：不传 trip，字段为空。
- 编辑：传入已有 Trip，字段预填充，标题为「编辑行程」。

行程状态由起止日期相对今天自动派生，故表单不收集状态字段；
保存时由 TripStore 按日期重算。
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QDate, QStringListModel, Qt
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
)

from app import i18n
from app.data.places import places_for
from app.models.trip import Trip


class TripFormDialog(QDialog):
    """行程输入表单（新建 / 编辑）。"""

    def __init__(self, parent=None, trip: Optional[Trip] = None) -> None:
        super().__init__(parent)
        self._is_edit = trip is not None
        self._build_ui()
        if trip is not None:
            self._prefill(trip)
        self._retranslate_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)

        self.title_label = QLabel(self)
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.title_edit = QLineEdit(self)
        self.form_layout.addRow(self.title_label, self.title_edit)

        self.destination_label = QLabel(self)
        self.destination_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.destination_edit = QLineEdit(self)
        self._build_destination_completer()
        self.form_layout.addRow(self.destination_label, self.destination_edit)

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

    def _build_destination_completer(self) -> None:
        """为目的地输入框配置地名自动补全。"""
        self._completer_model = QStringListModel(self)
        self.destination_completer = QCompleter(self._completer_model, self)
        self.destination_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.destination_completer.setFilterMode(Qt.MatchContains)
        # 输入框获得焦点并开始输入时即弹出候选
        self.destination_completer.setCompletionMode(QCompleter.PopupCompletion)
        popup = self.destination_completer.popup()
        popup.setStyleSheet(
            "QListView { background-color: #ffffff; border: 1px solid #d1d5db;"
            " selection-background-color: #2563eb; selection-color: #ffffff;"
            " font-size: 14px; }"
            "QListView::item { padding: 4px 8px; }"
        )
        self.destination_edit.setCompleter(self.destination_completer)
        self._populate_completer()

    def _populate_completer(self) -> None:
        """按当前语言填充补全候选地名。"""
        self._completer_model.setStringList(places_for(i18n.get_lang()))

    def _on_start_changed(self, new_start: QDate) -> None:
        self.end_edit.setMinimumDate(new_start)
        if self.end_edit.date() < new_start:
            self.end_edit.setDate(new_start)

    def _prefill(self, trip: Trip) -> None:
        self.title_edit.setText(trip.title)
        self.destination_edit.setText(trip.destination)
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
        self.destination_label.setText(i18n.t("form_destination"))
        self.destination_edit.setPlaceholderText(i18n.t("form_destination_placeholder"))
        self.start_label.setText(i18n.t("form_start"))
        self.end_label.setText(i18n.t("form_end"))
        self._populate_completer()
        title_key = "form_dialog_title_edit" if self._is_edit else "form_dialog_title_new"
        self.setWindowTitle(i18n.t(title_key))
        self.button_box.button(QDialogButtonBox.Ok).setText(i18n.t("btn_confirm"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(i18n.t("btn_cancel"))

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
            "destination": self.destination_edit.text().strip(),
            "start_date": self.start_edit.date().toString("yyyy-MM-dd"),
            "end_date": self.end_edit.date().toString("yyyy-MM-dd"),
        }
