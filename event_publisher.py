"""Publish incident events to AWS SQS or the local queue."""

import json
import os


def publish_event(event):
    """Publish to SQS when configured; otherwise use the local queue."""

    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")

    queue_url = os.getenv("SQS_QUEUE_URL")

    if not queue_url:
        from event_queue import publish_event as publish_local_event

        return publish_local_event(event)

    import boto3

    sqs = boto3.client(
        "sqs",
        region_name=os.getenv("AWS_REGION", "eu-west-2")
    )

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(event)
    )

    return {
        "status": "queued",
        "event_id": event.get("event_id"),
        "message_id": response["MessageId"]
    }
