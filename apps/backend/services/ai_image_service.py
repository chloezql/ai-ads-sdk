"""
AI Image Editing Service using fal.ai nano-banana model
Edits product images to match website styling
"""
import os
import hashlib
from typing import List, Dict, Any, Optional
import asyncio

try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False
    print("Warning: 'fal_client' not installed. AI image editing will be disabled.")

from config import settings
from services.file_upload_service import file_upload_service

# In-memory cache for edited images to avoid duplicate submissions
# Key: hash of (image_url + prompt), Value: edited_image_url
_edited_image_cache: Dict[str, str] = {}
# Track in-progress edits to avoid duplicate concurrent submissions
_editing_in_progress: Dict[str, asyncio.Task] = {}


class AIImageService:
    """Service for editing product images using AI"""
    
    def __init__(self):
        if not FAL_AVAILABLE:
            self.enabled = False
            print("[AIImage] AI image editing disabled - fal_client not installed")
            return
        
        # Configure fal client from settings
        fal_key = settings.FAL_KEY or os.getenv("FAL_API_KEY")  # Fallback to env var
        if not fal_key:
            self.enabled = False
            print("[AIImage] AI image editing disabled - FAL_KEY not set in config or environment")
            return
        
        self.enabled = True
        self.model = settings.FAL_MODEL
        self.fal_key = fal_key
        
        # Set API key in environment for fal_client (it reads from FAL_KEY env var)
        os.environ["FAL_KEY"] = self.fal_key
        
        print(f"[AIImage] Initialized with model: {self.model} (using async API)")
    
    def _get_cache_key(self, image_url: str, prompt: str) -> str:
        """Generate cache key from image URL and prompt"""
        cache_data = f"{image_url}::{prompt}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    async def edit_single_image(
        self,
        image_url: str,
        prompt: str,
        index: int = 0,
        api_base_url: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Edit a single product image with caching to avoid duplicate submissions
        
        Args:
            image_url: URL of the product image to edit (can be relative)
            prompt: Editing prompt based on page context
            index: Index for logging
            api_base_url: Base URL to convert relative URLs to absolute
        
        Returns:
            Dict with edited_image_url and status, or None if failed
        """
        if not self.enabled:
            print(f"[AIImage] Editing disabled, skipping image {index + 1}")
            return None
        
        # Generate cache key
        cache_key = self._get_cache_key(image_url, prompt)
        
        # Check cache first
        if cache_key in _edited_image_cache:
            cached_url = _edited_image_cache[cache_key]
            print(f"[AIImage] ✅ [{index + 1}] Using cached edited image: {cached_url[:60]}...")
            return {
                "edited_image_url": cached_url,
                "status": "cached",
                "index": index
            }
        
        # Check if edit is already in progress
        if cache_key in _editing_in_progress:
            print(f"[AIImage] ⏳ [{index + 1}] Edit already in progress, waiting for result...")
            try:
                # Wait for the in-progress edit to complete
                result = await _editing_in_progress[cache_key]
                if result and result.get("edited_image_url"):
                    print(f"[AIImage] ✅ [{index + 1}] Got result from concurrent edit: {result['edited_image_url'][:60]}...")
                    return result
                else:
                    print(f"[AIImage] ⚠️  [{index + 1}] Concurrent edit returned no result, will retry")
            except Exception as e:
                print(f"[AIImage] ⚠️  [{index + 1}] Error waiting for concurrent edit: {e}")
            # If concurrent edit failed, continue to create new edit
        
        # Create the edit task
        async def perform_edit():
            try:
                product_name = image_url.split('/')[-1] if '/' in image_url else image_url
                print(f"[AIImage] 🖼️  [{index + 1}] Starting edit for: {product_name[:50]}...")
                
                # Determine if this is a local file path or URL
                is_local_file = os.path.exists(image_url) and os.path.isfile(image_url)
                is_localhost_url = (
                    image_url.startswith('http://localhost') or 
                    image_url.startswith('https://localhost') or
                    image_url.startswith('http://127.0.0.1') or
                    image_url.startswith('https://127.0.0.1')
                )
                
                # If it's a local file, upload to Supabase storage
                if is_local_file:
                    print(f"[AIImage] 📤 [{index + 1}] Uploading local file to Supabase storage...")
                    try:
                        filename = os.path.basename(image_url)
                        uploaded_url = await file_upload_service.upload_file_from_path(image_url, filename)
                        if not uploaded_url:
                            print(f"[AIImage] ❌ [{index + 1}] Failed to upload local file to Supabase")
                            return None
                        absolute_image_url = uploaded_url
                        print(f"[AIImage] ✅ [{index + 1}] Image uploaded to Supabase: {uploaded_url[:60]}...")
                    except Exception as e:
                        print(f"[AIImage] ❌ [{index + 1}] Failed to upload local file: {e}")
                        return None
                elif is_localhost_url:
                    # If it's a localhost URL, download and upload to Supabase
                    print(f"[AIImage] 📤 [{index + 1}] Downloading from localhost and uploading to Supabase storage...")
                    try:
                        filename = os.path.basename(image_url) or "image.jpg"
                        uploaded_url = await file_upload_service.upload_file_from_url(image_url, filename)
                        if not uploaded_url:
                            print(f"[AIImage] ❌ [{index + 1}] Failed to upload localhost image to Supabase")
                            return None
                        absolute_image_url = uploaded_url
                        print(f"[AIImage] ✅ [{index + 1}] Image uploaded to Supabase: {uploaded_url[:60]}...")
                    except Exception as e:
                        print(f"[AIImage] ❌ [{index + 1}] Failed to upload localhost image: {e}")
                        return None
                else:
                    # It's a public URL or relative path, build absolute URL
                    absolute_image_url = image_url
                    if not image_url.startswith('http://') and not image_url.startswith('https://'):
                        if api_base_url:
                            absolute_image_url = f"{api_base_url.rstrip('/')}{image_url}"
                        else:
                            print(f"[AIImage] ⚠️  [{index + 1}] Warning: Relative URL {image_url} but no api_base_url provided")
                            return None
                    
                    # Check if the absolute URL is still localhost (after building from relative path)
                    if (
                        absolute_image_url.startswith('http://localhost') or 
                        absolute_image_url.startswith('https://localhost') or
                        absolute_image_url.startswith('http://127.0.0.1') or
                        absolute_image_url.startswith('https://127.0.0.1')
                    ):
                        # Download from localhost and upload to Supabase
                        print(f"[AIImage] 📤 [{index + 1}] Downloading from localhost and uploading to Supabase storage...")
                        try:
                            filename = os.path.basename(absolute_image_url) or "image.jpg"
                            uploaded_url = await file_upload_service.upload_file_from_url(absolute_image_url, filename)
                            if not uploaded_url:
                                print(f"[AIImage] ❌ [{index + 1}] Failed to upload localhost image to Supabase")
                                return None
                            absolute_image_url = uploaded_url
                            print(f"[AIImage] ✅ [{index + 1}] Image uploaded to Supabase: {uploaded_url[:60]}...")
                        except Exception as e:
                            print(f"[AIImage] ❌ [{index + 1}] Failed to upload localhost image: {e}")
                            return None
                
                print(f"[AIImage] 📝 [{index + 1}] Prompt: {prompt[:80]}...")
                print(f"[AIImage] 🔗 [{index + 1}] Using image URL: {absolute_image_url[:80]}...")
                
                # Use async API for cleaner parallel execution
                # Submit the job asynchronously (non-blocking)
                # fal_client.submit_async reads API key from FAL_KEY env var automatically
                handler = await fal_client.submit_async(
                    self.model,
                    arguments={
                        "prompt": prompt,
                        "image_urls": [absolute_image_url],
                        "num_images": 1,
                        "output_format": "webp"
                    }
                )
                
                request_id = handler.request_id
                print(f"[AIImage] 📤 [{index + 1}] Submitted job: {request_id}")
                
                # Poll for status updates and logs (non-blocking, allows other tasks to run)
                async for status in handler.iter_events(with_logs=True, interval=2.0):
                    # Handle logs if available
                    if hasattr(status, 'logs') and status.logs:
                        for log in status.logs:
                            if isinstance(log, dict) and log.get("message"):
                                print(f"[AIImage] 📊 [{index + 1}] {log['message']}")
                            elif hasattr(log, 'message'):
                                print(f"[AIImage] 📊 [{index + 1}] {log.message}")
                
                # Get the final result (awaits completion)
                result = await handler.get()
                
                # Extract generated image URL from async result
                # Result structure from handler.get() should be a dict
                generated_images = []
                if isinstance(result, dict):
                    # Try different possible result structures
                    generated_images = (
                        result.get("images") or 
                        result.get("data", {}).get("images") or 
                        result.get("output", {}).get("images") or
                        []
                    )
                elif hasattr(result, "images"):
                    img_data = result.images
                    generated_images = img_data if isinstance(img_data, list) else [img_data]
                elif hasattr(result, "data") and hasattr(result.data, "images"):
                    img_data = result.data.images
                    generated_images = img_data if isinstance(img_data, list) else [img_data]
                
                if not generated_images or len(generated_images) == 0:
                    print(f"[AIImage] ❌ [{index + 1}] No images returned from fal.ai")
                    return None
                
                # Get URL from first image (could be dict or object)
                first_image = generated_images[0]
                edited_url = first_image.get("url") if isinstance(first_image, dict) else getattr(first_image, "url", None)
                
                if not edited_url:
                    print(f"[AIImage] ❌ [{index + 1}] No URL in result from fal.ai")
                    return None
                
                print(f"[AIImage] ✅ [{index + 1}] Successfully edited: {edited_url[:60]}...")
                
                # Cache the result
                _edited_image_cache[cache_key] = edited_url
                
                return {
                    "edited_image_url": edited_url,
                    "status": "completed",
                    "index": index
                }
            except Exception as e:
                print(f"[AIImage] ❌ [{index + 1}] Error editing image: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Create task and mark as in-progress
        edit_task = asyncio.create_task(perform_edit())
        _editing_in_progress[cache_key] = edit_task
        
        try:
            # Wait for the edit to complete
            result = await edit_task
            return result
        finally:
            # Remove from in-progress
            if cache_key in _editing_in_progress:
                del _editing_in_progress[cache_key]
    
    async def edit_multi_product_image(
        self,
        products: List[Dict[str, Any]],
        prompt: str,
        api_base_url: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Edit multiple product images into one combined image
        
        Args:
            products: List of product dicts with 'image_url' (should match MULTI_PRODUCT_COUNT)
            prompt: Prompt for combining products
            api_base_url: Base URL to convert relative image_urls to absolute
        
        Returns:
            Dict with edited_image_url and product info, or None if failed
        """
        if not self.enabled:
            print("[AIImage] Editing disabled, skipping multi-product image")
            return None
        
        multi_product_count = settings.MULTI_PRODUCT_COUNT
        if len(products) != multi_product_count:
            print(f"[AIImage] ⚠️  edit_multi_product_image expects {multi_product_count} products, got {len(products)}")
            return None
        
        try:
            # Get both image URLs
            image_urls = []
            for i, product in enumerate(products):
                image_url = product.get("image_url")
                if not image_url:
                    print(f"[AIImage] ⚠️  Product {i + 1} ({product.get('name', 'unknown')}) has no image_url")
                    return None
                
                # Convert to absolute URL if needed
                is_local_file = os.path.exists(image_url) and os.path.isfile(image_url)
                is_localhost_url = (
                    image_url.startswith('http://localhost') or 
                    image_url.startswith('https://localhost') or
                    image_url.startswith('http://127.0.0.1') or
                    image_url.startswith('https://127.0.0.1')
                )
                
                if is_local_file:
                    filename = os.path.basename(image_url)
                    uploaded_url = await file_upload_service.upload_file_from_path(image_url, filename)
                    if not uploaded_url:
                        return None
                    image_urls.append(uploaded_url)
                elif is_localhost_url:
                    filename = os.path.basename(image_url) or "image.jpg"
                    uploaded_url = await file_upload_service.upload_file_from_url(image_url, filename)
                    if not uploaded_url:
                        return None
                    image_urls.append(uploaded_url)
                else:
                    absolute_image_url = image_url
                    if not image_url.startswith('http://') and not image_url.startswith('https://'):
                        if api_base_url:
                            absolute_image_url = f"{api_base_url.rstrip('/')}{image_url}"
                        else:
                            return None
                    image_urls.append(absolute_image_url)
            
            product_names = [p.get('name', f'Product {i+1}') for i, p in enumerate(products)]
            print(f"[AIImage] 🖼️  Combining {len(products)} products into one image: {', '.join(product_names)}")
            print(f"[AIImage] 📝 Prompt: {prompt[:80]}...")
            
            # Generate cache key from both images and prompt
            cache_data = f"{'::'.join(sorted(image_urls))}::{prompt}"
            cache_key = hashlib.md5(cache_data.encode()).hexdigest()
            
            # Check cache
            if cache_key in _edited_image_cache:
                cached_url = _edited_image_cache[cache_key]
                print(f"[AIImage] ✅ Using cached multi-product image: {cached_url[:60]}...")
                return {
                    "edited_image_url": cached_url,
                    "products": products,
                    "status": "cached"
                }
            
            # Submit job with both images
            handler = await fal_client.submit_async(
                self.model,
                arguments={
                    "prompt": prompt,
                    "image_urls": image_urls,  # Both product images
                    "num_images": 1,
                    "output_format": "webp"
                }
            )
            
            request_id = handler.request_id
            print(f"[AIImage] 📤 Submitted multi-product job: {request_id}")
            
            # Poll for status
            async for status in handler.iter_events(with_logs=True, interval=2.0):
                if hasattr(status, 'logs') and status.logs:
                    for log in status.logs:
                        if isinstance(log, dict) and log.get("message"):
                            print(f"[AIImage] 📊 {log['message']}")
            
            # Get result
            result = await handler.get()
            
            # Extract generated image URL
            generated_images = []
            if isinstance(result, dict):
                generated_images = (
                    result.get("images") or 
                    result.get("data", {}).get("images") or 
                    result.get("output", {}).get("images") or
                    []
                )
            elif hasattr(result, "images"):
                img_data = result.images
                generated_images = img_data if isinstance(img_data, list) else [img_data]
            
            if not generated_images or len(generated_images) == 0:
                print(f"[AIImage] ❌ No images returned from fal.ai")
                return None
            
            first_image = generated_images[0]
            edited_url = first_image.get("url") if isinstance(first_image, dict) else getattr(first_image, "url", None)
            
            if not edited_url:
                print(f"[AIImage] ❌ No URL in result from fal.ai")
                return None
            
            print(f"[AIImage] ✅ Successfully created multi-product image: {edited_url[:60]}...")
            
            # Cache the result
            _edited_image_cache[cache_key] = edited_url
            
            return {
                "edited_image_url": edited_url,
                "products": products,
                "status": "completed"
            }
            
        except Exception as e:
            print(f"[AIImage] ❌ Error creating multi-product image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def edit_images_batch(
        self,
        products: List[Dict[str, Any]],
        prompts: List[str],
        api_base_url: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Edit multiple product images in parallel using asyncio.gather
        Handles mixed case: first N products combined into one image, rest as individual images
        
        Args:
            products: List of product dicts with 'image_url'
            prompts: List of prompts (1 for multi-product, then 1 per remaining product)
            api_base_url: Base URL to convert relative image_urls to absolute
        
        Returns:
            List of results with edited_image_url:
            - 1 result for multi-product image (with all N products' info)
            - 1 result per remaining product (individual images)
        """
        if not self.enabled:
            print("[AIImage] Editing disabled, returning original images")
            return products
        
        multi_product_count = settings.MULTI_PRODUCT_COUNT
        
        # Validate prompts count
        # Expected: 1 prompt for multi-product (first N products) + 1 prompt per remaining product
        expected_prompts = 0
        if len(products) >= multi_product_count:
            expected_prompts = 1 + (len(products) - multi_product_count)  # 1 multi-product + remaining individual
        else:
            expected_prompts = len(products)  # All individual
        
        if len(prompts) != expected_prompts:
            print(f"[AIImage] Mismatch: {len(products)} products but {len(prompts)} prompts (expected {expected_prompts})")
            return products
        
        # Check if we have multi-product case (first prompt is for multi-product)
        if len(products) >= multi_product_count and len(prompts) > 0:
            # First N products go into multi-product image
            multi_products = products[:multi_product_count]
            multi_prompt = prompts[0]
            
            # Remaining products are individual
            remaining_products = products[multi_product_count:]
            remaining_prompts = prompts[1:]
            
            results = []
            
            # Process multi-product image
            if multi_products and multi_prompt:
                print(f"[AIImage] 🚀 Creating multi-product image from {len(multi_products)} products...")
                multi_result = await self.edit_multi_product_image(multi_products, multi_prompt, api_base_url)
                
                if multi_result and multi_result.get("edited_image_url"):
                    # Create combined result for multi-product image
                    product_names = [p.get("name", f"Product {i+1}") for i, p in enumerate(multi_products)]
                    product_ids = [p["id"] for p in multi_products]
                    product_descriptions = [p.get("description", "") for p in multi_products]
                    
                    combined_result = {
                        "id": "_".join(product_ids),
                        "name": " & ".join(product_names),
                        "description": " | ".join([d for d in product_descriptions if d]),
                        "price": multi_products[0].get("price"),
                        "currency": multi_products[0].get("currency", "USD"),
                        "edited_image_url": multi_result["edited_image_url"],
                        "match_score": max([p.get("match_score", 0) for p in multi_products]),
                        "is_multi_product": True,
                        "products": [
                            {
                                "id": p["id"],
                                "name": p.get("name", f"Product {i+1}"),
                                "image_url": p.get("image_url"),
                                "landing_url": p.get("landing_url")
                            }
                            for i, p in enumerate(multi_products)
                        ]
                    }
                    
                    # Add individual image_url and landing_url fields
                    for i, product in enumerate(multi_products):
                        if i == 0:
                            combined_result["image_url"] = product.get("image_url")
                            combined_result["landing_url"] = product.get("landing_url")
                        else:
                            combined_result[f"image_url_{i+1}"] = product.get("image_url")
                            combined_result[f"landing_url_{i+1}"] = product.get("landing_url")
                    
                    results.append(combined_result)
                    print(f"[AIImage] ✅ Multi-product image created successfully")
                else:
                    # Fallback: add original products if multi-product editing failed
                    results.extend(multi_products)
            
            # Process remaining individual products
            if remaining_products and remaining_prompts:
                print(f"[AIImage] 🚀 Processing {len(remaining_products)} individual product images...")
                import time
                start_time = time.time()
                
                # Create tasks for individual products
                tasks = []
                product_indices = []
                
                for i, (product, prompt) in enumerate(zip(remaining_products, remaining_prompts)):
                    image_url = product.get("image_url")
                    if not image_url:
                        print(f"[AIImage] ⚠️  Product {i + 1} ({product.get('name', 'unknown')}) has no image_url, skipping")
                        continue
                    
                    task = self.edit_single_image(image_url, prompt, i, api_base_url)
                    tasks.append(task)
                    product_indices.append(i)
                
                if tasks:
                    # Execute individual product edits in parallel
                    individual_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for idx, (original_idx, result) in enumerate(zip(product_indices, individual_results)):
                        product = remaining_products[original_idx].copy()
                        
                        if isinstance(result, Exception):
                            print(f"[AIImage] ❌ Error editing product {original_idx + 1} ({product.get('name', 'unknown')}): {result}")
                            results.append(product)
                        elif result and result.get("edited_image_url"):
                            product["edited_image_url"] = result["edited_image_url"]
                            results.append(product)
                        else:
                            print(f"[AIImage] ⚠️  No edited image returned for product {original_idx + 1} ({product.get('name', 'unknown')})")
                            results.append(product)
                    
                    elapsed_time = time.time() - start_time
                    print(f"[AIImage] ✅ Individual product editing complete: {len([r for r in results if r.get('edited_image_url')])} images in {elapsed_time:.2f}s")
                else:
                    results.extend(remaining_products)
            
            return results if results else products
        
        # Fallback: handle case where we don't have enough products for multi-product
        # Process all as individual products
        print(f"[AIImage] 🚀 Processing {len(products)} products as individual images...")
        import time
        start_time = time.time()
        
        tasks = []
        product_indices = []
        
        for i, (product, prompt) in enumerate(zip(products, prompts)):
            image_url = product.get("image_url")
            if not image_url:
                print(f"[AIImage] ⚠️  Product {i + 1} ({product.get('name', 'unknown')}) has no image_url, skipping")
                continue
            
            task = self.edit_single_image(image_url, prompt, i, api_base_url)
            tasks.append(task)
            product_indices.append(i)
        
        if not tasks:
            print("[AIImage] ⚠️  No valid tasks to execute")
            return products
        
        print(f"[AIImage] 📦 Executing {len(tasks)} image editing tasks in parallel...")
        
        # Execute all tasks in parallel
        edit_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        edited_products = []
        success_count = 0
        
        for idx, (original_idx, result) in enumerate(zip(product_indices, edit_results)):
            product = products[original_idx].copy()
            
            if isinstance(result, Exception):
                print(f"[AIImage] ❌ Error editing product {original_idx + 1} ({product.get('name', 'unknown')}): {result}")
                edited_products.append(product)
            elif result and result.get("edited_image_url"):
                product["edited_image_url"] = result["edited_image_url"]
                edited_products.append(product)
                success_count += 1
            else:
                print(f"[AIImage] ⚠️  No edited image returned for product {original_idx + 1} ({product.get('name', 'unknown')})")
                edited_products.append(product)
        
        elapsed_time = time.time() - start_time
        print(f"[AIImage] ✅ Parallel editing complete: {success_count}/{len(tasks)} images edited successfully in {elapsed_time:.2f}s")
        
        return edited_products


# Global service instance
ai_image_service = AIImageService()

