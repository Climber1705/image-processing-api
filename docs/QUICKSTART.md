# Quick Start Guide

[← Back to Main README](../README.md)

Get the Image Processing API up and running in minutes! This guide covers the fastest path to a working API.

## 5-Minute Quick Start

### Option 1: Docker (Recommended)

The fastest way to get started:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

This will:
- Build the Docker image
- Start the API with hot reload enabled
- Make the API available at [http://localhost:8000](http://localhost:8000)

Access the interactive API documentation at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Manual Setup

If you prefer to run locally without Docker:

```bash
# Clone the repository
git clone https://github.com/thomas-trotter/image-processing-api.git
cd image-processing-api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env-example .env

# Start the API
uvicorn app.main:app --reload
```

For detailed installation instructions, see the [Installation Guide](INSTALLATION.md).

## First Steps

### 1. Verify the API is Running

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Or visit [http://localhost:8000](http://localhost:8000) in your browser.

### 2. Upload an Image

Upload your first image:

```bash
curl -X POST "http://localhost:8000/images/upload" \
  -F "file=@photo.jpg" \
  -F "filename=my_photo" \
  -F "format=JPEG"
```

### 3. Process an Image

Resize an uploaded image:

```bash
curl -X POST "http://localhost:8000/images/edit/resize?image_name=my_photo.jpg&width=800&height=600"
```

### 4. Detect Objects

Detect objects in an image:

```bash
curl -X POST "http://localhost:8000/images/detect/bounding_boxes/?image_name=my_photo.jpg"
```

**Note**: The first detection request will take 1-3 minutes as the DETR model downloads. Subsequent requests will be faster.

## Interactive API Documentation

The easiest way to explore the API is through the interactive Swagger UI:

**Access it at:** [http://localhost:8000/docs](http://localhost:8000/docs)

This provides:
- All available endpoints
- Try-it-out functionality
- Request/response schemas
- Authentication (when implemented)

## Common First Tasks

### List All Images

```bash
curl http://localhost:8000/images/
```

### Get Image Details

```bash
curl http://localhost:8000/images/my_photo.jpg/detail
```

### Apply Image Filters

Convert to grayscale:
```bash
curl -X POST "http://localhost:8000/images/edit/grayscale?image_name=my_photo.jpg"
```

Adjust brightness:
```bash
curl -X POST "http://localhost:8000/images/edit/brightness?image_name=my_photo.jpg&factor=1.5"
```

### Delete an Image

```bash
curl -X DELETE "http://localhost:8000/images/my_photo.jpg/delete"
```

## Next Steps

- **Full API Reference**: See [API Documentation](API.md) for all endpoints and detailed examples
- **Installation Details**: See [Installation Guide](INSTALLATION.md) for environment configuration and advanced setup
- **Architecture**: Learn about the system design in [Architecture Overview](ARCHITECTURE.md)
- **Troubleshooting**: Having issues? Check the [Troubleshooting Guide](TROUBLESHOOTING.md)

## Need Help?

- Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues
- Review the [API Documentation](API.md) for endpoint details
- See the [Installation Guide](INSTALLATION.md) for setup problems

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)

