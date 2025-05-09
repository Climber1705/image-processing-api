
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

This project is licensed under the terms of the [MIT License](https://github.com/Climber1705/image-processing-api/blob/main/LICENSE).

