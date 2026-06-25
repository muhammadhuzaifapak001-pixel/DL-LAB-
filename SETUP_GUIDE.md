# SETUP & DEPLOYMENT GUIDE

Complete step-by-step instructions for all platforms.

## 📋 Prerequisites

- **Python 3.12+** (3.12.10 recommended)
- **Git** (for version control)
- **Docker** (optional, for containerization)
- **Kubernetes/Minikube** (optional, for orchestration)
- **~5GB disk space** (for dataset + dependencies)

---

## 🪟 WINDOWS SETUP

### 1. Clone Repository & Create Virtual Environment

```powershell
# Navigate to project directory
cd DL(Lab)

# Create Python 3.12 virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# If script execution is blocked:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install all requirements
pip install -r requirements.txt
```

**If PyTorch installation fails:**
```powershell
# Install CPU-only PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Then install remaining dependencies
pip install -r requirements.txt
```

### 3. Prepare Dataset

```powershell
# Create dataset directory
mkdir -Force .\Data\PlantVillage

# Copy PlantVillage images into this directory
# Expected structure:
# .\Data\PlantVillage\
#   ├── Apple___Apple_scab\
#   ├── Apple___Black_rot\
#   ├── ... (other disease classes)
#   └── ...
```

### 4. Verify Setup

```powershell
# Test imports
python -c "import torch, torchvision, mlflow, fastapi; print('✓ All imports OK')"

# Test data loading
python src/data_loader.py --help
```

---

## 🐧 LINUX / WSL2 SETUP

### Option A: Python 3.12 with Virtual Environment

```bash
# Install Python 3.12 (Ubuntu/Debian)
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Create virtual environment
python3.12 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Option B: Using Provided Script

```bash
# Make script executable
chmod +x scripts/setup_wsl_env.sh

# Run setup script (auto-handles torch installation)
bash scripts/setup_wsl_env.sh

# Activate after setup
source .venv312/bin/activate
```

### 3. Prepare Dataset (Linux)

```bash
# Create dataset directory
mkdir -p ./Data/PlantVillage

# Copy PlantVillage dataset images
# Set environment variable (optional)
export PLANTVILLAGE_PATH=/path/to/PlantVillage
```

### 4. Verify Setup

```bash
python -c "import torch, torchvision, mlflow, fastapi; print('✓ All imports OK')"
python src/data_loader.py
```

---

## 🚀 TRAINING MODELS

### Train Both Models (V1 & V2)

```bash
python src/train.py \
  --version both \
  --data-dir ./Data/PlantVillage \
  --epochs 15 \
  --batch-size 32
```

### Train Only V1 (Baseline)

```bash
python training/train_v1.py \
  --data-dir ./Data/PlantVillage \
  --epochs 15 \
  --batch-size 32
```

### Train Only V2 (Improved)

```bash
python training/train_v2.py \
  --data-dir ./Data/PlantVillage \
  --epochs 15 \
  --batch-size 24 \
  --learning-rate 0.0005
```

### Skip If Models Exist

```bash
python src/train.py --version both --data-dir ./Data/PlantVillage --skip-existing
```

**Output:**
- `models/plant_disease_v1.pth` - V1 model weights
- `models/plant_disease_v2.pth` - V2 model weights
- `models/class_names.json` - Dataset class names
- `models/metrics_v1.json` - V1 training metrics
- `models/metrics_v2.json` - V2 training metrics
- `mlruns/` - MLflow experiment tracking

---

## 📊 MLflow Experiment Tracking

### Start MLflow UI

```bash
mlflow ui --backend-store-uri file://$(pwd)/mlruns --port 5000
```

**On Windows PowerShell:**
```powershell
mlflow ui --backend-store-uri file://$PWD/mlruns --port 5000
```

**Access:** http://localhost:5000

### View Experiment Results

1. Open http://localhost:5000
2. Click on experiment: `plant_disease_detection`
3. Compare v1 and v2 runs:
   - Metrics: loss, accuracy over epochs
   - Parameters: learning rate, batch size, etc.
   - Artifacts: saved models, class names
4. Click "Compare" to see side-by-side metrics

---

## 🌐 API Deployment

### Run FastAPI Locally

```bash
uvicorn deployment.app:app --host 0.0.0.0 --port 8000 --reload
```

**Access:**
- API Root: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test Endpoints

#### 1. Health Check
```bash
curl -X GET http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "model_version": "v1",
  "device": "cuda" or "cpu"
}
```

#### 2. Root Endpoint
```bash
curl -X GET http://localhost:8000/
```

#### 3. Make Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@path/to/image.jpg"
```

Expected response:
```json
{
  "prediction": {
    "class_name": "class_5",
    "confidence": 0.94,
    "index": 5
  }
}
```

### Offline Prediction (CLI)

```bash
python deployment/predict.py \
  --image-path path/to/image.jpg \
  --model-version v1 \
  --model-path ./models/plant_disease_v1.pth \
  --class-names-path ./models/class_names.json
```

---

## 🐳 Docker Containerization

### Build Docker Image

```bash
docker build -t final-project:v1 .
```

**Verify:**
```bash
docker images final-project:v1
```

### Run Docker Container

```bash
docker run -p 8000:8000 final-project:v1
```

**With environment variables:**
```bash
docker run -p 8000:8000 \
  -e MODEL_VERSION=v1 \
  -e MODEL_PATH=/app/models/plant_disease_v1.pth \
  final-project:v1
```

**Test container:**
```bash
curl http://localhost:8000/health
```

### Docker Compose (Optional)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      MODEL_VERSION: v1
      PYTHONUNBUFFERED: 1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker-compose up
```

---

## ☸️ Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
# Install minikube (for local testing)
minikube start

# Verify cluster
kubectl cluster-info
```

### Deploy Application

```bash
# Apply deployment manifest
kubectl apply -f kubernetes/deployment.yaml

# Apply service manifest
kubectl apply -f kubernetes/service.yaml

# Check pods
kubectl get pods

# Check services
kubectl get services
```

### Access Application

```bash
# Port forward
kubectl port-forward svc/plant-disease-service 8000:8000

# Test
curl http://localhost:8000/health
```

### View Logs

```bash
# Get pod name
kubectl get pods -o name

# View logs
kubectl logs <pod-name>

# Tail logs
kubectl logs <pod-name> -f
```

### Cleanup

```bash
kubectl delete -f kubernetes/deployment.yaml
kubectl delete -f kubernetes/service.yaml
```

---

## 🧪 Unit Testing

### Run Tests

```bash
pip install pytest pytest-cov

pytest tests/ -v --cov=src --cov=deployment
```

### Create Test File

Create `tests/test_models.py`:
```python
import torch
import pytest
from src.model import BaselineCNN, ImprovedCNN

def test_baseline_output_shape():
    model = BaselineCNN(num_classes=15)
    x = torch.randn(2, 3, 224, 224)
    out = model(x)
    assert out.shape == (2, 15)

def test_improved_output_shape():
    model = ImprovedCNN(num_classes=15)
    x = torch.randn(2, 3, 224, 224)
    out = model(x)
    assert out.shape == (2, 15)
```

---

## 🔍 Code Quality Tools

### Linting

```bash
pip install flake8

flake8 src/ deployment/ training/ \
  --max-line-length=120 \
  --ignore=E501,W503
```

### Format Checking

```bash
pip install black

black --check src/ deployment/ training/

# Auto-fix
black src/ deployment/ training/
```

### Type Checking

```bash
pip install mypy

mypy src/ deployment/ --ignore-missing-imports
```

---

## 🐛 TROUBLESHOOTING

### Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'torch'`

**Solution:**
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows

# Or
source .venv/bin/activate  # Linux

# Install missing module
pip install torch torchvision
```

---

### Dataset Not Found

**Error:** `FileNotFoundError: Dataset directory not found`

**Solution:**
```bash
# Check directory exists
ls ./Data/PlantVillage  # Linux/Mac
dir .\Data\PlantVillage  # Windows

# Set environment variable
export PLANTVILLAGE_PATH=/path/to/dataset  # Linux
set PLANTVILLAGE_PATH=C:\path\to\dataset  # Windows
```

---

### Docker Build Fails

**Error:** `failed to solve: python:3.12-slim: failed to resolve source metadata`

**Solution:**
- Verify internet connection
- Try on Linux/WSL instead of Windows
- Check proxy settings in Docker Desktop

---

### Kubernetes Pod Crashes

**Error:** `CrashLoopBackOff`

**Solution:**
```bash
# Check logs
kubectl logs <pod-name>

# Verify model files exist
kubectl exec <pod-name> -- ls -la /app/models/

# Debug pod
kubectl describe pod <pod-name>
```

---

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

---

## 📞 Quick Reference Commands

```bash
# Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Training
python src/train.py --version both --data-dir ./Data/PlantVillage --epochs 5

# MLflow
mlflow ui --port 5000

# API
uvicorn deployment.app:app --reload

# Docker
docker build -t final-project:v1 .
docker run -p 8000:8000 final-project:v1

# Kubernetes
kubectl apply -f kubernetes/
kubectl get pods
kubectl port-forward svc/plant-disease-service 8000:8000

# Linting
flake8 src/
black src/
mypy src/

# Testing
pytest tests/ -v --cov=src
```

---

## 📚 Documentation Links

- [PyTorch Documentation](https://pytorch.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

**Last Updated:** 2026-06-25  
**Python Version:** 3.12+  
**Status:** Production Ready
