"""
Pinterest inspiration search service supporting:
1. Live Pinterest API v5 integration (when PINTEREST_ACCESS_TOKEN is provided)
2. Curated dynamic fashion inspiration library with piece breakdowns (top, bottom, footwear, outerwear)
3. Dynamic trend queries matching user's selected garment tags, colors, and occasion contexts.
"""
import os
import requests
from typing import List, Optional, Dict, Any, Tuple
from .models import PinterestInspiration, PinterestInspirationPiece, Occasion

PINTEREST_API_BASE = "https://api.pinterest.com/v5"

# Curated high-aesthetic inspiration library spanning diverse garments, colors, and occasions
CURATED_INSPIRATIONS: List[Dict[str, Any]] = [
    {
        "id": "pin_blue_tee_casual_1",
        "title": "Minimal French Navy Tee & Khaki Chinos",
        "keywords": ["blue t-shirt", "navy t-shirt", "t-shirt", "blue", "casual", "men", "unisex"],
        "occasion": Occasion.CASUAL,
        "style": "minimalist",
        "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/mens-navy-t-shirt-outfit/",
        "vibe_description": "Effortless Parisian everyday street style balancing deep navy with warm earth tones.",
        "pieces": [
            {
                "slot": "top",
                "description": "Fitted navy blue crewneck t-shirt in heavy organic cotton",
                "garment_type": "t-shirt",
                "color": "navy blue",
                "style": "minimalist"
            },
            {
                "slot": "bottom",
                "description": "Relaxed tapered khaki chinos",
                "garment_type": "chinos",
                "color": "beige",
                "style": "smart casual"
            },
            {
                "slot": "footwear",
                "description": "Clean white minimalist low-top leather sneakers",
                "garment_type": "white minimalist sneakers",
                "color": "white",
                "style": "minimalist"
            }
        ]
    },
    {
        "id": "pin_blue_tee_streetwear_2",
        "title": "Urban Blue Tee with Dark Washed Denim",
        "keywords": ["blue t-shirt", "t-shirt", "blue", "streetwear", "casual"],
        "occasion": Occasion.STREETWEAR,
        "style": "streetwear",
        "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/streetwear-outfits/",
        "vibe_description": "Modern urban street aesthetic with relaxed proportions and contrasting dark denim.",
        "pieces": [
            {
                "slot": "top",
                "description": "Boxy oversized royal blue t-shirt",
                "garment_type": "t-shirt",
                "color": "blue",
                "style": "streetwear"
            },
            {
                "slot": "bottom",
                "description": "Straight-leg black washed jeans",
                "garment_type": "black jeans",
                "color": "black",
                "style": "streetwear"
            },
            {
                "slot": "outerwear",
                "description": "Lightweight denim trucker jacket",
                "garment_type": "denim jacket",
                "color": "blue",
                "style": "casual"
            },
            {
                "slot": "footwear",
                "description": "Retro running sneakers with neutral accents",
                "garment_type": "running sneakers",
                "color": "grey",
                "style": "streetwear"
            }
        ]
    },
    {
        "id": "pin_white_shirt_work_1",
        "title": "Tailored Smart Workwear: Crisp White Shirt & Charcoal Trousers",
        "keywords": ["shirt", "white", "formal dress shirt", "casual shirt", "work", "formal"],
        "occasion": Occasion.WORK,
        "style": "smart casual",
        "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/business-casual-men/",
        "vibe_description": "Sophisticated office look pairing immaculate white cotton with pleated charcoal tailoring.",
        "pieces": [
            {
                "slot": "top",
                "description": "Crisp white tailored button-down shirt",
                "garment_type": "formal dress shirt",
                "color": "white",
                "style": "formal"
            },
            {
                "slot": "bottom",
                "description": "Tailored charcoal grey dress trousers",
                "garment_type": "tailored trousers",
                "color": "charcoal",
                "style": "formal"
            },
            {
                "slot": "outerwear",
                "description": "Slim navy wool blazer jacket",
                "garment_type": "tailored blazer",
                "color": "navy blue",
                "style": "formal"
            },
            {
                "slot": "footwear",
                "description": "Burnished dark brown leather loafers",
                "garment_type": "leather loafers",
                "color": "brown",
                "style": "smart casual"
            }
        ]
    },
    {
        "id": "pin_blazer_date_night_1",
        "title": "Evening Date Night: Navy Blazer & Black Denim",
        "keywords": ["blazer", "tailored blazer", "outerwear", "navy blue", "date_night", "party"],
        "occasion": Occasion.DATE_NIGHT,
        "style": "chic",
        "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/mens-date-night-outfit/",
        "vibe_description": "Refined evening silhouette combining sharp tailoring with high-contrast slim denim.",
        "pieces": [
            {
                "slot": "outerwear",
                "description": "Unstructured navy blue tailored blazer",
                "garment_type": "tailored blazer",
                "color": "navy blue",
                "style": "chic"
            },
            {
                "slot": "top",
                "description": "Fine merino wool black crewneck sweater",
                "garment_type": "crewneck sweater",
                "color": "black",
                "style": "minimalist"
            },
            {
                "slot": "bottom",
                "description": "Clean black slim jeans",
                "garment_type": "black jeans",
                "color": "black",
                "style": "chic"
            },
            {
                "slot": "footwear",
                "description": "Sleek black leather chelsea boots",
                "garment_type": "chelsea boots",
                "color": "black",
                "style": "chic"
            }
        ]
    },
    {
        "id": "pin_black_hoodie_streetwear_1",
        "title": "Monochrome Streetwear: Heavyweight Hoodie & Cargo Pants",
        "keywords": ["hoodie", "black", "top", "streetwear", "casual"],
        "occasion": Occasion.STREETWEAR,
        "style": "streetwear",
        "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/hoodie-outfit-men/",
        "vibe_description": "Tactical urban streetwear aesthetic with utility pocketing and chunky sneakers.",
        "pieces": [
            {
                "slot": "top",
                "description": "Heavyweight black drop-shoulder hoodie",
                "garment_type": "hoodie",
                "color": "black",
                "style": "streetwear"
            },
            {
                "slot": "bottom",
                "description": "Olive green utility cargo trousers",
                "garment_type": "cargo pants",
                "color": "olive green",
                "style": "streetwear"
            },
            {
                "slot": "footwear",
                "description": "White low-top sneakers with gum sole",
                "garment_type": "white minimalist sneakers",
                "color": "white",
                "style": "streetwear"
            }
        ]
    },
    {
        "id": "pin_chinos_casual_1",
        "title": "Weekend Stroll: Beige Chinos & White Cotton Tee",
        "keywords": ["chinos", "beige", "khaki", "bottom", "casual", "date_night"],
        "occasion": Occasion.CASUAL,
        "style": "casual",
        "image_url": "https://images.unsplash.com/photo-1479064555552-3ef4979f8908?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/khaki-pants-outfit/",
        "vibe_description": "Clean coastal prep look with breathable cottons and neutral palette.",
        "pieces": [
            {
                "slot": "bottom",
                "description": "Relaxed pleated beige chinos",
                "garment_type": "chinos",
                "color": "beige",
                "style": "casual"
            },
            {
                "slot": "top",
                "description": "Classic white crewneck t-shirt",
                "garment_type": "t-shirt",
                "color": "white",
                "style": "minimalist"
            },
            {
                "slot": "outerwear",
                "description": "Dark blue denim trucker jacket",
                "garment_type": "denim jacket",
                "color": "navy blue",
                "style": "casual"
            },
            {
                "slot": "footwear",
                "description": "White leather minimalist sneakers",
                "garment_type": "white minimalist sneakers",
                "color": "white",
                "style": "minimalist"
            }
        ]
    },
    {
        "id": "pin_denim_jacket_casual_1",
        "title": "Classic Americana: Denim Jacket, White Tee & Black Trousers",
        "keywords": ["denim jacket", "jacket", "outerwear", "blue", "casual", "streetwear"],
        "occasion": Occasion.CASUAL,
        "style": "casual",
        "image_url": "https://images.unsplash.com/photo-1495105787522-5334e3ffa0ef?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/denim-jacket-outfits/",
        "vibe_description": "Timeless casual staple look grounded with crisp monochrome basics.",
        "pieces": [
            {
                "slot": "outerwear",
                "description": "Medium wash vintage denim jacket",
                "garment_type": "denim jacket",
                "color": "blue",
                "style": "casual"
            },
            {
                "slot": "top",
                "description": "Soft organic white t-shirt",
                "garment_type": "t-shirt",
                "color": "white",
                "style": "minimalist"
            },
            {
                "slot": "bottom",
                "description": "Slim tapered black jeans",
                "garment_type": "black jeans",
                "color": "black",
                "style": "casual"
            },
            {
                "slot": "footwear",
                "description": "Black leather chelsea boots",
                "garment_type": "chelsea boots",
                "color": "black",
                "style": "casual"
            }
        ]
    },
    {
        "id": "pin_formal_suit_1",
        "title": "Modern Executive: Charcoal Suit & Crisp White Shirt",
        "keywords": ["formal", "work", "trousers", "blazer", "formal dress shirt", "charcoal"],
        "occasion": Occasion.FORMAL,
        "style": "formal",
        "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=800&q=80",
        "source_url": "https://www.pinterest.com/ideas/mens-formal-suit/",
        "vibe_description": "Pinnacle executive formalwear with sculpted shoulders and tailored drape.",
        "pieces": [
            {
                "slot": "outerwear",
                "description": "Tailored charcoal two-button blazer",
                "garment_type": "tailored blazer",
                "color": "charcoal",
                "style": "formal"
            },
            {
                "slot": "top",
                "description": "Fine twill white formal dress shirt",
                "garment_type": "formal dress shirt",
                "color": "white",
                "style": "formal"
            },
            {
                "slot": "bottom",
                "description": "Matching charcoal tailored trousers",
                "garment_type": "tailored trousers",
                "color": "charcoal",
                "style": "formal"
            },
            {
                "slot": "footwear",
                "description": "Polished black oxford dress shoes",
                "garment_type": "dress shoes",
                "color": "black",
                "style": "formal"
            }
        ]
    }
]


class PinterestService:
    def __init__(self):
        self.access_token = os.getenv("PINTEREST_ACCESS_TOKEN", "").strip()

    def set_access_token(self, token: str):
        self.access_token = token.strip()

    def _query_live_pinterest_api(self, query: str, limit: int = 5) -> List[PinterestInspiration]:
        """Call official Pinterest API v5 if access token is available."""
        if not self.access_token:
            return []
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            # Search / pins endpoint
            url = f"{PINTEREST_API_BASE}/pins"
            params = {"page_size": limit}
            res = requests.get(url, headers=headers, params=params, timeout=5)
            if res.status_code == 200:
                pins = res.json().get("items", [])
                inspirations = []
                for p in pins:
                    media = p.get("media", {}).get("images", {}).get("600x", {})
                    img_url = media.get("url")
                    if img_url:
                        inspirations.append(
                            PinterestInspiration(
                                id=f"pin_api_{p.get('id')}",
                                title=p.get("title") or "Pinterest Style Look",
                                query_used=query,
                                image_url=img_url,
                                source_url=f"https://www.pinterest.com/pin/{p.get('id')}",
                                occasion=Occasion.CASUAL,
                                style="trending",
                                pieces=[],
                                vibe_description=p.get("description") or "Curated from live Pinterest feed"
                            )
                        )
                return inspirations
        except Exception as e:
            print(f"[Pinterest API Error] {e}")
        return []

    def search_inspirations(
        self,
        garment_type: str,
        color: str,
        occasion: Optional[Occasion] = None,
        style: Optional[str] = None,
        gender: str = "men",
        limit: int = 4
    ) -> List[PinterestInspiration]:
        """
        Retrieves top inspiration outfits for a given item query:
        Constructs prompt: '{color} {garment_type} outfit {gender}'
        Matches against Pinterest data, decomposing looks into top, bottom, and footwear slots.
        """
        constructed_query = f"{color} {garment_type} outfit {gender}".strip().lower()

        # Try live API first if token present
        live_results = self._query_live_pinterest_api(constructed_query, limit=limit)
        if live_results:
            return live_results

        # Fallback to curated high-aesthetic inspirations with intelligent semantic scoring
        scored: List[Tuple[float, Dict[str, Any]]] = []
        tokens = set(constructed_query.split() + [garment_type.lower(), color.lower()])
        if occasion:
            tokens.add(occasion.value)
        if style:
            tokens.add(style.lower())

        for entry in CURATED_INSPIRATIONS:
            score = 0.0
            kw_set = set(entry.get("keywords", []))
            
            # Exact garment match
            for kw in kw_set:
                if garment_type.lower() in kw:
                    score += 4.0
                if color.lower() in kw:
                    score += 3.0
                if any(t in kw for t in tokens):
                    score += 1.5

            if occasion and entry.get("occasion") == occasion:
                score += 3.0
            if style and style.lower() in entry.get("style", "").lower():
                score += 2.0

            scored.append((score, entry))

        # Sort highest score first
        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [item for _, item in scored[:limit]]

        # Convert to Pydantic models
        results: List[PinterestInspiration] = []
        for c in top_candidates:
            pieces = [PinterestInspirationPiece(**p) for p in c.get("pieces", [])]
            results.append(
                PinterestInspiration(
                    id=c["id"],
                    title=c["title"],
                    query_used=constructed_query,
                    image_url=c["image_url"],
                    source_url=c.get("source_url"),
                    occasion=c["occasion"],
                    style=c["style"],
                    pieces=pieces,
                    vibe_description=c["vibe_description"]
                )
            )

        return results


# Singleton instance
_PINTEREST_INSTANCE = None

def get_pinterest_service() -> PinterestService:
    global _PINTEREST_INSTANCE
    if _PINTEREST_INSTANCE is None:
        _PINTEREST_INSTANCE = PinterestService()
    return _PINTEREST_INSTANCE
