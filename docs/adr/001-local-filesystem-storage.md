# ADR 001: Local filesystem storage

**Status:** Accepted  
**Date:** 2026-07-05

## Context

Images are stored in three lifecycle folders (`uploaded`, `edited`, `detected`). The API needs read/write/move/delete semantics, and services should not depend on a specific backend.

`BaseImageStorage` (`app/storage/base_storage.py`) defines the contract; `LocalImageStorage` (`app/storage/local_storage.py`) is the only implementation.

## Decision

Use the **local filesystem** as the storage backend for this project scope.

- Paths come from `Settings` (`UPLOADED_FOLDER`, `EDITED_FOLDER`, `DETECTED_FOLDER`).
- Docker Compose mounts named volumes for persistence in production (`docker-compose.yml`).
- SQLite holds metadata (dimensions, format, content hash); bytes stay on disk.

## Alternatives considered

| Option | Why not (for now) |
|--------|-------------------|
| **S3 / object storage** | Adds credentials, bucket policy, and local-dev friction. Valuable for a multi-instance deployment, but this service runs as a single process with in-process DETR. |
| **Database BLOBs** | Couples large binary payloads to SQLite backups and migrations; poor fit for image serving. |
| **NFS / shared volume** | Helps horizontal scaling but does not remove the need for a remote object API at scale. |

## Consequences

**Positive**

- Zero external storage dependencies for development and demos.
- Straightforward Docker setup with volume mounts.
- `BaseImageStorage` keeps a clear seam if a second backend is added later.

**Negative**

- Not suitable for multi-replica deployments without a shared filesystem or object store.
- Disk usage grows with uploads; no built-in lifecycle policy beyond API delete/clear endpoints.

## Follow-up (if extended)

1. Implement `S3ImageStorage` (or MinIO for local dev) behind `BaseImageStorage`.
2. Select backend via `STORAGE_BACKEND=local|s3` in settings.
3. Keep SQLite metadata paths consistent with the active storage driver.
