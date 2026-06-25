Linux (WSL) setup and run instructions

Prerequisites
- WSL2 with Ubuntu 22.04+ or a Linux machine
- Docker (optional for container runs)

Quick setup

1. Clone the repo and enter workspace

```bash
git clone <your-repo-url>
cd DL(Lab)
```

2. Create virtualenv and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Prepare dataset

Download PlantVillage dataset and place it at `Data/PlantVillage` or set env variable:

```bash
export PLANTVILLAGE_PATH=/path/to/PlantVillage
```

4. Train baseline model (v1)

```bash
python training/train_v1.py --data-dir "$PLANTVILLAGE_PATH" --epochs 15 --batch-size 32
```

5. If needed, inspect existing model and generate placeholder `class_names.json`:

```bash
python scripts/diagnose_model.py --model-path models/plant_disease_v1.pth --out models/class_names.json
```

6. Run API locally

```bash
export MODEL_VERSION=v1
export CLASS_NAMES_PATH=./models/class_names.json
uvicorn deployment.app:app --host 0.0.0.0 --port 8000
```

7. Build Docker image

```bash
docker build -t final-project:v1 .
docker run -p 8000:8000 --env MODEL_VERSION=v1 --env CLASS_NAMES_PATH=/app/models/class_names.json final-project:v1
```

Notes
- Use Linux for training to avoid Windows-specific path issues and to match course requirements.
- The repo includes CI and Kubernetes manifests; adjust `kubernetes/deployment.yaml` to use `v1` by default if you don't have `v2` model weights.
