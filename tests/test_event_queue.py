import pytest

from event_queue import (
    publish_event,
    receive_event,
    get_queue_size
)
from event_worker import process_next_event
from incident_events import create_incident_event


@pytest.fixture(autouse=True)
def clear_queue():
    """Ensure each test starts with an empty queue."""
    while receive_event() is not None:
        pass


def test_publish_event_adds_event_to_queue():
    event = create_incident_event({
        "target_name": "Broken Test API",
        "reason": "HTTP 404 response"
    })

    result = publish_event(event)

    assert result["status"] == "queued"
    assert result["event_id"] == event["event_id"]
    assert get_queue_size() == 1


def test_receive_event_removes_event_from_queue():
    event = {
        "event_id": "test-001",
        "event_type": "incident.detected",
        "incident": {
            "target_name": "Broken Test API",
            "reason": "HTTP 404 response"
        }
    }

    publish_event(event)

    received = receive_event()

    assert received == event
    assert get_queue_size() == 0


def test_queue_returns_to_empty_after_receiving_event():
    event = {
        "event_id": "test-event-123",
        "event_type": "incident.detected",
        "incident": {
            "target_name": "Test API",
            "reason": "HTTP 404 response"
        }
    }

    publish_event(event)

    assert get_queue_size() == 1
    assert receive_event() == event
    assert get_queue_size() == 0


def test_worker_processes_queued_event():
    event = create_incident_event({
        "target_name": "Broken Test API",
        "reason": "HTTP 404 response"
    })

    publish_event(event)
    result = process_next_event()

    assert result["status"] == "processed"
    assert result["event_id"] == event["event_id"]
    assert get_queue_size() == 0


def test_worker_handles_empty_queue():
    result = process_next_event()

    assert result["status"] == "empty"
    assert get_queue_size() == 0


def test_publish_rejects_invalid_event():
    with pytest.raises(ValueError, match="Event must be a dictionary"):
        publish_event("invalid event")
