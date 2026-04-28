"""
BlotQuant Grad-CAM — Explainable AI Attention Maps

Generates visual heatmaps showing which image regions drive 
ResNet18's quality score. Uses gradient-weighted class activation
mapping (Grad-CAM) on the final convolutional layer.

Reference: Selvaraju et al., "Grad-CAM: Visual Explanations from
Deep Networks via Gradient-based Localization", ICCV 2017
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

_TORCH_AVAILABLE = False
_gradcam_model = None
_gradcam_transform = None
_activations = None
_gradients = None

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    _TORCH_AVAILABLE = True
except ImportError:
    pass


def _hook_fn_forward(module, input, output):
    global _activations
    _activations = output.detach()


def _hook_fn_backward(module, grad_input, grad_output):
    global _gradients
    _gradients = grad_output[0].detach()


def _load_gradcam_model():
    """Load ResNet18 with hooks for Grad-CAM on layer4."""
    global _gradcam_model, _gradcam_transform
    if _gradcam_model is not None:
        return _gradcam_model, _gradcam_transform
    
    if not _TORCH_AVAILABLE:
        return None, None
    
    logger.info("Loading ResNet18 for Grad-CAM...")
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)
    model.eval()
    
    # Register hooks on the last convolutional layer (layer4)
    target_layer = model.layer4[-1].conv2
    target_layer.register_forward_hook(_hook_fn_forward)
    target_layer.register_full_backward_hook(_hook_fn_backward)
    
    _gradcam_model = model
    _gradcam_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])
    
    logger.info("Grad-CAM model ready (target: layer4)")
    return _gradcam_model, _gradcam_transform


def compute_gradcam(image_bytes: bytes) -> Dict[str, Any]:
    """
    Generate Grad-CAM heatmap for the input image.
    
    Returns:
        - heatmap: 2D list (7×7 grid) of attention weights (0-1)
        - focus_region: which quadrant has highest attention
        - attention_spread: how distributed the attention is
        - peak_attention: maximum attention value
    """
    global _activations, _gradients
    
    model, transform = _load_gradcam_model()
    if model is None:
        return _fallback_gradcam(image_bytes)
    
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return _fallback_gradcam(image_bytes)
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    input_tensor = transform(img_rgb).unsqueeze(0)
    input_tensor.requires_grad_(True)
    
    # Forward pass
    model.zero_grad()
    output = model(input_tensor)
    
    # Use the max class score as the target
    max_class = output.argmax(dim=1)
    score = output[0, max_class]
    
    # Backward pass
    score.backward()
    
    if _activations is None or _gradients is None:
        return _fallback_gradcam(image_bytes)
    
    # Grad-CAM computation
    weights = torch.mean(_gradients, dim=[2, 3], keepdim=True)  # Global avg pool gradients
    cam = torch.sum(weights * _activations, dim=1).squeeze()
    cam = torch.relu(cam)  # ReLU to keep only positive contributions
    
    # Normalize to [0, 1]
    if cam.max() > 0:
        cam = cam / cam.max()
    
    cam_np = cam.numpy()
    h, w = cam_np.shape  # Typically 7×7 for ResNet18
    
    # Convert to list for JSON serialization
    heatmap = [[round(float(cam_np[r, c]), 3) for c in range(w)] for r in range(h)]
    
    # Compute attention statistics
    flat = cam_np.flatten()
    peak = round(float(np.max(flat)), 3)
    mean_att = round(float(np.mean(flat)), 3)
    
    # Attention spread (entropy-like measure)
    normalized = flat / (flat.sum() + 1e-10)
    spread = round(float(-np.sum(normalized * np.log2(normalized + 1e-10))), 3)
    max_entropy = np.log2(len(flat))
    spread_ratio = round(spread / max_entropy, 3) if max_entropy > 0 else 0
    
    # Determine focus quadrant
    mid_r, mid_c = h // 2, w // 2
    quadrants = {
        "top_left": float(np.mean(cam_np[:mid_r, :mid_c])),
        "top_right": float(np.mean(cam_np[:mid_r, mid_c:])),
        "bottom_left": float(np.mean(cam_np[mid_r:, :mid_c])),
        "bottom_right": float(np.mean(cam_np[mid_r:, mid_c:])),
    }
    focus_region = max(quadrants, key=quadrants.get)
    
    return {
        "heatmap": heatmap,
        "grid_size": [h, w],
        "peak_attention": peak,
        "mean_attention": mean_att,
        "attention_spread": spread_ratio,
        "focus_region": focus_region,
        "quadrant_scores": {k: round(v, 3) for k, v in quadrants.items()},
        "method": "resnet18_gradcam",
        "interpretation": (
            f"Model attention concentrated in {focus_region.replace('_', ' ')} region. "
            f"Spread ratio: {spread_ratio} (1.0 = uniform, 0.0 = focused). "
            f"Peak attention: {peak}."
        ),
    }


def _fallback_gradcam(image_bytes: bytes) -> Dict[str, Any]:
    """Generate attention-like heatmap using edge detection when PyTorch unavailable."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        empty = [[0.0] * 7 for _ in range(7)]
        return {"heatmap": empty, "grid_size": [7, 7], "peak_attention": 0,
                "mean_attention": 0, "attention_spread": 0, "focus_region": "center",
                "quadrant_scores": {}, "method": "fallback", "interpretation": "N/A"}
    
    # Use Sobel edge magnitude as a proxy for "attention"
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)
    
    # Resize to 7×7 grid
    resized = cv2.resize(magnitude, (7, 7), interpolation=cv2.INTER_AREA)
    if resized.max() > 0:
        resized = resized / resized.max()
    
    heatmap = [[round(float(resized[r, c]), 3) for c in range(7)] for r in range(7)]
    
    return {
        "heatmap": heatmap, "grid_size": [7, 7],
        "peak_attention": round(float(resized.max()), 3),
        "mean_attention": round(float(resized.mean()), 3),
        "attention_spread": 0.5, "focus_region": "center",
        "quadrant_scores": {}, "method": "sobel_edge_fallback",
        "interpretation": "Edge-based attention proxy (PyTorch unavailable)",
    }
