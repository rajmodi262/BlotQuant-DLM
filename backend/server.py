"""
BlotQuant Backend — FastAPI Server (v3.0)

Serves the real DLM pipeline (OpenCV + Monte Carlo) instead of
proxying to an external LLM API. All analysis runs locally.

Storage: Uses local JSON files — NO database required.
This makes the project fully portable (zip → extract → run).
"""

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path so ml_pipeline can be imported
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml_pipeline.pipeline import run_full_analysis
from ml_pipeline.patch_forensics import generate_ela_image

# --- Config ---
UPLOAD_DIR = ROOT_DIR / 'data' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_DIR = ROOT_DIR / 'data' / 'db'
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DB_DIR / 'analyses.json'

# --- App ---
app = FastAPI(title="BlotQuant DLM API", version="3.0.0")
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Sample images (bundled locally — no external URLs) ---
SAMPLE_DIR = UPLOAD_DIR  # samples live alongside uploads
SAMPLE_IMAGES = [
    {
        "id": "sample-1",
        "name": "Multi-lane Western Blot",
        "filename": "sample-blot.png",
        "thumbnail": "/api/images/sample-blot.png",
        "description": "Multi-lane blot with protein markers (10-35 kDa)",
    },
    {
        "id": "sample-2",
        "name": "PVDF Membrane Blot",
        "filename": "sample-blot-2.png",
        "thumbnail": "/api/images/sample-blot-2.png",
        "description": "4-lane PVDF membrane with chemiluminescent bands",
    },
    {
        "id": "sample-3",
        "name": "Overexposed Blot",
        "filename": "sample-blot-3.png",
        "thumbnail": "/api/images/sample-blot-3.png",
        "description": "Overexposed blot with saturated bands — tests forensics",
    },
]


# ============================================================
# Simple JSON File Database (no MongoDB needed)
# ============================================================

def _load_db() -> list:
    """Load all analyses from the JSON file."""
    if not DB_FILE.exists():
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_db(records: list):
    """Save all analyses to the JSON file."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def _insert_analysis(doc: dict):
    """Insert a single analysis record."""
    records = _load_db()
    records.insert(0, doc)  # newest first
    # Keep only the last 100 analyses
    _save_db(records[:100])


def _find_analysis(analysis_id: str) -> dict | None:
    """Find a single analysis by ID."""
    for rec in _load_db():
        if rec.get("id") == analysis_id:
            return rec
    return None


def _list_analyses(limit: int = 50) -> list:
    """List recent analyses (without image_path for privacy)."""
    records = _load_db()[:limit]
    cleaned = []
    for rec in records:
        r = {k: v for k, v in rec.items() if k != "image_path"}
        cleaned.append(r)
    return cleaned


# ============================================================
# API Endpoints
# ============================================================

@api_router.get("/")
async def root():
    return {"message": "BlotQuant DLM API v3.0", "engine": "local_cv_dlm_v3"}


@api_router.post("/analyze")
async def analyze_blot(file: UploadFile = File(...)):
    """Analyze an uploaded Western blot image using the local DLM pipeline."""
    allowed = ['image/jpeg', 'image/png', 'image/webp']
    content_type = file.content_type or 'image/png'
    if content_type not in allowed:
        raise HTTPException(400, f"Unsupported file type: {content_type}. Use JPEG, PNG, or WebP.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 10MB.")

    # Save image to disk
    analysis_id = str(uuid.uuid4())
    ext = content_type.split('/')[-1].replace('jpeg', 'jpg')
    filename = f"{analysis_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(contents)

    # Run the real ML pipeline
    try:
        results = run_full_analysis(contents)
    except Exception as e:
        logger.error(f"ML pipeline failed: {e}", exc_info=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    doc = {
        "id": analysis_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "image_name": file.filename or "uploaded_blot.png",
        "image_path": str(filepath),
        "image_url": f"/api/images/{filename}",
        "image_mime": content_type,
        "status": "completed",
        "engine": "blotquant_dlm_v3",
        "results": results,
    }
    _insert_analysis(doc)

    return {
        "id": analysis_id,
        "created_at": doc["created_at"],
        "image_name": doc["image_name"],
        "image_url": doc["image_url"],
        "image_mime": content_type,
        "status": "completed",
        "results": results,
    }


@api_router.post("/analyze-sample/{sample_id}")
async def analyze_sample(sample_id: str):
    """Analyze a built-in sample image (read from local disk)."""
    sample = next((s for s in SAMPLE_IMAGES if s["id"] == sample_id), None)
    if not sample:
        raise HTTPException(404, "Sample not found")

    # Read sample from local disk — no network needed
    sample_path = SAMPLE_DIR / sample["filename"]
    if not sample_path.exists():
        raise HTTPException(404, f"Sample file not found: {sample['filename']}")

    with open(sample_path, "rb") as f:
        contents = f.read()

    content_type = "image/png"

    # Copy to a unique analysis file
    analysis_id = str(uuid.uuid4())
    filename = f"{analysis_id}.png"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(contents)

    try:
        results = run_full_analysis(contents)
    except Exception as e:
        logger.error(f"ML pipeline failed: {e}", exc_info=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    doc = {
        "id": analysis_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "image_name": sample["name"],
        "image_path": str(filepath),
        "image_url": f"/api/images/{filename}",
        "image_mime": content_type,
        "status": "completed",
        "engine": "blotquant_dlm_v3",
        "results": results,
    }
    _insert_analysis(doc)

    return {
        "id": analysis_id,
        "created_at": doc["created_at"],
        "image_name": doc["image_name"],
        "image_url": doc["image_url"],
        "image_mime": content_type,
        "status": "completed",
        "results": results,
    }


@api_router.get("/analyses")
async def list_analyses():
    """List recent analyses."""
    return _list_analyses(50)


@api_router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get a specific analysis by ID."""
    doc = _find_analysis(analysis_id)
    if not doc:
        raise HTTPException(404, "Analysis not found")
    # Convert image_path to URL
    result = {k: v for k, v in doc.items() if k != "image_path"}
    if "image_url" not in result and "image_path" in doc:
        filename = Path(doc["image_path"]).name
        result["image_url"] = f"/api/images/{filename}"
    return result


@api_router.get("/images/{filename}")
async def get_image(filename: str):
    """Serve an uploaded image from disk."""
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Image not found")
    return FileResponse(filepath)


@api_router.get("/ela/{filename}")
async def get_ela_image(filename: str):
    """Generate and serve ELA (Error Level Analysis) image for forensic comparison."""
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Image not found")

    with open(filepath, "rb") as f:
        image_bytes = f.read()

    ela = generate_ela_image(image_bytes)
    if ela is None:
        raise HTTPException(500, "Failed to generate ELA image")

    import cv2
    ela_filename = f"ela_{filename}"
    ela_path = UPLOAD_DIR / ela_filename
    cv2.imwrite(str(ela_path), ela)
    return FileResponse(ela_path, media_type="image/png")


@api_router.get("/samples")
async def get_samples():
    """Return available sample images."""
    return SAMPLE_IMAGES


# ============================================================
# App Configuration
# ============================================================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
