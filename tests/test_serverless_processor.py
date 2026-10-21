import pytest

from incident_events import create_incident_event
from serverless_processor import process_incident_event


def test_process_valid_incident_event():
    incident = {
        "target_name": "Broken Test API",
        "reason": "HTTP 404 response"
    }
    event = create_incident_event(incident)

    result = process_incident_event(event)

    assert result["event_id"] == event["event_id"]
    assert result["status"] == "processed"
    assert "Broken Test API" in result["message"]
    assert "HTTP 404 response" in result["message"]


def test_reject_non_dictionary_event():
    with pytest.raises(ValueError, match="Event must be a dictionary"):
        process_incident_event("invalid event")


def test_reject_unsupported_event_type():
    event = {
        "event_type": "incident.recovered",
        "incident": {}
    }

    with pytest.raises(ValueError, match="Unsupported event type"):
        process_incident_event(event)


def test_reject_missing_incident_details():
    event = {
        "event_type": "incident.detected",
        "incident": None
    }

    with pytest.raises(ValueError, match="must contain incident details"):
        process_incident_event(event)
