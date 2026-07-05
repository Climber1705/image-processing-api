# Installation Guide

[← Back to Main README](../README.md)

Complete installation and configuration guide for the Image Processing API.

## Prerequisites

### Required

- **Python 3.12+** - The project is built and tested with Python 3.12
- **pip** - Python package manager (usually included with Python)
- **Internet Connection** - Required for initial model download from Hugging Face

### System Requirements

- **Disk Space**: ~3-4GB minimum
  - Base Python dependencies: ~2GB
  - PyTorch and ML libraries: ~1-2GB
  - DETR model (downloaded on first use): ~500MB-1GB
- **Memory (RAM)**:
  - Minimum: 4GB RAM
  - Recommended: 8GB+ RAM for better performance
  - For ML inference: 8GB+ RAM recommended
- **Optional**: GPU support for faster ML model inference (CUDA-compatible GPU recommended)

### Docker Prerequisites

For Docker deployment:
- [Docker](https://www.docker.com/get-started) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed (usually included with Docker Desktop)

## Manual Installation

### 1. Clone the Repository & Set Up a Virtual Environment

Clone the repository and create a virtual environment for isolating dependencies:

```bash
git clone https://github.com/thomas-trotter/image-processing-api.git
cd image-processing-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure the Environment

Copy the environment variables template and modify it to match your local setup:

```bash
cp .env-example .env
# Edit .env with the appropriate values
```

#### Environment Variables

The following environment variables can be configured in your `.env` file:

##### `DEBUG` (boolean, default: `False`)

- Set to `True` for development environment
- Enables debug mode with detailed error messages
- Set to `False` for production environment
- **Use Cases**:
  - `True`: Development, testing, debugging
  - `False`: Production deployments

##### `LOG_LEVEL` (string, default: `INFO`)

- Controls the verbosity of logging output
- Available options:
  - `DEBUG`: Detailed information for troubleshooting (most verbose)
  - `INFO`: General operational information (recommended for production)
  - `WARNING`: Indicates potential issues or important situations
  - `ERROR`: Errors that might require attention
  - `CRITICAL`: Severe errors that likely result in a crash or failure (least verbose)
- **Use Cases**:
  - `DEBUG`: Development, troubleshooting issues
  - `INFO`: Production environments, general monitoring
  - `WARNING`/`ERROR`/`CRITICAL`: Production with minimal logging

**Example `.env` file for development:**
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

**Example `.env` file for production:**
```env
DEBUG=False
LOG_LEVEL=INFO
```

**Note**: Logs are written to `logs/app.log`. The log file location and format are configured in the application code.

### 4. Run the API

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Once the server is running, access the interactive API documentation at:  
[http://localhost:8000/docs](http://localhost:8000/docs)

## Docker Installation

The project includes Docker containerization for both development and production environments. Docker ensures consistent environments across different systems and simplifies deployment.

### Development Environment

Run the API in development mode with hot reload enabled:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Development Features:**
- Hot reload enabled (code changes are automatically reflected)
- Volume mounts for live code updates
- DEBUG mode enabled
- Detailed logging (LOG_LEVEL=DEBUG)
- Accessible at [http://localhost:8000](http://localhost:8000)

**Stop the development container:**
```bash
docker-compose -f docker-compose.dev.yml down
```

### Production Environment

Run the API in production mode:

```bash
docker-compose -f docker-compose.yml up --build -d
```

**Production Features:**
- Optimized image size (build dependencies removed after installation)
- Health checks configured (uses `/health` endpoint)
- Automatic restart on failure
- Production logging (LOG_LEVEL=INFO)
- Persistent data volumes for images and logs
- Runs in detached mode (`-d` flag)

**View logs:**
```bash
docker-compose -f docker-compose.yml logs -f
```

**Stop the production container:**
```bash
docker-compose -f docker-compose.yml down
```

**Stop and remove volumes (⚠️ deletes all data):**
```bash
docker-compose -f docker-compose.yml down -v
```

### Running Tests in Docker

Run the test suite inside a Docker container:

```bash
docker-compose -f docker-compose.dev.yml run --rm app pytest
```

Run tests with coverage:
```bash
docker-compose -f docker-compose.dev.yml run --rm app pytest --cov=app --cov-report=html
```

### Docker Features

- **Automatic Testing**: Tests run during image build (build fails if tests fail or coverage < 80%)
- **Health Checks**: Docker healthcheck configured using the `/health` endpoint
- **Optimized Images**: Build dependencies removed after installation to minimize image size
- **Data Persistence**: Named volumes for uploaded images, edited images, detected outputs, and logs
- **Environment Configuration**: Separate configurations for development and production

### Docker Compose Files

- **`docker-compose.dev.yml`**: Development configuration with hot reload
- **`docker-compose.yml`**: Production configuration with health checks and restart policies

For more information about the Docker setup, see the `Dockerfile` and docker-compose configuration files.

## Port Configuration

The API runs on port **8000** by default. If you need to change the port:

### For Docker

- Edit `docker-compose.yml` or `docker-compose.dev.yml`
- Change the port mapping from `"8000:8000"` to `"<your-port>:8000"` in the `ports` section
- Example: `"8080:8000"` to access the API on port 8080

### For Manual Setup

- Use the `--port` flag: `uvicorn app.main:app --reload --port 8080`
- Or set the `PORT` environment variable (if supported by your deployment)

**Note**: If port 8000 is already in use, you'll see an error like "Address already in use". Change the port using one of the methods above.

## Verification

After installation, verify the API is working:

1. **Check health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Access interactive docs:**
   Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser

3. **Test root endpoint:**
   ```bash
   curl http://localhost:8000/
   ```

## Next Steps

- **Quick Start**: See [Quick Start Guide](QUICKSTART.md) for immediate usage examples
- **API Reference**: See [API Documentation](API.md) for all available endpoints
- **Production Deployment**: See [Deployment Guide](DEPLOYMENT.md) for production best practices
- **Troubleshooting**: See [Troubleshooting Guide](TROUBLESHOOTING.md) if you encounter issues

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)

