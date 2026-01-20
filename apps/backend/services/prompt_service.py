"""
Prompt generation service for AI image editing
Creates prompts based on page context (topics, keywords, visual_styles) to match web styling
"""
from typing import Dict, Any, List, Optional


def create_editing_prompt(
    page_context: Dict[str, Any],
    product_name: str
) -> str:
    """
    Create a prompt for editing product images to match page styling
    
    Args:
        page_context: Page context containing topics, keywords, visual_styles
        product_name: Name of the product being edited
    
    Returns:
        Formatted prompt string for nano-banana/edit model
    """
    topics = page_context.get("topics", [])
    keywords = page_context.get("keywords", [])
    visual_styles = page_context.get("visual_styles", {}) or {}
    
    # Build prompt
    prompt_parts = []
    
    # Base instruction
    prompt_parts.append(f"Edit this product image ({product_name}) to match the website's visual style and theme.")
    
    # Add topics
    if topics:
        topics_str = ", ".join(topics)
        prompt_parts.append(f"Match the page topics: {topics_str}.")
    
    # Add visual styles
    if visual_styles:
        style_parts = []
        
        if visual_styles.get("theme"):
            style_parts.append(f"theme: {visual_styles['theme']}")
        
        if visual_styles.get("backgroundColor"):
            style_parts.append(f"background color: {visual_styles['backgroundColor']}")
        
        if visual_styles.get("textColor"):
            style_parts.append(f"text color: {visual_styles['textColor']}")
        
        if visual_styles.get("primaryColor"):
            style_parts.append(f"primary color: {visual_styles['primaryColor']}")
        
        if visual_styles.get("fontFamily"):
            style_parts.append(f"font style: {visual_styles['fontFamily']}")
        
        if visual_styles.get("accentColors"):
            accent_colors = ", ".join(visual_styles["accentColors"][:3])  # Limit to 3
            style_parts.append(f"accent colors: {accent_colors}")
        
        if style_parts:
            prompt_parts.append(f"Apply visual styles: {', '.join(style_parts)}.")
    
    # Add relevant keywords (top 10 most relevant)
    if keywords:
        relevant_keywords = keywords[:10]
        keywords_str = ", ".join(relevant_keywords)
        prompt_parts.append(f"Incorporate these style elements: {keywords_str}.")
    
    # Add critical rules
    prompt_parts.append("CRITICAL: Preserve the product's core appearance and functionality. Only adjust colors, lighting, and styling to match the website. Do NOT change the product itself.")
    prompt_parts.append("Make the product image feel native to the website's design aesthetic.")
    
    # Combine all parts
    prompt = " ".join(prompt_parts)
    
    return prompt


def create_batch_prompts(
    page_context: Dict[str, Any],
    products: List[Dict[str, Any]]
) -> List[str]:
    """
    Create prompts for multiple products
    
    Args:
        page_context: Page context
        products: List of product dicts with 'name' field
    
    Returns:
        List of prompts, one per product
    """
    return [
        create_editing_prompt(page_context, product.get("name", "Product"))
        for product in products
    ]

