"""
Product matching using cosine similarity

This module finds the most relevant products for a given page context
based on semantic embeddings.
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from models.product import Product


class ProductMatcher:
    """Match products to page context using cosine similarity"""
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
        
        Returns:
            Similarity score between 0 and 1 (higher = more similar)
        """
        if not vec1 or not vec2:
            return 0.0
        
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Handle zero vectors
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = np.dot(a, b) / (norm_a * norm_b)
        
        # Clamp to [0, 1] range (sometimes rounding errors cause slightly > 1)
        return float(max(0.0, min(1.0, similarity)))
    
    def find_best_products(
        self,
        page_embedding: List[float],
        products: List[Product],
        top_k: int = 5,
        min_score: float = 0.0,
        page_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find most relevant products for a page
        
        Args:
            page_embedding: Page content embedding vector
            products: List of products with embeddings
            top_k: Number of top products to return
            min_score: Minimum similarity score threshold
        
        Returns:
            List of dictionaries with product and score:
            [
                {"product": Product, "score": 0.85},
                ...
            ]
        """
        if not page_embedding:
            print("[Matcher] No page embedding provided")
            return []
        
        scores = []
        all_scores = []  # Track all scores for debugging
        
        # Topic-based exclusion filters - exclude mismatched categories
        exclude_keywords_by_topic = {
            'lifestyle': ['camping', 'outdoor', 'hiking', 'trail', 'backpacking', 'wilderness', 'tent', 'lantern', 'survival', 'cot', 
                          'headphone', 'earphone', 'bluetooth', 'wireless', 'technology', 'electronic', 'projector', 'ipad', 'tablet', 'printer'],
            'health': ['camping', 'outdoor', 'hiking', 'adventure', 'headphone', 'earphone', 'technology', 'electronic'],
            'outdoor': ['headphone', 'earphone', 'ipad', 'tablet', 'printer', 'projector', 'technology', 'electronic', 
                        'bedding', 'comforter', 'pillow', 'mirror', 'vase', 'silverware', 'decor', 'furniture'],
            'technology': ['camping', 'outdoor', 'hiking', 'tent', 'lantern', 'cot', 'backpacking',
                           'bedding', 'comforter', 'pillow', 'mirror', 'vase', 'silverware', 'decor', 'furniture']
        }
        
        # Map topics to categories (for boost/penalty logic)
        topic_category_map = {
            'lifestyle': 'lifestyle',
            'health': 'lifestyle',  # Health maps to lifestyle category
            'outdoor': 'outdoor',
            'technology': 'technology',
            'tech': 'technology'
        }
        
        # Get unique categories from all topics
        page_categories = set()
        for topic in page_topics:
            category = topic_category_map.get(topic)
            if category:
                page_categories.add(category)
        
        # For boost/penalty: use primary category if single-category, otherwise use first topic's category
        is_single_category = len(page_categories) == 1
        preferred_category = list(page_categories)[0] if is_single_category else topic_category_map.get(page_topics[0]) if page_topics else None
        
        excluded_count = 0
        for product in products:
            # Skip inactive products
            if not product.active:
                continue
            
            # Skip products without embeddings
            if not hasattr(product, 'product_embedding') or not product.product_embedding:
                continue
            
            # Apply topic-based filtering
            if page_topics:
                product_text = f"{product.name} {product.description}".lower()
                excluded = False
                
                for topic in page_topics:
                    if topic in exclude_keywords_by_topic:
                        exclude_keywords = exclude_keywords_by_topic[topic]
                        for keyword in exclude_keywords:
                            if keyword in product_text:
                                excluded = True
                                excluded_count += 1
                                break
                        if excluded:
                            break
                
                if excluded:
                    continue
            
            # Calculate similarity
            similarity = self.cosine_similarity(page_embedding, product.product_embedding)
            all_scores.append(similarity)
            
            # Apply threshold
            if similarity >= min_score:
                # Boost score for products matching page's primary category
                product_category = self._categorize_product(product)
                boosted_score = similarity
                
                # Apply topic-based boost/penalty
                if preferred_category:
                    if product_category == preferred_category:
                        # Boost products from preferred category (but keep within [0, 1] range)
                        boosted_score = min(1.0, similarity * 1.15)  # 15% boost
                    elif product_category in ['technology', 'lifestyle', 'outdoor'] and product_category != preferred_category:
                        # Penalize products from other main categories
                        boosted_score = similarity * 0.7  # 30% penalty
                
                scores.append({
                    "product": product,
                    "score": boosted_score,
                    "original_score": similarity,  # Keep original for debugging
                    "category": product_category
                })
        
        if excluded_count > 0:
            print(f"[Matcher] Excluded {excluded_count} products based on topic filters")
        
        # Log all scores for debugging
        if all_scores:
            all_scores.sort(reverse=True)
            print(f"[Matcher] All product scores: {[f'{s:.3f}' for s in all_scores[:10]]}...")
            print(f"[Matcher] Score stats: min={min(all_scores):.3f}, max={max(all_scores):.3f}, avg={sum(all_scores)/len(all_scores):.3f}")
        
        # Sort by similarity (highest first)
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Log all scores for debugging
        print(f"[Matcher] Calculated {len(scores)} products above threshold {min_score}")
        if scores:
            print(f"[Matcher] Score range: {scores[-1]['score']:.3f} - {scores[0]['score']:.3f}")
            print(f"[Matcher] Top 5 scores:")
            for i, item in enumerate(scores[:5]):
                print(f"  {i+1}. {item['product'].name[:60]}... (score: {item['score']:.3f})")
        
        # Diversify by topic for multi-topic pages
        result = self._diversify_by_topics(scores, page_topics, top_k)
        
        print(f"[Matcher] Returning top {len(result)} products (diversified: {len(result) != min(len(scores), top_k)})")
        
        return result
    
    def _categorize_product(self, product: Product) -> str:
        """
        Categorize a product into topic categories based on keywords
        
        Returns:
            Category: 'outdoor', 'technology', 'lifestyle', or 'other'
        """
        product_text = f"{product.name} {product.description}".lower()
        
        # Check category keywords (order matters - check most specific first)
        # Tech keywords (check before lifestyle to catch tech-specific items)
        tech_keywords = ['headphone', 'earphone', 'sleep headphone', 'bluetooth headphone', 'ipad', 'tablet', 'computer', 'laptop', 'printer', 'projector', 'tech', 'electronic', 'bluetooth', 'wireless', 'gadget', 'camera']
        # Outdoor keywords
        outdoor_keywords = ['camping', 'outdoor', 'hiking', 'trail', 'backpacking', 'wilderness', 'tent', 'lantern', 'survival', 'cot', 'camping cot', 'camping tent', 'camping light']
        # Lifestyle keywords (home decor, fashion, beauty)
        lifestyle_keywords = ['bedding', 'comforter', 'pillow', 'mirror', 'vase', 'ceramic vase', 'silverware', 'decor', 'furniture', 'home', 'fashion', 'beauty', 'jewelry', 'necklace', 'farmhouse', 'irregular mirror']
        
        # Check in order: tech first (to catch tech items before they match lifestyle)
        if any(keyword in product_text for keyword in tech_keywords):
            return 'technology'
        elif any(keyword in product_text for keyword in outdoor_keywords):
            return 'outdoor'
        elif any(keyword in product_text for keyword in lifestyle_keywords):
            return 'lifestyle'
        else:
            return 'other'
    
    def _diversify_by_topics(
        self,
        scores: List[Dict[str, Any]],
        page_topics: Optional[List[str]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Diversify product selection across topics for multi-topic pages
        For single-topic pages, prioritize products from the matching category
        
        Args:
            scores: Sorted list of product scores (already sorted by boosted scores)
            page_topics: List of page topics
            top_k: Number of products to return
        
        Returns:
            Diversified list of products
        """
        if not page_topics:
            # No topics - just return top K
            return scores[:top_k]
        
        # Map all topics to categories
        topic_category_map = {
            'lifestyle': 'lifestyle',
            'health': 'lifestyle',  # Health maps to lifestyle category
            'outdoor': 'outdoor',
            'technology': 'technology',
            'tech': 'technology'
        }
        
        # Get unique categories from all topics
        page_categories = set()
        category_counts = {}  # Count how many topics map to each category
        
        for topic in page_topics:
            category = topic_category_map.get(topic)
            if category:
                page_categories.add(category)
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Filter out minor categories if one category dominates
        # If one category has >= 2/3 of the topics, treat as single-category
        total_mapped_topics = sum(category_counts.values())
        if total_mapped_topics > 0:
            dominant_category = max(category_counts.items(), key=lambda x: x[1])
            dominant_ratio = dominant_category[1] / total_mapped_topics
            
            # If one category dominates (>= 66% of topics), treat as single-category
            if dominant_ratio >= 0.66:
                is_single_category = True
                preferred_category = dominant_category[0]
                page_categories = {preferred_category}  # Filter to dominant only
                print(f"[Matcher] Dominant category detected: {preferred_category} ({dominant_category[1]}/{total_mapped_topics} topics, {dominant_ratio:.0%})")
            else:
                is_single_category = len(page_categories) == 1
                preferred_category = list(page_categories)[0] if is_single_category else None
        else:
            is_single_category = len(page_categories) == 1
            preferred_category = list(page_categories)[0] if is_single_category else None
        
        # Primary topic for logging
        primary_topic = page_topics[0] if page_topics else None
        
        if is_single_category and preferred_category:
            # Single topic page - prioritize products from preferred category
            # Products are already sorted by boosted scores (preferred category boosted)
            # But ensure we return mostly preferred category if available
            preferred_products = [item for item in scores if item.get('category') == preferred_category]
            other_products = [item for item in scores if item.get('category') != preferred_category]
            
            # Prefer products from preferred category, but allow some others if needed
            result = preferred_products[:top_k]
            if len(result) < top_k and other_products:
                # Fill remaining slots with other products
                remaining = top_k - len(result)
                result.extend(other_products[:remaining])
            
            if preferred_products:
                matched_count = len([r for r in result if r.get('category') == preferred_category])
                print(f"[Matcher] Single-category page (topics: {page_topics} -> {preferred_category}): Prioritized {matched_count}/{len(result)} products from {preferred_category} category")
            
            return result[:top_k]
        
        # Multi-category page - diversify across categories
        print(f"[Matcher] Multi-category page (topics: {page_topics} -> categories: {page_categories}): Diversifying across categories")
        
        # Categorize products
        categorized = {
            'outdoor': [],
            'technology': [],
            'lifestyle': [],
            'other': []
        }
        
        for item in scores:
            category = self._categorize_product(item['product'])
            categorized[category].append(item)
        
        # Count available categories
        available_categories = [cat for cat in categorized if categorized[cat]]
        print(f"[Matcher] Products categorized: {', '.join(f'{cat}:{len(categorized[cat])}' for cat in available_categories)}")
        
        # Prioritize categories that match page topics
        priority_categories = [cat for cat in page_categories if cat in categorized and categorized[cat]]
        other_categories = [cat for cat in ['outdoor', 'technology', 'lifestyle', 'other'] if cat not in page_categories and cat in categorized and categorized[cat]]
        
        # Diversify: prioritize matching categories, then others
        result = []
        used_product_ids = set()
        categories_used = set()
        
        # First, select from priority categories (matching page topics)
        max_rounds = top_k
        round_num = 0
        
        while len(result) < top_k and round_num < max_rounds:
            # Prioritize matching categories
            for category in priority_categories:
                if len(result) >= top_k:
                    break
                
                category_products = categorized[category]
                if not category_products:
                    continue
                
                # Find next unused product in this category
                for item in category_products:
                    product_id = item['product'].id
                    if product_id not in used_product_ids:
                        result.append(item)
                        used_product_ids.add(product_id)
                        categories_used.add(category)
                        break
            
            round_num += 1
            
            # If we've exhausted priority categories, try other categories
            if len(result) < top_k:
                for category in other_categories:
                    if len(result) >= top_k:
                        break
                    
                    category_products = categorized[category]
                    if not category_products:
                        continue
                    
                    for item in category_products:
                        product_id = item['product'].id
                        if product_id not in used_product_ids:
                            result.append(item)
                            used_product_ids.add(product_id)
                            categories_used.add(category)
                            if len(result) >= top_k:
                                break
            
            # If still need more, fill remaining with best overall scores
            if len(result) < top_k:
                for item in scores:
                    product_id = item['product'].id
                    if product_id not in used_product_ids:
                        result.append(item)
                        used_product_ids.add(product_id)
                        if len(result) >= top_k:
                            break
        
        # Ensure we return exactly top_k (or less if not enough products)
        result = result[:top_k]
        
        if len(categories_used) > 1:
            print(f"[Matcher] Diversified across {len(categories_used)} categories: {', '.join(categories_used)}")
        
        return result
    
    def match_by_topics(
        self,
        page_topics: List[str],
        products: List[Product],
        topic_product_map: Optional[Dict[str, List[str]]] = None
    ) -> List[Product]:
        """
        Simple topic-based matching (fallback when embeddings unavailable)
        
        Args:
            page_topics: List of detected topics from page
            products: List of products
            topic_product_map: Optional mapping of topics to product categories
        
        Returns:
            List of products matching the topics
        """
        if not page_topics:
            return []
        
        # Default topic mapping
        if topic_product_map is None:
            topic_product_map = {
                'outdoor': ['camping', 'outdoor', 'adventure', 'hiking', 'survival'],
                'technology': ['tech', 'computer', 'software', 'gadget', 'electronic'],
                'lifestyle': ['fashion', 'home', 'decor', 'wellness', 'beauty'],
                'health': ['fitness', 'health', 'wellness', 'medical'],
                'business': ['business', 'professional', 'office', 'productivity'],
            }
        
        matched_products = []
        
        for product in products:
            if not product.active:
                continue
            
            # Check if product name or description matches topics
            product_text = f"{product.name} {product.description}".lower()
            
            for page_topic in page_topics:
                # Get related keywords for this topic
                related_keywords = topic_product_map.get(page_topic, [page_topic])
                
                # Check if any keyword appears in product text
                if any(keyword in product_text for keyword in related_keywords):
                    matched_products.append(product)
                    break  # Only add once per product
        
        print(f"[Matcher] Topic-based matching: {len(matched_products)} products for topics {page_topics}")
        
        return matched_products


# Global matcher instance
product_matcher = ProductMatcher()

