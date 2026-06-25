import argparse
from pathlib import Path

import torch

from deployment.utils import load_class_names, load_model, predict_image, preprocess_image


def main():
    parser = argparse.ArgumentParser(description="Run an offline prediction using a saved plant disease model.")
    parser.add_argument("--image-path", type=str, required=True, help="Path to the input image file.")
    parser.add_argument("--model-version", type=str, default="v1", choices=["v1", "v2"])
    parser.add_argument(
        "--model-path",
        type=str,
        default="./models/plant_disease_v1.pth",
        help="Path to the PyTorch model weights file.",
    )
    parser.add_argument(
        "--class-names-path",
        type=str,
        default="./models/class_names.json",
        help="Path to the class names JSON file.",
    )
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    class_names = load_class_names(Path(args.class_names_path))
    model = load_model(
        Path(args.model_path),
        version=args.model_version,
        num_classes=len(class_names),
        device=device,
    )

    with open(args.image_path, "rb") as image_file:
        image_bytes = image_file.read()

    tensor = preprocess_image(image_bytes, device)
    result = predict_image(model, tensor, class_names)
    print("Prediction:")
    print(result)


if __name__ == "__main__":
    main()
