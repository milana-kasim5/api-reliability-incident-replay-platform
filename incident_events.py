from datetime import datetime, timezone
from uuid import uuid4


def create_incident_event(incident):
    """Create a standard event describing an API incident."""

    return {
        "event_id": str(uuid4()),
        "event_type": "incident.detected",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "incident": incident
    }
                                                                                                    