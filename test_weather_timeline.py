#!/usr/bin/env python3
"""Test script to check weather timeline data flow"""

import json
import logging
from datetime import datetime
from src.workflows.comment_generation_workflow import run_comment_generation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_weather_timeline():
    """Test weather timeline data generation"""
    
    # Run generation for a single location
    location = "東京"
    llm_provider = "openai"
    
    logger.info(f"Testing generation for location: {location}")
    
    result = run_comment_generation(
        location_name=location,
        target_datetime=None,
        llm_provider=llm_provider
    )
    
    logger.info("Generation completed")
    logger.info(f"Success: {result.get('success')}")
    
    # Check generation_metadata
    generation_metadata = result.get('generation_metadata', {})
    logger.info(f"generation_metadata keys: {list(generation_metadata.keys())}")
    
    # Check period_forecasts
    period_forecasts = generation_metadata.get('period_forecasts')
    if period_forecasts:
        logger.info(f"period_forecasts found! Count: {len(period_forecasts)}")
        logger.info(f"period_forecasts type: {type(period_forecasts)}")
    else:
        logger.warning("period_forecasts NOT found in generation_metadata")
    
    # Check weather_timeline
    weather_timeline = generation_metadata.get('weather_timeline')
    if weather_timeline:
        logger.info("weather_timeline found!")
        logger.info(f"weather_timeline type: {type(weather_timeline)}")
        logger.info(f"weather_timeline keys: {list(weather_timeline.keys()) if isinstance(weather_timeline, dict) else 'Not a dict'}")
        
        if isinstance(weather_timeline, dict):
            future_forecasts = weather_timeline.get('future_forecasts', [])
            logger.info(f"future_forecasts count: {len(future_forecasts)}")
            if future_forecasts:
                logger.info(f"First forecast: {json.dumps(future_forecasts[0], ensure_ascii=False, indent=2)}")
    else:
        logger.warning("weather_timeline NOT found in generation_metadata")
    
    # Pretty print the entire result
    logger.info("Full generation_metadata:")
    logger.info(json.dumps(generation_metadata, ensure_ascii=False, indent=2, default=str))

if __name__ == "__main__":
    test_weather_timeline()