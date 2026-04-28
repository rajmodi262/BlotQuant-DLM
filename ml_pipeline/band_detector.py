"""
BlotQuant Band Detector
Uses OpenCV adaptive thresholding + contour detection for band localization.
This is a classical computer-vision approach that provides deterministic,
reproducible results — unlike an LLM call.

For production, this module can be swapped with a fine-tuned YOLOv8 model
once a labeled dataset is available.
"""

import cv2
import numpy as np
from typing import List, Dict, Any


def detect_bands(image_bytes: bytes) -> Dict[str, Any]:
    """
    Detect bands and lanes in a western blot image using
    adaptive thresholding and contour analysis.
    
    Returns dict matching the API schema:
      { "bands": [...], "lanes": [...] }
    """
    # Decode image
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"bands": [], "lanes": []}

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- Pre-processing ---
    # CLAHE for contrast enhancement (handles variable exposure)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

    # Adaptive threshold — works across different blot exposures
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=31,
        C=10
    )

    # Morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

    # --- Find contours ---
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by area and aspect ratio to find bands
    min_area = (h * w) * 0.0005   # at least 0.05% of image
    max_area = (h * w) * 0.15     # no more than 15%
    
    band_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = bw / max(bh, 1)
        # Bands are typically wider than tall (aspect > 0.5)
        if aspect < 0.3 or aspect > 15:
            continue
        band_contours.append((x, y, bw, bh, area))

    # Sort by position: top-to-bottom, then left-to-right
    band_contours.sort(key=lambda b: (b[1], b[0]))

    # --- Lane detection via vertical projection ---
    # Sum pixel intensities vertically to find lane boundaries
    vertical_proj = np.sum(thresh, axis=0).astype(float)
    vertical_proj = vertical_proj / vertical_proj.max() if vertical_proj.max() > 0 else vertical_proj
    
    # Smooth the projection
    kernel_size = max(w // 30, 5)
    if kernel_size % 2 == 0:
        kernel_size += 1
    smoothed = cv2.GaussianBlur(vertical_proj.reshape(1, -1), (kernel_size, 1), 0).flatten()
    
    # Find peaks in vertical projection (lane centers)
    lane_threshold = 0.15
    lane_centers = []
    in_peak = False
    peak_start = 0
    
    for i in range(len(smoothed)):
        if smoothed[i] > lane_threshold and not in_peak:
            in_peak = True
            peak_start = i
        elif (smoothed[i] <= lane_threshold or i == len(smoothed) - 1) and in_peak:
            in_peak = False
            center = (peak_start + i) // 2
            width = i - peak_start
            if width > w * 0.02:  # lane must be at least 2% of image width
                lane_centers.append((center, width))

    # Build lanes
    lanes = []
    for i, (center, lw) in enumerate(lane_centers):
        lanes.append({
            "id": i + 1,
            "label": f"Lane {i + 1}",
            "position_x_pct": round((center / w) * 100, 1),
            "width_pct": round((lw / w) * 100, 1),
        })

    # --- Assign bands to lanes ---
    bands = []
    for idx, (x, y, bw, bh, area) in enumerate(band_contours):
        band_center_x = x + bw / 2
        
        # Find closest lane
        lane_id = 1
        min_dist = float("inf")
        for lane in lanes:
            lane_x = (lane["position_x_pct"] / 100) * w
            dist = abs(band_center_x - lane_x)
            if dist < min_dist:
                min_dist = dist
                lane_id = lane["id"]

        # Extract ROI for intensity measurement
        roi = gray[y:y+bh, x:x+bw]
        raw_intensity = int(np.sum(255 - roi))
        # Normalize intensity: 0-1 where 1 = darkest
        mean_val = np.mean(roi)
        normalized_intensity = round(1.0 - (mean_val / 255.0), 3)

        # Estimate molecular weight from vertical position (rough linear scale)
        # Top of gel = high MW, bottom = low MW (typical range ~10-250 kDa)
        y_fraction = y / h
        estimated_mw = int(250 - (y_fraction * 240))

        # Confidence based on contour properties
        solidity = area / max(cv2.contourArea(cv2.convexHull(cnt)), 1)
        confidence = round(min(0.99, max(0.3, solidity * 0.7 + 0.3)), 2)

        bands.append({
            "id": idx + 1,
            "lane": lane_id,
            "label": f"Band {idx + 1}",
            "position_y_pct": round(((y + bh / 2) / h) * 100, 1),
            "position_x_pct": round(((x + bw / 2) / w) * 100, 1),
            "width_pct": round((bw / w) * 100, 1),
            "height_pct": round((bh / h) * 100, 1),
            "intensity": normalized_intensity,
            "intensity_raw": raw_intensity,
            "molecular_weight_kda": estimated_mw,
            "confidence": confidence,
        })

    # If no lanes were detected, create a single default lane
    if not lanes:
        lanes = [{"id": 1, "label": "Lane 1", "position_x_pct": 50.0, "width_pct": 80.0}]

    return {"bands": bands, "lanes": lanes}
