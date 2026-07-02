# Docker deployment guide

## Files used for deployment
- Dockerfile: builds the FastAPI app container
- deployment/app.py: API service for classification
- models/plant_disease_v1.pth: trained model weights
- models/class_names.json: class labels

## Build and run locally
```bash
docker build -t plant-disease-api .
docker run -p 8000:8000 plant-disease-api
```

## Test the API
```bash
curl http://localhost:8000/health
```

## Hugging Face Spaces with Docker
1. Create a new Hugging Face Space using Docker.
2. Upload this repository.
3. Hugging Face will build from the Dockerfile automatically.
4. Open the public URL once the container starts.

## Notes
- The app expects the model files in the models folder before building.
- The API endpoints are `/health` and `/predict`.
