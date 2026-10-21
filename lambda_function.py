import json

from serverless_processor import process_incident_event


def lambda_handler(event, context):
    """Process incident events delivered by an SQS trigger."""

    records = event.get("Records", [])
    processed = []

    for record in records:
        try:
            body = json.loads(record["body"])
            result = process_incident_event(body)
            processed.append(result)

            print(f"Successfully processed incident: {json.dumps(result)}")

        except Exception as error:
            print(f"Failed to process SQS message: {error}")
            raise

    response = {
        "statusCode": 200,
        "processed_count": len(processed),
        "results": processed
    }

    print(f"Batch processing complete: {json.dumps(response)}")

    return response