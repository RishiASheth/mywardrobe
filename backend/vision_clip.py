"""
Vision-Language model integration using CLIP for automated wardrobe tagging
and feature extraction.
"""
import io
import os
from typing import List, Dict, Any, Tuple
from PIL import Image
import torch
import open_clip

from .models import GarmentCategory, Occasion, AutoTagProposal

# Global model cache
_MODEL = None
_PREPROCESS = None
_TOKENIZER = None
_DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

# Taxonomy definitions with category mappings
GARMENT_TYPES_TAXONOMY = {
    "t-shirt": GarmentCategory.TOP,
    "casual shirt": GarmentCategory.TOP,
    "formal dress shirt": GarmentCategory.TOP,
    "hoodie": GarmentCategory.TOP,
    "crewneck sweater": GarmentCategory.TOP,
    "cardigan": GarmentCategory.TOP,
    "polo shirt": GarmentCategory.TOP,
    "tank top": GarmentCategory.TOP,
    "denim jacket": GarmentCategory.OUTERWEAR,
    "leather jacket": GarmentCategory.OUTERWEAR,
    "tailored blazer": GarmentCategory.OUTERWEAR,
    "trench coat": GarmentCategory.OUTERWEAR,
    "bomber jacket": GarmentCategory.OUTERWEAR,
    "puffer jacket": GarmentCategory.OUTERWEAR,
    "blue jeans": GarmentCategory.BOTTOM,
    "black jeans": GarmentCategory.BOTTOM,
    "chinos": GarmentCategory.BOTTOM,
    "tailored trousers": GarmentCategory.BOTTOM,
    "cargo pants": GarmentCategory.BOTTOM,
    "sweatpants": GarmentCategory.BOTTOM,
    "shorts": GarmentCategory.BOTTOM,
    "pleated skirt": GarmentCategory.BOTTOM,
    "midi dress": GarmentCategory.ONE_PIECE,
    "white minimalist sneakers": GarmentCategory.FOOTWEAR,
    "running sneakers": GarmentCategory.FOOTWEAR,
    "leather loafers": GarmentCategory.FOOTWEAR,
    "chelsea boots": GarmentCategory.FOOTWEAR,
    "dress shoes": GarmentCategory.FOOTWEAR,
}

COLORS_TAXONOMY = [
    "black", "white", "navy blue", "light blue", "beige",
    "grey", "charcoal", "brown", "olive green", "burgundy",
    "emerald green", "red", "cream", "khaki", "pastel pink", "yellow"
]

STYLES_TAXONOMY = [
    "minimalist", "casual", "smart casual", "formal",
    "streetwear", "athletic", "vintage", "chic"
]

OCCASIONS_TAXONOMY = {
    "casual everyday": Occasion.CASUAL,
    "office business work": Occasion.WORK,
    "formal elegant evening": Occasion.FORMAL,
    "streetwear weekend": Occasion.STREETWEAR,
    "party festive celebration": Occasion.PARTY,
    "date night romantic": Occasion.DATE_NIGHT,
    "athletic gym workout": Occasion.ATHLETIC,
}


def get_clip_model():
    """Lazy load OpenCLIP model to save initialization time."""
    global _MODEL, _PREPROCESS, _TOKENIZER
    if _MODEL is None:
        print(f"[CLIP] Loading ViT-B-32 model on {_DEVICE}...")
        _MODEL, _, _PREPROCESS = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai", device=_DEVICE
        )
        _TOKENIZER = open_clip.get_tokenizer("ViT-B-32")
        _MODEL.eval()
        print("[CLIP] Model loaded successfully.")
    return _MODEL, _PREPROCESS, _TOKENIZER


def extract_image_embedding(image_input) -> List[float]:
    """
    Generate normalized 512-dim embedding for an image.
    image_input can be a file path, bytes, or PIL Image.
    """
    model, preprocess, _ = get_clip_model()
    
    if isinstance(image_input, (str, os.PathLike)):
        pil_img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, bytes):
        pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("RGB")
    else:
        raise ValueError("Unsupported image input type")

    image_tensor = preprocess(pil_img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        features = model.encode_image(image_tensor)
        features /= features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).cpu().numpy().tolist()


def extract_text_embedding(text: str) -> List[float]:
    """Generate normalized 512-dim embedding for a text query."""
    model, _, tokenizer = get_clip_model()
    tokens = tokenizer([text]).to(_DEVICE)
    with torch.no_grad():
        features = model.encode_text(tokens)
        features /= features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).cpu().numpy().tolist()


def compute_zero_shot_probs(image_features: torch.Tensor, text_prompts: List[str]) -> List[Tuple[str, float]]:
    """Compute normalized softmax probabilities over a list of candidate prompts."""
    model, _, tokenizer = get_clip_model()
    tokens = tokenizer(text_prompts).to(_DEVICE)
    with torch.no_grad():
        text_features = model.encode_text(tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        # Cosine similarity scaled by 100
        similarity = (image_features @ text_features.T) * 100.0
        probs = similarity.softmax(dim=-1).squeeze(0).cpu().numpy()
    
    results = [(prompt, float(prob)) for prompt, prob in zip(text_prompts, probs)]
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def auto_tag_clothing_image(image_input) -> AutoTagProposal:
    """
    End-to-end zero-shot classifier:
    Classifies clothing into garment type, category, primary color,
    style, and occasion context with confidence scores.
    """
    model, preprocess, _ = get_clip_model()
    
    if isinstance(image_input, (str, os.PathLike)):
        pil_img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, bytes):
        pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
    else:
        pil_img = image_input.convert("RGB")

    image_tensor = preprocess(pil_img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        img_features = model.encode_image(image_tensor)
        img_features /= img_features.norm(dim=-1, keepdim=True)

    # 1. Garment Type
    garment_prompts = [f"a photograph of a {g}" for g in GARMENT_TYPES_TAXONOMY.keys()]
    garment_scores = compute_zero_shot_probs(img_features, garment_prompts)
    top_garment_prompt, garment_conf = garment_scores[0]
    best_garment = list(GARMENT_TYPES_TAXONOMY.keys())[garment_prompts.index(top_garment_prompt)]
    best_category = GARMENT_TYPES_TAXONOMY[best_garment]

    # 2. Color
    color_prompts = [f"a {c} colored clothing garment" for c in COLORS_TAXONOMY]
    color_scores = compute_zero_shot_probs(img_features, color_prompts)
    best_color = COLORS_TAXONOMY[color_prompts.index(color_scores[0][0])]
    color_conf = color_scores[0][1]
    
    secondary_color = None
    if len(color_scores) > 1 and color_scores[1][1] > 0.20:
        secondary_color = COLORS_TAXONOMY[color_prompts.index(color_scores[1][0])]

    # 3. Style
    style_prompts = [f"{s} clothing fashion style" for s in STYLES_TAXONOMY]
    style_scores = compute_zero_shot_probs(img_features, style_prompts)
    best_style = STYLES_TAXONOMY[style_prompts.index(style_scores[0][0])]
    style_conf = style_scores[0][1]

    # 4. Occasions (can have multiple applicable occasions)
    occ_keys = list(OCCASIONS_TAXONOMY.keys())
    occ_prompts = [f"ideal for {k}" for k in occ_keys]
    occ_scores = compute_zero_shot_probs(img_features, occ_prompts)
    
    matched_occasions = [OCCASIONS_TAXONOMY[occ_keys[occ_prompts.index(occ_scores[0][0])]]]
    if len(occ_scores) > 1 and occ_scores[1][1] > 0.25:
        second_occ = OCCASIONS_TAXONOMY[occ_keys[occ_prompts.index(occ_scores[1][0])]]
        if second_occ not in matched_occasions:
            matched_occasions.append(second_occ)

    suggested_tags = [
        best_garment,
        best_color,
        best_style,
        *[occ.value for occ in matched_occasions]
    ]
    if secondary_color:
        suggested_tags.append(secondary_color)

    # Normalize garment name for UI display
    display_garment = best_garment.replace("white minimalist ", "").replace("tailored ", "")

    return AutoTagProposal(
        garment_type=display_garment,
        category=best_category,
        color=best_color,
        secondary_color=secondary_color,
        style=best_style,
        occasions=matched_occasions,
        confidence_scores={
            "garment_confidence": round(float(garment_conf), 3),
            "color_confidence": round(float(color_conf), 3),
            "style_confidence": round(float(style_conf), 3),
        },
        suggested_tags=suggested_tags
    )
