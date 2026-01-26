"""
Ad request data model
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class AdRequest(BaseModel):
    """Simplified ad request from SDK - only URL and basic info"""
    
    # Publisher identification
    publisher_id: str = Field(..., description="Publisher API key")
    
    # URL to crawl
    url: str = Field(..., description="Page URL to extract context from")
    
    # Environment (from browser)
    device_type: str = Field(default="desktop", description="Device type: mobile, tablet, desktop")
    viewport_width: Optional[int] = Field(None, description="Browser viewport width")
    viewport_height: Optional[int] = Field(None, description="Browser viewport height")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    
    # Persona information (from external website)
    persona_data: Optional[dict] = Field(None, description="Persona data from external website")
    
    # Ad slot
    slot_id: str = Field(..., description="Ad slot identifier")
    slot_width: Optional[int] = Field(None, description="Ad slot width")
    slot_height: Optional[int] = Field(None, description="Ad slot height")

