# Email.ing: Privacy-First AI Email Management

## Overview

Email.ing is a full-stack, machine-learning-powered application built to solve "Information Overload" in the modern inbox. Most AI email tools require users to sacrifice privacy by sending raw, sensitive data to cloud LLMs. Email.ing bridges this gap by using a modular AI architecture that masks personally identifiable information (PII) locally before any data leaves the user's environment.

## Architecture

![Email.ing Architecture](docs/Emailing_Architecture%20Diagram.png)

## Key Design Choices

1. **Hybrid AI Architecture (Task Specialization)**
   * **Local Llama 3 (via Ollama)**: Handles Classification and Urgency Scoring on a local GPU. This keeps the sensitive "judgment" logic on-device and eliminates per-token costs for high-frequency metadata extraction.
   * **Gemini 2.5 Flash**: Dedicated to Action-Oriented Summarization. This leverages a powerful cloud model for creative synthesis while only sending sanitized, masked data.
2. **Privacy-First PII Safety Vault**
   * The system implements a deterministic masking layer using Microsoft Presidio and a lightweight SpaCy model. It identifies entities like names, emails, and phone numbers and replaces them with placeholders. The mapping is stored in a local vault, allowing the system to deanonymize summaries locally once they return from the cloud
3. **Engineering for Latency (Parallel Inference)**
   * To mitigate the latency of running LLMs locally, I implemented a ThreadPoolExecutor to run Llama classifications in parallel. This allows the system to overlap wait-times for local API responses, maintaining a total pipeline latency of approximately 2.5 seconds per email.
4. Asynchronous Orchestration
   * I utilized Redis as a message broker and Celery for task orchestration. This ensures that the heavy ingestion and AI processing are decoupled from the FastAPI request-response cycle, keeping the UI highly responsive.

## Technical Stack

* **Backend:** FastAPI, SQLAlchemy, Pydantic
* **Task Queue:** Celery, Redis
* **AI/ML:** Llama 3 (Local), Gemini 2.5, Microsoft Presidio
* **Frontend:** Next.js, TypeScript, Tailwind CSS
* **DevOps:** Docker Compose with GPU passthrough for local LLM acceleration

## **How to Run**

#### **1. Prerequisites**

* **Docker & Docker Compose**
* **NVIDIA GPU** (Recommended for local Llama acceleration)
* **Ollama:** Must be installed and running locally. Run `ollama pull llama3.2` to ensure the classification model is available.

#### **2. Setup Environment Variables**

Create a `.env` file in the root directory with the following configuration:

**Plaintext**

```
# Database
DB_URL=postgresql://user:password@db:5432/email_ing

# Security (Generate your own keys)
JWT_SECRET_KEY=your_random_jwt_secret
ENCRYPTION_KEY=your_fernet_encryption_key
ALGORITHM=HS256

# Google OAuth (From Google Cloud Console)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth
GOOGLE_METADATA_URL=https://accounts.google.com/.well-known/openid-configuration
SCOPES=openid email profile https://www.googleapis.com/auth/gmail.readonly

# External APIs
GEMINI_API_KEY=your_gemini_api_key

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

#### **3. Launch the Application**

**Bash**

```
# Build and start the containers
docker-compose up --build

# Run database migrations
docker-compose exec backend alembic upgrade head
```

The frontend will be accessible at `http://localhost:3000` and the API at `http://localhost:8000`.

---

## **Attribution and Authorship**

I,  **Joshua Angel** , am the sole creator and primary contributor of this project.

The project utilizes the following open-source libraries:

* **FastAPI** for the backend API layer.
* **Microsoft Presidio** for PII detection.
* **Celery & Redis** for asynchronous task management.
* **Next.js** for the frontend interface.
