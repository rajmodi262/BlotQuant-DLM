"""
BlotQuant Extended Analysis Features
Additional signal-processing and quality metrics for comprehensive blot analysis.

These complement the DL features with domain-specific measurements.
"""

import cv2
import numpy as np
from typing import Dict, Any, List


def compute_extended_features(image_bytes: bytes, bands: List[Dict], lanes: List[Dict]) -> Dict[str, Any]:
    """
    Compute all extended analysis features in one pass.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    features = {}

    # 1. Signal-to-Noise Ratio per band
    features["snr"] = _compute_snr(gray, bands, h, w)

    # 2. Lane Uniformity
    features["lane_uniformity"] = _compute_lane_uniformity(bands, lanes)

    # 3. Band Sharpness (Laplacian variance per ROI)
    features["band_sharpness"] = _compute_band_sharpness(gray, bands, h, w)

    # 4. Background Gradient Analysis
    features["background_gradient"] = _compute_background_gradient(gray)

    # 5. Saturation Check
    features["saturation"] = _compute_saturation(gray)

    # 6. Band Symmetry Scores
    features["band_symmetry"] = _compute_band_symmetry(gray, bands, h, w)

    # 7. Gel Loading Evenness
    features["loading_evenness"] = _compute_loading_evenness(bands, lanes)

    # 8. Transfer Efficiency
    features["transfer_efficiency"] = _compute_transfer_efficiency(gray)

    # 9. Dynamic Range
    features["dynamic_range"] = {
        "min_pixel": int(gray.min()),
        "max_pixel": int(gray.max()),
        "range": int(gray.max()) - int(gray.min()),
        "range_pct": round((int(gray.max()) - int(gray.min())) / 255 * 100, 1),
        "status": "good" if (gray.max() - gray.min()) > 150 else "moderate" if (gray.max() - gray.min()) > 80 else "poor",
    }

    # 10. Overall image statistics
    features["image_stats"] = {
        "width": w,
        "height": h,
        "mean_intensity": round(float(gray.mean()), 1),
        "std_intensity": round(float(gray.std()), 1),
        "total_bands": len(bands),
        "total_lanes": len(lanes),
    }

    return features


def _compute_snr(gray: np.ndarray, bands: List[Dict], h: int, w: int) -> Dict:
    """Signal-to-Noise Ratio: band signal vs local background noise."""
    snr_values = []
    for band in bands:
        cx = band["position_x_pct"] / 100 * w
        cy = band["position_y_pct"] / 100 * h
        bw = band["width_pct"] / 100 * w
        bh = band["height_pct"] / 100 * h
        x1, y1 = max(0, int(cx - bw/2)), max(0, int(cy - bh/2))
        x2, y2 = min(w, int(cx + bw/2)), min(h, int(cy + bh/2))

        roi = gray[y1:y2, x1:x2]
        if roi.size == 0:
            snr_values.append(0)
            continue

        signal = 255 - float(np.mean(roi))  # inverted: dark = signal

        # Background: region above and below the band
        bg_regions = []
        pad = max(int(bh * 0.5), 5)
        if y1 - pad > 0:
            bg_regions.append(gray[max(0, y1-pad):y1, x1:x2])
        if y2 + pad < h:
            bg_regions.append(gray[y2:min(h, y2+pad), x1:x2])
        
        if bg_regions:
            bg = np.concatenate([r.flatten() for r in bg_regions if r.size > 0])
            noise = float(np.std(bg)) if bg.size > 0 else 1.0
        else:
            noise = 1.0

        snr = signal / max(noise, 0.01)
        snr_values.append(round(snr, 2))

    avg_snr = round(float(np.mean(snr_values)), 2) if snr_values else 0
    return {
        "per_band": snr_values,
        "average": avg_snr,
        "status": "excellent" if avg_snr > 10 else "good" if avg_snr > 5 else "moderate" if avg_snr > 2 else "poor",
    }


def _compute_lane_uniformity(bands: List[Dict], lanes: List[Dict]) -> Dict:
    """How uniform is the total intensity across lanes."""
    lane_totals = {}
    for band in bands:
        lid = band.get("lane", 1)
        lane_totals.setdefault(lid, 0)
        lane_totals[lid] += band.get("intensity", 0)

    if len(lane_totals) < 2:
        return {"cv": 0, "status": "single_lane", "lane_totals": lane_totals}

    values = list(lane_totals.values())
    mean_val = np.mean(values)
    std_val = np.std(values)
    cv = round(float(std_val / max(mean_val, 0.001)), 3)

    return {
        "cv": cv,
        "lane_totals": {str(k): round(v, 3) for k, v in lane_totals.items()},
        "status": "uniform" if cv < 0.2 else "moderate" if cv < 0.5 else "uneven",
    }


def _compute_band_sharpness(gray: np.ndarray, bands: List[Dict], h: int, w: int) -> Dict:
    """Laplacian variance of each band — measures edge sharpness."""
    sharpness = []
    for band in bands:
        cx = band["position_x_pct"] / 100 * w
        cy = band["position_y_pct"] / 100 * h
        bw = band["width_pct"] / 100 * w
        bh = band["height_pct"] / 100 * h
        x1, y1 = max(0, int(cx - bw/2)), max(0, int(cy - bh/2))
        x2, y2 = min(w, int(cx + bw/2)), min(h, int(cy + bh/2))

        roi = gray[y1:y2, x1:x2]
        if roi.size < 9:
            sharpness.append(0)
            continue

        lap = cv2.Laplacian(roi, cv2.CV_64F)
        sharpness.append(round(float(lap.var()), 1))

    avg = round(float(np.mean(sharpness)), 1) if sharpness else 0
    return {
        "per_band": sharpness,
        "average": avg,
        "status": "sharp" if avg > 200 else "moderate" if avg > 50 else "blurry",
    }


def _compute_background_gradient(gray: np.ndarray) -> Dict:
    """Detect if there's a systematic gradient across the membrane."""
    h, w = gray.shape

    # Sample background from top and bottom strips
    top_strip = gray[:int(h * 0.1), :].mean()
    bottom_strip = gray[int(h * 0.9):, :].mean()
    left_strip = gray[:, :int(w * 0.1)].mean()
    right_strip = gray[:, int(w * 0.9):].mean()

    vertical_gradient = abs(float(top_strip - bottom_strip))
    horizontal_gradient = abs(float(left_strip - right_strip))

    return {
        "vertical": round(vertical_gradient, 1),
        "horizontal": round(horizontal_gradient, 1),
        "status": (
            "uniform" if max(vertical_gradient, horizontal_gradient) < 15
            else "mild_gradient" if max(vertical_gradient, horizontal_gradient) < 40
            else "significant_gradient"
        ),
    }


def _compute_saturation(gray: np.ndarray) -> Dict:
    """Check for clipped pixels (over/under-exposed regions)."""
    total = gray.size
    blacks = int(np.sum(gray <= 5))
    whites = int(np.sum(gray >= 250))

    return {
        "black_pixels": blacks,
        "white_pixels": whites,
        "black_pct": round(blacks / total * 100, 2),
        "white_pct": round(whites / total * 100, 2),
        "status": (
            "good" if (blacks / total < 0.02 and whites / total < 0.02)
            else "moderate_clipping" if (blacks / total < 0.1 and whites / total < 0.1)
            else "severe_clipping"
        ),
    }


def _compute_band_symmetry(gray: np.ndarray, bands: List[Dict], h: int, w: int) -> Dict:
    """Score how symmetric each band is (left vs right half of ROI)."""
    symmetry = []
    for band in bands:
        cx = band["position_x_pct"] / 100 * w
        cy = band["position_y_pct"] / 100 * h
        bw = band["width_pct"] / 100 * w
        bh = band["height_pct"] / 100 * h
        x1, y1 = max(0, int(cx - bw/2)), max(0, int(cy - bh/2))
        x2, y2 = min(w, int(cx + bw/2)), min(h, int(cy + bh/2))

        roi = gray[y1:y2, x1:x2]
        if roi.size < 4 or roi.shape[1] < 2:
            symmetry.append(0.5)
            continue

        mid = roi.shape[1] // 2
        left = roi[:, :mid].astype(float)
        right = roi[:, -mid:][:, ::-1].astype(float)  # flip right half

        if left.shape != right.shape:
            min_w = min(left.shape[1], right.shape[1])
            left = left[:, :min_w]
            right = right[:, :min_w]

        if left.size == 0:
            symmetry.append(0.5)
            continue

        diff = np.mean(np.abs(left - right))
        sym_score = max(0, 1.0 - diff / 128)
        symmetry.append(round(sym_score, 3))

    avg = round(float(np.mean(symmetry)), 3) if symmetry else 0.5
    return {
        "per_band": symmetry,
        "average": avg,
        "status": "symmetric" if avg > 0.8 else "moderate" if avg > 0.6 else "asymmetric",
    }


def _compute_loading_evenness(bands: List[Dict], lanes: List[Dict]) -> Dict:
    """How evenly protein was loaded across lanes."""
    lane_intensities = {}
    for band in bands:
        lid = band.get("lane", 1)
        lane_intensities.setdefault(lid, []).append(band.get("intensity", 0))

    lane_sums = {k: sum(v) for k, v in lane_intensities.items()}
    
    if not lane_sums:
        return {"evenness_score": 0, "status": "no_data"}

    values = list(lane_sums.values())
    ideal = np.mean(values)
    deviations = [abs(v - ideal) / max(ideal, 0.001) for v in values]
    evenness = max(0, 1.0 - np.mean(deviations))

    return {
        "evenness_score": round(float(evenness), 3),
        "lane_sums": {str(k): round(v, 3) for k, v in lane_sums.items()},
        "status": "even" if evenness > 0.8 else "moderate" if evenness > 0.5 else "uneven",
    }


def _compute_transfer_efficiency(gray: np.ndarray) -> Dict:
    """Analyze intensity gradient across the membrane as a proxy for transfer efficiency."""
    h, w = gray.shape

    # Divide into horizontal strips and measure average intensity
    n_strips = 5
    strip_h = h // n_strips
    strip_means = []
    for i in range(n_strips):
        strip = gray[i * strip_h:(i + 1) * strip_h, :]
        strip_means.append(float(strip.mean()))

    # Check for systematic falloff (poor transfer)
    diffs = [strip_means[i+1] - strip_means[i] for i in range(len(strip_means)-1)]
    max_diff = max(abs(d) for d in diffs) if diffs else 0
    
    # Score: small gradients = good transfer
    score = max(0, 1.0 - max_diff / 50)

    return {
        "score": round(score, 3),
        "strip_means": [round(m, 1) for m in strip_means],
        "max_gradient": round(max_diff, 1),
        "status": "efficient" if score > 0.8 else "moderate" if score > 0.5 else "poor",
    }
