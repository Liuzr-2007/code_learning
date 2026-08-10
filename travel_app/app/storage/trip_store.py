"""TripStore：行程数据的本地 JSON 持久化。

文件存放在用户数据目录（QStandardPaths.AppDataLocation）下的 trips.json，
目录不存在时自动创建。写入采用原子替换，避免程序中途崩溃导致文件损坏。

行程状态由起止日期相对今天自动派生：
- 读取时（load_all）会校正状态并在有变化时回写，保证文件与现实同步；
- 写入时（add/update）按日期重算状态后再落盘。
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import List, Optional

from PyQt5.QtCore import QStandardPaths

from app.models.trip import Trip, compute_status


class TripStore:
    """行程存储，单实例在 MainWindow 中创建并共享给行程页与详情页。"""

    def __init__(self, filename: str = "trips.json") -> None:
        self._filepath = self._resolve_filepath(filename)

    @staticmethod
    def _resolve_filepath(filename: str) -> str:
        data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not data_dir:
            # 退回到程序所在目录
            data_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, filename)

    @property
    def filepath(self) -> str:
        return self._filepath

    def _load_raw(self) -> List[Trip]:
        """纯读取，不做状态校正。"""
        if not os.path.exists(self._filepath):
            return []
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(raw, list):
            return []
        return [Trip.from_dict(item) for item in raw if isinstance(item, dict)]

    def load_all(self) -> List[Trip]:
        """读取全部行程，并按当前日期校正状态；有变化则回写文件。"""
        trips = self._load_raw()
        changed = False
        for trip in trips:
            new_status = compute_status(trip.start_date, trip.end_date)
            if new_status != trip.status:
                trip.status = new_status
                changed = True
        if changed:
            self.save_all(trips)
        return trips

    def save_all(self, trips: List[Trip]) -> None:
        """原子写入：先写临时文件，再替换目标文件。"""
        data = [trip.to_dict() for trip in trips]
        dirname = os.path.dirname(self._filepath)
        fd, tmp_path = tempfile.mkstemp(prefix="trips_", suffix=".json", dir=dirname)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def add(self, trip: Trip) -> None:
        trip.status = compute_status(trip.start_date, trip.end_date)
        trips = self._load_raw()
        trips.append(trip)
        self.save_all(trips)

    def delete(self, trip_id: str) -> None:
        trips = self._load_raw()
        self.save_all([t for t in trips if t.id != trip_id])

    def get(self, trip_id: str) -> Optional[Trip]:
        """按 id 取单条行程（含状态校正），不存在返回 None。"""
        for trip in self.load_all():
            if trip.id == trip_id:
                return trip
        return None

    def update(self, trip: Trip) -> None:
        """更新指定 id 的行程；id 不存在则忽略。状态按日期重算。"""
        trip.status = compute_status(trip.start_date, trip.end_date)
        trips = self._load_raw()
        for i, t in enumerate(trips):
            if t.id == trip.id:
                trips[i] = trip
                break
        self.save_all(trips)
