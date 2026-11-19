"""
FastAPI Backend Application for My Wardrobe: AI Outfit Recommendation System.
"""
import os
import uuid
import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .models import (
    WardrobeItem,
    GarmentCategory,
    Occasion,
    AutoTagProposal,
    OutfitRecommendation
)
from .vision_clip import (
    auto_tag_clothing_image,
    extract_image_embedding,
    GARMENT_TYPES_TAXONOMY,
    COLORS_TAXONOMY,
    STYLES_TAXONOMY,
    OCCASIONS_TAXONOMY
)
from .vector_db import get_vector_db
from .pinterest_service import get_pinterest_service, CURATED_INSPIRATIONS
from .recommender import get_recommender
from .seed_data import seed_sample_wardrobe

app = FastAPI(
    title="My Wardrobe - AI Outfit Recommendation System",
    description="Vision-Language automated wardrobe cataloging, Qdrant vector search, and Pinterest outfit matching pipeline.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Pydantic request models
class ConfirmItemRequest(BaseModel):
    name: str
    category: GarmentCategory
    garment_type: str
    color: str
    style: str
    occasions: List[Occasion]
    tags: List[str] = []
    image_url: str
    notes: Optional[str] = None


class RecommendByItemRequest(BaseModel):
    item_id: str
    occasion: Optional[Occasion] = None
    gender: str = "men"


class RecommendByOccasionRequest(BaseModel):
    occasion: Occasion
    gender: str = "men"


class PinterestTokenRequest(BaseModel):
    access_token: str


@app.on_event("startup")
async def startup_event():
    """Ensure sample wardrobe is indexed on startup if empty."""
    try:
        db = get_vector_db()
        items = db.get_all_items()
        if not items:
            print("[Startup] Initializing default curated wardrobe...")
            seed_sample_wardrobe(force=False)
    except Exception as e:
        print(f"[Startup Warning] {e}")


@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "My Wardrobe API running. Please check /static/index.html"}


# -------------------------------------------------------------
# Catalog & Vision-Language Tagging Endpoints
# -------------------------------------------------------------

@app.post("/api/catalog/upload-and-tag", response_model=Dict[str, Any])
async def upload_and_tag(file: UploadFile = File(...)):
    """
    1. Saves uploaded image.
    2. Runs zero-shot Vision-Language Model (CLIP) to infer:
       - Garment type (e.g. t-shirt, jeans, chinos)
       - Category (top, bottom, footwear, etc.)
       - Colors (primary and secondary)
       - Style (minimalist, streetwear, smart casual, etc.)
       - Occasions (casual, work, formal, etc.)
       - Suggested tags & confidence metrics.
    """
    try:
        content = await file.read()
        file_ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        unique_name = f"upload_{uuid.uuid4().hex[:10]}{file_ext}"
        saved_path = os.path.join(UPLOADS_DIR, unique_name)

        with open(saved_path, "wb") as f:
            f.write(content)

        # Run CLIP zero-shot auto tagger
        proposal = auto_tag_clothing_image(content)

        # Suggested item name
        suggested_name = f"{proposal.color.title()} {proposal.garment_type.title()}"

        return {
            "success": True,
            "image_url": f"/static/uploads/{unique_name}",
            "suggested_name": suggested_name,
            "proposal": proposal.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image classification failed: {str(e)}")


@app.post("/api/catalog/confirm", response_model=WardrobeItem)
async def confirm_item(req: ConfirmItemRequest):
    """
    Saves the user-reviewed clothing item and indexes its 512-dim CLIP
    feature vector into Qdrant for semantic similarity search.
    """
    try:
        db = get_vector_db()
        item_id = f"item_{uuid.uuid4().hex[:8]}"

        item = WardrobeItem(
            id=item_id,
            name=req.name,
            category=req.category,
            garment_type=req.garment_type,
            color=req.color,
            style=req.style,
            occasions=req.occasions,
            tags=req.tags,
            image_url=req.image_url,
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            notes=req.notes
        )

        # Map static url to file path
        if req.image_url.startswith("/static/uploads/"):
            rel_file = req.image_url.replace("/static/uploads/", "")
            local_image_path = os.path.join(UPLOADS_DIR, rel_file)
            vector = extract_image_embedding(local_image_path)
        else:
            # External URL or fallback
            vector = extract_image_embedding(req.image_url)

        # Upsert into Qdrant
        db.upsert_item(item, vector)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index item: {str(e)}")


@app.get("/api/catalog/items", response_model=List[WardrobeItem])
def get_catalog_items(
    category: Optional[str] = Query(None),
    occasion: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """List all wardrobe items with filtering."""
    db = get_vector_db()
    items = db.get_all_items()

    if category and category.lower() != "all":
        items = [it for it in items if it.category.value == category.lower()]

    if occasion and occasion.lower() != "all":
        items = [it for it in items if any(o.value == occasion.lower() for o in it.occasions)]

    if search:
        q = search.lower()
        items = [
            it for it in items
            if q in it.name.lower() or q in it.garment_type.lower() or q in it.color.lower() or any(q in t.lower() for t in it.tags)
        ]

    return items


@app.get("/api/catalog/items/{item_id}", response_model=WardrobeItem)
def get_single_item(item_id: str):
    db = get_vector_db()
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/api/catalog/items/{item_id}")
def delete_single_item(item_id: str):
    db = get_vector_db()
    success = db.delete_item(item_id)
    return {"success": success, "deleted_id": item_id}


# -------------------------------------------------------------
# Recommendation & Matching Pipeline Endpoints
# -------------------------------------------------------------

@app.post("/api/recommend/by-item", response_model=List[OutfitRecommendation])
def recommend_outfits_by_item(req: RecommendByItemRequest):
    """
    Outfit Recommendation Pipeline:
    1. Takes selected wardrobe item (e.g. blue t-shirt).
    2. Queries Pinterest API / style trends for outfits featuring that garment.
    3. Uses CLIP to extract complementary visual pieces (e.g. bottoms, footwear).
    4. Cross-references target pieces against the user's wardrobe inventory in Qdrant.
    5. Returns wearable suggestions with compatibility scores and styling advice.
    """
    try:
        recommender = get_recommender()
        recommendations = recommender.recommend_by_item(
            item_id=req.item_id,
            occasion=req.occasion,
            gender=req.gender
        )
        return recommendations
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@app.post("/api/recommend/by-occasion", response_model=List[OutfitRecommendation])
def recommend_outfits_by_occasion(req: RecommendByOccasionRequest):
    """Recommends complete outfits filtered by context (work, casual, formal, party, etc.)."""
    try:
        recommender = get_recommender()
        recommendations = recommender.recommend_by_occasion(
            occasion=req.occasion,
            gender=req.gender
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Occasion recommendation failed: {str(e)}")


# -------------------------------------------------------------
# Utility, Seed & Settings Endpoints
# -------------------------------------------------------------

@app.post("/api/catalog/seed")
def seed_catalog(force: bool = False):
    """Populates or resets the starter wardrobe with real clothes & embeddings."""
    count = seed_sample_wardrobe(force=force)
    return {"success": True, "count": count}


@app.get("/api/stats")
def get_wardrobe_stats():
    """Overview statistics for wardrobe dashboard."""
    db = get_vector_db()
    items = db.get_all_items()
    categories_count = {}
    occasions_count = {}

    for it in items:
        cat = it.category.value
        categories_count[cat] = categories_count.get(cat, 0) + 1
        for occ in it.occasions:
            occasions_count[occ.value] = occasions_count.get(occ.value, 0) + 1

    return {
        "total_items": len(items),
        "by_category": categories_count,
        "by_occasion": occasions_count
    }


@app.get("/api/taxonomies")
def get_taxonomies():
    """Returns available categories, colors, garment types, styles, and occasions."""
    return {
        "categories": [c.value for c in GarmentCategory],
        "garment_types": list(GARMENT_TYPES_TAXONOMY.keys()),
        "colors": COLORS_TAXONOMY,
        "styles": STYLES_TAXONOMY,
        "occasions": [o.value for o in Occasion]
    }


@app.get("/api/pinterest/trends")
def get_pinterest_trends():
    """Returns curated aesthetic Pinterest looks."""
    return CURATED_INSPIRATIONS


@app.post("/api/settings/pinterest-token")
def set_pinterest_token(req: PinterestTokenRequest):
    """Configure Pinterest API developer token."""
    pinterest = get_pinterest_service()
    pinterest.set_access_token(req.access_token)
    return {"success": True, "configured": bool(req.access_token)}
