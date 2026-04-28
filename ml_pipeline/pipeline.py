"""
BlotQuant ML Pipeline — Unified Analysis Entry Point (v3.0)

Orchestrates all DLM components:
  1. Band Detection (OpenCV adaptive thresholding)
  2. Intensity Quantification (Densitometry)
  3. Uncertainty Estimation (Monte Carlo simulation)
  4. Authenticity Scoring (Image forensics)
  5. Deep Learning Features (ResNet18 transfer learning)
  6. Extended Analysis (SNR, sharpness, symmetry, etc.)
  7. Patch Forensics (EfficientNet-B0 heatmap)         ← NEW v3.0
  8. Grad-CAM Attention Maps (Explainable AI)           ← NEW v3.0
  9. SSIM Band Comparison (Structural similarity)       ← NEW v3.0
 10. Spectral Analysis (FFT frequency domain)           ← NEW v3.0
"""

import logging
from typing import Dict, Any

from .band_detector import detect_bands
from .quantifier import quantify_intensities, detect_normalization_strategy
from .uncertainty import monte_carlo_uncertainty
from .authenticity import score_authenticity
from .dl_features import compute_dl_quality_score, extract_roi_features, compute_band_similarity
from .extended_features import compute_extended_features
from .patch_forensics import compute_patch_forensics, generate_ela_image
from .grad_cam import compute_gradcam
from .ssim_spectral import compute_ssim_analysis, compute_spectral_analysis

logger = logging.getLogger(__name__)


def run_full_analysis(image_bytes: bytes) -> Dict[str, Any]:
    """
    Run the complete BlotQuant DLM pipeline v3.0 on a western blot image.
    
    This is a local, deterministic pipeline — no external API calls.
    Now includes: ResNet18, EfficientNet-B0, Grad-CAM, SSIM, FFT.
    
    Args:
        image_bytes: Raw image file bytes (JPEG/PNG/WebP)
    
    Returns:
        Complete analysis result matching the frontend schema.
    """
    logger.info("Starting BlotQuant DLM pipeline v3.0...")

    # Step 1: Band Detection
    logger.info("[1/10] Running band detection...")
    detection = detect_bands(image_bytes)
    bands = detection["bands"]
    lanes = detection["lanes"]
    logger.info(f"  → Detected {len(bands)} bands across {len(lanes)} lanes")

    # Step 2: Intensity Quantification
    logger.info("[2/10] Running intensity quantification...")
    bands = quantify_intensities(image_bytes, bands)

    # Step 3: Normalization Strategy Inference
    normalization = detect_normalization_strategy(bands)
    logger.info(f"  → Normalization: {normalization['strategy']}")

    # Step 4: Uncertainty Estimation
    logger.info("[3/10] Running Monte Carlo uncertainty estimation...")
    uncertainty = monte_carlo_uncertainty(image_bytes, bands)

    # Step 5: Authenticity Scoring
    logger.info("[4/10] Running authenticity forensics...")
    authenticity = score_authenticity(image_bytes)
    logger.info(f"  → Score: {authenticity['score']}, Classification: {authenticity['classification']}")

    # Step 6: Deep Learning Feature Extraction (ResNet18)
    logger.info("[5/10] Running ResNet18 deep learning feature extraction...")
    dl_quality = compute_dl_quality_score(image_bytes)
    logger.info(f"  → Quality score: {dl_quality['quality_score']} (method: {dl_quality['method']})")

    # Band-level DL features
    roi_features = extract_roi_features(image_bytes, bands)
    band_similarity = compute_band_similarity(roi_features)
    logger.info(f"  → Band similarity: avg={band_similarity['avg_similarity']}")

    # Step 7: Extended Features
    logger.info("[6/10] Computing extended analysis features...")
    extended = compute_extended_features(image_bytes, bands, lanes)

    # Step 8: Patch-Based Forensics (EfficientNet-B0) ← NEW v3.0
    logger.info("[7/10] Running EfficientNet-B0 patch forensics (8×8 grid)...")
    patch_forensics = compute_patch_forensics(image_bytes, grid_size=8)
    logger.info(f"  → Method: {patch_forensics['method']}, Max anomaly: {patch_forensics['max_score']}, Suspicious: {patch_forensics['suspicious_count']}")

    # Step 9: Grad-CAM Attention Maps ← NEW v3.0
    logger.info("[8/10] Generating Grad-CAM attention heatmap...")
    gradcam = compute_gradcam(image_bytes)
    logger.info(f"  → Focus: {gradcam['focus_region']}, Spread: {gradcam['attention_spread']}")

    # Step 10: SSIM Band Comparison ← NEW v3.0
    logger.info("[9/10] Computing SSIM structural similarity...")
    ssim_analysis = compute_ssim_analysis(image_bytes, bands)
    logger.info(f"  → Avg inter-band SSIM: {ssim_analysis['avg_inter_ssim']}, Avg bg SSIM: {ssim_analysis['avg_bg_ssim']}")

    # Step 11: Spectral Analysis (FFT) ← NEW v3.0
    logger.info("[10/10] Running FFT spectral analysis...")
    spectral = compute_spectral_analysis(image_bytes)
    logger.info(f"  → Periodic noise: {spectral['has_periodic_noise']}, Entropy: {spectral['spectral_entropy']}")

    # Build summary
    band_count = len(bands)
    lane_count = len(lanes)
    auth_pct = int(authenticity["score"] * 100)
    quality_pct = int(dl_quality["quality_score"] * 100)
    norm_str = normalization["strategy"].replace("_", " ")
    
    model_list = [dl_quality["method"]]
    if patch_forensics["method"] != "fallback":
        model_list.append(patch_forensics["method"])
    model_str = " + ".join(model_list)
    
    summary = (
        f"Detected {band_count} protein bands across {lane_count} lane(s). "
        f"Normalization: {norm_str}. "
        f"Authenticity: {auth_pct}% ({authenticity['classification'].replace('_', ' ')}). "
        f"Image quality: {quality_pct}% ({model_str}). "
        f"Patch forensics: {patch_forensics['suspicious_count']} suspicious regions. "
        f"Grad-CAM focus: {gradcam['focus_region'].replace('_', ' ')}. "
        f"SSIM avg: {ssim_analysis['avg_inter_ssim']}. "
        f"Spectral: {'periodic noise detected' if spectral['has_periodic_noise'] else 'clean'}. "
        f"Monte Carlo CI computed over 30 iterations."
    )

    result = {
        "bands": bands,
        "lanes": lanes,
        "normalization": normalization,
        "uncertainty": uncertainty,
        "authenticity": authenticity,
        "dl_quality": dl_quality,
        "band_similarity": band_similarity,
        "extended": extended,
        "patch_forensics": patch_forensics,
        "gradcam": gradcam,
        "ssim_analysis": ssim_analysis,
        "spectral_analysis": spectral,
        "summary": summary,
    }

    logger.info("Pipeline v3.0 complete — 10 stages, 35+ features.")
    return result
