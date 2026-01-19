"""
Auto-load products from flat file structure on startup
Products are stored as: [name].jpg and [name]_description.txt
"""
from pathlib import Path
from typing import List, Optional, Dict

from config import settings
from models.product import ProductCreate, ProductUpdate
from ingestion.products import product_pipeline


def parse_description_file(desc_file: Path) -> dict:
    """Parse [name]_description.txt file into product data"""
    
    content = desc_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Parse metadata from top of file
    metadata = {}
    description_lines = []
    in_description = False
    
    for line in lines:
        if not in_description and ':' in line and not line.startswith(' '):
            # Metadata line
            key, value = line.split(':', 1)
            metadata[key.strip().lower()] = value.strip()
        else:
            # Description content
            in_description = True
            if line.strip():  # Skip empty lines at start
                description_lines.append(line)
    
    # Extract required fields
    name = metadata.get('name', '')
    if not name:
        raise ValueError("Product 'name' is required in description file")
    
    url = metadata.get('url', '')
    if not url:
        raise ValueError("Product 'url' is required in description file")
    
    # Extract optional fields
    price = metadata.get('price', '')
    try:
        price = float(price) if price else None
    except ValueError:
        price = None
    
    # Full description is everything after metadata
    description = '\n'.join(description_lines).strip()
    if not description:
        description = name  # Fallback to name if no description
    
    return {
        'name': name,
        'description': description,
        'price': price,
        'currency': 'USD',
        'landing_url': url
    }


def find_product_pairs(products_dir: Path) -> Dict[str, Dict[str, Path]]:
    """
    Find matching image and description files
    Returns dict: {base_name: {'image': Path, 'description': Path}}
    """
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    products = {}
    
    # Find all image files
    for img_file in products_dir.iterdir():
        if not img_file.is_file():
            continue
        
        ext = img_file.suffix.lower()
        if ext not in image_extensions:
            continue
        
        # Get base name without extension
        base_name = img_file.stem
        
        # Look for corresponding description file
        desc_file = products_dir / f"{base_name}_description.txt"
        
        if desc_file.exists():
            products[base_name] = {
                'image': img_file,
                'description': desc_file
            }
    
    return products


def load_product_from_files(base_name: str, files: Dict[str, Path]) -> Optional[str]:
    """Load a product from image + description files, returns product ID if successful"""
    
    try:
        # Parse description
        product_data = parse_description_file(files['description'])
        
        # Set image path
        product_data['image_url'] = str(files['image'])
        
        # Create product
        product_create = ProductCreate(**product_data)
        product = product_pipeline.ingest_product(product_create)
        
        print(f"[AutoLoader] Loaded: {product.name} ({base_name})")
        return product.id
        
    except Exception as e:
        print(f"[AutoLoader] Error loading {base_name}: {e}")
        return None


def auto_load_products():
    """
    Auto-load products from flat file structure
    Called on startup if products.json is empty
    Generates embeddings for all products
    """
    from storage.products import product_storage
    from embeddings.generator import embedding_generator
    
    # Check if products already exist
    existing = product_storage.get_all(active_only=False)
    if existing:
        print(f"[AutoLoader] {len(existing)} products already loaded")
        
        # Check if embeddings need to be generated
        needs_embedding = [p for p in existing if not p.product_embedding]
        if needs_embedding:
            print(f"[AutoLoader] Generating embeddings for {len(needs_embedding)} products...")
            for product in needs_embedding:
                try:
                    product_data = product.model_dump()
                    embedding = embedding_generator.generate_product_embedding(product_data)
                    # Update product with embedding using ProductUpdate
                    update_data = ProductUpdate(product_embedding=embedding)
                    product_storage.update(product.id, update_data)
                    print(f"[AutoLoader] Generated embedding for: {product.name}")
                except Exception as e:
                    print(f"[AutoLoader] Error generating embedding for {product.name}: {e}")
            
            print(f"[AutoLoader] Embeddings generated for {len(needs_embedding)} products")
        else:
            print("[AutoLoader] All products have embeddings")
        
        return
    
    print("[AutoLoader] No products found, scanning files...")
    
    # Scan for product files
    products_dir = settings.PRODUCTS_DIR
    if not products_dir.exists():
        print("[AutoLoader] Products directory not found")
        return
    
    product_pairs = find_product_pairs(products_dir)
    
    if not product_pairs:
        print("[AutoLoader] No product files found in assets/products/")
        print("[AutoLoader] Expected: [name].jpg and [name]_description.txt")
        return
    
    print(f"[AutoLoader] Found {len(product_pairs)} product pairs")
    
    # Load each product
    loaded = 0
    for base_name, files in product_pairs.items():
        product_id = load_product_from_files(base_name, files)
        if product_id:
            # Generate embedding for the product
            try:
                product = product_storage.get(product_id)
                if product:
                    product_data = product.model_dump()
                    embedding = embedding_generator.generate_product_embedding(product_data)
                    # Update product with embedding using ProductUpdate
                    update_data = ProductUpdate(product_embedding=embedding)
                    product_storage.update(product_id, update_data)
                    print(f"[AutoLoader] Generated embedding for: {product.name}")
            except Exception as e:
                print(f"[AutoLoader] Error generating embedding: {e}")
            
            loaded += 1
    
    print(f"[AutoLoader] Successfully loaded {loaded}/{len(product_pairs)} products with embeddings")
