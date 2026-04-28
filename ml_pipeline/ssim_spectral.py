"""
BlotQuant SSIM + FFT Spectral Analysis

Two complementary analysis methods:
1. SSIM — Structural Similarity between band regions
2. FFT — Frequency domain analysis for artifact detection

References:
  - Wang et al., "Image Quality Assessment: From Error Visibility to 
    Structural Similarity", IEEE TIP 2004
  - Fridrich & Kodovsky, "Rich Models for Steganalysis", IEEE TIFS 2012
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────
#  SSIM Band Comparison
# ────────────────────────────────────────────────

def _ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Compute SSIM between two grayscale images (resized to match)."""
    size = (64, 64)
    a = cv2.resize(img1, size, interpolation=cv2.INTER_AREA)
    b = cv2.resize(img2, size, interpolation=cv2.INTER_AREA)
    
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    mu_a = np.mean(a)
    mu_b = np.mean(b)
    sigma_a = np.std(a)
    sigma_b = np.std(b)
    sigma_ab = np.mean((a - mu_a) * (b - mu_b))
    
    ssim_val = ((2 * mu_a * mu_b + C1) * (2 * sigma_ab + C2)) / \
               ((mu_a**2 + mu_b**2 + C1) * (sigma_a**2 + sigma_b**2 + C2))
    
    return round(float(ssim_val), 4)


def compute_ssim_analysis(image_bytes: bytes, bands: List[Dict]) -> Dict[str, Any]:
    """
    Compute SSIM between all band pairs and between bands and background.
    
    Returns:
        - inter_band_ssim: pairwise SSIM matrix between bands
        - band_bg_ssim: SSIM of each band vs background region
        - avg_inter_ssim: average pairwise SSIM
        - avg_bg_ssim: average band-to-background SSIM
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None or len(bands) < 1:
        return {"inter_band_ssim": [], "band_bg_ssim": [], "avg_inter_ssim": 0,
                "avg_bg_ssim": 0, "method": "ssim"}
    
    h, w = img.shape
    
    # Extract band ROIs
    rois = []
    for b in bands:
        cx = int(b["position_x_pct"] / 100 * w)
        cy = int(b["position_y_pct"] / 100 * h)
        bw = max(10, int(b["width_pct"] / 100 * w))
        bh = max(10, int(b["height_pct"] / 100 * h))
        x1, y1 = max(0, cx - bw // 2), max(0, cy - bh // 2)
        x2, y2 = min(w, cx + bw // 2), min(h, cy + bh // 2)
        roi = img[y1:y2, x1:x2]
        rois.append(roi if roi.size > 0 else np.zeros((10, 10), dtype=np.uint8))
    
    # Background sample (top-left corner, typically no bands)
    bg_h, bg_w = min(h // 4, 80), min(w // 4, 80)
    background = img[:bg_h, :bg_w]
    if background.size == 0:
        background = np.zeros((10, 10), dtype=np.uint8)
    
    # Inter-band SSIM matrix
    n = len(rois)
    ssim_matrix = []
    pairwise = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                s = _ssim(rois[i], rois[j])
                row.append(s)
                if j > i:
                    pairwise.append(s)
        ssim_matrix.append(row)
    
    # Band-to-background SSIM
    bg_ssims = [_ssim(roi, background) for roi in rois]
    
    avg_inter = round(float(np.mean(pairwise)), 4) if pairwise else 0.0
    avg_bg = round(float(np.mean(bg_ssims)), 4) if bg_ssims else 0.0
    
    return {
        "inter_band_ssim": ssim_matrix,
        "band_bg_ssim": bg_ssims,
        "avg_inter_ssim": avg_inter,
        "avg_bg_ssim": avg_bg,
        "max_inter_ssim": round(float(max(pairwise)), 4) if pairwise else 0.0,
        "method": "ssim",
        "interpretation": (
            "High inter-band similarity detected — possible duplication"
            if avg_inter > 0.9
            else "Normal structural variation between bands"
        ),
    }


# ────────────────────────────────────────────────
#  FFT Spectral Analysis
# ────────────────────────────────────────────────

def compute_spectral_analysis(image_bytes: bytes) -> Dict[str, Any]:
    """
    Perform 2D FFT analysis to detect:
    - Periodic noise patterns (scanner artifacts)
    - Frequency anomalies (compositing artifacts)
    - Power spectrum characteristics
    
    Returns spectral features and an 8×8 power spectrum grid.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {"power_spectrum": [], "has_periodic_noise": False,
                "dominant_frequency": 0, "spectral_entropy": 0, "method": "fft"}
    
    # Compute 2D FFT
    f_transform = np.fft.fft2(img.astype(np.float64))
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.abs(f_shift)
    
    # Log magnitude spectrum
    log_magnitude = np.log1p(magnitude)
    
    # Normalize to [0, 1]
    if log_magnitude.max() > 0:
        log_magnitude = log_magnitude / log_magnitude.max()
    
    # Downsample to 8×8 grid for visualization
    spectrum_grid = cv2.resize(log_magnitude, (8, 8), interpolation=cv2.INTER_AREA)
    power_spectrum = [[round(float(spectrum_grid[r, c]), 3) for c in range(8)] for r in range(8)]
    
    # Detect periodic noise (strong peaks away from center)
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    
    # Create a mask that excludes the DC component (center)
    mask = np.ones_like(magnitude, dtype=bool)
    r_exclude = min(h, w) // 8
    y_grid, x_grid = np.ogrid[:h, :w]
    center_mask = (y_grid - cy)**2 + (x_grid - cx)**2 <= r_exclude**2
    mask[center_mask] = False
    
    # Check for strong peaks in the masked region
    outer_values = magnitude[mask]
    threshold = np.mean(outer_values) + 4 * np.std(outer_values)
    peak_count = int(np.sum(magnitude[mask] > threshold))
    has_periodic_noise = peak_count > 5
    
    # Dominant frequency (distance from center of strongest peak)
    if outer_values.max() > 0:
        peak_idx = np.unravel_index(np.argmax(magnitude * mask), magnitude.shape)
        dominant_freq = round(float(np.sqrt((peak_idx[0] - cy)**2 + (peak_idx[1] - cx)**2)), 1)
    else:
        dominant_freq = 0.0
    
    # Spectral entropy
    flat_spec = spectrum_grid.flatten()
    flat_spec = flat_spec / (flat_spec.sum() + 1e-10)
    flat_spec = flat_spec[flat_spec > 0]
    spectral_entropy = round(float(-np.sum(flat_spec * np.log2(flat_spec + 1e-10))), 3)
    
    # Radial power distribution (energy at different frequency bands)
    radial_bins = 4
    radial_power = []
    max_r = min(h, w) // 2
    for i in range(radial_bins):
        r_inner = int(i * max_r / radial_bins)
        r_outer = int((i + 1) * max_r / radial_bins)
        ring_mask = ((y_grid - cy)**2 + (x_grid - cx)**2 >= r_inner**2) & \
                    ((y_grid - cy)**2 + (x_grid - cx)**2 < r_outer**2)
        ring_power = float(np.mean(log_magnitude[ring_mask])) if ring_mask.any() else 0
        radial_power.append(round(ring_power, 3))
    
    return {
        "power_spectrum": power_spectrum,
        "grid_size": 8,
        "has_periodic_noise": has_periodic_noise,
        "periodic_peak_count": peak_count,
        "dominant_frequency": dominant_freq,
        "spectral_entropy": spectral_entropy,
        "radial_power": radial_power,
        "method": "fft_2d",
        "interpretation": (
            f"Periodic noise detected ({peak_count} frequency peaks) — possible scanner artifacts"
            if has_periodic_noise
            else "No significant periodic noise — image appears naturally captured"
        ),
    }
