from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List, Dict
import sqlite3
import json

app = FastAPI(title="Telemetry Collector")

DB = "telemetry.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.execute(
    "CREATE TABLE IF NOT EXISTS traces (trace_id TEXT PRIMARY KEY, payload TEXT)"
)

class Event(BaseModel):
    event_id: str
    timestamp: str
    data: Dict[str, Any]

class Repo(BaseModel):
    name: str
    working_commit: str
    branch: str

class Trace(BaseModel):
    trace_id: str
    developer_id: str
    repo: Repo
    events: List[Event]

@app.post("/trace")
def receive_trace(trace: Trace):
    payload = trace.dict()
    conn.execute(
        "INSERT OR REPLACE INTO traces (trace_id, payload) VALUES (?, ?)",
        (trace.trace_id, json.dumps(payload)),
    )
    conn.commit()
    return {"status": "stored", "trace_id": trace.trace_id}

