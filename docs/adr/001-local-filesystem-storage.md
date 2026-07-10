# ADR 001: Local Filesystem Storage

## Status

Accepted

## Context

The Image Processing API stores image bytes for three lifecycle folders (`uploaded`, `edited`, `detected`). We need durable storage that keeps the project self-contained for local development, Docker deployment, and internship-level portfolio review without requiring cloud credentials.

## Decision

Use the **local filesystem** behind a storage abstraction (`BaseImageStorage` / `LocalImageStorage` in `app/storage/`). Image metadata (filename, dimensions, content hash, folder) lives in **SQLite** via SQLAlchemy (`app/models/image.py`).

Files are written under configurable paths (`UPLOADED_FOLDER`, `EDITED_FOLDER`, `DETECTED_FOLDER` in `app/core/config.py`). Upload deduplication uses content-hash uniqueness per folder in the database.

## Consequences

**Positive**

- Zero external infrastructure for development and demos
- Fast iteration; easy to inspect files on disk during debugging
- `BaseImageStorage` allows a future S3-compatible backend without changing service code

**Negative**

- Not horizontally scalable without shared storage (NFS, object store)
- Backup requires coordinating filesystem snapshots with SQLite backups
- Container restarts need mounted volumes (`docker-compose.yml`) to preserve data

## Migration path

1. Implement `S3ImageStorage(BaseImageStorage)` with the same interface as `LocalImageStorage`
2. Select backend via settings (e.g. `STORAGE_BACKEND=local|s3`)
3. Optional one-time migration script to copy existing files and update `ImageRecord.path` values
