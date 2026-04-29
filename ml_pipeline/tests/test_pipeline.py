import pytest
import os
from pathlib import Path

# Need to ensure backend can load properly for testing
os.environ["BLOTQUANT_PORT"] = "8005"

from ml_pipeline.band_detector import detect_bands
from ml_pipeline.dl_features import extract_features, compute_dl_quality_score

SAMPLE_IMG = Path(__file__).parent.parent.parent / "data" / "dataset" / "images" / "sample-001.png"

def test_band_detector_structure():
    if not SAMPLE_IMG.exists():
        pytest.skip("Sample image not found")
        
    with open(SAMPLE_IMG, "rb") as f:
        img_bytes = f.read()
        
    result = detect_bands(img_bytes)
    assert "bands" in result
    assert "lanes" in result
    assert isinstance(result["bands"], list)

def test_band_detector_invalid_input():
    result = detect_bands(b"not an image")
    assert result == {"bands": [], "lanes": []}

def test_dl_quality_score_structure():
    if not SAMPLE_IMG.exists():
        pytest.skip("Sample image not found")
        
    with open(SAMPLE_IMG, "rb") as f:
        img_bytes = f.read()
        
    result = compute_dl_quality_score(img_bytes)
    assert "quality_score" in result
    assert "method" in result
    assert 0 <= result["quality_score"] <= 1.0
