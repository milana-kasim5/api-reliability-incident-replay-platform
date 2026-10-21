from flask import Flask, request, jsonify
from contextlib import closing
import requests
import time

from database import get_connection, init_db

from incident_events import create_incident_event
from event_publisher import publish_event
from event_worker import process_next_event


app = Flask(__name__)

# Create database tables if they do not exist
init_db()


def get_all(query, parameters=()):
    """Return database rows as a list of dictionaries."""
    with closing(get_connection()) as connection:
        rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]


@app.route("/health")
def health():
    return {"status": "ok"}


# List registered targets
@app.route("/targets", methods=["GET"])
def get_targets():
    targets = get_all(
        "SELECT id, name, url FROM targets ORDER BY id"
    )
    return {"targets": targets}


# Register a new target
@app.route("/targets", methods=["POST"])
def create_target():
    data = request.get_json(silent=True)

    if not data:
        return {"error": "A JSON request body is required"}, 400

    name = data.get("name")
    url = data.get("url")

    if not isinstance(name, str) or not name.strip():
        return {"error": "A target name is required"}, 400

    if not isinstance(url, str) or not url.startswith(
        ("http://", "https://")
    ):
        return {"error": "A valid HTTP or HTTPS URL is required"}, 400

    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO targets (name, url) VALUES (?, ?)",
                (name.strip(), url)
            )
            target_id = cursor.lastrowid

    target = {
        "id": target_id,
        "name": name.strip(),
        "url": url
    }

    return {"message": "Target registered", "target": target}, 201


# Update a target's URL
@app.route("/targets/<int:target_id>", methods=["PUT"])
def update_target(target_id):
    data = request.get_json(silent=True)

    if not data:
        return {"error": "A JSON request body is required"}, 400

    url = data.get("url")

    if not isinstance(url, str) or not url.startswith(
        ("http://", "https://")
    ):
        return {"error": "A valid HTTP or HTTPS URL is required"}, 400

    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE targets SET url = ? WHERE id = ?",
                (url, target_id)
            )

            if cursor.rowcount == 0:
                return {"error": "Target not found"}, 404

            row = connection.execute(
                "SELECT id, name, url FROM targets WHERE id = ?",
                (target_id,)
            ).fetchone()

    return {"message": "Target updated", "target": dict(row)}


# Check all registered APIs
@app.route("/check", methods=["POST"])
def check_targets():
    targets = get_all(
        "SELECT id, name, url FROM targets ORDER BY id"
    )

    new_results = []
    new_incidents = []
    recovered_incidents = []

    for target in targets:
        start_time = time.perf_counter()
        error_message = None

        try:
            response = requests.get(
                target["url"],
                timeout=5
            )

            status_code = response.status_code
            success = response.ok

        except requests.RequestException as error:
            status_code = None
            success = False
            error_message = str(error)

        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        result = {
            "target_id": target["id"],
            "target_name": target["name"],
            "url": target["url"],
            "status_code": status_code,
            "response_time_ms": duration_ms,
            "success": success
        }

        if error_message:
            result["error"] = error_message

        created_incident = None
        with closing(get_connection()) as connection:
            with connection:
                # Save every check permanently
                connection.execute(
                    """
                    INSERT INTO checks (
                        target_id, target_name, url, status_code,
                        response_time_ms, success, error
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        target["id"],
                        target["name"],
                        target["url"],
                        status_code,
                        duration_ms,
                        int(success),
                        error_message
                    )
                )

                # Find any existing open incident for this target
                open_incident = connection.execute(
                    """
                    SELECT id FROM incidents
                    WHERE target_id = ? AND status = 'open'
                    ORDER BY id LIMIT 1
                    """,
                    (target["id"],)
                ).fetchone()

                if not success and open_incident is None:
                    reason = error_message or (
                        f"HTTP {status_code} response"
                    )

                    cursor = connection.execute(
                        """
                        INSERT INTO incidents (
                            target_id, target_name, status,
                            reason, response_time_ms
                        )
                        VALUES (?, ?, 'open', ?, ?)
                        """,
                        (
                            target["id"],
                            target["name"],
                            reason,
                            duration_ms
                        )
                    )

                    incident = {
                        "id": cursor.lastrowid,
                        "target_id": target["id"],
                        "target_name": target["name"],
                        "status": "open",
                        "reason": reason,
                        "response_time_ms": duration_ms
                    }

                    new_incidents.append(incident)
                    created_incident = incident

                elif success and open_incident is not None:
                    incident_id = open_incident["id"]

                    connection.execute(
                        """
                        UPDATE incidents
                        SET status = 'resolved',
                            resolved_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (incident_id,)
                    )

                    recovered_incidents.append({
                        "incident_id": incident_id,
                        "target_name": target["name"],
                        "status": "resolved"
                    })

        if created_incident is not None:
            event = create_incident_event(created_incident)
            publish_event(event)

        new_results.append(result)

    return {
        "message": "API checks completed",
        "results": new_results,
        "new_incidents": new_incidents,
        "recovered_incidents": recovered_incidents
    }


# Retrieve all recorded checks
@app.route("/checks", methods=["GET"])
def get_checks():
    checks = get_all(
        """
        SELECT id, target_id, target_name, url, status_code,
               response_time_ms, success, error, checked_at
        FROM checks
        ORDER BY id
        """
    )

    for check in checks:
        check["success"] = bool(check["success"])

    return {"checks": checks}


# Retrieve incident history
@app.route("/incidents", methods=["GET"])
def get_incidents():
    incidents = get_all(
        """
        SELECT id, target_id, target_name, status, reason,
               response_time_ms, created_at, resolved_at
        FROM incidents
        ORDER BY id
        """
    )

    return {"incidents": incidents}


@app.route("/events", methods=["POST"])
def create_event():
    """Create and queue an incident event."""

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    incident = data.get("incident")

    if not isinstance(incident, dict):
        return jsonify({
            "error": "Incident details must be a JSON object"
        }), 400

    event = create_incident_event(incident)
    queue_result = publish_event(event)

    return jsonify({
        "message": "Incident event queued",
        "event": event,
        "queue": queue_result
    }), 202


@app.route("/process-next-event", methods=["POST"])
def process_queued_event():
    """Process the next queued incident event."""

    result = process_next_event()
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True)
