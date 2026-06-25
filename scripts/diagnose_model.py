"""
Diagnostic helper to inspect a PyTorch model file and generate a placeholder class_names.json
Usage:
  python scripts/diagnose_model.py --model-path models/plant_disease_v1.pth --out models/class_names.json

This script must be run in an environment with torch installed (recommended: Linux/WSL).
"""
import argparse
import json
import logging
from pathlib import Path

import torch

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from src.model import get_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--version", choices=["v1", "v2"], default="v1")
    parser.add_argument("--out", type=str, default="models/class_names.json")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    out_path = Path(args.out)

    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        return

    # Load state dict to inspect final layer size
    state = torch.load(model_path, map_location="cpu")

    # Attempt to detect final linear layer weight shape
    num_classes = None
    for k, v in state.items():
        if k.endswith(".weight") and v.ndim == 2:
            # heuristic: classifier final layer often named classifier.6.weight or classifier.8.weight
            num_classes = v.shape[0]

    if num_classes is None:
        # fallback: instantiate model and inspect last layer
        model = get_model(version=args.version, num_classes=10)
        try:
            model.load_state_dict(state)
            for m in model.modules():
                if isinstance(m, torch.nn.Linear):
                    num_classes = m.out_features
        except Exception:
            pass

    if num_classes is None:
        logger.error("Could not determine number of classes from the model. Please provide class_names.json manually.")
        return

    logger.info(f"Detected num_classes={num_classes}")

    # Create placeholder class names
    class_names = [f"class_{i}" for i in range(num_classes)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)

    logger.info(f"Wrote placeholder class names to {out_path}")


if __name__ == "__main__":
    main()
