# Email.ing: Privacy-First AI Email Management

## Overview

Email.ing is a full-stack application designed to categorize, score for urgency, and summarize emails using a modular LLM architecture. It prioritizes user privacy by masking PII before any data leaves the local environment.

## Architecture

![Emailing Architecture Diagram](docs\Emailing_Architecture Diagram.png "Architecture")

## Key Features

* **Modular AI Architecture:** Uses local Llama 3 (via Ollama) for classification and Gemini 2.5 for summarization.
* **PII Safety Vault:** Utilizes Microsoft Presidio to detect and mask sensitive information (names, locations, etc.) before AI processing, swapping them back into the final summary locally.
* **Asynchronous Scaling:** Implements Celery and Redis to handle batch processing of email headers and bodies without blocking the main application thread.
* **Real-time Insights:** Displays "Inference Time" per email to monitor AI performance and latency.

## Technical Stack

* **Backend:** FastAPI, SQLAlchemy, Pydantic
* **Task Queue:** Celery, Redis
* **AI/ML:** Llama 3 (Local), Gemini 2.5, Microsoft Presidio
* **Frontend:** Next.js, TypeScript, Tailwind CSS
* **DevOps:** Docker Compose with GPU passthrough for local LLM acceleration

## How to Run

1. **Environment:** Requires Docker and an NVIDIA GPU (for optimal Llama performance)
2. **Setup:** Clone the repo and create a `.env` with your `GEMINI_API_KEY` and Google OAuth credentials
3. **Command:** Run `docker-compose up --build`
4. **Access:** The frontend will be available at `localhost:3000` and the API at `localhost:8000`
