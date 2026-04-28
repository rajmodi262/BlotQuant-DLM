"""
BlotQuant Patch-Based Forensic Analysis (EfficientNet-B0)

Divides the image into an N×N grid of patches and scores each
for manipulation indicators using EfficientNet-B0 features.

The resulting heatmap reveals spatially-localized anomalies
that global analysis (ResNet18) would miss.

Reference:
  - Tan & Le, "EfficientNet: Rethinking Model Scaling", ICML 2019
  - Patch-based forensic analysis approach inspired by Proofig & Imagetwin
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

_TORCH_AVAILABLE = False
_eff_model = None
_eff_transform = None

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    _TORCH_AVAILABLE = True
except ImportError:
    pass


def _load_efficientnet():
    """Load and cache EfficientNet-B0 as a feature extractor."""
    global _eff_model, _eff_transform
    if _eff_model is not None:
        return _eff_model, _eff_transform

    if not _TORCH_AVAILABLE:
        return None, None

    logger.info("Loading EfficientNet-B0 for patch forensics...")
    weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
    model = models.efficientnet_b0(weights=weights)

    # Remove classifier — keep feature extractor (1280-dim)
    model.classifier = nn.Identity()
    for param in model.parameters():
        param.requires_grad = False
    model.eval()
    _eff_model = model

    _eff_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    logger.info("EfficientNet-B0 loaded (1280-dim feature extractor)")
    return _eff_model, _eff_transform


def _compute_patch_score(features: np.ndarray) -> float:
    """
    Score a single patch for anomaly indicators using feature statistics.
    
    Anomalous patches (manipulated regions) typically show:
    - Unusual activation patterns vs natural image statistics
    - Lower entropy (simpler/synthetic texture)
    - Extreme sparsity (over- or under-activated)
    """
    l2 = float(np.linalg.norm(features))
    sparsity = float(np.mean(features > 0))
    std = float(np.std(features))
    
    # Feature entropy
    hist, _ = np.histogram(features, bins=30, density=True)
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
    
    # Anomaly score: deviation from "natural" statistics
    # Natural images: moderate L2, balanced sparsity (~0.5), moderate entropy
    norm_dev = abs(l2 - 15.0) / 15.0  # deviation from typical L2
    sparsity_dev = abs(sparsity - 0.5) * 2
    entropy_dev = max(0, 1.0 - entropy / 6.0)
    
    score = (norm_dev * 0.3 + sparsity_dev * 0.3 + entropy_dev * 0.4)
    return round(min(1.0, max(0.0, score)), 3)


def compute_patch_forensics(image_bytes: bytes, grid_size: int = 8) -> Dict[str, Any]:
    """
    Divide image into grid_size × grid_size patches and analyze each.
    
    Returns:
        - patch_scores: 2D list of anomaly scores (0=clean, 1=suspicious)
        - max_score: highest anomaly in any patch
        - mean_score: average anomaly across all patches
        - suspicious_patches: list of (row, col) pairs with score > threshold
        - grid_size: the grid dimension used
    """
    model, transform = _load_efficientnet()
    
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return _fallback_patch_forensics(image_bytes, grid_size)

    h, w = img.shape[:2]
    patch_h = h // grid_size
    patch_w = w // grid_size
    
    patch_scores = []
    all_features = []
    
    for row in range(grid_size):
        row_scores = []
        for col in range(grid_size):
            y1, y2 = row * patch_h, (row + 1) * patch_h
            x1, x2 = col * patch_w, (col + 1) * patch_w
            patch = img[y1:y2, x1:x2]
            
            if patch.size == 0:
                row_scores.append(0.0)
                continue
            
            if model is not None:
                patch_rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
                tensor = transform(patch_rgb).unsqueeze(0)
                with torch.no_grad():
                    features = model(tensor).squeeze().numpy()
                score = _compute_patch_score(features)
                all_features.append(features)
            else:
                # Fallback: use OpenCV statistics
                score = _opencv_patch_score(patch)
            
            row_scores.append(score)
        patch_scores.append(row_scores)
    
    # Compute spatial consistency (how uniform scores are)
    flat_scores = [s for row in patch_scores for s in row]
    mean_score = round(float(np.mean(flat_scores)), 3)
    max_score = round(float(np.max(flat_scores)), 3)
    std_score = round(float(np.std(flat_scores)), 3)
    
    # Identify suspicious patches (>= 0.5 threshold)
    threshold = 0.5
    suspicious = []
    for r, row in enumerate(patch_scores):
        for c, s in enumerate(row):
            if s >= threshold:
                suspicious.append({"row": r, "col": c, "score": s})
    
    return {
        "patch_scores": patch_scores,
        "grid_size": grid_size,
        "max_score": max_score,
        "mean_score": mean_score,
        "std_score": std_score,
        "spatial_consistency": round(1.0 - std_score, 3),
        "suspicious_count": len(suspicious),
        "suspicious_patches": suspicious,
        "method": "efficientnet_b0_patch" if model is not None else "opencv_patch",
        "interpretation": (
            "No significant anomalies detected" if max_score < 0.4
            else "Mild anomalies in some regions" if max_score < 0.6
            else "Significant anomalies detected — review highlighted patches"
        ),
    }


def _opencv_patch_score(patch: np.ndarray) -> float:
    """Fallback patch scoring using OpenCV when PyTorch unavailable."""
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    
    # Laplacian variance (edge sharpness)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    edge_score = min(1.0, lap_var / 500)
    
    # Local noise estimation
    noise = float(np.std(gray.astype(float)))
    noise_score = abs(noise - 40) / 80  # deviation from typical noise
    
    # Histogram entropy
    hist = cv2.calcHist([gray], [0], None, [64], [0, 256]).flatten()
    hist = hist / (hist.sum() + 1e-10)
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
    entropy_score = max(0, 1.0 - entropy / 5.0)
    
    return round(min(1.0, edge_score * 0.3 + noise_score * 0.3 + entropy_score * 0.4), 3)


def _fallback_patch_forensics(image_bytes: bytes, grid_size: int) -> Dict[str, Any]:
    """Full fallback when image can't be decoded."""
    empty = [[0.0] * grid_size for _ in range(grid_size)]
    return {
        "patch_scores": empty, "grid_size": grid_size,
        "max_score": 0.0, "mean_score": 0.0, "std_score": 0.0,
        "spatial_consistency": 1.0, "suspicious_count": 0,
        "suspicious_patches": [], "method": "fallback",
        "interpretation": "Unable to analyze",
    }


def generate_ela_image(image_bytes: bytes, quality: int = 90) -> np.ndarray:
    """
    Generate Error Level Analysis image for forensic comparison.
    
    ELA works by re-compressing the image at a known quality level
    and computing the difference. Manipulated regions show different
    error levels than the rest of the image.
    
    Returns: BGR image of the ELA result (enhanced for visibility)
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    
    # Re-compress at given quality
    _, compressed = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    recompressed = cv2.imdecode(compressed, cv2.IMREAD_COLOR)
    
    # Compute absolute difference and amplify
    diff = cv2.absdiff(img, recompressed)
    ela = diff * 20  # Amplify differences for visibility
    ela = np.clip(ela, 0, 255).astype(np.uint8)
    
    return ela
