import pytest
import app as app_module
import event_queue

from app import app
from database import get_connection, init_db
from unittest.mock import Mock


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Give each test its own temporary database.
    test_db = tmp_path / "test_api_reliability.db"
    monkeypatch.setattr(
        "database.DATABASE",
        str(test_db)
    )

    init_db()

    # Keep automated tests independent of AWS SQS.
    monkeypatch.setattr(
        app_module,
        "publish_event",
        event_queue.publish_event
    )

    # Start each test with a clean local event queue.
    while event_queue.receive_event() is not None:
        pass

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client
        
    # Remove any unprocessed events after each test.
    while event_queue.receive_event() is not None:
        pass


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_get_targets_initially_empty(client):
    response = client.get("/targets")

    assert response.status_code == 200
    assert response.get_json() == {"targets": []}


def test_create_target(client):
    response = client.post(
        "/targets",
        json={
            "name": "Test API",
            "url": "http://127.0.0.1:5000/health"
        }
    )

    assert response.status_code in (200, 201)

    data = response.get_json()
    assert data is not None


def test_check_creates_incident_for_failed_api(client, monkeypatch):
    # Register a target.
    client.post(
        "/targets",
        json={
            "name": "Broken Test API",
            "url": "http://example.com/test"
        }
    )

    # Simulate an HTTP 404 response.
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.ok = False

    monkeypatch.setattr(
        "app.requests.get",
        lambda *args, **kwargs: mock_response
    )

    response = client.post("/check")

    assert response.status_code == 200

    incidents = client.get("/incidents").get_json()["incidents"]
    assert len(incidents) == 1
    assert incidents[0]["status"] == "open"
    assert incidents[0]["reason"] == "HTTP 404 response"


def test_check_resolves_incident_after_recovery(client, monkeypatch):
    client.post(
        "/targets",
        json={
            "name": "Recovering Test API",
            "url": "http://example.com/test"
        }
    )

    # First check: API fails.
    failed_response = Mock()
    failed_response.status_code = 404
    failed_response.ok = False

    monkeypatch.setattr(
        "app.requests.get",
        lambda *args, **kwargs: failed_response
    )

    client.post("/check")

    # Second check: API recovers.
    healthy_response = Mock()
    healthy_response.status_code = 200
    healthy_response.ok = True

    monkeypatch.setattr(
        "app.requests.get",
        lambda *args, **kwargs: healthy_response
    )

    client.post("/check")

    incidents = client.get("/incidents").get_json()["incidents"]

    assert len(incidents) == 1
    assert incidents[0]["status"] == "resolved"


def test_repeated_failures_do_not_create_duplicate_incidents(
    client, monkeypatch
):
    client.post(
        "/targets",
        json={
            "name": "Repeated Failure API",
            "url": "http://example.com/test"
        }
    )

    failed_response = Mock()
    failed_response.status_code = 500
    failed_response.ok = False

    monkeypatch.setattr(
        "app.requests.get",
        lambda *args, **kwargs: failed_response
    )

    # Check the failing API three times.
    client.post("/check")
    client.post("/check")
    client.post("/check")

    incidents = client.get("/incidents").get_json()["incidents"]

    assert len(incidents) == 1
    assert incidents[0]["status"] == "open"
    assert incidents[0]["reason"] == "HTTP 500 response"


def test_create_target_rejects_missing_url(client):
    response = client.post(
        "/targets",
        json={"name": "Incomplete API"}
    )

    assert response.status_code == 400


def test_create_target_rejects_missing_name(client):
    response = client.post(
        "/targets",
        json={"url": "http://example.com"}
    )

    assert response.status_code == 400


def test_create_target_rejects_invalid_url(client):
    response = client.post(
        "/targets",
        json={
            "name": "Invalid URL API",
            "url": "not-a-valid-url"
        }
    )

    assert response.status_code == 400


def test_create_target_rejects_unsupported_url_scheme(client):
    response = client.post(
        "/targets",
        json={
            "name": "Unsupported Scheme API",
            "url": "ftp://example.com/file"
        }
    )

    assert response.status_code == 400


def test_events_endpoint_queues_incident_event(client):
    response = client.post(
        "/events",
        json={
            "incident": {
                "target_name": "Test API",
                "reason": "HTTP 404 response"
            }
        }
    )

    assert response.status_code == 202
    data = response.get_json()
    assert data["message"] == "Incident event queued"
    assert data["event"]["event_type"] == "incident.detected"
    assert data["queue"]["status"] == "queued"


def test_process_next_event_endpoint(client):
    client.post(
        "/events",
        json={
            "incident": {
                "target_name": "Test API",
                "reason": "HTTP 404 response"
            }
        }
    )

    response = client.post("/process-next-event")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "processed"


def test_events_endpoint_rejects_invalid_body(client):
    response = client.post("/events", json=[])

    assert response.status_code == 400
    assert "error" in response.get_json()
