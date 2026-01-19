"""
Context enrichment using Apify data
"""
from typing import Optional, Dict, Any
import asyncio

from models.page import SDKContext, EnrichedPageContext
from storage.page_context import page_context_storage
from ingestion.apify_pages import apify_crawler


class ContextEnricher:
    """Enrich SDK context with deep page understanding from Apify"""
    
    def __init__(self):
        self.crawler = apify_crawler
    
    def get_enriched_context(self, url: str) -> Optional[EnrichedPageContext]:
        """
        Get enriched context from cache, generate embedding if missing
        
        Args:
            url: Page URL
        
        Returns:
            Enriched context if available (with embedding generated if needed)
        """
        enriched = page_context_storage.get_enriched(url)
        
        # If cached context exists but has no embedding, generate it
        if enriched and not enriched.text_embedding:
            print(f"[Enricher] Generating missing embedding for cached context: {url}")
            try:
                from embeddings.generator import embedding_generator
                
                # Prepare page data for embedding
                page_data = {
                    'title': enriched.title,
                    'topics': enriched.topics or [],
                    'description': enriched.description,
                    'keywords': enriched.keywords or [],
                    'mainContent': enriched.main_content,
                    'headings': enriched.headings if hasattr(enriched, 'headings') else []
                }
                
                # Generate embedding
                embedding = embedding_generator.generate_page_embedding(page_data)
                enriched.text_embedding = embedding
                
                # Save updated context back to cache
                page_context_storage.store_enriched_context(enriched)
                print(f"[Enricher] ✅ Embedding generated ({len(embedding)} dimensions) and cached")
                
            except Exception as e:
                print(f"[Enricher] Error generating embedding: {e}")
                # Continue without embedding
        
        return enriched
    
    def should_trigger_crawl(self, url: str) -> bool:
        """
        Determine if we should trigger a new crawl
        
        Args:
            url: Page URL
        
        Returns:
            True if crawl should be triggered
        """
        # Check if already cached
        enriched = self.get_enriched_context(url)
        if enriched:
            return False
        
        # Check if already being crawled
        if page_context_storage.is_being_crawled(url):
            return False
        
        return True
    
    def merge_contexts(
        self,
        sdk_context: SDKContext,
        enriched_context: Optional[EnrichedPageContext]
    ) -> Dict[str, Any]:
        """
        Return Apify-extracted data (all content comes from Apify)
        
        Args:
            sdk_context: Minimal SDK context (URL + environment)
            enriched_context: Complete data from Apify crawl
        
        Returns:
            Complete context dictionary with Apify data
        """
        if enriched_context:
            # Return everything from Apify
            return {
                "url": enriched_context.url,
                "title": enriched_context.title,
                "headings": enriched_context.headings if hasattr(enriched_context, 'headings') else [],
                "visible_text": enriched_context.main_content,
                "keywords": enriched_context.keywords,
                "topics": enriched_context.topics,
                "visual_styles": enriched_context.visual_styles,
                "system_info": enriched_context.system_info,
                "has_enriched": True
            }
        else:
            # No Apify data - return minimal context
            return {
                "url": sdk_context.url,
                "title": None,
                "headings": [],
                "visible_text": None,
                "keywords": [],
                "topics": [],
                "visual_styles": {},
                "system_info": {},
                "has_enriched": False
            }
    
    async def get_or_enrich(self, sdk_context: SDKContext) -> Dict[str, Any]:
        """
        Get enriched context, waiting for crawl if needed
        
        This is the main method called by ad serving logic
        
        Args:
            sdk_context: SDK context from ad request
        
        Returns:
            Merged context (SDK + enriched from Apify)
        """
        url = sdk_context.url
        
        # Try to get enriched context
        enriched = self.get_enriched_context(url)
        
        # If not available, crawl now and wait for results
        if not enriched and self.should_trigger_crawl(url):
            print(f"[Enricher] No cache for {url}, crawling now...")
            enriched = await self.crawler.crawl_url_sync(url)
            # If crawl failed, try to get from cache anyway
            if not enriched:
                enriched = self.get_enriched_context(url)
        
        # Return merged context
        return self.merge_contexts(sdk_context, enriched)


# Global enricher instance
context_enricher = ContextEnricher()

