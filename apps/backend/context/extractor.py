"""
Context extraction from SDK requests (fast, real-time)
"""
from typing import Dict, Any, Optional
from models.page import SDKContext
from models.ad import AdRequest


class ContextExtractor:
    """Extract minimal context from SDK requests (URL + environment only)"""
    
    def extract_sdk_context(self, ad_request: AdRequest) -> SDKContext:
        """
        Extract minimal SDK context from ad request
        
        Args:
            ad_request: Ad request from SDK (URL + environment)
        
        Returns:
            Structured SDK context
        """
        return SDKContext(
            url=ad_request.url,
            device_type=ad_request.device_type,
            viewport_width=ad_request.viewport_width,
            viewport_height=ad_request.viewport_height,
            user_agent=ad_request.user_agent,
            slot_id=ad_request.slot_id,
            slot_width=ad_request.slot_width,
            slot_height=ad_request.slot_height
        )


# Global extractor instance
context_extractor = ContextExtractor()

