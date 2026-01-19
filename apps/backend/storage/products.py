"""
Product data storage layer (demo - simulates database)
"""
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from config import settings
from models.product import Product, ProductCreate, ProductUpdate


class ProductStorage:
    """In-memory product storage with JSON persistence"""
    
    def __init__(self, db_path: Path = settings.PRODUCTS_DB_PATH):
        self.db_path = db_path
        self._products: Dict[str, Product] = {}
        self._load()
    
    def _load(self):
        """Load products from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self._products = {
                        pid: Product(**pdata) for pid, pdata in data.items()
                    }
            except Exception as e:
                print(f"Error loading products: {e}")
                self._products = {}
        else:
            self._products = {}
    
    def _save(self):
        """Save products to JSON file"""
        try:
            with open(self.db_path, 'w') as f:
                data = {
                    pid: p.model_dump(mode='json') for pid, p in self._products.items()
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving products: {e}")
    
    def create(self, product_data: ProductCreate) -> Product:
        """Create a new product"""
        # Generate unique ID
        product_id = f"prod_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        product = Product(
            id=product_id,
            **product_data.model_dump()
        )
        
        self._products[product_id] = product
        self._save()
        return product
    
    def get(self, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        return self._products.get(product_id)
    
    def get_all(self, active_only: bool = True) -> List[Product]:
        """Get all products"""
        products = list(self._products.values())
        if active_only:
            products = [p for p in products if p.active]
        return products
    
    def update(self, product_id: str, update_data: ProductUpdate) -> Optional[Product]:
        """Update a product"""
        product = self._products.get(product_id)
        if not product:
            return None
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(product, field, value)
        
        product.updated_at = datetime.utcnow()
        self._save()
        return product
    
    def delete(self, product_id: str) -> bool:
        """Delete a product"""
        if product_id in self._products:
            del self._products[product_id]
            self._save()
            return True
        return False
    


# Global storage instance
product_storage = ProductStorage()

