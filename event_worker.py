from event_queue import receive_event
from serverless_processor import process_incident_event


def process_next_event():
    """Retrieve and process one queued incident event."""

    event = receive_event()

    if event is None:
        return {
            "status": "empty",
            "message": "No events available to process"
        }

    result = process_incident_event(event)

    return result
