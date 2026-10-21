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

## AWS Serverless Processing

The project supports an event-driven processing workflow using Amazon SQS and AWS Lambda.

When AWS integration is configured, the backend publishes incident events to the configured SQS queue. Lambda processes messages delivered by the queue trigger, and CloudWatch provides execution logs.

AWS credentials and queue configuration should be supplied securely through environment variables or the appropriate AWS configuration. Do not commit access keys, secrets, or `.env` files.

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