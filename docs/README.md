# Documentation Index

[← Back to Main README](../README.md)

Welcome to the Image Processing API documentation.

## Documentation Guide

### Getting Started

- **[Quick Start Guide](QUICKSTART.md)** — Get the API running in minutes (Docker or manual setup).

### Setup & Installation

- **[Installation Guide](INSTALLATION.md)** — Environment configuration and system requirements.
- **[Deployment Guide](DEPLOYMENT.md)** — Production Docker setup, health checks, and monitoring.

### API Reference

- **[API Documentation](API.md)** — Endpoints, rate limits, request/response examples.
- **[ML Serving](ML_SERVING.md)** — Inference pipeline, concurrency, and test tiers.

### Architecture & Development

- **[Architecture Overview](ARCHITECTURE.md)** — Bounded contexts, DETR model, design patterns.
- **[Development Guide](DEVELOPMENT.md)** — Testing, code structure, conventions.
- **[ADR 001: Local filesystem storage](adr/001-local-filesystem-storage.md)** — Why local disk was chosen over object storage.

### Troubleshooting

- **[Troubleshooting Guide](TROUBLESHOOTING.md)** — Common issues and FAQ.

## Code Layout

```
app/
├── api/routes/       # HTTP endpoints
├── core/             # Config, lifespan, logging
├── dependencies/     # FastAPI DI
├── media/            # Image CRUD bounded context
├── editing/          # Pillow transforms bounded context
├── vision/           # ML inference bounded context
├── storage/          # Filesystem abstraction
└── validation/       # Upload validation
```

See also: [Test Suite](../tests/README.md)

---

[← Back to Main README](../README.md)
