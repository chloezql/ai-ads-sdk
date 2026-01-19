"""
Page context data models
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SDKContext(BaseModel):
    """Minimal context from SDK - only URL and environment"""
    
    # URL to crawl
    url: str = Field(..., description="Page URL to extract")
    
    # Browser environment
    device_type: str = Field(default="desktop", description="Device type: mobile, tablet, desktop")
    viewport_width: Optional[int] = Field(None, description="Viewport width in pixels")
    viewport_height: Optional[int] = Field(None, description="Viewport height in pixels")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    # Ad slot info
    slot_id: str = Field(..., description="Ad slot identifier")
    slot_width: Optional[int] = Field(None, description="Ad slot width")
    slot_height: Optional[int] = Field(None, description="Ad slot height")


class EnrichedPageContext(BaseModel):
    """Enriched context from Apify crawl"""
    
    url: str = Field(..., description="Page URL")
    
    # Content extraction from Apify
    title: Optional[str] = Field(None, description="Page title")
    headings: List[str] = Field(default_factory=list, description="H1-H3 headings")
    main_content: Optional[str] = Field(None, description="Main article/content text")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    topics: List[str] = Field(default_factory=list, description="Detected topics")
    
    # Visual styles
    visual_styles: Dict[str, Any] = Field(default_factory=dict, description="Visual design elements")
    
    # System information
    system_info: Dict[str, Any] = Field(default_factory=dict, description="Browser/system information")
    
    # Metadata
    description: Optional[str] = Field(None)
    author: Optional[str] = Field(None)
    published_date: Optional[str] = Field(None)
    
    # Semantic understanding
    text_embedding: Optional[List[float]] = Field(None, description="Page content embedding")
    
    # Apify metadata
    apify_run_id: Optional[str] = Field(None, description="Apify actor run ID")
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Cache control
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    cache_valid_until: datetime = Field(default_factory=datetime.utcnow)


class PageContextCache(BaseModel):
    """Cache entry for page context"""
    
    url: str
    enriched_context: Optional[EnrichedPageContext] = None
    is_crawling: bool = Field(default=False, description="Whether a crawl is in progress")
    last_crawl_triggered: Optional[datetime] = None
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "enriched_context": {
                    "url": "https://example.com/article",
                    "title": "The Future of Technology",
                    "main_content": "Article content here...",
                    "keywords": ["technology", "innovation", "future"],
                    "topics": ["technology", "business"]
                },
                "is_crawling": False
            }
        }

