"""FastAPI server to bridge Streamlit backend and Nuxt frontend"""

import os
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config.app_config import get_config
from src.utils.error_handler import ErrorHandler, AppError
from src.types import (
    HistoryItem,
    LLMProvider,
    GenerationMetadata
)
from src.types.api_response import (
    ApiResponse,
    ApiError,
    CommentGenerationData,
    LocationData,
    HistoryData,
    ProvidersData,
    ProviderData
)

# Setup logging
config = get_config()
logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

try:
    from src.workflows.comment_generation_workflow import run_comment_generation
    from src.ui.streamlit_utils import load_locations, load_history, save_to_history
    logger.info("Successfully imported backend modules")
except ImportError as e:
    logger.error(f"Failed to import backend modules: {e}")
    # Fallback imports for testing
    def run_comment_generation(*args, **kwargs):
        return {"success": False, "error": "Backend not available"}
    def load_locations():
        return ["東京", "神戸", "大阪", "名古屋", "福岡"]
    def load_history():
        return []
    def save_to_history(*args, **kwargs):
        pass

app = FastAPI(title="Mobile Comment Generator API", version="1.0.0")

# CORS設定
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174").split(",")

# 本番環境ではより厳格なCORS設定を使用
if config.env == "production":
    CORS_ORIGINS = os.getenv("CORS_ORIGINS_PROD", "https://your-production-domain.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # セキュリティ強化: 認証情報を無効化
    allow_methods=["GET", "POST"],  # セキュリティ強化: 必要なメソッドのみ許可
    allow_headers=["Content-Type", "Authorization"],  # セキュリティ強化: 必要なヘッダーのみ許可
)

# Pydantic models
class CommentGenerationRequest(BaseModel):
    location: str
    llm_provider: LLMProvider = "gemini"
    target_datetime: Optional[str] = None
    exclude_previous: Optional[bool] = False

class CommentGenerationResponse(BaseModel):
    success: bool
    location: str
    comment: Optional[str] = None
    advice_comment: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LocationResponse(BaseModel):
    locations: List[str]

class HistoryResponse(BaseModel):
    history: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    status: str
    version: str

class BulkGenerationRequest(BaseModel):
    locations: List[str]
    llm_provider: LLMProvider = "gemini"

class BulkGenerationResponse(BaseModel):
    results: List[CommentGenerationResponse]
    total: int
    success_count: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok", version="1.0.0")

@app.get("/api/locations", response_model=LocationResponse)
async def get_locations():
    """Get available locations"""
    try:
        locations = await asyncio.to_thread(load_locations)
        logger.info(f"Loaded {len(locations)} locations")
        return LocationResponse(locations=locations)
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        logger.error(f"Failed to load locations: {error_response.error_message}")
        # Return fallback locations
        fallback_locations = ["東京", "神戸", "大阪", "名古屋", "福岡"]
        return LocationResponse(locations=fallback_locations)

@app.get("/api/history", response_model=HistoryResponse)
async def get_history():
    """Get generation history"""
    try:
        history = await asyncio.to_thread(load_history)
        logger.info(f"Loaded {len(history)} history items")
        return HistoryResponse(history=history)
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        logger.error(f"Failed to load history: {error_response.error_message}")
        # Return empty history on error
        return HistoryResponse(history=[])

@app.post("/api/generate", response_model=CommentGenerationResponse)
async def generate_comment(request: CommentGenerationRequest):
    """Generate weather comment for a location"""
    logger.info(f"Received request: {request}")
    logger.info(f"Generating comment for location: {request.location}, provider: {request.llm_provider}")
    
    try:
        # Validate request
        if not request.location or request.location.strip() == "":
            return CommentGenerationResponse(
                success=False,
                location="不明",
                error="地点が選択されていません"
            )
        
        # Use current time as the base for forecast calculations
        # The workflow will automatically calculate the forecast window based on config
        target_dt = datetime.now()
        
        logger.info(f"Target datetime: {target_dt} (current time for forecast calculation)")
        
        # Run comment generation
        result = await asyncio.to_thread(
            run_comment_generation,
            location_name=request.location,
            target_datetime=target_dt,
            llm_provider=request.llm_provider,
            exclude_previous=request.exclude_previous
        )
        
        logger.info(f"Generation result: success={result.get('success', False)}")
        
        # Extract response data
        success = result.get('success', False)
        comment = result.get('final_comment', '')
        error = result.get('error', None)
        advice_comment = result.get('generation_metadata', {}).get('selection_metadata', {}).get('selected_advice_comment', '')
        
        # Extract metadata - pass through the entire generation_metadata
        metadata = None
        if success and result.get('generation_metadata'):
            # Pass through the entire metadata object instead of reconstructing it
            metadata = result['generation_metadata']
        
        # Save to history if successful
        if success:
            await asyncio.to_thread(save_to_history, result, request.location, request.llm_provider)
        
        return CommentGenerationResponse(
            success=success,
            location=request.location,
            comment=comment,
            advice_comment=advice_comment,
            error=error,
            metadata=metadata
        )
        
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        logger.error(f"Error generating comment for {request.location}: {error_response.error_message}")
        
        return CommentGenerationResponse(
            success=False,
            location=request.location,
            comment=None,
            error=error_response.user_message,
            metadata=None
        )

@app.get("/api/providers")
async def get_llm_providers():
    """Get available LLM providers"""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI GPT", "description": "OpenAI's GPT models"},
            {"id": "gemini", "name": "Gemini", "description": "Google's Gemini AI"},
            {"id": "anthropic", "name": "Claude", "description": "Anthropic's Claude AI"}
        ]
    }

@app.post("/api/generate/bulk", response_model=BulkGenerationResponse)
async def generate_comments_bulk(request: BulkGenerationRequest):
    """Generate weather comments for multiple locations"""
    try:
        # Import here to avoid circular dependency
        from app_controller import CommentGenerationController
        
        # Initialize controller
        controller = CommentGenerationController()
        
        # Process locations in parallel (3 at a time)
        results = []
        BATCH_SIZE = 3
        
        for i in range(0, len(request.locations), BATCH_SIZE):
            batch = request.locations[i:i + BATCH_SIZE]
            
            # Run batch generation in thread pool
            batch_results = await asyncio.to_thread(
                controller.generate_comments_batch,
                locations=batch,
                llm_provider=request.llm_provider,
                max_workers=3
            )
            
            # Convert results to API response format
            for location, generation_result in zip(batch, batch_results):
                if generation_result.success:
                    result = CommentGenerationResponse(
                        success=True,
                        location=location,
                        comment=generation_result.data.comment,
                        advice_comment=generation_result.data.advice_comment,
                        metadata=generation_result.data.metadata.dict() if generation_result.data.metadata else None
                    )
                else:
                    result = CommentGenerationResponse(
                        success=False,
                        location=location,
                        comment=None,
                        advice_comment=None,
                        error=generation_result.error_message,
                        metadata=None
                    )
                results.append(result)
        
        # Calculate success count
        success_count = sum(1 for r in results if r.success)
        
        return BulkGenerationResponse(
            results=results,
            total=len(results),
            success_count=success_count
        )
        
    except Exception as e:
        logger.error(f"Bulk generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)