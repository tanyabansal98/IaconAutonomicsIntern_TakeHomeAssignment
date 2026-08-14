import json
import os
from datetime import datetime, timezone


class TrajectoryLogger:
    def __init__(self, run_id: str, log_dir: str = "run_logs"):
        self.run_id = run_id
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.path = os.path.join(log_dir, f"{run_id}.json")
        self.events = []

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log_event(self, event_type: str, **fields):
        event = {"timestamp": self._timestamp(), "type": event_type, **fields}
        self.events.append(event)
        self._flush()

    def _flush(self):
        with open(self.path, "w") as f:
            json.dump({"run_id": self.run_id, "events": self.events}, f, indent=2, default=str)

    def summary(self) -> str:
        n_calls = sum(1 for e in self.events if e["type"] == "tool_call")
        n_failures = sum(1 for e in self.events if e["type"] == "tool_failure")
        return f"Run {self.run_id}: {len(self.events)} events, {n_calls} tool calls, {n_failures} tool failures."