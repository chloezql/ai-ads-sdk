"""
AI Ads Core - Main Application Entry Point
Web content extraction and product storage
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from pathlib import Path

from config import settings
from api import ad_request
from ingestion.auto_loader import auto_load_products

# Initialize FastAPI application
app = FastAPI(
    title="AI Ads Core",
    description="Web content extraction and product storage",
    version="1.0.0"
)

# Configure CORS for SDK integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify publisher domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(ad_request.router, prefix="/api", tags=["Context Extraction"])


@app.on_event("startup")
async def startup_event():
    """Auto-load products on startup"""
    auto_load_products()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI Ads Core",
        "status": "running",
        "version": "1.0.0",
        "description": "Web content extraction"
    }

@app.get("/sdk/ai-ads.js")
async def serve_sdk():
    """Serve the SDK JavaScript file"""
    sdk_path = settings.BASE_DIR / "apps" / "sdk" / "dist" / "ai-ads.js"
    
    if not sdk_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "SDK file not found. Please build the SDK first."}
        )
    
    return FileResponse(
        path=sdk_path,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        }
    )


@app.get("/assets/products/{filename}")
async def serve_product_image(filename: str):
    """Serve product images"""
    import os
    
    # Security: prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid filename"}
        )
    
    image_path = settings.PRODUCTS_DIR / filename
    
    if not image_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Image not found"}
        )
    
    # Determine media type from extension
    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_types.get(ext, 'image/jpeg')
    
    return FileResponse(
        path=image_path,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
        }
    )


def main():
    """Run the application"""
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG
    )


if __name__ == "__main__":
    main()

