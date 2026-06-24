import json
import os
import random
import sys
import time
from argparse import ArgumentParser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import mlflow
import torch
import torch.nn as nn
import torch.optim as optim
from mlflow import pytorch

from src.data_loader import get_dataloaders
from src.evaluate import evaluate_model
from src.model import get_model

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODELS_DIR = ROOT_DIR / "models"
DEFAULT_MLRUNS_DIR = ROOT_DIR / "mlruns"
DEFAULT_CLASS_NAMES_PATH = DEFAULT_MODELS_DIR / "class_names.json"
DEFAULT_DATA_DIR = Path(os.getenv("PLANTVILLAGE_PATH", "./data/PlantVillage"))
DEFAULT_DATA_DIR_FALLBACK = Path(r"C:\Users\hasna\Downloads\PlantVillage\PlantVillage")


def set_seed(seed: int = 42):
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def configure_mlflow(experiment_name: str, tracking_dir: Path = DEFAULT_MLRUNS_DIR):
    tracking_uri = tracking_dir.resolve().as_uri()
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    return tracking_uri


def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / total if total else 0.0
    epoch_acc = 100.0 * correct / total if total else 0.0
    return epoch_loss, epoch_acc


def build_optimizer_and_scheduler(model, version: str, lr: float):
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = None
    if version == "v2":
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.6)
    return optimizer, scheduler


def train_model(
    version: str,
    data_dir: str | Path,
    batch_size: int = 32,
    num_epochs: int = 15,
    learning_rate: float = 0.001,
    experiment_name: str = "plant_disease_detection",
    skip_if_exists: bool = False,
):
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(data_dir).expanduser()

    if not data_dir.exists():
        data_dir = DEFAULT_DATA_DIR_FALLBACK

    print("=" * 70)
    print(f"Starting {version.upper()} training")
    print(f"Dataset directory: {data_dir}")
    print(f"Device: {device}")
    print("=" * 70)

    train_loader, val_loader, test_loader, class_names = get_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size,
    )

    model = get_model(version=version, num_classes=len(class_names)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer, scheduler = build_optimizer_and_scheduler(model, version, learning_rate)

    tracking_uri = configure_mlflow(experiment_name)
    print(f"MLflow tracking URI: {tracking_uri}")

    best_model_path = DEFAULT_MODELS_DIR / f"plant_disease_{version}.pth"
    DEFAULT_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if skip_if_exists and best_model_path.exists():
        print(f"Skipping {version} training because model already exists at {best_model_path}")
        return {
            "version": version,
            "model_path": str(best_model_path),
            "status": "skipped",
        }

    best_val_acc = 0.0

    with mlflow.start_run(run_name=f"{version}_{int(time.time())}") as run:
        mlflow.log_params(
            {
                "version": version,
                "batch_size": batch_size,
                "epochs": num_epochs,
                "learning_rate": learning_rate,
                "optimizer": "Adam",
                "loss": "CrossEntropyLoss",
            }
        )

        if version == "v2":
            mlflow.log_param("scheduler", "StepLR(step_size=5,gamma=0.6)")

        for epoch in range(1, num_epochs + 1):
            train_loss, train_acc = train_one_epoch(
                model, train_loader, criterion, optimizer, device
            )
            val_loss, val_acc = evaluate_model(model, val_loader, criterion, device)

            if scheduler is not None:
                scheduler.step()

            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("train_accuracy", train_acc, step=epoch)
            mlflow.log_metric("val_accuracy", val_acc, step=epoch)

            print(
                f"Epoch [{epoch}/{num_epochs}] "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%"
            )

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(model.state_dict(), best_model_path)
                print(f"Saved best model: {best_model_path} (Val Acc: {best_val_acc:.2f}%)")

        test_loss, test_acc = evaluate_model(model, test_loader, criterion, device)
        mlflow.log_metric("test_loss", test_loss)
        mlflow.log_metric("test_accuracy", test_acc)

        mlflow.log_artifact(str(best_model_path), artifact_path="model_artifacts")

        metrics = {
            "version": version,
            "device": str(device),
            "train_samples": len(train_loader.dataset),
            "val_samples": len(val_loader.dataset),
            "test_samples": len(test_loader.dataset),
            "best_val_accuracy": best_val_acc,
            "test_accuracy": test_acc,
            "best_val_loss": val_loss,
            "test_loss": test_loss,
            "model_path": str(best_model_path),
            "class_names_path": str(DEFAULT_CLASS_NAMES_PATH),
            "run_id": run.info.run_id,
        }

        save_json(metrics, DEFAULT_MODELS_DIR / f"metrics_{version}.json")
        save_json(class_names, DEFAULT_CLASS_NAMES_PATH)

        print("=" * 70)
        print(f"{version.upper()} training completed")
        print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
        print(f"Test Accuracy: {test_acc:.2f}%")
        print("=" * 70)

    return metrics


def compare_models():
    v1_path = DEFAULT_MODELS_DIR / "metrics_v1.json"
    v2_path = DEFAULT_MODELS_DIR / "metrics_v2.json"

    if not v1_path.exists() or not v2_path.exists():
        print("Skipping comparison: both v1 and v2 metrics files must exist.")
        return

    with open(v1_path, "r", encoding="utf-8") as handle:
        v1_metrics = json.load(handle)

    with open(v2_path, "r", encoding="utf-8") as handle:
        v2_metrics = json.load(handle)

    print("Model comparison summary")
    print("=" * 70)
    print(
        "Metric\t\tV1\t\tV2\n"
        f"Best Val Acc\t{v1_metrics['best_val_accuracy']:.2f}%\t\t{v2_metrics['best_val_accuracy']:.2f}%\n"
        f"Test Acc\t\t{v1_metrics['test_accuracy']:.2f}%\t\t{v2_metrics['test_accuracy']:.2f}%\n"
        f"Test Loss\t\t{v1_metrics['test_loss']:.4f}\t\t{v2_metrics['test_loss']:.4f}\n"
    )
    print("=" * 70)


def parse_args():
    parser = ArgumentParser(description="Train a plant disease detection model with MLflow.")
    parser.add_argument("--version", choices=["v1", "v2", "both"], default="both")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(DEFAULT_DATA_DIR),
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip training if the model weights already exist in models/",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.version in {"v1", "both"}:
        train_model(
            version="v1",
            data_dir=args.data_dir,
            batch_size=args.batch_size,
            num_epochs=args.epochs,
            learning_rate=args.learning_rate,
        )
    if args.version in {"v2", "both"}:
        train_model(
            version="v2",
            data_dir=args.data_dir,
            batch_size=args.batch_size,
            num_epochs=args.epochs,
            learning_rate=args.learning_rate * 0.5,
        )
    compare_models()
