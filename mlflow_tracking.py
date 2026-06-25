import argparse

from src.train import train_model


def parse_args():
    parser = argparse.ArgumentParser(description="Run MLflow tracked training for the plant disease detection project.")
    parser.add_argument("--version", choices=["v1", "v2", "both"], default="both")
    parser.add_argument("--data-dir", type=str, default="./Data/PlantVillage")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--learning-rate", type=float, default=0.001)
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
