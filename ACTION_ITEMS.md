# CRITICAL ACTION ITEMS - DO THIS NOW

## 🚨 PRIORITY 1: MUST FIX BEFORE SUBMISSION

### 1. Fix GitHub Actions Workflow (.github/workflows/ci-cd.yml)
**Status:** ❌ Will fail on docker/setup-buildx-action@v3

Replace entire workflow with:
```yaml
name: CI/CD

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: 3.12
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Validate Python syntax
        run: |
          python -m py_compile src/data_loader.py src/model.py src/train.py src/evaluate.py deployment/app.py deployment/utils.py deployment/predict.py training/train_v1.py training/train_v2.py mlflow_tracking.py scripts/diagnose_model.py
      - name: Build Docker image
        run: docker build -t plant-disease-app:latest .
      - name: Test Docker build
        run: docker run --rm plant-disease-app:latest python -c "from src.model import get_model; print('Build successful')"
```

---

### 2. Train Model V2 and Save Weights
**Status:** ⚠️ v2.pth may not exist; Kubernetes will crash

**Run this command:**
```bash
python training/train_v2.py --data-dir ./Data/PlantVillage --epochs 10 --batch-size 24
```

This will create `models/plant_disease_v2.pth`

---

### 3. Create Model Comparison Report
**Status:** ❌ Missing v1 vs v2 analysis

Create file: `MODEL_COMPARISON_REPORT.md`

```markdown
# Model Comparison Report: V1 vs V2

## Training Results

| Metric | Model V1 | Model V2 | Improvement |
|--------|----------|----------|-------------|
| Best Validation Accuracy | X% | Y% | +Z% |
| Test Accuracy | X% | Y% | +Z% |
| Test Loss | X | Y | -Z% |
| Training Time | X min | Y min | Z% |
| Model Parameters | X | Y | +Z% |

## Architecture Differences

### Model V1 (Baseline)
- 4 convolutional blocks
- 256 channels max
- 512 classifier neurons
- Dropout: 0.4, 0.3

### Model V2 (Improved)
- 5 convolutional blocks
- 512 channels max
- 1024 classifier neurons
- Dropout: 0.5, 0.4
- Learning Rate Scheduler: StepLR

## Conclusion
Model V2 shows X% improvement in test accuracy over V1.
```

---

### 4. Add Transfer Learning (OPTIONAL but recommended)
**Status:** ❌ Not using pretrained weights

Modify `src/model.py` to add:
```python
def get_pretrained_model(num_classes: int = 15):
    import torchvision.models as models
    model = models.resnet50(pretrained=True)
    # Freeze early layers
    for param in model.layer1.parameters():
        param.requires_grad = False
    # Replace final layer
    model.fc = torch.nn.Linear(2048, num_classes)
    return model
```

Then use in training:
```bash
python training/train_v2.py --use-pretrained --data-dir ./Data/PlantVillage
```

---

### 5. Verify Model Files Exist
**Status:** ⚠️ Partially done

Check:
```bash
ls -la models/
# Should show:
# - plant_disease_v1.pth  ✓
# - plant_disease_v2.pth  (may be missing)
# - class_names.json      ✓
```

---

## 🟡 PRIORITY 2: STRONGLY RECOMMENDED

### 6. Add Unit Tests
Create `tests/test_models.py`:
```python
import torch
import pytest
from src.model import BaselineCNN, ImprovedCNN

class TestModels:
    def test_baseline_forward(self):
        model = BaselineCNN(num_classes=15)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 15)

    def test_improved_forward(self):
        model = ImprovedCNN(num_classes=15)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 15)
```

Run:
```bash
pip install pytest
pytest tests/
```

---

### 7. Add Early Stopping
Modify `src/train.py` to add:
```python
patience = 5
patience_counter = 0
best_val_loss = float('inf')

for epoch in range(1, num_epochs + 1):
    # ... training code ...
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch}")
            break
```

---

### 8. Pin Requirements.txt Versions
Replace ranges with exact versions:
```
torch==2.3.1
torchvision==0.18.1
numpy==1.26.4
pandas==2.2.0
scikit-learn==1.5.0
matplotlib==3.9.0
Pillow==10.3.0
mlflow==2.14.0
fastapi==0.111.0
uvicorn==0.30.0
python-multipart==0.0.9
opencv-python==4.10.0
efficientnet-pytorch==0.7.1
PyYAML==6.0
```

---

## 🟢 PRIORITY 3: NICE TO HAVE

### 9. Improve Logging
Add to `deployment/app.py`:
```python
import logging
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    try:
        app.state.model = load_model(...)
        logger.info(f"Model {MODEL_VERSION} loaded successfully")
    except Exception as exc:
        logger.error(f"Failed to load model: {exc}")
```

---

### 10. Add Response Models
Add to `deployment/app.py`:
```python
from pydantic import BaseModel

class PredictionResponse(BaseModel):
    class_name: str
    confidence: float
    index: int

@app.post("/predict", response_model=dict)
async def predict(file: UploadFile = File(...)):
    # ... existing code ...
    return {"prediction": result}
```

---

## 📋 SUBMISSION CHECKLIST

- [ ] GitHub Actions workflow fixed and passing
- [ ] Model V2 trained and saved to models/plant_disease_v2.pth
- [ ] Model comparison report created
- [ ] class_names.json exists (✓ already done)
- [ ] Docker image builds successfully
- [ ] Docker container runs and /health returns 200
- [ ] Kubernetes deployment tested
- [ ] MLflow UI shows both model runs
- [ ] FastAPI /predict endpoint works
- [ ] All Python files validate (syntax check passed)
- [ ] README complete with setup instructions
- [ ] Screenshots captured for documentation
- [ ] Git repository initialized with all files
- [ ] .gitignore properly configured

---

## 🚀 QUICK START COMMANDS

```bash
# 1. Activate environment
.\.venv\Scripts\Activate.ps1

# 2. Train V2 if not done
python training/train_v2.py --data-dir ./Data/PlantVillage --epochs 5

# 3. View MLflow
mlflow ui --port 5000

# 4. Test API
uvicorn deployment.app:app --reload

# 5. Build Docker
docker build -t final-project:v1 .

# 6. Run Docker
docker run -p 8000:8000 final-project:v1
```

Then screenshot everything!

---

**Expected time to complete: 2-3 hours**
**After fixes: Expected score: 85-92/100**
