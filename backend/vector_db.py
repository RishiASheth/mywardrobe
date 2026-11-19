"""
Qdrant vector database service for indexing and semantic similarity matching of wardrobe items.
"""
import os
import uuid
import json
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

from .models import WardrobeItem, GarmentCategory, Occasion

COLLECTION_NAME = "wardrobe_items"
VECTOR_DIM = 512
STORAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qdrant_storage"))
INVENTORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "wardrobe_inventory.json"))


class WardrobeVectorDB:
    def __init__(self, storage_path: str = STORAGE_PATH):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.client = QdrantClient(path=self.storage_path)
        self._ensure_collection()
        self._sync_inventory_from_db()

    def _ensure_collection(self):
        """Creates the Qdrant collection if not already existing."""
        collections = [col.name for col in self.client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_DIM,
                    distance=models.Distance.COSINE
                )
            )
            print(f"[Qdrant] Created collection '{COLLECTION_NAME}' with {VECTOR_DIM}-dim cosine vectors.")

    def _item_to_uuid(self, item_id: str) -> str:
        """Deterministic UUID from custom item ID string."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, item_id))

    def _save_inventory_backup(self, items: List[WardrobeItem]):
        """Persist structured wardrobe items to JSON for quick recovery and easy inspection."""
        try:
            data = [item.model_dump() for item in items]
            with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to write inventory backup: {e}")

    def _sync_inventory_from_db(self):
        """Ensure JSON file is present."""
        if not os.path.exists(INVENTORY_FILE):
            self._save_inventory_backup([])

    def upsert_item(self, item: WardrobeItem, vector: List[float]) -> WardrobeItem:
        """Insert or update a wardrobe item with its CLIP vector embedding."""
        point_id = self._item_to_uuid(item.id)
        payload = item.model_dump()
        payload["occasions_str"] = [occ.value for occ in item.occasions]
        payload["category_str"] = item.category.value

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

        # Update local inventory backup
        all_items = self.get_all_items()
        # replace or append
        updated = [it for it in all_items if it.id != item.id]
        updated.append(item)
        self._save_inventory_backup(updated)
        return item

    def get_all_items(self) -> List[WardrobeItem]:
        """Fetch all stored wardrobe items from Qdrant scroll API."""
        try:
            records, _ = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            items = []
            for record in records:
                if record.payload:
                    payload = dict(record.payload)
                    # convert occasions
                    payload["occasions"] = [Occasion(o) for o in payload.get("occasions", []) if o in [x.value for x in Occasion]]
                    payload["category"] = GarmentCategory(payload.get("category", "top"))
                    items.append(WardrobeItem(**payload))
            return items
        except Exception as e:
            print(f"[Qdrant] Error fetching items: {e}")
            if os.path.exists(INVENTORY_FILE):
                with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [WardrobeItem(**d) for d in data]
            return []

    def get_item(self, item_id: str) -> Optional[WardrobeItem]:
        """Fetch item by its custom ID."""
        point_id = self._item_to_uuid(item_id)
        records = self.client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[point_id],
            with_payload=True
        )
        if records and records[0].payload:
            payload = dict(records[0].payload)
            payload["occasions"] = [Occasion(o) for o in payload.get("occasions", []) if o in [x.value for x in Occasion]]
            payload["category"] = GarmentCategory(payload.get("category", "top"))
            return WardrobeItem(**payload)
        return None

    def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID from both vector storage and catalog."""
        point_id = self._item_to_uuid(item_id)
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.PointIdsList(points=[point_id])
        )
        all_items = [it for it in self.get_all_items() if it.id != item_id]
        self._save_inventory_backup(all_items)
        return True

    def search_similar(
        self,
        query_vector: List[float],
        category: Optional[GarmentCategory] = None,
        occasion: Optional[Occasion] = None,
        limit: int = 5,
        score_threshold: float = 0.20
    ) -> List[Dict[str, Any]]:
        """
        Cosine similarity search in Qdrant with optional category / occasion filters.
        Returns list of dicts: {"item": WardrobeItem, "score": float}
        """
        conditions = []
        if category:
            conditions.append(
                models.FieldCondition(
                    key="category_str",
                    match=models.MatchValue(value=category.value)
                )
            )
        if occasion:
            conditions.append(
                models.FieldCondition(
                    key="occasions_str",
                    match=models.MatchAny(any=[occasion.value])
                )
            )

        query_filter = models.Filter(must=conditions) if conditions else None

        # Execute search
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True
        ).points

        matches = []
        for res in results:
            if res.payload:
                payload = dict(res.payload)
                payload["occasions"] = [Occasion(o) for o in payload.get("occasions", []) if o in [x.value for x in Occasion]]
                payload["category"] = GarmentCategory(payload.get("category", "top"))
                matches.append({
                    "item": WardrobeItem(**payload),
                    "score": round(float(res.score), 4)
                })
        return matches


# Singleton instance
_DB_INSTANCE = None

def get_vector_db() -> WardrobeVectorDB:
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        _DB_INSTANCE = WardrobeVectorDB()
    return _DB_INSTANCE
