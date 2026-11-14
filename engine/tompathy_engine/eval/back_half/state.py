"""Durable limits and status for explicitly invoked, private benchmark runs."""
import json
from datetime import UTC, datetime, timedelta

from .reporting import public_receipt, save_json


class PilotDeadline:
    """A restart cannot grant a fresh budget; downtime counts conservatively."""

    def __init__(self, path, *, hours=8, now=lambda: datetime.now(UTC)):
        self.path, self.now, self.hours = path, now, hours
        if path.exists():
            self.state = json.loads(path.read_text(encoding="utf8"))
            start = datetime.fromisoformat(self.state["startedAt"])
            end = datetime.fromisoformat(self.state["expiresAt"])
            if start.tzinfo is None or end-start != timedelta(hours=hours):
                raise ValueError("Pilot deadline differs from its fixed budget")
        else:
            start = now()
            self.state = {"startedAt":start.isoformat(), "expiresAt":(start+timedelta(hours=hours)).isoformat(),
                          "definition":f"{hours}-hour wall ceiling across resumes; downtime counts conservatively"}
            save_json(path,self.state)

    def check(self):
        if self.now() >= datetime.fromisoformat(self.state["expiresAt"]):
            raise RuntimeError(f"{self.hours}-hour pilot ceiling reached; resuming does not reset it")


def finalize(report, output, backend):
    """A failed unload must remain visible without erasing completed measurements."""
    try:
        if backend:
            backend.close(recover=True)
    except Exception as error:
        report.update(status="cleanup-failed",cleanupError=type(error).__name__,productionAdmission=False)
        raise
    finally:
        save_json(output,public_receipt(report))
