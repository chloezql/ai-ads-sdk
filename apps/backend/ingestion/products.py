"""
Product ingestion pipeline - simplified version
Stores products locally
"""
from typing import List
from pathlib import Path

from config import settings
from models.product import Product, ProductCreate
from storage.products import product_storage


class ProductIngestionPipeline:
    """Pipeline for ingesting products"""
    
    def ingest_product(self, product_data: ProductCreate) -> Product:
        """
        Ingest a single product
        
        Args:
            product_data: Product creation data
        
        Returns:
            Created product
        """
        # Create product
        product = product_storage.create(product_data)
        print(f"Created product {product.id}: {product.name}")
        return product
    
    def ingest_batch(self, products_data: List[ProductCreate]) -> List[Product]:
        """
        Ingest multiple products
        
        Args:
            products_data: List of product creation data
        
        Returns:
            List of created products
        """
        products = []
        
        for i, product_data in enumerate(products_data):
            print(f"\nIngesting product {i+1}/{len(products_data)}")
            try:
                product = self.ingest_product(product_data)
                products.append(product)
            except Exception as e:
                print(f"Error ingesting product {product_data.name}: {e}")
        
        return products


# Global pipeline instance
product_pipeline = ProductIngestionPipeline()
