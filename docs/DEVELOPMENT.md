# Development Guide

[← Back to Main README](../README.md)

Development guidelines and testing instructions for the Image Processing API.

## Development Environment Setup

### Prerequisites

- Python 3.12+
- pip
- Git

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thomas-trotter/image-processing-api.git
   cd image-processing-api
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env-example .env
   # Edit .env with DEBUG=True and LOG_LEVEL=DEBUG for development
   ```

5. **Run the API in development mode:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Testing

The project includes a comprehensive test suite with unit and integration tests, targeting 80%+ code coverage.

### Test Structure

The test suite is organized into two main categories:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
  - Services: image_editor, crud_operations, metadata_handler, local_storage, detection_service
  - Managers: image_manager, edit_manager, detection_manager
  - Utils: file_utils, directory_utils, validators

- **Integration Tests** (`tests/integration/`): Test API endpoints and end-to-end workflows
  - Image routes: upload, list, get details, delete, move, clear all
  - Editing routes: resize, rotate, grayscale, blur, sharpen, brightness, contrast
  - Detection routes: bounding boxes, detected objects
  - End-to-end workflows: complete user scenarios

### Running Tests

#### Run All Tests

```bash
pytest
```

#### Run Unit Tests Only

```bash
pytest tests/unit
```

#### Run Integration Tests Only

```bash
pytest tests/integration
```

#### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html
```

The HTML coverage report will be generated in `htmlcov/index.html`.

#### Run a Specific Test File

```bash
pytest tests/unit/services/test_image_editor.py
```

#### Run Tests with Verbose Output

```bash
pytest -v
```

#### Run Tests in Docker

```bash
docker-compose -f docker-compose.dev.yml run --rm app pytest
```

Run tests with coverage in Docker:
```bash
docker-compose -f docker-compose.dev.yml run --rm app pytest --cov=app --cov-report=html
```

### Test Configuration

The project uses configuration files to standardize test execution:

#### `pytest.ini`

Configures pytest behavior:
- Test discovery paths and patterns
- Coverage settings (80% minimum threshold)
- Async test mode configuration
- Test markers for unit and integration tests
- Default command-line options

#### `.coveragerc`

Configures coverage reporting:
- Source directories to measure
- Files and patterns to omit from coverage
- Report formatting and precision
- Exclusion patterns for generated code

These files ensure consistent test execution across different environments and CI/CD pipelines.

### Test Coverage

The test suite maintains 80%+ code coverage. Coverage reports are generated automatically when running tests with the `--cov` flag. The project uses pytest-cov for coverage tracking and HTML report generation.

**Coverage Requirements:**
- Minimum 80% code coverage
- Build fails if coverage is below threshold
- All new code should include tests

For comprehensive test documentation, including detailed test descriptions, fixtures, and testing strategies, see the [Test Suite Documentation](../tests/README.md).

## Code Structure and Conventions

### Project Structure

```
app/
├── api/          # API routes and endpoints
├── core/         # Configuration and infrastructure
├── managers/     # Business logic coordination
├── schemas/      # Request/response models
├── services/     # Core business logic
└── utils/        # Utility functions
```

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names

### Architecture Patterns

- **Layered Architecture**: Routes → Managers → Services → Utils
- **Dependency Injection**: Services receive dependencies through constructors
- **Async/Await**: Use async functions for I/O operations
- **Error Handling**: Use appropriate HTTP exceptions and error responses

### Module Organization

Each module has a specific responsibility:
- **API**: HTTP request handling
- **Managers**: Business logic coordination
- **Services**: Core functionality implementation
- **Schemas**: Data validation and serialization
- **Utils**: Reusable helper functions

## Future Improvements

Stay tuned for these upcoming features:

- **Authentication**:  
  Secure the API with user authentication.

- **Batch Operations**:  
  Enable batch processing for uploading and processing multiple images at once.

- **Extended Format & Filters**:  
  Support more image file formats (e.g., WebP, BMP) and advanced image effects (e.g., crop, watermarks)

- **Pagination Support**:  
  Efficiently handle large image collections by paginating through the results.

## Debugging

### Enable Debug Mode

Set `DEBUG=True` in your `.env` file for detailed error messages.

### View Logs

- Application logs: `logs/app.log`
- Docker logs: `docker-compose logs -f`
- Test output: Use `pytest -v` for verbose output

### Common Debugging Tasks

- **Check API health**: `curl http://localhost:8000/health`
- **View test coverage**: Open `htmlcov/index.html` in browser
- **Inspect Docker containers**: `docker-compose ps`
- **Check environment variables**: Verify `.env` file settings

## Additional Resources

- [Quick Start Guide](QUICKSTART.md) - Get started quickly
- [Installation Guide](INSTALLATION.md) - Detailed setup
- [Architecture Overview](ARCHITECTURE.md) - System design
- [API Documentation](API.md) - API reference
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)

