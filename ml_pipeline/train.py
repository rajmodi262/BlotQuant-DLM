"""
BlotQuant Fine-Tuning Script — Train ResNet18 on Western Blot Quality Assessment

This script fine-tunes a pretrained ResNet18 on our labeled dataset of Western blot
images using heavy data augmentation (13 source images → 500+ augmented samples).

The model learns to predict a quality score (0-1) for blot images, replacing the
previous approach of using frozen ImageNet feature statistics.

Usage:
    python -m ml_pipeline.train

Output:
    ml_pipeline/weights/resnet18_blot_quality.pth
    ml_pipeline/weights/patch_classifier.pth
"""

import os
import sys
import json
import math
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
ROOT = Path(__file__).parent.parent
DATASET_DIR = ROOT / "data" / "dataset" / "images"
ANNOTATION_FILE = ROOT / "data" / "dataset" / "annotations" / "annotations.json"
WEIGHTS_DIR = Path(__file__).parent / "weights"
WEIGHTS_DIR.mkdir(exist_ok=True)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    from torchvision import models, transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.error("PyTorch is required for training. Install with: pip install torch torchvision")


# ─────────────────────────────────────────────
#  Quality Label Mapping
# ─────────────────────────────────────────────

QUALITY_MAP = {
    "excellent": 0.95,
    "good": 0.80,
    "moderate": 0.55,
    "poor": 0.25,
}

def _load_annotations() -> Dict[str, float]:
    """Load quality labels from annotations.json."""
    if not ANNOTATION_FILE.exists():
        logger.warning(f"Annotation file not found: {ANNOTATION_FILE}")
        return {}

    with open(ANNOTATION_FILE, "r") as f:
        data = json.load(f)

    labels = {}
    for entry in data:
        filename = entry.get("filename", "")
        quality = entry.get("annotations", {}).get("quality", {}).get("overall", "good")
        labels[filename] = QUALITY_MAP.get(quality, 0.6)

    return labels


# ─────────────────────────────────────────────
#  Augmentation-Heavy Dataset
# ─────────────────────────────────────────────

class BlotQualityDataset(Dataset):
    """
    Dataset that generates augmented samples from source images.
    
    With 13 source images and augmentation_factor=40, this produces 520 training
    samples — enough for effective transfer learning with a frozen backbone.
    """

    def __init__(self, image_dir: Path, labels: Dict[str, float], augmentation_factor: int = 40):
        self.samples = []
        self.labels_map = labels
        self.augmentation_factor = augmentation_factor

        for img_file in sorted(image_dir.glob("*.png")):
            quality = labels.get(img_file.name, 0.7)
            self.samples.append((img_file, quality))

        logger.info(f"Loaded {len(self.samples)} source images × {augmentation_factor} augmentations = {len(self)} training samples")

        # Heavy augmentation pipeline for blot images
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.1),
            transforms.RandomGrayscale(p=0.2),
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Clean transform for validation
        self.clean_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.samples) * self.augmentation_factor

    def __getitem__(self, idx):
        source_idx = idx % len(self.samples)
        img_path, quality = self.samples[source_idx]

        img = cv2.imread(str(img_path))
        if img is None:
            # Return a black image with neutral quality
            tensor = torch.zeros(3, 224, 224)
            return tensor, torch.tensor([0.5], dtype=torch.float32)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Apply augmentation
        tensor = self.transform(img_rgb)

        # Add noise to label for regularization (±0.05)
        noisy_quality = quality + np.random.uniform(-0.05, 0.05)
        noisy_quality = max(0.0, min(1.0, noisy_quality))

        return tensor, torch.tensor([noisy_quality], dtype=torch.float32)


# ─────────────────────────────────────────────
#  Model Architecture
# ─────────────────────────────────────────────

def build_quality_model() -> nn.Module:
    """
    ResNet18 with fine-tuned last 2 blocks + custom regression head.
    
    Architecture:
        ResNet18 (layer1-2 frozen, layer3-4 trainable)
        → AdaptiveAvgPool → 512-dim
        → Linear(512, 128) → ReLU → Dropout(0.3)
        → Linear(128, 1) → Sigmoid
    """
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)

    # Freeze early layers (generic features like edges, textures)
    for name, param in model.named_parameters():
        if "layer3" not in name and "layer4" not in name and "fc" not in name:
            param.requires_grad = False

    # Replace classification head with quality regression head
    model.fc = nn.Sequential(
        nn.Linear(512, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 1),
        nn.Sigmoid(),
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info(f"Model: {trainable:,} trainable / {total:,} total parameters ({trainable/total*100:.1f}%)")

    return model


def build_patch_classifier() -> nn.Module:
    """
    Small classifier head for patch-based forensics.
    
    Takes 1280-dim EfficientNet features → binary anomaly prediction.
    Trained on patches from good vs. degraded images.
    """
    return nn.Sequential(
        nn.Linear(1280, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 64),
        nn.ReLU(),
        nn.Linear(64, 1),
        nn.Sigmoid(),
    )


# ─────────────────────────────────────────────
#  Training Loop
# ─────────────────────────────────────────────

def train_quality_model(epochs: int = 25, lr: float = 1e-4, batch_size: int = 16):
    """Train the ResNet18 quality regression model."""
    logger.info("=" * 60)
    logger.info("  PHASE 1: Training ResNet18 Blot Quality Model")
    logger.info("=" * 60)

    labels = _load_annotations()
    if not labels:
        logger.error("No labels found. Cannot train.")
        return None

    # Also add the 3 sample-blot images with assumed quality
    for extra in ["sample-blot.png", "sample-blot-2.png", "sample-blot-3.png"]:
        extra_path = ROOT / "data" / "uploads" / extra
        if extra_path.exists():
            # Copy to dataset dir for training
            import shutil
            dest = DATASET_DIR / extra
            if not dest.exists():
                shutil.copy2(extra_path, dest)
            labels[extra] = 0.80 if "3" not in extra else 0.30  # sample-blot-3 is overexposed

    dataset = BlotQualityDataset(DATASET_DIR, labels, augmentation_factor=40)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=True)

    model = build_quality_model()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on: {device}")
    model = model.to(device)

    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.MSELoss()

    best_loss = float("inf")

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        n_batches = 0

        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        scheduler.step()
        avg_loss = total_loss / max(n_batches, 1)

        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), str(WEIGHTS_DIR / "resnet18_blot_quality.pth"))

        if (epoch + 1) % 5 == 0 or epoch == 0:
            logger.info(f"  Epoch {epoch+1:2d}/{epochs} | Loss: {avg_loss:.6f} | Best: {best_loss:.6f} | LR: {scheduler.get_last_lr()[0]:.2e}")

    logger.info(f"✓ Quality model saved to: {WEIGHTS_DIR / 'resnet18_blot_quality.pth'}")
    logger.info(f"  Final best loss: {best_loss:.6f}")
    return model


def train_patch_classifier(quality_model=None, epochs: int = 15, lr: float = 5e-4):
    """
    Train the patch-based forensics classifier.
    
    Strategy: Extract patches from good images (label=0, authentic) and
    from degraded/augmented images (label=1, anomalous).
    """
    logger.info("=" * 60)
    logger.info("  PHASE 2: Training Patch Forensics Classifier")
    logger.info("=" * 60)

    labels = _load_annotations()

    # Load EfficientNet for feature extraction
    weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
    effnet = models.efficientnet_b0(weights=weights)
    effnet.classifier = nn.Identity()
    for param in effnet.parameters():
        param.requires_grad = False
    effnet.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    effnet = effnet.to(device)

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Augmentation for generating "manipulated" patches
    degrade_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomResizedCrop(224, scale=(0.3, 0.6)),
        transforms.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.5),
        transforms.GaussianBlur(kernel_size=7, sigma=(2.0, 5.0)),
        transforms.RandomRotation(45),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    logger.info("  Extracting patch features from dataset...")
    features_list = []
    labels_list = []

    for img_file in sorted(DATASET_DIR.glob("*.png")):
        img = cv2.imread(str(img_file))
        if img is None:
            continue

        quality = labels.get(img_file.name, 0.7)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        grid_size = 4

        # Extract authentic patches from good images
        for row in range(grid_size):
            for col in range(grid_size):
                y1, y2 = row * (h // grid_size), (row + 1) * (h // grid_size)
                x1, x2 = col * (w // grid_size), (col + 1) * (w // grid_size)
                patch = img_rgb[y1:y2, x1:x2]
                if patch.size == 0:
                    continue

                # Authentic patch
                tensor = transform(patch).unsqueeze(0).to(device)
                with torch.no_grad():
                    feat = effnet(tensor).squeeze().cpu()
                features_list.append(feat)
                labels_list.append(0.0 if quality >= 0.6 else 1.0)

                # Generate degraded version as "anomalous"
                tensor_deg = degrade_transform(patch).unsqueeze(0).to(device)
                with torch.no_grad():
                    feat_deg = effnet(tensor_deg).squeeze().cpu()
                features_list.append(feat_deg)
                labels_list.append(1.0)

    features_tensor = torch.stack(features_list)
    labels_tensor = torch.tensor(labels_list, dtype=torch.float32).unsqueeze(1)

    logger.info(f"  Extracted {len(features_list)} patch features ({sum(1 for l in labels_list if l == 0)} clean, {sum(1 for l in labels_list if l == 1)} anomalous)")

    # Train classifier
    classifier = build_patch_classifier().to(device)
    optimizer = optim.Adam(classifier.parameters(), lr=lr)
    criterion = nn.BCELoss()

    dataset_size = len(features_tensor)
    for epoch in range(epochs):
        # Shuffle
        perm = torch.randperm(dataset_size)
        features_shuffled = features_tensor[perm].to(device)
        labels_shuffled = labels_tensor[perm].to(device)

        classifier.train()
        total_loss = 0.0
        batch_size = 32
        n_batches = 0

        for i in range(0, dataset_size, batch_size):
            batch_feat = features_shuffled[i:i+batch_size]
            batch_labels = labels_shuffled[i:i+batch_size]

            optimizer.zero_grad()
            pred = classifier(batch_feat)
            loss = criterion(pred, batch_labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            # Compute accuracy
            classifier.eval()
            with torch.no_grad():
                all_pred = classifier(features_tensor.to(device))
                predicted = (all_pred > 0.5).float()
                correct = (predicted == labels_tensor.to(device)).sum().item()
                accuracy = correct / len(labels_tensor) * 100
            logger.info(f"  Epoch {epoch+1:2d}/{epochs} | Loss: {avg_loss:.4f} | Accuracy: {accuracy:.1f}%")

    torch.save(classifier.state_dict(), str(WEIGHTS_DIR / "patch_classifier.pth"))
    logger.info(f"✓ Patch classifier saved to: {WEIGHTS_DIR / 'patch_classifier.pth'}")
    return classifier


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def main():
    if not TORCH_AVAILABLE:
        logger.error("PyTorch is required. Install: pip install torch torchvision")
        sys.exit(1)

    logger.info("🧬 BlotQuant Deep Learning Training Pipeline")
    logger.info(f"   Dataset: {DATASET_DIR}")
    logger.info(f"   Weights: {WEIGHTS_DIR}")
    logger.info("")

    # Phase 1: Quality model
    quality_model = train_quality_model(epochs=25, lr=1e-4)

    # Phase 2: Patch classifier
    patch_classifier = train_patch_classifier(quality_model, epochs=15)

    logger.info("")
    logger.info("=" * 60)
    logger.info("  ✅ ALL TRAINING COMPLETE")
    logger.info(f"  → resnet18_blot_quality.pth")
    logger.info(f"  → patch_classifier.pth")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
