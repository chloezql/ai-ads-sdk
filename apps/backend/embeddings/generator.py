"""
Semantic embeddings generator using Sentence-BERT

This module provides text-to-vector conversion for:
- Page content (from Apify)
- Product descriptions
"""
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingGenerator:
    """Generate semantic embeddings using Sentence-BERT"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model
        
        Args:
            model_name: HuggingFace model name
                - 'all-MiniLM-L6-v2': Fast, 384 dimensions (default)
                - 'all-mpnet-base-v2': Better quality, 768 dimensions
        """
        print(f"[Embeddings] Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"[Embeddings] Model loaded. Dimension: {self.dimension}")
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
        
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimension
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient)
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts but keep track of indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)
        
        if not valid_texts:
            return [[0.0] * self.dimension for _ in texts]
        
        # Generate embeddings for valid texts
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        
        # Create result with zero vectors for empty texts
        result = [[0.0] * self.dimension for _ in texts]
        for i, embedding in zip(valid_indices, embeddings):
            result[i] = embedding.tolist()
        
        return result
    
    def prepare_page_text(self, page_data: Dict[str, Any]) -> str:
        """
        Prepare page data into rich text representation for embedding
        
        Args:
            page_data: Page context dictionary
        
        Returns:
            Combined text representation
        """
        parts = []
        
        # Title (highest weight)
        if page_data.get('title'):
            parts.append(f"Title: {page_data['title']}")
        
        # Topics (high weight - explicitly extracted themes)
        if page_data.get('topics'):
            topics_str = ', '.join(page_data['topics'])
            parts.append(f"Topics: {topics_str}")
        
        # Description (medium weight)
        if page_data.get('description'):
            parts.append(f"Description: {page_data['description']}")
        
        # Keywords (medium weight - good semantic signals)
        if page_data.get('keywords'):
            # Take top 20 keywords
            keywords = page_data['keywords'][:20]
            keywords_str = ', '.join(keywords)
            parts.append(f"Keywords: {keywords_str}")
        
        # Main content (truncated - context)
        if page_data.get('main_content') or page_data.get('mainContent'):
            content = page_data.get('main_content') or page_data.get('mainContent')
            # Take first 1000 chars to avoid token limits
            content_snippet = content[:1000] if content else ''
            if content_snippet:
                parts.append(f"Content: {content_snippet}")
        
        # Headings (good structural signals)
        if page_data.get('headings'):
            # Take top 10 headings
            headings = page_data['headings'][:10]
            headings_str = ', '.join(headings)
            parts.append(f"Headings: {headings_str}")
        
        return "\n\n".join(parts)
    
    def prepare_product_text(self, product_data: Dict[str, Any]) -> str:
        """
        Prepare product data into text representation for embedding
        
        Args:
            product_data: Product dictionary
        
        Returns:
            Combined text representation
        """
        parts = []
        
        # Product name (high weight)
        if product_data.get('name'):
            parts.append(f"Product: {product_data['name']}")
        
        # Price tier (useful for audience matching)
        if product_data.get('price'):
            price = product_data['price']
            if price > 100:
                price_tier = "luxury"
            elif price > 30:
                price_tier = "mid-range"
            else:
                price_tier = "budget"
            parts.append(f"Price tier: {price_tier}")
        
        # Description (main content)
        if product_data.get('description'):
            parts.append(f"Description: {product_data['description']}")
        
        return "\n\n".join(parts)
    
    def generate_page_embedding(self, page_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for page context
        
        Args:
            page_data: Page context dictionary
        
        Returns:
            Embedding vector
        """
        text = self.prepare_page_text(page_data)
        return self.generate(text)
    
    def generate_product_embedding(self, product_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for product
        
        Args:
            product_data: Product dictionary
        
        Returns:
            Embedding vector
        """
        text = self.prepare_product_text(product_data)
        return self.generate(text)


# Global embedding generator instance
embedding_generator = EmbeddingGenerator()

