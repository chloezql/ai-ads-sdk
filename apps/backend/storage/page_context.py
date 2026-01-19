"""
Page context storage (demo - simulates cache)
"""
import json
from typing import Optional, Dict
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

from config import settings
from models.page import EnrichedPageContext, PageContextCache


class PageContextStorage:
    """In-memory page context storage with JSON persistence"""
    
    def __init__(self, db_path: Path = settings.PAGE_CONTEXT_DB_PATH):
        self.db_path = db_path
        self._cache: Dict[str, PageContextCache] = {}
        self._load()
    
    def _load(self):
        """Load page contexts from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self._cache = {
                        url: PageContextCache(**cache_data)
                        for url, cache_data in data.items()
                    }
            except Exception as e:
                print(f"Error loading page contexts: {e}")
                self._cache = {}
        else:
            self._cache = {}
    
    def _save(self):
        """Save page contexts to JSON file"""
        try:
            with open(self.db_path, 'w') as f:
                data = {
                    url: cache.model_dump(mode='json')
                    for url, cache in self._cache.items()
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving page contexts: {e}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for caching (remove fragments, trailing slashes)"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        return normalized
    
    def get(self, url: str) -> Optional[PageContextCache]:
        """Get cached page context"""
        normalized_url = self._normalize_url(url)
        cache = self._cache.get(normalized_url)
        
        if cache:
            # Check if cache is still valid
            age = datetime.utcnow() - cache.cached_at
            if age.total_seconds() > settings.PAGE_CONTEXT_CACHE_TTL:
                # Cache expired
                return None
        
        return cache
    
    def get_enriched(self, url: str) -> Optional[EnrichedPageContext]:
        """Get enriched context if available"""
        cache = self.get(url)
        if cache and cache.enriched_context:
            return cache.enriched_context
        return None
    
    def set_crawling_status(self, url: str, is_crawling: bool):
        """Mark URL as being crawled"""
        normalized_url = self._normalize_url(url)
        
        if normalized_url not in self._cache:
            self._cache[normalized_url] = PageContextCache(
                url=normalized_url,
                is_crawling=is_crawling,
                last_crawl_triggered=datetime.utcnow() if is_crawling else None
            )
        else:
            cache = self._cache[normalized_url]
            cache.is_crawling = is_crawling
            if is_crawling:
                cache.last_crawl_triggered = datetime.utcnow()
        
        self._save()
    
    def store_enriched_context(self, enriched_context: EnrichedPageContext):
        """Store enriched page context"""
        normalized_url = self._normalize_url(enriched_context.url)
        
        cache = PageContextCache(
            url=normalized_url,
            enriched_context=enriched_context,
            is_crawling=False,
            cached_at=datetime.utcnow()
        )
        
        self._cache[normalized_url] = cache
        self._save()
    
    def is_being_crawled(self, url: str) -> bool:
        """Check if URL is currently being crawled"""
        cache = self.get(url)
        if not cache:
            return False
        
        # Check if crawl was triggered recently (within last 5 minutes)
        if cache.is_crawling and cache.last_crawl_triggered:
            age = datetime.utcnow() - cache.last_crawl_triggered
            if age.total_seconds() < 300:  # 5 minutes
                return True
        
        return False
    
    def invalidate(self, url: str):
        """Invalidate cache for a URL"""
        normalized_url = self._normalize_url(url)
        if normalized_url in self._cache:
            del self._cache[normalized_url]
            self._save()
    
    def clear_all(self):
        """Clear all cached contexts"""
        self._cache = {}
        self._save()


# Global storage instance
page_context_storage = PageContextStorage()

