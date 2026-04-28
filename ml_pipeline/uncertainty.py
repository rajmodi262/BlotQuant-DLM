"""
BlotQuant Uncertainty Quantification
Monte Carlo simulation for generating real confidence intervals.

Instead of asking an LLM to hallucinate CI values, this module:
1. Adds controlled Gaussian noise to the image
2. Re-runs the intensity measurement N times
3. Computes actual mean, std, and 95% CI from the distribution
"""

import cv2
import numpy as np
from typing import List, Dict, Any


def monte_carlo_uncertainty(
    image_bytes: bytes,
    bands: List[Dict],
    n_simulations: int = 30,
    noise_std: float = 8.0,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations to compute real uncertainty estimates.
    
    For each band:
      - Add Gaussian noise to the image N times
      - Re-measure intensity in the band ROI
      - Report mean, std, and 95% confidence interval
    
    Args:
        image_bytes: Raw image bytes
        bands: List of detected bands with position info
        n_simulations: Number of MC iterations (more = tighter CI)
        noise_std: Standard deviation of additive Gaussian noise
        seed: Random seed for reproducibility
    
    Returns:
        List of uncertainty records matching the API schema
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None or not bands:
        return []

    h, w = img.shape[:2]
    rng = np.random.RandomState(seed)
    
    uncertainty = []
    
    for band in bands:
        # Extract band ROI coordinates
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
            uncertainty.append({
                "band_id": band["id"],
                "mean_intensity": band.get("intensity", 0),
                "std_dev": 0.0,
                "ci_lower": band.get("intensity", 0),
                "ci_upper": band.get("intensity", 0),
                "confidence_level": 0.95,
            })
            continue

        # Run Monte Carlo simulations
        intensities = []
        for _ in range(n_simulations):
            # Add Gaussian noise
            noise = rng.normal(0, noise_std, roi.shape)
            noisy_roi = np.clip(roi.astype(float) + noise, 0, 255)
            
            # Measure intensity (inverted: dark = high)
            inverted = 255 - noisy_roi
            mean_val = np.mean(inverted) / 255.0
            intensities.append(mean_val)

        intensities = np.array(intensities)
        mean_i = float(np.mean(intensities))
        std_i = float(np.std(intensities))
        
        # 95% confidence interval
        ci_lower = float(np.percentile(intensities, 2.5))
        ci_upper = float(np.percentile(intensities, 97.5))

        uncertainty.append({
            "band_id": band["id"],
            "mean_intensity": round(mean_i, 4),
            "std_dev": round(std_i, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "confidence_level": 0.95,
        })

    return uncertainty
