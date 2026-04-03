# services/result_store.py

from collections import deque
from datetime import datetime, timezone
from ..models.schemas import DetectionEvent, SoilReading


class ResultStore:
    def __init__(self):
        self.events      = deque(maxlen=100)
        self.listening   = False
        self.latest_soil: SoilReading | None = None
        self._total      = 0          # lifetime count, survives deque trimming

    # ── Detection events ───────────────────────────────────────────
    def add_event(self, event: DetectionEvent):
        self.events.appendleft(event)
        self._total += 1

    def get_latest(self) -> DetectionEvent | None:
        try:
            return self.events[0]
        except IndexError:
            return None

    def get_history(self) -> tuple[list[DetectionEvent], int]:
        return list(self.events), self._total

    # ── Soil readings ──────────────────────────────────────────────
    def update_soil(self, moisture: float, timestamp: datetime, temp_c: float | None = None):
        self.latest_soil = SoilReading(
            timestamp=timestamp,
            moisture_pct=round(moisture, 1),
            temp_c=round(temp_c, 1) if temp_c is not None else None
        )

    def get_soil(self) -> SoilReading | None:
        return self.latest_soil

    # ── Listener state ─────────────────────────────────────────────
    def set_listening(self, value: bool):
        self.listening = value