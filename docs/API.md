# API Documentation

[← Back to Main README](../README.md)

Complete API reference for the Image Processing API.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

Access the interactive Swagger UI at: [http://localhost:8000/docs](http://localhost:8000/docs)

The Swagger UI provides:
- Complete endpoint documentation
- Try-it-out functionality
- Request/response schemas
- Authentication (when implemented)

## Endpoints Overview

### System Routes

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/` | Root endpoint with welcome message | None |
| GET | `/health/live` | Liveness probe | None |
| GET | `/health/ready` | Readiness probe (model + storage) | None |

### Image Management (`/images`)

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/images` | Upload a new image | 10/min |
| GET | `/images` | List images with pagination | 60/min |
| DELETE | `/images` | Delete all images in folder | 2/hour |
| GET | `/images/{image_name}` | Get image metadata | 30/min |
| GET | `/images/{image_name}/dimensions` | Get image dimensions | 20/min |
| PATCH | `/images/{image_name}` | Move image between folders | 20/min |
| DELETE | `/images/{image_name}` | Delete an image | 10/min |

### Image Editing (`/images/{image_name}/edits`)

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/images/{image_name}/edits/resize` | Resize image | 10/min |
| POST | `/images/{image_name}/edits/grayscale` | Convert to grayscale | 20/min |
| POST | `/images/{image_name}/edits/rotate` | Rotate image | 15/min |
| POST | `/images/{image_name}/edits/blur` | Apply blur filter | 10/min |
| POST | `/images/{image_name}/edits/sharpen` | Sharpen image | 10/min |
| POST | `/images/{image_name}/edits/brightness` | Adjust brightness | 20/min |
| POST | `/images/{image_name}/edits/contrast` | Adjust contrast | 20/min |

### Object Detection (`/v1/inference`)

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/v1/inference/detect` | Detect objects (metadata only) | 10/min |
| POST | `/v1/inference/detect/visualize` | Detect with bounding-box visualization | 5/min |
| GET | `/v1/inference/models` | Model metadata and readiness | 30/min |

Both detect endpoints accept either a **multipart file upload** or a **stored image reference** via query params (`image_name`, `folder`).

## Example Requests

### Upload an Image

```bash
curl -X POST "http://localhost:8000/images" \
  -F "file=@photo.jpg" \
  -F "filename=my_photo" \
  -F "format=JPEG"
```

**Response:**
```json
{
  "message": "Image uploaded successfully",
  "filename": "my_photo.jpg",
  "format": "JPEG"
}
```

### List Images

```bash
curl http://localhost:8000/images
```

**Response:**
```json
{
  "images": [
    {
      "name": "my_photo.jpg",
      "format": "JPEG",
      "size": 1234567,
      "uploaded_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

### Get Image Details

```bash
curl http://localhost:8000/images/my_photo.jpg
```

### Get Image Dimensions

```bash
curl http://localhost:8000/images/my_photo.jpg/dimensions
```

### Resize an Image

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/resize?width=800&height=600"
```

**Query Parameters:**
- `width` (required): New width in pixels
- `height` (required): New height in pixels

### Rotate an Image

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/rotate" \
  -H "Content-Type: application/json" \
  -d '{"degrees": 90, "expand": true}'

### Convert to Grayscale

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/grayscale"
```

### Apply Blur Filter

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/blur?radius=5"
```

**Query Parameters:**
- `radius` (optional): Blur radius (default: 2)

### Sharpen Image

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/sharpen"
```

### Adjust Brightness

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/brightness?factor=1.5"
```

**Query Parameters:**
- `factor` (required): Brightness factor (1.0 = no change, >1.0 = brighter, <1.0 = darker)

### Adjust Contrast

```bash
curl -X POST "http://localhost:8000/images/photo.jpg/edits/contrast?factor=1.2"
```

**Query Parameters:**
- `factor` (required): Contrast factor (1.0 = no change, >1.0 = more contrast)

### Detect Objects (multipart upload)

```bash
curl -X POST "http://localhost:8000/v1/inference/detect" \
  -F "file=@photo.jpg"
```

**Response:**
```json
{
  "message": "Detection completed successfully",
  "detections": [
    {
      "label": "person",
      "confidence": 0.95,
      "box": [100.0, 150.0, 200.0, 300.0]
    }
  ],
  "model_name": "facebook/detr-resnet-50",
  "model_version": null,
  "detection_count": 1
}
```

### Detect Objects (stored image reference)

```bash
curl -X POST "http://localhost:8000/v1/inference/detect?image_name=photo.jpg&folder=uploaded"
```

### Detect with Visualization

```bash
curl -X POST "http://localhost:8000/v1/inference/detect/visualize?persist=false" \
  -F "file=@photo.jpg"
```

Returns `annotated_image_base64` when `persist=false`. Set `persist=true` to save to the `detected` folder.

### List Model Info

```bash
curl http://localhost:8000/v1/inference/models
```

**Note**: The model loads at startup. First boot may take 1–3 minutes while DETR weights download from Hugging Face.

### Move Image Between Folders

```bash
curl -X PATCH "http://localhost:8000/images/my_photo.jpg" \
  -H "Content-Type: application/json" \
  -d '{"source_folder": "uploaded", "target_folder": "edited"}'

### Delete an Image

```bash
curl -X DELETE "http://localhost:8000/images/my_photo.jpg"
```

### Clear All Images

```bash
curl -X DELETE "http://localhost:8000/images?folder=uploaded"
```

**Query Parameters:**
- `folder` (optional): Folder to clear (uploaded, edited, detected). Defaults to all folders.

## Rate Limiting

The API implements rate limiting to ensure fair usage and prevent abuse. Rate limits are applied per endpoint and are reset periodically. If you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

Rate limits are specified in the endpoint tables above. Common limits:
- Image upload: 10 requests per minute
- Image listing: 60 requests per minute
- Object detection: 5–10 requests per minute depending on endpoint
- Image editing: 10-20 requests per minute depending on operation

## Error Responses

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Image Formats

Supported image formats:
- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)

Maximum file size: 5MB per image

## Additional Resources

- [Quick Start Guide](QUICKSTART.md) - Get started quickly
- [Installation Guide](INSTALLATION.md) - Detailed setup instructions
- [Architecture Overview](ARCHITECTURE.md) - System design and architecture

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)

