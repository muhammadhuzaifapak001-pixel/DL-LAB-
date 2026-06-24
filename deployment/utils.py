import io
import json
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from src.model import get_model


def load_class_names(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Class names file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_transform(image_size: int = 224):
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def read_image_bytes(image_bytes: bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def preprocess_image(image_bytes: bytes, device: torch.device):
    image = read_image_bytes(image_bytes)
    transform = build_transform()
    tensor = transform(image).unsqueeze(0).to(device)
    return tensor


def load_model(model_path: Path, version: str, num_classes: int, device: torch.device):
    if not model_path.exists():
        raise FileNotFoundError(f"Model weights not found: {model_path}")

    model = get_model(version=version, num_classes=num_classes)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def predict_image(model, image_tensor: torch.Tensor, class_names):
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        score, index = torch.max(probabilities, dim=1)

    return {
        "class_name": class_names[index.item()],
        "confidence": float(score.item()),
        "index": int(index.item()),
    }
