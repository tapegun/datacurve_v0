import os
import sqlite3
import json
import subprocess
import tempfile
import shutil
from pathlib import Path


def run_cmd(cmd, cwd=None):
    """Run a shell command and return (stdout, stderr, exitcode)."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate()
    return out.decode(), err.decode(), proc.returncode


def apply_patch(patch_text, repo_path):
    """Apply a unified diff patch to the repo using `patch` CLI."""
    patch_file = Path(tempfile.mkstemp(suffix=".patch")[1])
    patch_file.write_text(patch_text)
    out, err, code = run_cmd(f"patch -p1 < {patch_file}", cwd=repo_path)
    patch_file.unlink(missing_ok=True)
    if code != 0:
        print("⚠️ Patch failed:\n", err)
        return False
    else:
        print("✅ Patch applied successfully.")
    return True


def validate_trace(trace_id: str, db_path="telemetry.db", base_repo="fake_codebase"):
    # Connect to telemetry DB
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT event_json, repo FROM events WHERE trace_id = ?", (trace_id,)
    ).fetchall()
    conn.close()

    if not rows:
        raise ValueError(f"No events found for trace_id={trace_id}")

    # Parse events and repo info
    events = []
    repo_info = json.loads(rows[0][1])
    for row in rows:
        ev = json.loads(row[0])
        events.append(ev)

    # Sort by timestamp to replay chronologically
    events.sort(key=lambda e: e.get("timestamp", ""))

    working_commit = repo_info.get("working_commit", "unknown")
    print(f"🔍 Validating trace {trace_id} for repo '{repo_info['name']}' at commit {working_commit}")

    # Prepare isolated validation environment
    temp_dir = Path(tempfile.mkdtemp(prefix=f"validate_{trace_id[:8]}_"))
    repo_path = temp_dir / base_repo
    shutil.copytree(base_repo, repo_path)
    print(f"✅ Copied codebase to temporary dir: {repo_path}")

    # Initialize a new git branch for reproducibility
    run_cmd("git init", cwd=repo_path)
    run_cmd(f"git checkout -b validate-{trace_id[:8]}", cwd=repo_path)
    run_cmd(f"git add . && git commit -m 'base commit {working_commit}'", cwd=repo_path)

    all_good = True

    for idx, ev in enumerate(events, 1):
        diff = ev["data"].get("diff", "")
        event_id = ev.get("event_id")
        if not diff.strip():
            continue

        print(f"\n🧩 Applying event {idx} ({event_id}) diff...")
        if not apply_patch(diff, repo_path):
            all_good = False
            break

        # Run pytest
        print("▶️ Running pytest...")

        out, err, code = run_cmd("pytest -q --tb=short --disable-warnings", cwd=repo_path)
        # Parse 'X passed' and 'Y failed' from output
        passed = 0
        failed = 0
        for line in (out + "\n" + err).splitlines():
            line = line.strip().lower()
            if "passed" in line:
                try:
                    passed = int(line.split("passed")[0].strip().split()[-1])
                except Exception:
                    pass
            if "failed" in line:
                try:
                    failed = int(line.split("failed")[0].strip().split()[-1])
                except Exception:
                    pass

        trace_passed = ev["data"].get("results", {}).get("passed", -1)
        trace_failed = ev["data"].get("results", {}).get("failed", -1)

        print(out or err)
        if passed == trace_passed and failed == trace_failed:
            print(f"✅ Event {event_id}: results match telemetry ({passed} passed, {failed} failed)")
        else:
            print(f"❌ Event {event_id}: mismatch — trace says {trace_passed}/{trace_failed}, actual {passed}/{failed}")
            all_good = False

        # Commit applied diff
        run_cmd(f"git add . && git commit -m 'apply {event_id}'", cwd=repo_path)

    if all_good:
        print(f"\n🎉 Trace {trace_id} successfully validated — diffs reproduce claimed test results.")
    else:
        print(f"\n⚠️ Trace {trace_id} failed validation — one or more events did not match telemetry results.")

    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_trace.py <trace_id>")
        sys.exit(1)

    validate_trace(sys.argv[1])
