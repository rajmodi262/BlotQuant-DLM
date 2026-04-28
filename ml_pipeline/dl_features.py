"""
BlotQuant Deep Learning Feature Extractor
Uses pretrained ResNet18 as a fixed feature extractor for transfer learning.

This is real, citable deep learning:
  - ResNet18 pretrained on ImageNet (1.2M images, 1000 classes)
  - Frozen weights — used as a feature extractor (no training needed)
  - Outputs a 512-dimensional feature vector per image/ROI
  - Features encode texture, edges, contrast, and structure at multiple scales

Reference: He et al., "Deep Residual Learning for Image Recognition", CVPR 2016
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing PyTorch — graceful fallback if not available
_TORCH_AVAILABLE = False
_model = None
_transform = None

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    _TORCH_AVAILABLE = True
    logger.info("PyTorch available — DL features enabled")
except ImportError:
    logger.warning("PyTorch not installed — DL features will use fallback mode")


def _load_model():
    """Load and cache the ResNet18 feature extractor (lazy initialization)."""
    global _model, _transform
    if _model is not None:
        return _model, _transform

    if not _TORCH_AVAILABLE:
        return None, None

    logger.info("Loading ResNet18 pretrained model...")
    
    # Load pretrained ResNet18
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)
    
    # Remove the classification head — keep only the feature extractor
    # This outputs a 512-dimensional feature vector
    model.fc = nn.Identity()
    
    # Freeze all weights — we're using it as a fixed feature extractor
    for param in model.parameters():
        param.requires_grad = False
    
    model.eval()
    _model = model
    
    # Standard ImageNet preprocessing
    _transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
    
    logger.info("ResNet18 loaded successfully (512-dim feature extractor)")
    return _model, _transform


def extract_features(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Extract a 512-dimensional feature vector from an image using ResNet18.
    
    Returns numpy array of shape (512,) or None if PyTorch is unavailable.
    """
    model, transform = _load_model()
    if model is None:
        return None

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # Convert BGR to RGB for PyTorch
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Preprocess and extract
    input_tensor = transform(img_rgb).unsqueeze(0)  # Add batch dimension
    
    with torch.no_grad():
        features = model(input_tensor)
    
    return features.squeeze().numpy()


def extract_roi_features(image_bytes: bytes, bands: List[Dict]) -> List[np.ndarray]:
    """
    Extract ResNet18 feature vectors for each detected band ROI.
    
    Returns list of 512-dim feature vectors, one per band.
    """
    model, transform = _load_model()
    if model is None:
        return [None] * len(bands)

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return [None] * len(bands)

    h, w = img.shape[:2]
    features_list = []

    for band in bands:
        cx = band["position_x_pct"] / 100 * w
        cy = band["position_y_pct"] / 100 * h
        bw = band["width_pct"] / 100 * w
        bh = band["height_pct"] / 100 * h

        x1 = max(0, int(cx - bw / 2))
        y1 = max(0, int(cy - bh / 2))
        x2 = min(w, int(cx + bw / 2))
        y2 = min(h, int(cy + bh / 2))

        roi = img[y1:y2, x1:x2]
        if roi.size == 0:
            features_list.append(None)
            continue

        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        input_tensor = transform(roi_rgb).unsqueeze(0)
        
        with torch.no_grad():
            feat = model(input_tensor)
        
        features_list.append(feat.squeeze().numpy())

    return features_list


def compute_dl_quality_score(image_bytes: bytes) -> Dict[str, Any]:
    """
    Compute image quality metrics using ResNet18 feature analysis.
    
    The feature vector statistics reveal:
    - Feature magnitude (L2 norm) → overall signal strength
    - Feature sparsity → how many neurons activate strongly
    - Feature entropy → information richness
    - Feature std → variability in the representation
    
    Returns a quality score (0-1) and detailed metrics.
    """
    features = extract_features(image_bytes)
    
    if features is None:
        # Fallback: use OpenCV-based quality estimation
        return _fallback_quality_score(image_bytes)

    # Feature statistics
    l2_norm = float(np.linalg.norm(features))
    mean_activation = float(np.mean(features))
    std_activation = float(np.std(features))
    max_activation = float(np.max(features))
    sparsity = float(np.mean(features > 0))  # fraction of positive activations (ReLU)
    
    # Feature entropy (discretized)
    hist, _ = np.histogram(features, bins=50, density=True)
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
    
    # Normalize to quality score
    # High quality images have: moderate L2 norm, high entropy, balanced sparsity
    norm_score = min(1.0, l2_norm / 25.0)  # typical range 10-30
    entropy_score = min(1.0, entropy / 8.0)  # typical range 4-8
    sparsity_score = 1.0 - abs(sparsity - 0.5) * 2  # best around 0.5
    
    quality = round((norm_score * 0.3 + entropy_score * 0.4 + sparsity_score * 0.3), 3)
    quality = max(0.0, min(1.0, quality))

    return {
        "quality_score": quality,
        "method": "resnet18_feature_analysis",
        "metrics": {
            "feature_l2_norm": round(l2_norm, 2),
            "feature_mean": round(mean_activation, 4),
            "feature_std": round(std_activation, 4),
            "feature_max": round(max_activation, 4),
            "feature_sparsity": round(sparsity, 3),
            "feature_entropy": round(entropy, 3),
        },
        "interpretation": {
            "signal_strength": "strong" if l2_norm > 20 else "moderate" if l2_norm > 10 else "weak",
            "information_richness": "high" if entropy > 6 else "moderate" if entropy > 4 else "low",
            "activation_balance": "balanced" if 0.3 < sparsity < 0.7 else "imbalanced",
        },
    }


def compute_band_similarity(roi_features: List[np.ndarray]) -> Dict[str, Any]:
    """
    Compute pairwise cosine similarity between band ROI features.
    
    High similarity between bands in different lanes suggests:
    - Same protein detected across lanes (expected)
    - Or potential copy-paste manipulation (unexpected)
    
    Low similarity suggests different proteins or varying expression.
    """
    valid = [(i, f) for i, f in enumerate(roi_features) if f is not None]
    
    if len(valid) < 2:
        return {"similarity_matrix": [], "avg_similarity": 0.0, "method": "resnet18_cosine"}

    # Compute pairwise cosine similarity
    n = len(valid)
    sim_matrix = []
    similarities = []
    
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                a = valid[i][1]
                b = valid[j][1]
                cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
                row.append(round(cos_sim, 3))
                if j > i:
                    similarities.append(cos_sim)
        sim_matrix.append(row)

    avg_sim = round(float(np.mean(similarities)), 3) if similarities else 0.0
    max_sim = round(float(np.max(similarities)), 3) if similarities else 0.0

    return {
        "similarity_matrix": sim_matrix,
        "band_indices": [v[0] for v in valid],
        "avg_similarity": avg_sim,
        "max_similarity": max_sim,
        "method": "resnet18_cosine",
        "interpretation": (
            "High cross-band similarity detected — bands may represent the same protein or region"
            if max_sim > 0.95
            else "Normal variation in band features"
        ),
    }


def _fallback_quality_score(image_bytes: bytes) -> Dict[str, Any]:
    """OpenCV-based fallback when PyTorch is not available."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {"quality_score": 0.5, "method": "fallback", "metrics": {}}

    # Laplacian variance (blur detection)
    lap_var = cv2.Laplacian(img, cv2.CV_64F).var()
    blur_score = min(1.0, lap_var / 500)

    # Dynamic range
    dynamic_range = (float(img.max()) - float(img.min())) / 255
    
    # Histogram uniformity
    hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
    hist = hist / hist.sum()
    hist_entropy = float(-np.sum(hist[hist > 0] * np.log2(hist[hist > 0] + 1e-10)))
    entropy_score = min(1.0, hist_entropy / 8.0)

    quality = round(blur_score * 0.4 + dynamic_range * 0.3 + entropy_score * 0.3, 3)

    return {
        "quality_score": quality,
        "method": "opencv_fallback",
        "metrics": {
            "blur_score": round(blur_score, 3),
            "dynamic_range": round(dynamic_range, 3),
            "histogram_entropy": round(hist_entropy, 3),
        },
        "interpretation": {
            "sharpness": "sharp" if blur_score > 0.6 else "moderate" if blur_score > 0.3 else "blurry",
            "contrast": "good" if dynamic_range > 0.6 else "moderate" if dynamic_range > 0.3 else "low",
        },
    }
