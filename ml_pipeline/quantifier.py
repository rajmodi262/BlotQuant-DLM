"""
BlotQuant Intensity Quantifier (Densitometry)
Real OpenCV-based pixel intensity integration.

This replaces the LLM-generated fake intensity values with actual
densitometric measurements — the gold standard for Western blot analysis.
"""

import cv2
import numpy as np
from typing import List, Dict, Any


def quantify_intensities(image_bytes: bytes, bands: List[Dict]) -> List[Dict]:
    """
    For each detected band, compute real densitometric values:
      - integrated_density: sum of (255 - pixel) values in ROI
      - mean_intensity: average intensity (0-1, 1=darkest)
      - background_corrected: intensity after local background subtraction
    
    Returns the bands list with updated intensity values.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None or not bands:
        return bands

    h, w = img.shape[:2]
    
    # Collect raw integrated densities for normalization
    raw_densities = []
    updated_bands = []

    for band in bands:
        # Convert percentage positions to pixel coordinates
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
            updated_bands.append(band)
            raw_densities.append(0)
            continue

        # Invert: dark bands = high values
        inverted = 255 - roi

        # Local background estimation (border pixels)
        border_width = max(2, min(roi.shape[0], roi.shape[1]) // 6)
        bg_top = img[max(0, y1 - border_width):y1, x1:x2] if y1 > border_width else np.array([])
        bg_bottom = img[y2:min(h, y2 + border_width), x1:x2] if y2 + border_width < h else np.array([])
        
        bg_values = []
        if bg_top.size > 0:
            bg_values.extend((255 - bg_top).flatten().tolist())
        if bg_bottom.size > 0:
            bg_values.extend((255 - bg_bottom).flatten().tolist())
        
        bg_mean = np.mean(bg_values) if bg_values else 0

        # Integrated density (background corrected)
        corrected = np.clip(inverted.astype(float) - bg_mean, 0, 255)
        integrated_density = float(np.sum(corrected))
        
        # Raw integrated density
        raw_integrated = float(np.sum(inverted))
        
        # Mean intensity (normalized 0-1)
        mean_intensity = float(np.mean(corrected)) / 255.0

        band_copy = dict(band)
        band_copy["intensity_raw"] = int(raw_integrated)
        band_copy["intensity_bg_corrected"] = round(integrated_density, 1)
        band_copy["background_estimate"] = round(float(bg_mean), 1)
        
        updated_bands.append(band_copy)
        raw_densities.append(integrated_density)

    # Normalize intensities: max = 1.0
    max_density = max(raw_densities) if raw_densities else 1
    if max_density == 0:
        max_density = 1

    for i, band in enumerate(updated_bands):
        band["intensity"] = round(raw_densities[i] / max_density, 3)

    return updated_bands


def detect_normalization_strategy(bands: List[Dict]) -> Dict[str, Any]:
    """
    Infer normalization strategy by analyzing band patterns.
    
    Heuristics:
    - If there's a band present in every lane at similar MW → likely housekeeping protein
    - If total lane intensities are similar → total protein staining
    - Otherwise → no normalization detected
    """
    if not bands:
        return {
            "strategy": "none_detected",
            "reference_protein": None,
            "confidence": 0.0,
            "description": "No bands detected for normalization analysis."
        }

    # Group bands by lane
    lanes = {}
    for band in bands:
        lid = band.get("lane", 1)
        lanes.setdefault(lid, []).append(band)

    if len(lanes) < 2:
        return {
            "strategy": "none_detected",
            "reference_protein": None,
            "confidence": 0.3,
            "description": "Single lane detected. Normalization requires multiple lanes."
        }

    # Check for a common band across all lanes (similar MW ± 15 kDa)
    all_mws = []
    for lid, lane_bands in lanes.items():
        for b in lane_bands:
            all_mws.append((lid, b.get("molecular_weight_kda", 0), b.get("intensity", 0)))

    # Find MW values that appear in most lanes
    num_lanes = len(lanes)
    mw_buckets = {}
    for lid, mw, intensity in all_mws:
        bucket = round(mw / 15) * 15  # Group by 15 kDa buckets
        mw_buckets.setdefault(bucket, set()).add(lid)

    # Check if any MW bucket spans all lanes
    for bucket_mw, lane_set in mw_buckets.items():
        if len(lane_set) >= num_lanes * 0.8:
            # Common housekeeping proteins and their typical MWs
            housekeeping = {
                42: "β-Actin", 37: "GAPDH", 55: "α-Tubulin",
                50: "β-Tubulin", 90: "HSP90", 70: "HSP70",
            }
            
            closest_hk = None
            min_diff = float("inf")
            for hk_mw, hk_name in housekeeping.items():
                if abs(bucket_mw - hk_mw) < min_diff:
                    min_diff = abs(bucket_mw - hk_mw)
                    closest_hk = hk_name
            
            ref_name = closest_hk if min_diff < 20 else f"~{bucket_mw} kDa protein"
            
            return {
                "strategy": "housekeeping_protein",
                "reference_protein": ref_name,
                "confidence": round(len(lane_set) / num_lanes, 2),
                "description": f"A band at ~{bucket_mw} kDa is present across {len(lane_set)}/{num_lanes} lanes, consistent with a housekeeping protein loading control ({ref_name})."
            }

    # Check total protein normalization (similar total intensity per lane)
    lane_totals = []
    for lid in sorted(lanes.keys()):
        total = sum(b.get("intensity", 0) for b in lanes[lid])
        lane_totals.append(total)

    if lane_totals:
        cv = np.std(lane_totals) / max(np.mean(lane_totals), 0.001)
        if cv < 0.3:
            return {
                "strategy": "total_protein",
                "reference_protein": None,
                "confidence": round(1.0 - cv, 2),
                "description": f"Total lane intensities are relatively uniform (CV={cv:.2f}), suggesting total protein normalization."
            }

    return {
        "strategy": "none_detected",
        "reference_protein": None,
        "confidence": 0.5,
        "description": "No consistent loading control pattern detected across lanes."
    }
