# Plant Disease Detection Using CNN with MLOps

## Problem Statement

Detect plant diseases from leaf images using a convolutional neural network. Accurate detection enables farmers to identify crop issues early, reduce losses, and improve agricultural productivity.

## Real-world Significance

Plant disease detection is critical for agriculture and food security. An automated model can help smallholders and agronomists make faster decisions, reduce pesticide misuse, and preserve crop yield.

## Dataset Source

- PlantVillage dataset
- Expected to be stored under `./data/PlantVillage`
- The dataset should contain class subfolders for each plant disease category

## Expected Outcomes

- Baseline CNN model (v1)
- Improved CNN model (v2) with augmentation, regularization, and scheduler
- MLflow experiment tracking for parameters, metrics, runs, and artifacts
- FastAPI model serving with `/`, `/health`, and `/predict`
- Docker containerization and Kubernetes deployment manifests

## Project Structure

- `src/`
  - `data_loader.py` - dataset loading and augmentation
  - `model.py` - baseline and improved CNN models
  - `train.py` - MLflow-tracked training pipeline
  - `evaluate.py` - evaluation helper functions
- `training/`
  - `train_v1.py` - entrypoint for baseline training
  - `train_v2.py` - entrypoint for improved training
- `deployment/`
  - `app.py` - FastAPI application
  - `utils.py` - model loading and inference utilities
  - `predict.py` - offline prediction CLI
- `kubernetes/`
  - `deployment.yaml` - Kubernetes deployment manifest
  - `service.yaml` - Kubernetes service manifest
- `models/` - saved model weights and metadata
- `mlruns/` - MLflow tracking artifacts
- `data/` - dataset placeholder directory
- `.github/workflows/ci-cd.yml` - CI/CD workflow
- `Dockerfile` - container image definition
- `requirements.txt` - Python dependencies

## Linux Recommendation

This project is best developed and tested on Linux, preferably Ubuntu 22.04 or 24.04.

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Prepare dataset:
```bash
mkdir -p data/PlantVillage
# copy PlantVillage images into data/PlantVillage
```

## Training

Train both versions:
```bash
python src/train.py --version both --data-dir ./data/PlantVillage --epochs 15 --batch-size 32
```

Train a single version:
```bash
python training/train_v1.py --data-dir ./data/PlantVillage
python training/train_v2.py --data-dir ./data/PlantVillage
```

## MLflow

Start MLflow UI:
```bash
mlflow ui --backend-store-uri file://$PWD/mlruns --port 5000
```

## API

Run FastAPI:
```bash
uvicorn deployment.app:app --host 0.0.0.0 --port 8000
```

Predict:
```bash
curl -X POST "http://localhost:8000/predict" -F "file=@path/to/image.jpg"
```

## Docker

Build and run:
```bash
docker build -t final-project:v1 .
docker run -p 8000:8000 final-project:v1
```

## Kubernetes

```bash
minikube start
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl get pods
kubectl get services
```
