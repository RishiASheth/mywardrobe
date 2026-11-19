# My Wardrobe — AI Outfit Recommendation System

An intelligent, end-to-end wardrobe cataloging and outfit recommendation platform powered by **CLIP (Vision-Language Model)**, **Pinterest Style Trends**, and **Qdrant Vector Database**.

---

## 🌟 Key Features

1. **Automated Wardrobe Cataloging (Zero-Shot VLM)**
   - Upload any clothing photograph (flat-lay, hanger, or model shot).
   - Automatically detects **Garment Type** (e.g., *t-shirt, chinos, tailored blazer, hoodie*), **Primary & Secondary Colors**, **Fashion Style** (*minimalist, streetwear, smart casual*), and **Occasion Contexts** (*casual, work, formal, date night*).
   - Allows users to review, edit, and add custom tags before saving.
   - Computes a normalized **512-dimensional CLIP embedding** (`ViT-B-32`) for visual similarity.

2. **Pinterest Style Inspiration & Decomposition Engine**
   - When the user selects a closet piece (e.g., a **Navy Blue T-Shirt**), the system formulates aesthetic style queries (e.g., `"navy blue t-shirt outfit men casual"`).
   - Queries Pinterest style boards / trends and decomposes candidate looks into complementary slots (**top**, **bottom**, **footwear**, **outerwear**, **accessories**).
   - Supports both a **hybrid curated Pinterest style repository** and **live Pinterest API v5 integration** with developer access tokens.

3. **Vector-Based Closet Cross-Referencing (Qdrant)**
   - Queries the user's personal wardrobe indexed in **Qdrant** using cosine similarity.
   - Finds the best matching items from the user's actual clothes to recreate the Pinterest look.
   - Calculates a **Match Compatibility Score** (e.g., *94% Match*), generates **Color Harmony Swatches**, and provides **AI Stylist Advice**.
   - Identifies any missing slots (e.g., *"Missing: white minimalist sneakers"*) with suggestions on what to add to complete the look.

4. **Occasion-Based Lookbook**
   - Filter ready-to-wear outfits by context: **Casual**, **Work / Office**, **Formal**, **Date Night**, and **Streetwear**.

5. **Luxury Obsidian & Gold Modern UI**
   - Glassmorphic interface with Google Fonts typography, KPI badges, drag-and-drop auto-tagging modal, and interactive side-by-side outfit studio.

---

## 🏗️ Architecture

```
mywardrobe/
├── backend/
│   ├── main.py              # FastAPI server & REST API endpoints
│   ├── models.py            # Pydantic data schemas
│   ├── vision_clip.py       # OpenCLIP ViT-B-32 zero-shot tagging & feature extractor
│   ├── vector_db.py         # Qdrant local vector database client & storage
│   ├── pinterest_service.py # Hybrid Pinterest trend search & outfit decomposition
│   ├── recommender.py       # Cross-referencing engine (Pinterest vs Closet vectors)
│   └── seed_data.py         # Starter curated wardrobe catalog
├── static/
│   ├── index.html           # Luxury responsive UI
│   ├── styles.css           # Vanilla CSS design system (glassmorphism & gold accents)
│   ├── app.js               # Reactive frontend logic
│   └── uploads/             # Clothing photos & cached media
├── qdrant_storage/          # Persistent Qdrant vector database files
├── wardrobe_inventory.json  # Catalog backup data
└── venv/                    # Virtual environment
```

---

## 🚀 Getting Started

### 1. Start the Application

The server runs on FastAPI / Uvicorn:

```bash
./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. Access the Web App

Open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

### 3. Usage Walkthrough

1. **Explore the Starter Closet**: 10 essential pieces are pre-indexed in Qdrant with real CLIP vectors.
2. **Style Any Piece**: Click **"✨ Style with Pinterest AI"** on any wardrobe card (e.g., Navy Blue T-Shirt).
3. **Review Outfits**: View the Pinterest look on the left, your matched closet pieces on the right, and the match percentage.
4. **Add Your Own Clothes**: Click **"+ Add Clothes"** to drop a photo and watch the CLIP model automatically tag and index it into Qdrant.
5. **Occasion Lookbook**: Click the **"Occasion Lookbook"** tab to view curated outfits tailored for *Casual*, *Work*, or *Formal* events.
