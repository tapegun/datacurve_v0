
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict
import sqlite3
import json

app = FastAPI(title="Telemetry Collector")

DB = "telemetry.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.execute(
    "CREATE TABLE IF NOT EXISTS events (trace_id TEXT, event_id TEXT, developer_id TEXT, repo TEXT, event_json TEXT, PRIMARY KEY(trace_id, event_id))"
)

class EventUpload(BaseModel):
    trace_id: str
    developer_id: str
    repo: Dict[str, Any]
    event: Dict[str, Any]  # must contain event_id

@app.post("/event")
def receive_event(event_upload: EventUpload):
    event_id = event_upload.event.get("event_id")
    if not event_id:
        return {"status": "error", "reason": "event_id missing"}
    try:
        conn.execute(
            "INSERT OR IGNORE INTO events (trace_id, event_id, developer_id, repo, event_json) VALUES (?, ?, ?, ?, ?)",
            (
                event_upload.trace_id,
                event_id,
                event_upload.developer_id,
                json.dumps(event_upload.repo),
                json.dumps(event_upload.event),
            ),
        )
        conn.commit()
        return {"status": "stored", "trace_id": event_upload.trace_id, "event_id": event_id}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

