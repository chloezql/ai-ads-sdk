# AI Ads Core

An AI-powered context-aware ad network that matches ads to page content using semantic embeddings and generates context-aware product images.

## Features

- **Context-Aware Matching**: Uses Sentence-BERT embeddings to match products to page content
- **AI Image Editing**: Automatically styles product images to match page visual themes using fal.ai
- **Apify Integration**: Deep page content extraction via Apify actors
- **Local Product Storage**: Simple file-based product management
- **JavaScript SDK**: Easy integration for publishers

## Prerequisites

- **Python 3.11+** (recommended: use conda environment)
- **Node.js 18+** (for building SDK)
- **Apify Account** (for web content extraction)
- **fal.ai Account** (for AI image editing)
- **Supabase Account** (for image storage)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chloezql/ai-ads-sdk.git
cd ai-ads-core
```

### 2. Set Up Python Environment

```bash
# Create and activate conda environment (recommended)
conda create -n aiads python=3.11
conda activate aiads

# Or use virtualenv
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The first time you run the backend, `sentence-transformers` will download the model (~400MB). This may take a few minutes.

### 4. Build the SDK

```bash
cd apps/sdk
npm install
npm run build
cd ../..
```

This creates `apps/sdk/dist/ai-ads.js` which is served by the backend.

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_PORT=9000  # Backend port (default: 8000)

# Apify Configuration (Required for web crawling)
APIFY_API_TOKEN=your_apify_token_here
APIFY_ACTOR_ID=tropical_lease/web-context-extractor

# AI Image Editing (Required for image styling)
FAL_KEY=your_fal_ai_key_here
FAL_MODEL=fal-ai/nano-banana/edit

# Supabase Storage (Required for hosting product images)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

**Get API Keys:**
- **Apify**: https://console.apify.com/account/integrations
- **fal.ai**: https://fal.ai/dashboard/keys
- **Supabase**: https://app.supabase.com/project/_/settings/api

## Running Locally

### Start the Backend

```bash
# Option 1: Using the start script (if using conda)
./start-backend.sh

# Option 2: Manual start
cd apps/backend
python main.py
```

The backend will:
- Auto-load products from `assets/products/` on startup
- Start on `http://localhost:9000` (or port specified in `.env`)
- Serve the SDK at `http://localhost:9000/sdk/ai-ads.js`
- Serve product images at `http://localhost:9000/assets/products/{filename}`

**Verify it's running:**
```bash
curl http://localhost:9000/
```

Expected response:
```json
{
  "service": "AI Ads Core",
  "status": "running",
  "version": "1.0.0"
}
```

## Local Testing

### 1. Test API Endpoint Directly

```bash
curl -X POST http://localhost:9000/api/extract_context \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_id": "demo",
    "url": "https://ai-ads-demo-site.vercel.app/",
    "device_type": "desktop",
    "viewport_width": 1920,
    "viewport_height": 1080,
    "slot_id": "test-slot"
  }'
```

**Response includes:**
- Enriched page context (title, headings, keywords, topics, visual styles)
- Top 3 matched products with similarity scores
- AI-edited product images (styled to match page context)

### 2. Test SDK Integration

Create a test HTML file:

```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Ads Test</title>
</head>
<body>
    <h1>Test Page</h1>
    
    <!-- Ad slot -->
    <div id="aiads-slot-1" style="width: 100%; height: 300px; border: 1px solid #ccc;"></div>
    
    <!-- Load SDK -->
    <script src="http://localhost:9000/sdk/ai-ads.js"></script>
    <script>
        // Initialize SDK
        aiAds.init({
            apiBaseUrl: 'http://localhost:9000',
            publisherId: 'demo'
        });
    </script>
</body>
</html>
```

Open the HTML file in a browser. The SDK will:
1. Extract page context
2. Send request to backend
3. Render matched product ads in the slot

### 3. Test with Local Demo Site

If you have a local demo site running on `http://localhost:8000`:

1. Ensure backend is running on `http://localhost:9000`
2. Add SDK script to your demo site:
   ```html
   <script src="http://localhost:9000/sdk/ai-ads.js"></script>
   <script>
       aiAds.init({
           apiBaseUrl: 'http://localhost:9000',
           publisherId: 'demo'
       });
   </script>
   ```
3. Add ad slots:
   ```html
   <div id="aiads-slot-1" style="width: 100%; height: 300px;"></div>
   ```

## Product Storage

Products are stored locally in `assets/products/` as file pairs:

```
assets/products/
├── product1.jpg
├── product1_description.txt
├── headphones.png
└── headphones_description.txt
```

### Product Description Format

Each `[name]_description.txt` file should contain:

```
name: Product Name
price: 99.99
url: https://example.com/product

Product description text here. This will be used for semantic matching.
```

**Fields:**
- `name`: Product name (required)
- `price`: Product price (required, numeric)
- `url`: Landing page URL (required)
- Description text: Used for semantic matching (required)

Products are automatically loaded on backend startup and embeddings are generated for matching.

## API Endpoints

### POST `/api/extract_context`

Extract page context, match products, and return styled ads.

**Request:**
```json
{
  "publisher_id": "pub_001",
  "url": "https://example.com/article",
  "device_type": "desktop",
  "viewport_width": 1920,
  "viewport_height": 1080,
  "slot_id": "slot-1"
}
```

**Response:**
```json
{
  "success": true,
  "context": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "headings": ["Heading 1", "Heading 2"],
    "keywords": ["keyword1", "keyword2"],
    "topics": ["technology", "lifestyle"],
    "visual_styles": {
      "theme": "light",
      "backgroundColor": "rgb(255, 255, 255)",
      "textColor": "rgb(0, 0, 0)",
      "primaryColor": "rgb(102, 126, 234)",
      "fontFamily": "Arial",
      "fontSize": "16px"
    },
    "has_enriched": true
  },
  "matched_products": [
    {
      "id": "prod_123",
      "name": "Product Name",
      "description": "Product description",
      "price": 99.99,
      "currency": "USD",
      "image_url": "http://localhost:9000/assets/products/product.jpg",
      "edited_image_url": "https://fal.ai/...",
      "landing_url": "https://example.com/product",
      "match_score": 0.85
    }
  ],
  "timestamp": "2026-01-18T12:00:00.000000"
}
```

### GET `/sdk/ai-ads.js`

Serves the bundled SDK JavaScript file for browser integration.

### GET `/assets/products/{filename}`

Serves product images from local storage.

### GET `/`

Health check endpoint.

## Architecture

```
┌─────────────┐
│   Browser   │
│  (Publisher)│
└──────┬──────┘
       │
       │ 1. Load SDK
       │ 2. Extract context
       │ 3. Request ads
       ▼
┌─────────────────┐
│  Backend API    │
│  (FastAPI)      │
└────────┬────────┘
         │
         ├─► Apify Actor (web crawling)
         ├─► Sentence-BERT (embeddings)
         ├─► Product Matcher (cosine similarity)
         ├─► fal.ai (image editing)
         └─► Supabase (image storage)
```

## Storage Locations

- **Products**: `apps/backend/storage/products.json` (auto-generated)
- **Page Context Cache**: `apps/backend/storage/page_context.json` (24h TTL)
- **Product Images**: `assets/products/` (local files)
- **SDK Bundle**: `apps/sdk/dist/ai-ads.js` (build output)

## Troubleshooting

### Backend won't start

- Check Python version: `python --version` (should be 3.11+)
- Check `.env` file exists and has required keys
- Verify port is not in use: `lsof -i :9000`

### SDK not loading

- Build the SDK: `cd apps/sdk && npm run build`
- Check `apps/sdk/dist/ai-ads.js` exists
- Verify backend is serving SDK: `curl http://localhost:9000/sdk/ai-ads.js`

### No products matched

- Ensure products exist in `assets/products/` with description files
- Check backend logs for product loading messages
- Verify embeddings were generated (check `storage/products.json`)

### Apify errors

- Verify `APIFY_API_TOKEN` is set correctly
- Check Apify actor ID matches your actor
- Ensure target URLs are publicly accessible (not localhost)

### Image editing fails

- Verify `FAL_KEY` is set correctly
- Check `SUPABASE_URL` and `SUPABASE_KEY` are configured
- Ensure product images are accessible (uploaded to Supabase)

## Development

### Rebuild SDK After Changes

```bash
cd apps/sdk
npm run build
```

### View Backend Logs

Backend runs with auto-reload enabled. Check console output for:
- Product loading status
- Embedding generation
- API requests
- Image editing progress

## License

MIT
