from queue import Queue, Empty


# Local queue for incident events
_incident_queue = Queue()


def publish_event(event):
    """Add an incident event to the queue."""

    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")

    _incident_queue.put(event)

    return {
        "status": "queued",
        "event_id": event.get("event_id")
    }


def receive_event():
    """Retrieve the next event without waiting if the queue is empty."""

    try:
        return _incident_queue.get_nowait()
    except Empty:
        return None


def get_queue_size():
    """Return the number of events waiting in the queue."""

    return _incident_queue.qsize()
