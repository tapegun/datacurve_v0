import json
import requests
from pathlib import Path


BACKEND_URL = "http://localhost:8000/event"



def upload_event_data(event_upload):
    try:
        r = requests.post(BACKEND_URL, json=event_upload, timeout=5)
        print("Upload status:", r.status_code, r.text)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        print("Network unavailable, saving locally.")
        return False


def upload_queued_events():
    queue_file = Path("queued_traces.jsonl")
    if not queue_file.exists():
        return
    lines = queue_file.read_text().splitlines()
    if not lines:
        return
    remaining = []
    for line in lines:
        try:
            event_upload = json.loads(line)
        except Exception as e:
            print(f"Skipping invalid line in queue: {e}")
            continue
        if not upload_event_data(event_upload):
            remaining.append(line)
    if remaining:
        queue_file.write_text("\n".join(remaining) + "\n")
    else:
        queue_file.unlink()


def upload_trace_events(trace_path: str):
    with open(trace_path, "r") as f:
        trace = json.load(f)
    trace_id = trace["trace_id"]
    developer_id = trace["developer_id"]
    repo = trace["repo"]
    for event in trace["events"]:
        event_upload = {
            "trace_id": trace_id,
            "developer_id": developer_id,
            "repo": repo,
            "event": event,
        }
        if not upload_event_data(event_upload):
            queue_file = Path("queued_traces.jsonl")
            with queue_file.open("a") as f:
                f.write(json.dumps(event_upload) + "\n")


if __name__ == "__main__":
    upload_queued_events()
    upload_trace_events("trace_example.json")

