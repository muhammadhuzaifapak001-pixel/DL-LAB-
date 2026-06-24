import argparse

from src.train import train_model


def parse_args():
    parser = argparse.ArgumentParser(description="Train the improved v2 plant disease model.")
    parser.add_argument("--data-dir", type=str, default="./data/PlantVillage")
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--learning-rate", type=float, default=0.0005)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train_model(
        version="v2",
        data_dir=args.data_dir,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
