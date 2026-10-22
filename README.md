# API Reliability & Incident Replay Platform

A full-stack API monitoring platform that checks endpoint availability, records response times, tracks incidents, and processes incident events using AWS serverless services.

## Features

- **API monitoring:** Run health checks against configured API endpoints.
- **Performance tracking:** Record HTTP status codes, response times, and check outcomes.
- **Incident management:** Detect failed checks and track incidents, including recovery.
- **Interactive dashboard:** View monitored APIs, check statistics, response times, and recent incidents.
- **Event processing:** Publish incident events to Amazon SQS and process them using AWS Lambda.
- **Local development:** Use Flask and SQLite to run and test the core application locally.
- **Automated tests:** Test API endpoints, event queue behaviour, and serverless processing.

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python, Flask, REST API |
| Frontend | React, TypeScript, Vite |
| Database | SQLite |
| Cloud and serverless | AWS SQS, AWS Lambda, Amazon CloudWatch |
| Testing | pytest |
| Development tools | Git, GitHub, Postman |

## Architecture

1. The React dashboard communicates with the Flask backend.
2. Flask checks configured API targets and records their results in SQLite.
3. Failed checks can create incidents, while subsequent successful checks can identify recovery.
4. Incident events are published to Amazon SQS when configured, with a local queue fallback for development.
5. AWS Lambda processes events received through the SQS trigger, with execution logs available in CloudWatch.

## Getting Started

### Prerequisites

- Python 3.11 or compatible version
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd api-reliability-incident-replay-platform
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the HTTPS URL of your GitHub repository.

### 2. Set up the Python backend

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the backend dependencies listed in your project's dependency file. If the project does not yet contain one, create a `requirements.txt` with the required packages before running:

```bash
pip install -r requirements.txt
```

### 3. Start the backend

```bash
python app.py
```

The Flask API runs locally at `http://127.0.0.1:5000`.

### 4. Start the frontend

Open another terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend availability |
| GET | `/targets` | Retrieve monitored API targets |
| POST | `/targets` | Add a monitored target |
| PUT | `/targets/<id>` | Update a target |
| POST | `/check` | Run health checks for configured targets |
| GET | `/checks` | Retrieve recorded health checks |
| GET | `/incidents` | Retrieve incident records |
| POST | `/events` | Publish an incident event |
| POST | `/process-next-event` | Process the next event in the local queue |

## Event Processing Configuration

The application supports two event-processing modes:

- **Local mode (default):** Events are placed on an in-memory queue and processed by the local event worker.
- **AWS serverless mode:** Events are sent to Amazon SQS and processed by an AWS Lambda function.

### Enable AWS Serverless Processing

1. Create an Amazon SQS queue and deploy the Lambda function using the project's `lambda_function.py` and `serverless_processor.py` files.
2. Configure the Lambda function with an SQS trigger for your queue.
3. Configure AWS credentials locally using an AWS CLI profile or another supported AWS credentials provider.
4. Set the `SQS_QUEUE_URL` environment variable to your queue's URL before starting the Flask application:

   ```bash
   export SQS_QUEUE_URL="YOUR_SQS_QUEUE_URL"
   python app.py
   ```

When `SQS_QUEUE_URL` is configured, the application publishes incident events to AWS SQS. Without it, the application uses the local in-memory queue.

**Note:** Replace the example URL with the URL of your own SQS queue. Do not commit AWS credentials, secret keys, or your local `.env` file to version control. AWS resources may incur charges.

## Running Tests

From the project root, with the virtual environment activated:

```bash
python -m pytest tests/ -v
```

## Future Improvements

- Add configurable monitoring intervals and background scheduling.
- Improve incident history, filtering, and visualisation.
- Add authentication and role-based access control.
- Expand monitoring configuration and test coverage.