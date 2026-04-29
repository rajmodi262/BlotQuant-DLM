"""
BlotQuant Deep Learning Feature Extractor (v4.0 — Fine-Tuned)

Uses ResNet18 fine-tuned on Western blot quality data for domain-specific
quality assessment. Falls back to frozen ImageNet if fine-tuned weights
are not available.

Training: Run `python -m ml_pipeline.train` to generate weights.
Weights:  ml_pipeline/weights/resnet18_blot_quality.pth

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
_quality_model = None
_transform = None
_is_finetuned = False

WEIGHTS_DIR = Path(__file__).parent / "weights"

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    _TORCH_AVAILABLE = True
    logger.info("PyTorch available — DL features enabled")
except ImportError:
    logger.warning("PyTorch not installed — DL features will use fallback mode")


def _build_quality_head():
    """Build the quality regression head (must match train.py architecture)."""
    return nn.Sequential(
        nn.Linear(512, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 1),
        nn.Sigmoid(),
    )


def _load_model():
    """Load the feature extractor model (fine-tuned or frozen)."""
    global _model, _transform, _is_finetuned
    if _model is not None:
        return _model, _transform

    if not _TORCH_AVAILABLE:
        return None, None

    weights_path = WEIGHTS_DIR / "resnet18_blot_quality.pth"

    if weights_path.exists():
        # ✅ FINE-TUNED MODEL — trained on actual Western blot data
        logger.info("Loading FINE-TUNED ResNet18 (blot quality model)...")
        model = models.resnet18(weights=None)  # Don't load ImageNet weights
        model.fc = _build_quality_head()
        
        state_dict = torch.load(str(weights_path), map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)
        _is_finetuned = True
        logger.info("✓ Fine-tuned model loaded — domain-specific quality assessment active")
    else:
        # Fallback: frozen ImageNet features
        logger.warning("Fine-tuned weights not found. Using frozen ImageNet ResNet18.")
        logger.warning(f"  Run `python -m ml_pipeline.train` to generate: {weights_path}")
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights)
        model.fc = nn.Identity()
        _is_finetuned = False

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

    return _model, _transform


def _load_feature_extractor():
    """Load a ResNet18 without the fc head for feature extraction."""
    global _quality_model
    if _quality_model is not None:
        return _quality_model

    if not _TORCH_AVAILABLE:
        return None

    weights_path = WEIGHTS_DIR / "resnet18_blot_quality.pth"

    if weights_path.exists():
        model = models.resnet18(weights=None)
        model.fc = _build_quality_head()
        state_dict = torch.load(str(weights_path), map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)
        # Remove the fc head to get 512-dim features
        model.fc = nn.Identity()
    else:
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights)
        model.fc = nn.Identity()

    for param in model.parameters():
        param.requires_grad = False
    model.eval()
    _quality_model = model
    return _quality_model


def extract_features(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Extract a 512-dimensional feature vector from an image using ResNet18.
    
    Returns numpy array of shape (512,) or None if PyTorch is unavailable.
    """
    model = _load_feature_extractor()
    _, transform = _load_model()
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
    model = _load_feature_extractor()
    _, transform = _load_model()
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
    Compute image quality score using the fine-tuned ResNet18 model.
    
    If fine-tuned weights are available, the model directly predicts a quality
    score (0-1) trained on labeled Western blot data.
    
    If not, falls back to feature statistics analysis.
    """
    model, transform = _load_model()

    if model is None:
        return _fallback_quality_score(image_bytes)

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return _fallback_quality_score(image_bytes)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    input_tensor = transform(img_rgb).unsqueeze(0)

    with torch.no_grad():
        output = model(input_tensor)

    if _is_finetuned:
        # Direct quality prediction from fine-tuned model
        quality = round(float(output.squeeze().item()), 3)
        method = "resnet18_finetuned_blot"

        # Also extract features for detailed metrics
        features = extract_features(image_bytes)
        if features is not None:
            l2_norm = float(np.linalg.norm(features))
            sparsity = float(np.mean(features > 0))
            hist, _ = np.histogram(features, bins=50, density=True)
            hist = hist[hist > 0]
            entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
        else:
            l2_norm, sparsity, entropy = 0, 0, 0

        return {
            "quality_score": quality,
            "method": method,
            "model_type": "fine-tuned on Western blot dataset",
            "metrics": {
                "feature_l2_norm": round(l2_norm, 2),
                "feature_sparsity": round(sparsity, 3),
                "feature_entropy": round(entropy, 3),
            },
            "interpretation": {
                "signal_strength": "strong" if l2_norm > 20 else "moderate" if l2_norm > 10 else "weak",
                "information_richness": "high" if entropy > 6 else "moderate" if entropy > 4 else "low",
                "activation_balance": "balanced" if 0.3 < sparsity < 0.7 else "imbalanced",
            },
        }
    else:
        # Frozen ImageNet fallback — use feature statistics
        features = output.squeeze().numpy()
        l2_norm = float(np.linalg.norm(features))
        mean_activation = float(np.mean(features))
        std_activation = float(np.std(features))
        sparsity = float(np.mean(features > 0))
        
        hist, _ = np.histogram(features, bins=50, density=True)
        hist = hist[hist > 0]
        entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
        
        norm_score = min(1.0, l2_norm / 25.0)
        entropy_score = min(1.0, entropy / 8.0)
        sparsity_score = 1.0 - abs(sparsity - 0.5) * 2
        
        quality = round((norm_score * 0.3 + entropy_score * 0.4 + sparsity_score * 0.3), 3)
        quality = max(0.0, min(1.0, quality))

        return {
            "quality_score": quality,
            "method": "resnet18_imagenet_features",
            "model_type": "frozen ImageNet (not fine-tuned)",
            "metrics": {
                "feature_l2_norm": round(l2_norm, 2),
                "feature_mean": round(mean_activation, 4),
                "feature_std": round(std_activation, 4),
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
    """
    valid = [(i, f) for i, f in enumerate(roi_features) if f is not None]
    
    if len(valid) < 2:
        return {"similarity_matrix": [], "avg_similarity": 0.0, "method": "resnet18_cosine"}

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

    method = "resnet18_finetuned_cosine" if _is_finetuned else "resnet18_cosine"

    return {
        "similarity_matrix": sim_matrix,
        "band_indices": [v[0] for v in valid],
        "avg_similarity": avg_sim,
        "max_similarity": max_sim,
        "method": method,
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
        "model_type": "classical CV (no PyTorch)",
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
