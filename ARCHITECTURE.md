# AtmosSense Architecture

This document outlines the high-level system architecture and request flow for AtmosSense.

## Request Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Nginx as Nginx (Edge Cache)
    participant API as API Gateway (Django)
    participant Redis as Redis (Cache & Rate Limits)
    participant External as External Weather API
    participant Celery as Celery (Worker)
    participant RMQ as RabbitMQ (Message Broker)
    participant DB as PostgreSQL

    %% Synchronous / Cached Flow
    Client->>Nginx: GET /api/forecast?region=NYC
    alt Is Cached at Edge?
        Nginx-->>Client: Return Cached Response (HTTP 200)
    else Not at Edge
        Nginx->>API: Forward Request
        API->>Redis: Check Rate Limit (Token Bucket)
        alt Rate Limit Exceeded
            API-->>Nginx: HTTP 429 Too Many Requests
            Nginx-->>Client: HTTP 429 Too Many Requests
        else Rate Limit OK
            API->>Redis: Check Forecast Cache
            alt Cache Hit
                Redis-->>API: Return Forecast
                API-->>Nginx: Return Forecast (HTTP 200)
                Nginx-->>Client: Return Forecast (HTTP 200)
            else Cache Miss (Asynchronous ML Flow)
                API->>External: Fetch current conditions (if needed)
                External-->>API: Current conditions
                API->>RMQ: Enqueue ML Inference Task (Job ID: 123)
                API-->>Nginx: HTTP 202 Accepted {job_id: 123}
                Nginx-->>Client: HTTP 202 Accepted {job_id: 123}
            end
        end
    end

    %% Asynchronous Processing
    Note over RMQ, DB: Background Processing
    RMQ->>Celery: Deliver ML Task (Job ID: 123)
    Celery->>Celery: Run ML Inference Model (Scikit-learn)
    Celery->>DB: Save Forecast Results
    Celery->>Redis: Update Cache for Region
    Celery->>Redis: Mark Job 123 as COMPLETE

    %% Polling Flow
    Client->>API: GET /api/jobs/123
    API->>Redis: Check Job Status
    Redis-->>API: Status: COMPLETE, Result: [...]
    API-->>Client: Return Forecast Results (HTTP 200)
```

## Component Roles
1. **Nginx**: Reverse proxy, SSL termination, and CDN-style Edge caching for static/public assets.
2. **Django & DRF (API Gateway)**: Handles authentication, rate limiting, cache checking, and enqueuing background tasks. Exposes Prometheus metrics and structured logs.
3. **Redis**: In-memory data store for the Token Bucket rate limiting counters, application-level caching, and job status tracking.
4. **RabbitMQ**: Highly reliable message broker that holds the queue of pending ML inference tasks.
5. **Celery Workers**: Scalable background workers that consume tasks from RabbitMQ, execute CPU-heavy ML inference (Scikit-learn) without blocking web requests, and gracefully shut down.
6. **PostgreSQL**: Persistent relational storage for historical weather data, user data, and long-term forecast archives.
7. **Prometheus / Grafana (Observability)**: Scrapes the `/metrics` endpoint to monitor API latency, HTTP status codes, and Celery queue depth.
