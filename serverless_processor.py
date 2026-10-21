def process_incident_event(event):
    """Process an incident event independently of the Flask API."""

    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")

    if event.get("event_type") != "incident.detected":
        raise ValueError("Unsupported event type")

    incident = event.get("incident")

    if not isinstance(incident, dict):
        raise ValueError("Event must contain incident details")

    return {
        "event_id": event.get("event_id"),
        "status": "processed",
        "message": (
            f"Incident detected for "
            f"{incident.get('target_name', 'Unknown API')}: "
            f"{incident.get('reason', 'Unknown reason')}"
        )
    }
