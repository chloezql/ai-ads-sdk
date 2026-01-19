# AI Ads Core

Web content extraction with Apify and local product storage.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure Apify token
cp env.example .env
# Edit .env and add APIFY_API_TOKEN

# Start backend (auto-loads products)
cd apps/backend
python main.py
```

## Product Storage

Place products directly in `assets/products/` as file pairs:

```
assets/products/
├── product1.jpg
├── product1_description.txt
├── headphones.png
└── headphones_description.txt
```

**[name]_description.txt** format:
```
name: Product Name
price: 99.99
url: https://example.com/product

Product description text here.
```

Products auto-load on startup.

## API

**POST /api/extract_context** - Extract page context

Crawls URL with Apify, waits for results, returns enriched context.

Request:
```json
{
  "publisher_id": "pub_001",
  "url": "https://example.com/article",
  "title": "Article Title",
  "headings": ["Heading 1"],
  "visible_text": "Page content...",
  "device_type": "desktop",
  "slot_id": "slot-1"
}
```

Response:
```json
{
  "success": true,
  "context": {
    "url": "...",
    "title": "...",
    "keywords": ["keyword1", "keyword2"],
    "topics": ["topic1"],
    "has_enriched": true
  }
}
```

**GET /health** - Health check

## Storage

- Products: `data/products.json`
- Processed images: `assets/products/processed/`
- Page cache: `data/page_context.json` (24h TTL)

## Configuration

`.env` file:
- `APIFY_API_TOKEN` - Required for page crawling
- `API_PORT` - Default 8000
