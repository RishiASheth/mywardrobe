"""
Data models for My Wardrobe AI Outfit Recommendation System.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GarmentCategory(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"
    FOOTWEAR = "footwear"
    ONE_PIECE = "one_piece"
    ACCESSORY = "accessory"


class Occasion(str, Enum):
    CASUAL = "casual"
    WORK = "work"
    FORMAL = "formal"
    STREETWEAR = "streetwear"
    PARTY = "party"
    DATE_NIGHT = "date_night"
    ATHLETIC = "athletic"


class WardrobeItem(BaseModel):
    id: str
    name: str
    category: GarmentCategory
    garment_type: str  # e.g. "t-shirt", "chinos", "blazer", "sneakers"
    color: str  # e.g. "navy blue", "beige", "white"
    style: str  # e.g. "minimalist", "casual", "smart casual", "streetwear"
    occasions: List[Occasion] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    image_url: str
    created_at: str
    notes: Optional[str] = None


class AutoTagProposal(BaseModel):
    garment_type: str
    category: GarmentCategory
    color: str
    secondary_color: Optional[str] = None
    style: str
    occasions: List[Occasion]
    confidence_scores: Dict[str, float]
    suggested_tags: List[str]


class PinterestInspirationPiece(BaseModel):
    slot: str  # "top", "bottom", "footwear", "outerwear", "accessory"
    description: str  # e.g. "White crisp button-down shirt"
    garment_type: str
    color: str
    style: str


class PinterestInspiration(BaseModel):
    id: str
    title: str
    query_used: str
    image_url: str
    source_url: Optional[str] = None
    occasion: Occasion
    style: str
    pieces: List[PinterestInspirationPiece]
    vibe_description: str


class MatchedSlot(BaseModel):
    slot: str
    target_description: str
    user_item: Optional[WardrobeItem] = None
    similarity_score: float = 0.0
    status: str  # "matched", "missing", "alternative"
    advice: Optional[str] = None


class OutfitRecommendation(BaseModel):
    id: str
    title: str
    occasion: Occasion
    style: str
    inspiration: PinterestInspiration
    anchor_item: Optional[WardrobeItem] = None
    matched_slots: List[MatchedSlot]
    overall_match_score: float
    color_palette: List[str]
    styling_advice: str
