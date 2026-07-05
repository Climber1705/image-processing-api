# Test Suite Documentation

## Overview

Unit and integration tests for the Image Processing API, targeting 80%+ code coverage.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/
│   ├── api/                 # Health route tests
│   ├── media/               # Media domain tests
│   ├── services/            # Service layer tests
│   ├── utils/               # Utility tests
│   └── vision/              # Vision/inference tests
└── integration/             # API endpoint integration tests
```

## Running Tests

### Fast tier (CI default — skips slow model-download tests)

```bash
pytest -m "not inference"
```

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=app --cov-report=html
```

### Run slow inference tests (requires model download)

```bash
pytest -m inference
```

## Test Coverage by Domain

| Domain | Key test files |
|--------|----------------|
| Media | `test_service.py`, `test_upload_duplicate.py`, `test_hash.py` |
| Editing | `test_image_editor.py` |
| Vision | `test_inference_service.py`, `test_inference_engine.py`, `test_image_loader.py`, `test_mappers.py`, `test_visualizer.py` |
| Integration | `test_image_routes.py`, `test_editing_routes.py`, `test_inference_routes.py`, `test_end_to_end.py` |

## Fixtures

Shared fixtures in `conftest.py`:

- `temp_directories` — isolated upload/edit/detect folders
- `test_settings` — Settings scoped to temp directories
- `mock_inference_engine` — mocked DETR engine (avoids model download)
- `test_client` / `test_client_with_overrides` — FastAPI TestClient variants

See [ML Serving](../docs/ML_SERVING.md) for inference test tier details.
