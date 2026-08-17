# AtmosSense: ML-Driven Weather Forecasting Backend

Welcome to **AtmosSense**, a production-ready, scalable weather forecasting backend built with Django, applying system design principles from Gaurav Sen and Sriniously ("Backend from First Principles"). 

## Architectural Decisions

### Why Celery & RabbitMQ for Background Tasks?
Running Machine Learning inference within a synchronous request-response cycle is an anti-pattern. ML tasks are often CPU-intensive and can take variable amounts of time. 
* **Decoupling**: Celery allows us to decouple the web tier (which should be fast and responsive) from the heavy ML inference tier.
* **Why not a simpler queue?**: While simpler alternatives exist (like Django Q or threading), RabbitMQ provides enterprise-grade durability, message acknowledgments, and complex routing. Celery pairs perfectly with RabbitMQ to offer task retries, monitoring, and horizontal scaling of worker nodes independently of the web servers. This ensures that a surge in forecasting requests won't bring down our API servers.

### Why Redis Caching?
Weather forecasts for a specific region are highly cacheable because meteorological data doesn't change every second. 
* **Performance**: Redis is an in-memory data store that provides sub-millisecond response times.
* **Database & API Protection**: By caching regional forecasts, we drastically reduce read loads on our PostgreSQL database and minimize costly (and rate-limited) calls to external weather APIs. 

### How Token-Bucket Rate Limiting Protects External Quotas
External weather APIs typically enforce strict rate limits (e.g., 60 requests per minute). If our system exceeds this, our API key could be suspended, causing a complete system outage.
* **The Strategy**: We implement a Token Bucket algorithm at our API Gateway level. It allows bursts of traffic up to a maximum bucket size but refills tokens at a steady rate. If a client requests data and we don't have a token, we return an HTTP 429 (Too Many Requests) rather than hitting the external API. This acts as a circuit breaker, ensuring we *never* exceed our external quota, regardless of user traffic spikes.

## Functional Flow

The core functional flow of the application is:
1. A user requests weather/forecast for a city or region.
2. The backend fetches live data from an external weather API.
3. An ML model (**Scikit-learn**) predicts upcoming conditions based on this live data.
4. The predicted result is returned to the client.

## Key Features Implemented
* API Gateway with Token-Bucket Rate Limiting
* Asynchronous ML Inference via Celery/RabbitMQ with polling
* Multi-layer Caching (Redis + CDN-style Edge caching)
* 12-Factor App Configuration Management
* Structured Logging, Prometheus Metrics, Health Checks
* Graceful Shutdowns for Web and Worker nodes
* Comprehensive Pytest Suite
* Full Dockerization (Docker Compose)
* OpenAPI/Swagger Documentation
