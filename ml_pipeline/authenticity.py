"""
BlotQuant Authenticity Scorer
Image forensics for detecting potential manipulation in Western blots.

Uses multiple real signal-processing techniques:
1. Error Level Analysis (ELA) — detects JPEG re-compression artifacts
2. Noise consistency analysis — spliced regions have different noise profiles
3. Edge coherence — manipulated bands often have unnaturally sharp edges
4. Copy-move detection via ORB feature matching

This replaces the LLM "guess" with actual forensic measurements.
"""

import cv2
import numpy as np
from typing import Dict, Any, List


def score_authenticity(image_bytes: bytes) -> Dict[str, Any]:
    """
    Run forensic analysis on a western blot image.
    
    Returns dict matching API schema:
    {
        "score": 0.0 - 1.0  (1 = likely authentic),
        "classification": "likely_authentic" | "possibly_manipulated" | "likely_manipulated",
        "findings": [...],
        "manipulation_regions": [...]
    }
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return _default_result()

    findings = []
    scores = []

    # --- 1. Error Level Analysis (ELA) ---
    ela_score, ela_finding = _error_level_analysis(img)
    scores.append(ela_score)
    findings.append(ela_finding)

    # --- 2. Noise Consistency ---
    noise_score, noise_finding = _noise_consistency(img)
    scores.append(noise_score)
    findings.append(noise_finding)

    # --- 3. Edge Coherence ---
    edge_score, edge_finding = _edge_coherence(img)
    scores.append(edge_score)
    findings.append(edge_finding)

    # --- 4. Copy-Move Detection ---
    cm_score, cm_finding = _copy_move_detection(img)
    scores.append(cm_score)
    findings.append(cm_finding)

    # Weighted average
    weights = [0.3, 0.25, 0.2, 0.25]
    overall = sum(s * w for s, w in zip(scores, weights))
    overall = round(min(1.0, max(0.0, overall)), 2)

    if overall >= 0.75:
        classification = "likely_authentic"
    elif overall >= 0.45:
        classification = "possibly_manipulated"
    else:
        classification = "likely_manipulated"

    return {
        "score": overall,
        "classification": classification,
        "findings": findings,
        "manipulation_regions": [],
    }


def _error_level_analysis(img: np.ndarray) -> tuple:
    """
    Re-compress at quality 90 and measure difference.
    Manipulated regions show higher error levels.
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    _, encoded = cv2.imencode(".jpg", img, encode_param)
    recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    
    diff = cv2.absdiff(img, recompressed).astype(float)
    ela_map = np.mean(diff, axis=2)  # Average across channels
    
    # Analyze variance in ELA map — uniform = authentic, patchy = suspicious
    mean_ela = np.mean(ela_map)
    std_ela = np.std(ela_map)
    
    # High std relative to mean suggests inconsistent compression history
    ratio = std_ela / max(mean_ela, 0.001)
    
    if ratio < 1.5:
        score = 0.9
        finding = f"ELA: Uniform compression artifacts (ratio={ratio:.2f}). Consistent with an unmodified image."
    elif ratio < 3.0:
        score = 0.6
        finding = f"ELA: Moderate variation in compression artifacts (ratio={ratio:.2f}). Some regions may have been re-saved."
    else:
        score = 0.3
        finding = f"ELA: High variation in error levels (ratio={ratio:.2f}). Possible region-level manipulation detected."
    
    return score, finding


def _noise_consistency(img: np.ndarray) -> tuple:
    """
    Analyze noise profile across image blocks.
    Authentic images have consistent noise; spliced regions differ.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    block_size = 32
    noise_levels = []
    
    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block = gray[y:y+block_size, x:x+block_size].astype(float)
            # Estimate noise as high-frequency energy
            laplacian = cv2.Laplacian(block, cv2.CV_64F)
            noise = np.std(laplacian)
            noise_levels.append(noise)
    
    if not noise_levels:
        return 0.8, "Noise: Image too small for block analysis."
    
    noise_arr = np.array(noise_levels)
    cv_noise = np.std(noise_arr) / max(np.mean(noise_arr), 0.001)
    
    if cv_noise < 0.6:
        score = 0.9
        finding = f"Noise: Consistent noise profile across image blocks (CV={cv_noise:.2f}). No splicing indicators."
    elif cv_noise < 1.2:
        score = 0.6
        finding = f"Noise: Moderate noise variation (CV={cv_noise:.2f}). May indicate different source regions."
    else:
        score = 0.25
        finding = f"Noise: High noise inconsistency (CV={cv_noise:.2f}). Strong indicator of image compositing."
    
    return score, finding


def _edge_coherence(img: np.ndarray) -> tuple:
    """
    Check if band edges are unnaturally sharp.
    Real bands have gradual edges; pasted bands often have crisp borders.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Canny edge detection at two thresholds
    edges_tight = cv2.Canny(gray, 100, 200)
    edges_loose = cv2.Canny(gray, 50, 100)
    
    # Ratio of tight to loose edges
    tight_count = np.sum(edges_tight > 0)
    loose_count = np.sum(edges_loose > 0)
    
    if loose_count == 0:
        return 0.8, "Edge: No significant edges detected."
    
    ratio = tight_count / loose_count
    
    if ratio < 0.6:
        score = 0.9
        finding = f"Edge: Natural edge gradient (ratio={ratio:.2f}). Band boundaries appear organic."
    elif ratio < 0.8:
        score = 0.6
        finding = f"Edge: Moderately sharp edges (ratio={ratio:.2f}). Some bands may have enhanced contrast."
    else:
        score = 0.3
        finding = f"Edge: Unnaturally sharp edges (ratio={ratio:.2f}). Possible cut-paste manipulation."
    
    return score, finding


def _copy_move_detection(img: np.ndarray) -> tuple:
    """
    Detect duplicated regions using ORB feature matching.
    Copy-move forgery is common in fraudulent blots.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    orb = cv2.ORB_create(nfeatures=500)
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    
    if descriptors is None or len(keypoints) < 10:
        return 0.85, "Copy-move: Insufficient features for analysis."
    
    # Self-match using brute force
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(descriptors, descriptors, k=2)
    
    # Look for suspiciously similar but spatially distant features
    suspicious = 0
    min_distance_px = max(img.shape[0], img.shape[1]) * 0.05
    
    for match_pair in matches:
        if len(match_pair) < 2:
            continue
        m, n = match_pair
        # Skip self-matches
        if m.queryIdx == m.trainIdx:
            continue
        # Good match + spatially distant
        if m.distance < 30:
            pt1 = keypoints[m.queryIdx].pt
            pt2 = keypoints[m.trainIdx].pt
            spatial_dist = np.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)
            if spatial_dist > min_distance_px:
                suspicious += 1
    
    ratio = suspicious / max(len(matches), 1)
    
    if ratio < 0.02:
        score = 0.9
        finding = f"Copy-move: No duplicated regions found ({suspicious} suspicious matches)."
    elif ratio < 0.08:
        score = 0.5
        finding = f"Copy-move: Some similar features detected ({suspicious} matches). May indicate repeated patterns or actual duplication."
    else:
        score = 0.2
        finding = f"Copy-move: High number of duplicated features ({suspicious} matches). Strong copy-move indicator."
    
    return score, finding


def _default_result() -> Dict[str, Any]:
    return {
        "score": 0.0,
        "classification": "unknown",
        "findings": ["Image could not be decoded for forensic analysis."],
        "manipulation_regions": [],
    }
