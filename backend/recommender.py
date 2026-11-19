"""
AI Outfit Recommendation and Cross-Referencing Engine:
Cross-references Pinterest inspiration looks with user's Qdrant wardrobe vectors.
"""
from typing import List, Optional, Dict, Any
import uuid

from .models import (
    WardrobeItem,
    GarmentCategory,
    Occasion,
    PinterestInspiration,
    MatchedSlot,
    OutfitRecommendation
)
from .vision_clip import extract_text_embedding
from .vector_db import get_vector_db
from .pinterest_service import get_pinterest_service

SLOT_CATEGORY_MAP = {
    "top": GarmentCategory.TOP,
    "bottom": GarmentCategory.BOTTOM,
    "outerwear": GarmentCategory.OUTERWEAR,
    "footwear": GarmentCategory.FOOTWEAR,
    "one_piece": GarmentCategory.ONE_PIECE,
    "accessory": GarmentCategory.ACCESSORY
}


def _slot_to_category(slot_name: str) -> Optional[GarmentCategory]:
    return SLOT_CATEGORY_MAP.get(slot_name.lower())


def _generate_styling_advice(anchor: Optional[WardrobeItem], matched_slots: List[MatchedSlot], occasion: Occasion) -> str:
    matched_names = [s.user_item.name for s in matched_slots if s.user_item]
    missing_slots = [s.slot for s in matched_slots if s.status == "missing"]
    
    advice_parts = []
    if anchor:
        advice_parts.append(f"Grounded by your {anchor.color} {anchor.garment_type}.")
    
    if len(matched_names) > 1:
        advice_parts.append(f"Paired seamlessly with your {', '.join(matched_names[1:])}.")
    
    if not missing_slots:
        advice_parts.append(f"You have all essential pieces in your closet to rock this {occasion.value} look with confidence!")
    else:
        advice_parts.append(f"To elevate this look further, consider styling with {', '.join(missing_slots)}.")

    return " ".join(advice_parts)


def _extract_palette(anchor: Optional[WardrobeItem], matched_slots: List[MatchedSlot]) -> List[str]:
    colors = []
    if anchor and anchor.color:
        colors.append(anchor.color)
    for slot in matched_slots:
        if slot.user_item and slot.user_item.color and slot.user_item.color not in colors:
            colors.append(slot.user_item.color)
    return colors if colors else ["monochrome", "neutral"]


class OutfitRecommender:
    def __init__(self):
        self.db = get_vector_db()
        self.pinterest = get_pinterest_service()

    def recommend_by_item(
        self,
        item_id: str,
        occasion: Optional[Occasion] = None,
        gender: str = "men"
    ) -> List[OutfitRecommendation]:
        """
        Finds Pinterest style inspiration matching the anchor item,
        then uses CLIP to cross-reference complementary pieces against
        the user's own wardrobe inventory stored in Qdrant.
        """
        anchor = self.db.get_item(item_id)
        if not anchor:
            raise ValueError(f"Wardrobe item '{item_id}' not found.")

        target_occasion = occasion or (anchor.occasions[0] if anchor.occasions else Occasion.CASUAL)
        inspirations = self.pinterest.search_inspirations(
            garment_type=anchor.garment_type,
            color=anchor.color,
            occasion=target_occasion,
            style=anchor.style,
            gender=gender
        )

        recommendations: List[OutfitRecommendation] = []

        for insp in inspirations:
            matched_slots: List[MatchedSlot] = []
            slot_scores: List[float] = []

            # Add anchor item directly into its corresponding slot
            anchor_slot_name = anchor.category.value
            matched_slots.append(
                MatchedSlot(
                    slot=anchor_slot_name,
                    target_description=f"Your {anchor.color} {anchor.garment_type}",
                    user_item=anchor,
                    similarity_score=1.0,
                    status="matched"
                )
            )
            slot_scores.append(1.0)

            # Cross-reference remaining inspiration pieces against user's wardrobe in Qdrant
            for piece in insp.pieces:
                piece_cat = _slot_to_category(piece.slot)
                
                # Skip if this is the anchor item's slot already filled
                if piece_cat == anchor.category:
                    continue

                # Query vector for the complementary piece
                query_text = f"a photo of {piece.color} {piece.garment_type} {piece.style}"
                query_vector = extract_text_embedding(query_text)

                # Search Qdrant for matching items in the user's closet
                search_results = self.db.search_similar(
                    query_vector=query_vector,
                    category=piece_cat,
                    limit=3,
                    score_threshold=0.18
                )

                if search_results:
                    best_match = search_results[0]
                    # Map cosine similarity (0.18 - 0.40) to human-friendly 80% - 98% compatibility
                    norm_sim = min(0.98, max(0.75, 0.70 + (best_match["score"] * 0.70)))
                    matched_slots.append(
                        MatchedSlot(
                            slot=piece.slot,
                            target_description=piece.description,
                            user_item=best_match["item"],
                            similarity_score=round(norm_sim, 2),
                            status="matched"
                        )
                    )
                    slot_scores.append(norm_sim)
                else:
                    matched_slots.append(
                        MatchedSlot(
                            slot=piece.slot,
                            target_description=piece.description,
                            user_item=None,
                            similarity_score=0.0,
                            status="missing",
                            advice=f"Missing: {piece.description}. Add a {piece.color} {piece.garment_type} to complete this look."
                        )
                    )
                    slot_scores.append(0.35)  # Penalty for missing slot

            # Calculate overall outfit score
            overall_score = round((sum(slot_scores) / max(len(slot_scores), 1)) * 100, 1)

            rec = OutfitRecommendation(
                id=f"rec_{uuid.uuid4().hex[:8]}",
                title=f"{insp.title}",
                occasion=target_occasion,
                style=insp.style,
                inspiration=insp,
                anchor_item=anchor,
                matched_slots=matched_slots,
                overall_match_score=min(overall_score, 98.0),
                color_palette=_extract_palette(anchor, matched_slots),
                styling_advice=_generate_styling_advice(anchor, matched_slots, target_occasion)
            )
            recommendations.append(rec)

        return recommendations

    def recommend_by_occasion(
        self,
        occasion: Occasion,
        gender: str = "men"
    ) -> List[OutfitRecommendation]:
        """
        Suggests full outfits for a context/occasion (casual, work, formal, etc.)
        synthesized from the user's available wardrobe pieces.
        """
        all_items = self.db.get_all_items()
        if not all_items:
            return []

        # Find items tagged with this occasion or fallback to any top
        candidates = [it for it in all_items if occasion in it.occasions]
        if not candidates:
            candidates = [it for it in all_items if it.category == GarmentCategory.TOP] or all_items

        results: List[OutfitRecommendation] = []
        for cand in candidates[:3]:
            try:
                recs = self.recommend_by_item(item_id=cand.id, occasion=occasion, gender=gender)
                if recs:
                    results.append(recs[0])
            except Exception as e:
                print(f"[Recommend Error] {e}")

        return results


# Singleton
_RECOMMENDER_INSTANCE = None

def get_recommender() -> OutfitRecommender:
    global _RECOMMENDER_INSTANCE
    if _RECOMMENDER_INSTANCE is None:
        _RECOMMENDER_INSTANCE = OutfitRecommender()
    return _RECOMMENDER_INSTANCE
