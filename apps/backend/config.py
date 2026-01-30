"""
Configuration management for AI Ads Backend
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    
    def get_port(self) -> int:
        """Get port from Railway PORT env var or fallback to API_PORT"""
        import os
        return int(os.getenv("PORT", self.API_PORT))
    
    # Apify Configuration
    APIFY_API_TOKEN: Optional[str] = None
    APIFY_ACTOR_ID: str = "tropical_lease/web-context-extractor"
    APIFY_TIMEOUT_SECS: int = 300  # 5 minutes
    
    # AI Image Editing (fal.ai) Configuration
    FAL_KEY: Optional[str] = None
    FAL_MODEL: str = "fal-ai/nano-banana/edit"
    
    # Supabase Storage Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    PRODUCTS_DIR: Path = ASSETS_DIR / "products"
    
    # Data Storage
    STORAGE_DIR: Path = Path(__file__).parent / "storage"
    PRODUCTS_DB_PATH: Path = STORAGE_DIR / "products.json"
    PAGE_CONTEXT_DB_PATH: Path = STORAGE_DIR / "page_context.json"
    
    # Cache Configuration
    PAGE_CONTEXT_CACHE_TTL: int = 86400  # 24 hours in seconds
    
    # Multi-Product Image Configuration
    MULTI_PRODUCT_COUNT: int = 2  # Number of products to combine in one image (default: 2)
    
    class Config:
        # Look for .env in project root (3 levels up from this file)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        self.PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
