import os
from pathlib import Path
from typing import Tuple

import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset


def get_transforms(image_size: int = 224):
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    return train_transform, eval_transform


def get_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    random_seed: int = 42,
    image_size: int = 224,
):
    """Create train, validation, and test dataloaders."""

    data_path = Path(data_dir).expanduser()
    if not data_path.exists():
        alternate_path = None
        if not data_path.is_absolute():
            parts = data_path.parts
            if len(parts) > 1 and parts[0].lower() == "data":
                alternate_path = Path.cwd() / "Data" / Path(*parts[1:])
            else:
                alternate_path = Path.cwd() / "Data" / data_path.name

            if alternate_path.exists():
                print(f"Dataset directory not found at {data_path}. Using alternate path {alternate_path}.")
                data_path = alternate_path

        if not data_path.exists():
            raise FileNotFoundError(
                f"Dataset directory not found: {data_path}. "
                "Please provide a valid PlantVillage dataset path."
            )

    train_transform, eval_transform = get_transforms(image_size=image_size)

    train_full_dataset = datasets.ImageFolder(root=str(data_path), transform=train_transform)
    eval_full_dataset = datasets.ImageFolder(root=str(data_path), transform=eval_transform)

    total_size = len(train_full_dataset)
    if total_size == 0:
        raise ValueError("No images found in the provided dataset directory.")

    train_size = int(total_size * train_ratio)
    val_size = int(total_size * val_ratio)
    test_size = total_size - train_size - val_size

    generator = torch.Generator().manual_seed(random_seed)
    indices = torch.randperm(total_size, generator=generator).tolist()

    train_indices = indices[:train_size]
    val_indices = indices[train_size : train_size + val_size]
    test_indices = indices[train_size + val_size :]

    train_dataset = Subset(train_full_dataset, train_indices)
    val_dataset = Subset(eval_full_dataset, val_indices)
    test_dataset = Subset(eval_full_dataset, test_indices)

    num_workers = 2 if os.name == "nt" else min(os.cpu_count() or 2, 4)
    pin_memory = torch.cuda.is_available()

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    return train_loader, val_loader, test_loader, train_full_dataset.classes


if __name__ == "__main__":
    import json

    data_dir = os.getenv("PLANTVILLAGE_PATH", r"./data/PlantVillage")
    train_loader, val_loader, test_loader, classes = get_dataloaders(
        data_dir=data_dir,
        batch_size=16,
    )

    print(f"Loaded dataset from: {data_dir}")
    print(f"Classes: {len(classes)}")
    print(json.dumps(classes, indent=2))
    print(f"Train batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    print(f"Test batches: {len(test_loader)}")
