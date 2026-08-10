"""Trip 行程数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

# 行程状态常量
STATUS_PLANNED = "planned"      # 未开始
STATUS_ONGOING = "ongoing"      # 进行中
STATUS_COMPLETED = "completed"  # 已完成
STATUS_ORDER = (STATUS_PLANNED, STATUS_ONGOING, STATUS_COMPLETED)


def compute_status(start_date: str, end_date: str) -> str:
    """根据当前日期与起止日期自动判定行程状态。

    - 今天早于出发日期 → 未开始
    - 今天处于起止日期之间（含首尾）→ 进行中
    - 今天晚于结束日期 → 已完成
    - 日期缺失或非法 → 未开始
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except (ValueError, TypeError):
        return STATUS_PLANNED
    today = date.today()
    if today < start:
        return STATUS_PLANNED
    if today > end:
        return STATUS_COMPLETED
    return STATUS_ONGOING


@dataclass
class Trip:
    """一条行程记录。

    日期统一以 ISO 字符串（YYYY-MM-DD）存储，便于 JSON 序列化与跨语言展示。
    status 由起止日期相对今天自动派生，存储层在读写时统一校正。
    """

    title: str
    destination: str
    start_date: str
    end_date: str
    status: str = STATUS_PLANNED
    id: str = field(default_factory=lambda: uuid4().hex)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trip":
        status = str(data.get("status", STATUS_PLANNED))
        if status not in STATUS_ORDER:
            status = STATUS_PLANNED
        return cls(
            id=str(data.get("id") or uuid4().hex),
            title=str(data.get("title", "")),
            destination=str(data.get("destination", "")),
            start_date=str(data.get("start_date", "")),
            end_date=str(data.get("end_date", "")),
            status=status,
        )
