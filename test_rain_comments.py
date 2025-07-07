#!/usr/bin/env python3
"""Test script to verify rain comment selection"""

import logging
from datetime import datetime
from src.workflows.comment_generation_workflow import CommentGenerationWorkflow
from src.config.unified_config import UnifiedConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Filter out verbose logs
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("src.repositories").setLevel(logging.WARNING)

def test_rain_comment_selection():
    """Test comment selection for a rainy location"""
    print("Testing rain comment selection...")
    
    # Initialize workflow
    config = UnifiedConfig()
    workflow = CommentGenerationWorkflow(config)
    
    # Test with a location that has rain
    location = "与那国島"  # This location has rain data
    
    print(f"\nGenerating comments for {location} (rainy weather)...")
    try:
        result = workflow.run({
            "location_name": location,
            "llm_provider": "anthropic"
        })
        
        if result:
            print(f"\n✓ Weather: {result.weather_forecast.weather_description}")
            print(f"✓ Precipitation: {result.weather_forecast.precipitation}mm")
            print(f"\n天気コメント: {result.final_weather_comment}")
            print(f"アドバイス: {result.final_advice_comment}")
            
            # Check if rain-related comment was selected
            if "雨" in result.final_weather_comment or "傘" in result.final_weather_comment:
                print("\n✅ SUCCESS: Rain-related comment was selected!")
            else:
                print("\n⚠️  WARNING: No rain-related terms found in comment")
        else:
            print("❌ No result returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rain_comment_selection()