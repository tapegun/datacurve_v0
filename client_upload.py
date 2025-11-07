import json
import requests
from pathlib import Path

BACKEND_URL = "http://localhost:8000/trace"

def upload_trace(trace_path: str):
    with open(trace_path, "r") as f:
        data = json.load(f)

    try:
        r = requests.post(BACKEND_URL, json=data, timeout=5)
        print("Upload status:", r.status_code, r.text)
    except requests.exceptions.RequestException:
        print("Network unavailable, saving locally.")
        queue_file = Path("queued_traces.jsonl")
        with queue_file.open("a") as f:
            f.write(json.dumps(data) + "\n")

if __name__ == "__main__":
    upload_trace("trace_example.json")

