"""
Seed utility to populate sample wardrobe items with real CLIP embeddings into Qdrant.
"""
import os
import requests
from PIL import Image, ImageDraw
import io
from .models import WardrobeItem, GarmentCategory, Occasion
from .vision_clip import extract_image_embedding
from .vector_db import get_vector_db

SAMPLE_ITEMS = [
    {
        "id": "item_navy_tee_01",
        "name": "Navy Blue Classic Crewneck T-Shirt",
        "category": GarmentCategory.TOP,
        "garment_type": "t-shirt",
        "color": "navy blue",
        "style": "minimalist",
        "occasions": [Occasion.CASUAL, Occasion.DATE_NIGHT, Occasion.STREETWEAR],
        "tags": ["navy blue", "t-shirt", "minimalist", "casual", "summer essential"],
        "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:00:00Z",
        "notes": "100% heavyweight combed cotton. Perfect base layer."
    },
    {
        "id": "item_white_shirt_02",
        "name": "Crisp White Oxford Button-Down",
        "category": GarmentCategory.TOP,
        "garment_type": "formal dress shirt",
        "color": "white",
        "style": "smart casual",
        "occasions": [Occasion.WORK, Occasion.FORMAL, Occasion.DATE_NIGHT],
        "tags": ["white", "formal dress shirt", "smart casual", "work", "tailored"],
        "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:05:00Z",
        "notes": "Classic collar, breathable twill."
    },
    {
        "id": "item_black_hoodie_03",
        "name": "Heavyweight Noir Drop-Shoulder Hoodie",
        "category": GarmentCategory.TOP,
        "garment_type": "hoodie",
        "color": "black",
        "style": "streetwear",
        "occasions": [Occasion.STREETWEAR, Occasion.CASUAL, Occasion.ATHLETIC],
        "tags": ["black", "hoodie", "streetwear", "cozy", "relaxed fit"],
        "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:10:00Z",
        "notes": "450 GSM french terry cotton."
    },
    {
        "id": "item_khaki_chinos_04",
        "name": "Pleated Tapered Beige Chinos",
        "category": GarmentCategory.BOTTOM,
        "garment_type": "chinos",
        "color": "beige",
        "style": "smart casual",
        "occasions": [Occasion.CASUAL, Occasion.WORK, Occasion.DATE_NIGHT],
        "tags": ["beige", "chinos", "smart casual", "versatile", "tapered"],
        "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:15:00Z",
        "notes": "Stretch cotton twill with relaxed thigh taper."
    },
    {
        "id": "item_dark_jeans_05",
        "name": "Straight Cut Raw Indigo Jeans",
        "category": GarmentCategory.BOTTOM,
        "garment_type": "blue jeans",
        "color": "blue",
        "style": "casual",
        "occasions": [Occasion.CASUAL, Occasion.STREETWEAR, Occasion.DATE_NIGHT],
        "tags": ["blue jeans", "denim", "casual", "raw indigo"],
        "image_url": "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:20:00Z",
        "notes": "Selvedge denim, timeless silhouette."
    },
    {
        "id": "item_charcoal_trousers_06",
        "name": "Tailored Charcoal Pleated Trousers",
        "category": GarmentCategory.BOTTOM,
        "garment_type": "tailored trousers",
        "color": "charcoal",
        "style": "formal",
        "occasions": [Occasion.WORK, Occasion.FORMAL],
        "tags": ["charcoal", "tailored trousers", "formal", "office", "wool blend"],
        "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:25:00Z",
        "notes": "Crisp pressed crease with waistband adjusters."
    },
    {
        "id": "item_navy_blazer_07",
        "name": "Unstructured Navy Wool Blazer",
        "category": GarmentCategory.OUTERWEAR,
        "garment_type": "tailored blazer",
        "color": "navy blue",
        "style": "smart casual",
        "occasions": [Occasion.WORK, Occasion.FORMAL, Occasion.DATE_NIGHT],
        "tags": ["navy blue", "tailored blazer", "outerwear", "smart casual"],
        "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:30:00Z",
        "notes": "Patch pockets, Italian hopsack wool."
    },
    {
        "id": "item_denim_jacket_08",
        "name": "Medium Wash Trucker Denim Jacket",
        "category": GarmentCategory.OUTERWEAR,
        "garment_type": "denim jacket",
        "color": "blue",
        "style": "casual",
        "occasions": [Occasion.CASUAL, Occasion.STREETWEAR],
        "tags": ["denim jacket", "blue", "casual", "vintage wash"],
        "image_url": "https://images.unsplash.com/photo-1495105787522-5334e3ffa0ef?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:35:00Z",
        "notes": "Heritage rivet buttons, classic trucker cut."
    },
    {
        "id": "item_white_sneakers_09",
        "name": "Minimalist White Leather Low-Tops",
        "category": GarmentCategory.FOOTWEAR,
        "garment_type": "white minimalist sneakers",
        "color": "white",
        "style": "minimalist",
        "occasions": [Occasion.CASUAL, Occasion.STREETWEAR, Occasion.DATE_NIGHT],
        "tags": ["white minimalist sneakers", "white", "sneakers", "leather"],
        "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:40:00Z",
        "notes": "Full-grain calfskin with margom rubber soles."
    },
    {
        "id": "item_brown_loafers_10",
        "name": "Burnished Dark Brown Penny Loafers",
        "category": GarmentCategory.FOOTWEAR,
        "garment_type": "leather loafers",
        "color": "brown",
        "style": "smart casual",
        "occasions": [Occasion.WORK, Occasion.FORMAL, Occasion.DATE_NIGHT],
        "tags": ["leather loafers", "brown", "formal", "dress shoes"],
        "image_url": "https://images.unsplash.com/photo-1533867617858-e7b97e060509?auto=format&fit=crop&w=600&q=80",
        "created_at": "2026-10-12T10:45:00Z",
        "notes": "Hand-painted patina with Goodyear welting."
    }
]


def create_fallback_item_image(color_name: str, garment_text: str) -> Image.Image:
    """Create a clean stylized garment placeholder if offline image fetch fails."""
    color_map = {
        "navy blue": (20, 35, 60),
        "white": (240, 240, 245),
        "black": (25, 25, 28),
        "beige": (220, 205, 180),
        "blue": (40, 80, 140),
        "charcoal": (45, 48, 55),
        "brown": (85, 55, 35),
    }
    bg = color_map.get(color_name, (70, 75, 85))
    img = Image.new("RGB", (400, 400), color=bg)
    draw = ImageDraw.Draw(img)
    # Draw simple frame and text
    draw.rectangle([20, 20, 380, 380], outline=(255, 255, 255, 120), width=3)
    return img


def seed_sample_wardrobe(force: bool = False):
    """Indexes sample wardrobe items into Qdrant vector database."""
    db = get_vector_db()
    existing = db.get_all_items()
    if existing and not force:
        print(f"[Seed] Wardrobe already has {len(existing)} items. Skipping seed.")
        return len(existing)

    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads"))
    os.makedirs(uploads_dir, exist_ok=True)

    print(f"[Seed] Seeding {len(SAMPLE_ITEMS)} curated wardrobe items...")
    count = 0
    for raw in SAMPLE_ITEMS:
        item = WardrobeItem(**raw)
        
        # Download or create local image cache
        local_filename = f"{item.id}.jpg"
        local_filepath = os.path.join(uploads_dir, local_filename)

        if not os.path.exists(local_filepath):
            try:
                res = requests.get(item.image_url, timeout=4)
                if res.status_code == 200:
                    with open(local_filepath, "wb") as f:
                        f.write(res.content)
                else:
                    img = create_fallback_item_image(item.color, item.garment_type)
                    img.save(local_filepath, "JPEG")
            except Exception:
                img = create_fallback_item_image(item.color, item.garment_type)
                img.save(local_filepath, "JPEG")

        # Set image_url to local static file
        item.image_url = f"/static/uploads/{local_filename}"

        # Generate CLIP embedding from image
        vector = extract_image_embedding(local_filepath)

        # Store in Qdrant
        db.upsert_item(item, vector)
        count += 1
        print(f"  [+] Indexed {item.name} ({item.category.value}) into Qdrant")

    print(f"[Seed] Successfully seeded {count} items.")
    return count
