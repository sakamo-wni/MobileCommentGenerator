"""FastAPI server to bridge Streamlit backend and Nuxt frontend"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CommentGenerationRequest(BaseModel):
    location: str
    llm_provider: str = "openai"
    target_datetime: Optional[str] = None

class CommentGenerationResponse(BaseModel):
    success: bool
    location: str
    comment: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LocationResponse(BaseModel):
    locations: List[str]

class HistoryResponse(BaseModel):
    history: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok", version="1.0.0")

@app.get("/api/locations", response_model=LocationResponse)
def get_locations():
    """Get available locations"""
    try:
        locations = load_locations()
        logger.info(f"Loaded {len(locations)} locations")
        return LocationResponse(locations=locations)
    except Exception as e:
        logger.error(f"Failed to load locations: {e}")
        # Return fallback locations
        fallback_locations = ["東京", "神戸", "大阪", "名古屋", "福岡"]
        return LocationResponse(locations=fallback_locations)

@app.get("/api/history", response_model=HistoryResponse)
def get_history():
    """Get generation history"""
    try:
        history = load_history()
        logger.info(f"Loaded {len(history)} history items")
        return HistoryResponse(history=history)
    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        # Return empty history on error
        return HistoryResponse(history=[])

@app.post("/api/generate", response_model=CommentGenerationResponse)
def generate_comment(request: CommentGenerationRequest):
    """Generate weather comment for a location"""
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
        result = run_comment_generation(
            location_name=request.location,
            target_datetime=target_dt,
            llm_provider=request.llm_provider
        )
        
        logger.info(f"Generation result: success={result.get('success', False)}")
        
        # Extract response data
        success = result.get('success', False)
        comment = result.get('final_comment', '')
        error = result.get('error', None)
        
        # Extract metadata
        metadata = None
        if success and result.get('generation_metadata'):
            gen_metadata = result['generation_metadata']
            metadata = {
                'weather_forecast_time': gen_metadata.get('weather_forecast_time'),
                'temperature': gen_metadata.get('temperature'),
                'weather_condition': gen_metadata.get('weather_condition'),
                'wind_speed': gen_metadata.get('wind_speed'),
                'humidity': gen_metadata.get('humidity'),
                'weather_timeline': gen_metadata.get('weather_timeline'),
                'llm_provider': request.llm_provider
            }
            
            # Add selection metadata if available
            selection_meta = gen_metadata.get('selection_metadata', {})
            if selection_meta:
                metadata.update({
                    'selected_weather_comment': selection_meta.get('selected_weather_comment'),
                    'selected_advice_comment': selection_meta.get('selected_advice_comment'),
                })
        
        # Save to history if successful
        if success:
            save_to_history(result, request.location, request.llm_provider)
        
        return CommentGenerationResponse(
            success=success,
            location=request.location,
            comment=comment,
            error=error,
            metadata=metadata
        )
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        logger.error(f"Error generating comment for {request.location}: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return CommentGenerationResponse(
            success=False,
            location=request.location,
            comment=None,
            error=f"生成エラー: {error_msg}",
            metadata=None
        )

@app.get("/api/providers")
def get_llm_providers():
    """Get available LLM providers"""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI GPT", "description": "OpenAI's GPT models"},
            {"id": "gemini", "name": "Gemini", "description": "Google's Gemini AI"},
            {"id": "anthropic", "name": "Claude", "description": "Anthropic's Claude AI"}
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)