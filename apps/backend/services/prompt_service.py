"""
Prompt generation service for AI image editing
Creates prompts based on page context (topics, keywords, visual_styles) to match web styling
"""
from typing import Dict, Any, List, Optional


def create_editing_prompt(
    page_context: Dict[str, Any],
    product_name: str,
    persona: Optional[Dict[str, Any]] = None
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
    
    # Add persona context FIRST - this should significantly influence the image
    if persona:
        time_of_day = persona.get('time_of_day')
        location = persona.get('location')
        weather = persona.get('weather')
        temperature = persona.get('temperature')
        os = persona.get('os')
        device_type = persona.get('device_type')
        
        persona_details = []
        if time_of_day:
            persona_details.append(f"Time of day: {time_of_day}")
        if location:
            persona_details.append(f"Location: {location}")
        if weather:
            persona_details.append(f"Weather: {weather}")
        if temperature:
            persona_details.append(f"Temperature: {temperature}")
        if os:
            persona_details.append(f"OS: {os}")
        if device_type:
            persona_details.append(f"Device: {device_type}")
        
        if persona_details:
            persona_context = ", ".join(persona_details)
            prompt_parts.append(f"PERSONALIZATION - User Environment: {persona_context}. Adjust the image lighting, atmosphere, color temperature, and mood to authentically reflect this specific user's environment. The time of day should influence lighting (brightness, shadows, natural vs artificial light). The weather should affect the atmosphere and color palette (temperature, saturation, environmental elements). The temperature should influence color temperature and overall mood (warm tones for hot, cool tones for cold). The location should inform regional context and settings. The device type may affect viewing optimization. Create a personalized visual experience that is distinctly different from other users viewing the same product.")
    
    # Add topics and environment generation
    if topics:
        topics_str = ", ".join(topics)
        prompt_parts.append(f"Match the page topics: {topics_str}.")
        prompt_parts.append(f"ENVIRONMENT GENERATION - Create a realistic, contextual environment/scene that relates to these topics ({topics_str}). Place the {product_name} naturally within this environment. For example: if the page is about home/office, show the product in a desk, table, or room setting; if about outdoor/camping, show it in a natural outdoor setting; if about technology, show it in a modern tech environment. The environment should enhance the product presentation and feel authentic to the page's theme. Include relevant background elements, surfaces, and contextual objects that make sense for the topics.")
    
    # Add visual styles
    if visual_styles:
        style_parts = []
        
        if visual_styles.get("theme"):
            style_parts.append(f"theme: {visual_styles['theme']}")
        
        if visual_styles.get("backgroundColor"):
            style_parts.append(f"background color: {visual_styles['backgroundColor']}")
        
        if visual_styles.get("primaryColor"):
            style_parts.append(f"primary color: {visual_styles['primaryColor']}")
        
        if visual_styles.get("fontFamily"):
            style_parts.append(f"font style: {visual_styles['fontFamily']}")
        
        if style_parts:
            prompt_parts.append(f"Apply visual styles: {', '.join(style_parts)}.")
        
        # Highlight accent colors separately and prominently
        if visual_styles.get("accentColors"):
            accent_colors = ", ".join(visual_styles["accentColors"][:5])  # Include up to 5 accent colors
            prompt_parts.append(f"CRITICAL - Accent Colors: Use these accent colors prominently throughout the image: {accent_colors}. These colors should be the primary color palette for styling elements, highlights, and visual accents. Make these accent colors highly visible and integrated into the image's color scheme.")
    
    # Add relevant keywords (top 10 most relevant)
    if keywords:
        relevant_keywords = keywords[:10]
        keywords_str = ", ".join(relevant_keywords)
        prompt_parts.append(f"Incorporate these style elements: {keywords_str}.")
    
    # Combine regular instructions
    prompt = " ".join(prompt_parts)
    
    # Add critical rules section - highlighted and separated
    critical_rules = []
    critical_rules.append("CRITICAL RULE 1: Do NOT add any text, labels, captions, words, or written content to the image. The image must contain only visual elements - no text whatsoever.")
    critical_rules.append("CRITICAL RULE 2: Remove ALL white or plain backgrounds. The product must be placed in a complete, realistic environment with appropriate background, surfaces, and contextual elements that match the website's atmosphere and visual style. Never show the product floating on a white or empty background. The environment should feel cohesive with the website's design aesthetic.")
    critical_rules.append("CRITICAL RULE 3: Make the product image feel native to the website's design aesthetic while maintaining the product's original form and structure. The environment should complement the product, not distract from it.")

    # Append critical rules with clear separation
    prompt += " " + " ".join(critical_rules)
    
    return prompt


def create_batch_prompts(
    page_context: Dict[str, Any],
    products: List[Dict[str, Any]],
    persona: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Create prompts for multiple products
    
    Args:
        page_context: Page context
        products: List of product dicts with 'name' field
        persona: Optional persona information for personalization
    
    Returns:
        List of prompts, one per product
    """
    return [
        create_editing_prompt(page_context, product.get("name", "Product"), persona)
        for product in products
    ]

