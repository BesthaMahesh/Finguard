import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt_auth import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "admin", "role": "ADMIN", "user_id": "usr-admin-01"})
    return {"Authorization": f"Bearer {token}"}

def parse_sse_events(text: str):
    events = []
    current_event = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if current_event:
                events.append(current_event)
                current_event = {}
            continue
        if line.startswith("event:"):
            current_event["event"] = line.replace("event:", "").strip()
        elif line.startswith("data:"):
            data_str = line.replace("data:", "").strip()
            try:
                current_event["data"] = json.loads(data_str)
            except Exception:
                current_event["data"] = data_str
    if current_event:
        events.append(current_event)
    return events

def test_stream_low_risk_fast_track(auth_headers):
    """
    Low risk transactions (score < 30) must fast-track:
    skip investigator and policy_compliance, reaching explainability and audit_reporter.
    """
    payload = {
        "step": 1,
        "type": "PAYMENT",
        "amount": 25.50,
        "name_orig": "C10001",
        "old_balance_org": 500.0,
        "new_balance_orig": 474.50,
        "name_dest": "M90001",
        "old_balance_dest": 0.0,
        "new_balance_dest": 0.0
    }
    response = client.post("/api/v1/agents/analyze/stream", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "run_start" in event_names
    assert "run_end" in event_names

    # Check agent nodes executed
    agents_started = [e["data"]["agent"] for e in events if e["event"] == "agent_start"]
    agents_ended = [e["data"]["agent"] for e in events if e["event"] == "agent_end"]

    # Intake, Data Quality, Fraud Detector, Market/Credit, Risk Assessment should run
    assert "intake" in agents_started
    assert "data_quality" in agents_started
    assert "fraud_detector" in agents_started
    assert "risk_assessment" in agents_started

    # Fast-track skips deep forensic investigation for routine payments
    assert "investigator" not in agents_started
    assert "policy_compliance" not in agents_started

    # Explainability and Audit Reporter should run
    assert "explainability" in agents_started
    assert "audit_reporter" in agents_ended

    # Verify run_end payload contains final verdict
    run_end_event = next(e for e in events if e["event"] == "run_end")
    assert "result" in run_end_event["data"]
    assert "risk_score" in run_end_event["data"]["result"]

def test_stream_replay_trace(auth_headers):
    """
    Verifies that a completed run is persisted and retrievable via GET /runs/{run_id}.
    """
    payload = {
        "step": 1,
        "type": "PAYMENT",
        "amount": 15.00,
        "name_orig": "C999",
        "old_balance_org": 200.0,
        "new_balance_orig": 185.0,
        "name_dest": "M888",
        "old_balance_dest": 0.0,
        "new_balance_dest": 0.0
    }
    resp = client.post("/api/v1/agents/analyze/stream", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    events = parse_sse_events(resp.text)
    run_start = next(e for e in events if e["event"] == "run_start")
    run_id = run_start["data"]["run_id"]

    # Retrieve stored run
    get_resp = client.get(f"/api/v1/agents/runs/{run_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["run_id"] == run_id
    assert len(data["events"]) > 0

