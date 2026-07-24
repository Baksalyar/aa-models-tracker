"""Best-effort BeanDashboard reporter for the GitHub Actions tracker."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCE = "artificial-analysis-models"
HOST = "github-actions"
ENVIRONMENT = "prod"


def _event_payload() -> dict[str, object]:
    tracker_status = os.environ.get("BEAN_REPORT_TRACKER_STATUS", "")
    commit_status = os.environ.get("BEAN_REPORT_COMMIT_STATUS", "")
    successful = tracker_status == "success" and commit_status not in {"failure", "cancelled"}
    reason = "success" if successful else "workflow_failure"
    metadata = {
        "status": "success" if successful else "failure",
        "reason": reason,
        "tracker_status": tracker_status,
        "commit_status": commit_status,
    }
    run_url = os.environ.get("GITHUB_RUN_URL")
    if run_url:
        metadata["github_run_url"] = run_url

    return {
        "level": "info" if successful else "error",
        "kind": "heartbeat",
        "code": "run_success" if successful else "run_failure",
        "message": "Artificial Analysis model tracker completed"
        if successful
        else "Artificial Analysis model tracker failed",
        "source": SOURCE,
        "host": HOST,
        "env": ENVIRONMENT,
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "metadata": metadata,
    }


def report() -> int:
    ingest_url = os.environ.get("BEAN_EVENT_INGEST_URL")
    token = os.environ.get("BEAN_EVENT_TOKEN")
    if not ingest_url or not token:
        print("BeanDashboard reporting is not configured; skipping.")
        return 0

    payload = _event_payload()
    if not payload["run_id"]:
        payload.pop("run_id")
    request = Request(
        ingest_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(response_payload, dict) or response_payload.get("accepted") is not True:
            raise RuntimeError(f"BeanDashboard rejected event: {response_payload!r}")
        print("BeanDashboard event accepted.")
    except (HTTPError, URLError, OSError, RuntimeError, ValueError) as exc:
        print(f"Warning: BeanDashboard reporting failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(report())
