"""
Product data models
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Product(BaseModel):
    """Product model for advertisers"""
    
    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: Optional[float] = Field(None, description="Product price")
    currency: str = Field(default="USD", description="Currency code")
    
    # Media
    image_url: str = Field(..., description="Product image URL/path")
    
    # Landing page
    landing_url: str = Field(..., description="Product landing page URL")
    
    # Status
    active: bool = Field(default=True, description="Whether product is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Semantic embedding
    product_embedding: Optional[List[float]] = Field(None, description="Semantic embedding vector")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "prod_001",
                "name": "Wireless Headphones",
                "description": "Premium noise-canceling wireless headphones with 30-hour battery life",
                "price": 299.99,
                "currency": "USD",
                "image_url": "/assets/products/raw/headphones.jpg",
                "category": "Electronics",
                "tags": ["audio", "wireless", "noise-canceling"],
                "brand": "AudioTech",
                "landing_url": "https://example.com/products/headphones"
            }
        }


class ProductCreate(BaseModel):
    """Model for creating a new product"""
    
    name: str
    description: str
    price: Optional[float] = None
    currency: str = "USD"
    image_url: str
    landing_url: str


class ProductUpdate(BaseModel):
    """Model for updating an existing product"""
    
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    landing_url: Optional[str] = None
    active: Optional[bool] = None
    product_embedding: Optional[List[float]] = None

