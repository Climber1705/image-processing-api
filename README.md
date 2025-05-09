
# 🖼️ Image Processing API

A **FastAPI**-powered RESTful service designed for efficient image management, processing, and object detection. Ideal for handling image uploads, applying transformations, and detecting objects in images.

## ✨ Key Features

- **🗂️ Image Management**  
  - Upload, retrieve, list, and delete images  
  - Store and manage images in a scalable way

- **🛠️ Image Processing**  
  - Apply various image filters (e.g., grayscale, sepia)  
  - Resize, rotate with expanding  
  - Adjust brightness, contrast, and other image properties  
  - Validate uploaded images for format and integrity

- **🔍 Object Detection**  
  - Detect objects within images using bounding boxes  
  - Return confidence scores for each detected object

- **🧹 Cleanup and Maintenance**  
  - Automatically clean up `__pycache__` folders when the API is shut down
    
---

# AI Model: DETR (DEtection TRansformer)

This project uses the **DEtection TRansformer (DETR)** model for object detection. DETR combines a Transformer architecture with a ResNet-50 backbone, enabling efficient and accurate object detection in images.

## Key Components:
- **Model**: `facebook/detr-resnet-50`
  - A pre-trained object detection model that uses Transformers to understand the global context.
  - Fine-tuned for detecting a wide variety of objects.

## Initialisation:
The processor and model are loaded as follows:

```python
from transformers import DetrImageProcessor, DetrForObjectDetection

# Initialise the image processor and model
self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50", ignore_mismatched_sizes=True)
```

- **`DetrImageProcessor`**: Pre-processes images for model input (resizing, normalisation, etc.).
- **`DetrForObjectDetection`**: Performs object detection and outputs bounding boxes and class predictions.

## Benefits:
- **End-to-End Pipeline**: Simplifies detection without the need for separate components like region proposal networks.
- **High Flexibility**: Can detect a wide variety of objects and is easily adaptable to custom datasets.
- **Transformer-Based**: Captures global image context, improving detection accuracy.

## Example Usage:

```python
# Process image and run object detection
inputs = self.processor(images=image, return_tensors="pt")
outputs = self.model(**inputs)

# Post-process to extract detections
results = self.processor.post_process_object_detection(outputs, target_sizes=[image.size[::-1]], threshold=0.9)[0]
```

## Model Information:
- **Model Name**: `facebook/detr-resnet-50`
- **Source**: [Hugging Face Model Hub](https://huggingface.co/facebook/detr-resnet-50)

---

## 🚀 Getting Started

Follow these steps to set up and run the Image Processing API on your local machine:

### 1. Clone the Repository & Set Up a Virtual Environment

Clone the repository and create a virtual environment for isolating dependencies:

```
git clone https://github.com/Climber1705/image-processing-api.git
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
cp .env.example .env
# Edit .env with the appropriate values (e.g., development, logging type)
```

### 4. Run the API

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Once the server is running, access the interactive API documentation at:  
[http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 **Repository Structure**
Here’s a quick overview of the project file structure:
```graphql
image-processing-api/
│
├── app/
│   ├── api/
│   |   ├── routes/
│   |   |   ├── __init__.py
│   |   |   ├── detection_routes.py
│   |   |   ├── editing_routes.py
│   |   |   └── image_routes.py
│   |   └── __init__.py          
│   ├── core/
│   |   ├── __init__.py
│   |   ├── config.py
│   |   ├── dependencies.py
│   |   ├── logging_config.py
│   |   └── rate_limiting.py      
│   ├── managers/
│   |   ├── __init__.py
│   |   ├── detection_manager.py
│   |   ├── edit_manager.py
│   |   └── image_manager.py 
|   ├── schemas/
│   |   ├── detection/
│   |   |   ├── __init__.py
│   |   |   └── detection_responses.py
│   |   ├── editing/
│   |   |   ├── __init__.py
│   |   |   ├── editing_requests.py
│   |   |   └── editing_responses.py
│   |   ├── image/
│   |   |   ├── __init__.py
│   |   |   ├── image_requests.py
│   |   |   └── image_responses.py
│   |   └── __init__.py 
|   ├── services/
│   |   ├── detection/
│   |   |   ├── __init__.py
│   |   |   └── detection_service.py
│   |   ├── image/
│   |   |   ├── storage/
│   |   |   |   ├── __init__.py
│   |   |   |   ├── base_storage.py
│   |   |   |   └── local_storage.py
│   |   |   ├── __init__.py
│   |   |   ├── crud_operations.py
│   |   |   ├── image_editor.py
│   |   |   └── metadata_handler.py
│   |   └── __init__.py   
|   ├── utils/
│   |   ├── file_operations/
│   |   |   ├── __init__.py.py
│   |   |   ├── directory_utils.py
│   |   |   └── file_utils.py
│   |   ├── system/
│   |   |   ├── __init__.py.py
│   |   |   ├── clean_up.py
│   |   |   └── lifespan.py
│   |   ├── validator/
│   |   |   ├── __init__.py.py
│   |   |   ├── base_validator.py
│   |   |   └── simple_validator.py
│   |   └── __init__.py   
|   ├── __init__.py             
│   └── main.py          
│── logs/ 
│   └── app.log    
│── .env-example
├── LICENSE      
├── README.md             
└── requirements.txt             
```

## 🛠️ Improvements

Stay tuned for these upcoming features:

- 🔒 **Authentication**:  
  Secure the API with user authentication.

- ⚡ **Asynchronous Processing**:  
  Improve API performance for handling large images or long-running tasks asynchronously.

- 🖼️ **Batch Operations**:  
  Enable batch processing for uploading and processing multiple images at once.

- 🎨 **Extended Format & Filters**:  
  Support more image file formats (e.g., WebP, BMP) and advanced image effects (e.g crop, watermarks)

- 📄 **Pagination Support**:  
  Efficiently handle large image collections by paginating through the results.

---

## 📄 License

This project is licensed under the terms of the [GNU License](https://github.com/Climber1705/image-processing-api/blob/main/LICENSE).

