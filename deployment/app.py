import os
import sys
from pathlib import Path

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile, status

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from deployment.utils import load_class_names, load_model, predict_image, preprocess_image

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
DEFAULT_MODEL_PATH = ROOT_DIR / "models" / f"plant_disease_{MODEL_VERSION}.pth"
DEFAULT_CLASS_NAMES_PATH = ROOT_DIR / "models" / "class_names.json"
MODEL_PATH = Path(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH))
CLASS_NAMES_PATH = Path(os.getenv("CLASS_NAMES_PATH", DEFAULT_CLASS_NAMES_PATH))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = FastAPI(title="Plant Disease Detection API", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    # Attempt to load class names and model, but don't crash the whole app on failure.
    try:
        app.state.class_names = load_class_names(CLASS_NAMES_PATH)
    except Exception as exc:
        app.state.class_names = None
        print(f"Warning: failed to load class names from {CLASS_NAMES_PATH}: {exc}")

    try:
        if app.state.class_names is not None:
            app.state.model = load_model(
                MODEL_PATH,
                MODEL_VERSION,
                num_classes=len(app.state.class_names),
                device=DEVICE,
            )
            app.state.model_version = MODEL_VERSION
        else:
            app.state.model = None
            app.state.model_version = MODEL_VERSION
            print("Model not loaded because class names are missing.")
    except Exception as exc:
        app.state.model = None
        app.state.model_version = MODEL_VERSION
        print(f"Warning: failed to load model from {MODEL_PATH}: {exc}")


@app.get("/")
async def root():
    return {
        "status": "Plant Disease Detection API is running",
        "model_version": app.state.model_version,
    }


@app.get("/health")
async def health():
    if getattr(app.state, "model", None) is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded")
    return {
        "status": "ok",
        "model_version": app.state.model_version,
        "device": str(DEVICE),
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a valid image file.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image file.")

    try:
        tensor = preprocess_image(image_bytes, DEVICE)
        result = predict_image(app.state.model, tensor, app.state.class_names)
        return {"prediction": result}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "deployment.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
