"""
Apify integration for page crawling and enrichment
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import httpx

from config import settings
from models.page import EnrichedPageContext
from storage.page_context import page_context_storage


class ApifyPageCrawler:
    """
    Apify integration for deep page context extraction
    
    This module calls Apify APIs to:
    1. Trigger actor runs for URL crawling
    2. Poll for completion
    3. Fetch and process results
    4. Store enriched context
    """
    
    def __init__(self):
        if not settings.APIFY_API_TOKEN:
            print("Warning: APIFY_API_TOKEN not set. Apify integration disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self.api_token = settings.APIFY_API_TOKEN
            self.actor_id = settings.APIFY_ACTOR_ID
            self.base_url = "https://api.apify.com/v2"
    
    async def trigger_crawl(self, url: str) -> Optional[str]:
        """
        Trigger Apify actor to crawl a URL
        
        Args:
            url: URL to crawl
        
        Returns:
            Actor run ID if successful
        """
        if not self.enabled:
            print("Apify integration disabled")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Call Apify actor (actor code is in Apify console)
                endpoint = f"{self.base_url}/acts/{self.actor_id}/runs"
                
                # Configure actor input - just pass the parameters
                # The actual crawling logic is in the actor code (Apify console)
                actor_input = {
                    "startUrls": [{"url": url}],
                    "maxRequestsPerCrawl": 1,
                    "maxConcurrency": 1
                }
                
                response = await client.post(
                    endpoint,
                    json=actor_input,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    run_id = data.get("data", {}).get("id")
                    print(f"Triggered Apify crawl for {url}, run_id: {run_id}")
                    return run_id
                else:
                    print(f"Error triggering Apify crawl: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error triggering Apify crawl: {e}")
            return None
    
    async def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Check status of Apify actor run
        
        Args:
            run_id: Actor run ID
        
        Returns:
            Run status data
        """
        if not self.enabled:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                endpoint = f"{self.base_url}/actor-runs/{run_id}"
                response = await client.get(
                    endpoint,
                    params={"token": self.api_token},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json().get("data")
                else:
                    print(f"Error getting run status: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error getting run status: {e}")
            return None
    
    async def fetch_results(self, run_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch results from completed actor run
        
        Args:
            run_id: Actor run ID
        
        Returns:
            List of result items
        """
        if not self.enabled:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # Get dataset ID from run
                run_status = await self.get_run_status(run_id)
                if not run_status:
                    return None
                
                dataset_id = run_status.get("defaultDatasetId")
                if not dataset_id:
                    return None
                
                # Fetch dataset items
                endpoint = f"{self.base_url}/datasets/{dataset_id}/items"
                response = await client.get(
                    endpoint,
                    params={"token": self.api_token},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error fetching results: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching results: {e}")
            return None
    
    async def process_and_store_results(self, url: str, results: List[Dict[str, Any]]):
        """
        Process crawl results, generate embeddings, and store enriched context
        
        Args:
            url: Original URL
            results: Crawl results from Apify
        """
        if not results:
            return
        
        try:
            from embeddings.generator import embedding_generator
            
            # Get first result (we only crawl one page)
            result = results[0]
            
            # Extract data from Apify result
            title = result.get('title', '')
            main_content = result.get('mainContent', '')
            headings = result.get('headings', [])
            description = result.get('description', '')
            author = result.get('author')
            keywords = result.get('keywords', [])
            topics = result.get('topics', [])
            visual_styles = result.get('visualStyles', {})
            system_info = result.get('systemInfo', {})
            
            # Create enriched context
            enriched_context = EnrichedPageContext(
                url=url,
                title=title,
                headings=headings,
                main_content=main_content[:2000],  # Limit stored content
                keywords=keywords,
                topics=topics,
                visual_styles=visual_styles,
                system_info=system_info,
                description=description,
                author=author,
                crawled_at=datetime.utcnow()
            )
            
            # Generate embedding for the page
            print(f"[Apify] Generating embedding for {url}...")
            try:
                page_data = {
                    'title': title,
                    'topics': topics,
                    'description': description,
                    'keywords': keywords,
                    'mainContent': main_content,
                    'headings': headings
                }
                embedding = embedding_generator.generate_page_embedding(page_data)
                enriched_context.text_embedding = embedding
                print(f"[Apify] Embedding generated ({len(embedding)} dimensions)")
            except Exception as e:
                print(f"[Apify] Error generating embedding: {e}")
                enriched_context.text_embedding = None
            
            # Store in cache
            page_context_storage.store_enriched_context(enriched_context)
            print(f"[Apify] Stored enriched context for {url}")
            
        except Exception as e:
            print(f"Error processing crawl results: {e}")
    
    async def crawl_url_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Synchronously crawl a URL and wait for results
        
        Args:
            url: URL to crawl
        
        Returns:
            Enriched page context data or None
        """
        if not self.enabled:
            print(f"Apify disabled, skipping crawl for {url}")
            return None
        
        # Mark as being crawled
        page_context_storage.set_crawling_status(url, True)
        
        try:
            # Trigger crawl
            run_id = await self.trigger_crawl(url)
            if not run_id:
                page_context_storage.set_crawling_status(url, False)
                return None
            
            # Poll for completion (with timeout from settings)
            max_wait = settings.APIFY_TIMEOUT_SECS if hasattr(settings, 'APIFY_TIMEOUT_SECS') else 300
            wait_interval = 5  # seconds
            elapsed = 0
            
            print(f"Waiting for Apify to complete crawl (max {max_wait}s)...")
            
            while elapsed < max_wait:
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
                
                status = await self.get_run_status(run_id)
                if not status:
                    continue
                
                run_status = status.get('status')
                
                if run_status == 'SUCCEEDED':
                    print(f"Apify crawl succeeded after {elapsed}s")
                    # Fetch and process results
                    results = await self.fetch_results(run_id)
                    if results:
                        await self.process_and_store_results(url, results)
                        # Return the stored context
                        stored_context = page_context_storage.get(url)
                        if stored_context and stored_context.enriched_context:
                            return stored_context.enriched_context
                    break
                    
                elif run_status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    print(f"Crawl failed with status: {run_status}")
                    break
                
                # Show progress
                if elapsed % 15 == 0:
                    print(f"Still waiting... ({elapsed}s elapsed, status: {run_status})")
            
            if elapsed >= max_wait:
                print(f"Apify crawl timed out after {max_wait}s")
            
            # Mark as completed
            page_context_storage.set_crawling_status(url, False)
            return None
            
        except Exception as e:
            print(f"Error in crawl process: {e}")
            page_context_storage.set_crawling_status(url, False)
            return None


# Global crawler instance
apify_crawler = ApifyPageCrawler()

