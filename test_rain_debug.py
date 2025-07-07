#!/usr/bin/env python3
"""Debug script to trace rain comment selection issue"""

import logging
from datetime import datetime
from src.workflows.comment_generation_workflow import CommentGenerationWorkflow
from src.config.unified_config import UnifiedConfig

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Focus on key modules
logging.getLogger("src.nodes.comment_selector").setLevel(logging.DEBUG)
logging.getLogger("src.nodes.weather_forecast_node").setLevel(logging.INFO)

# Filter out verbose logs
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("src.repositories").setLevel(logging.WARNING)

def test_rain_comment_selection():
    """Test comment selection for Nagano with rain at 15:00"""
    print("Testing rain comment selection for 長野...")
    print("Expected: Rain at 15:00 (1mm) should trigger rain-related comment")
    print("-" * 60)
    
    # Initialize workflow
    config = UnifiedConfig()
    workflow = CommentGenerationWorkflow(config)
    
    # Test with Nagano
    location = "長野"
    
    print(f"\nGenerating comments for {location}...")
    try:
        result = workflow.run({
            "location_name": location,
            "llm_provider": "anthropic"
        })
        
        if result:
            print(f"\n=== Weather Data Summary ===")
            print(f"Base time weather: {result.weather_forecast.weather_description}")
            print(f"Base time precipitation: {result.weather_forecast.precipitation}mm")
            
            # Check metadata for all 4 time points
            if hasattr(result, 'generation_metadata'):
                period_forecasts = result.generation_metadata.get('period_forecasts', [])
                if period_forecasts:
                    print(f"\n=== All 4 Time Points ===")
                    for forecast in period_forecasts:
                        print(f"{forecast.datetime.strftime('%H:%M')} - {forecast.weather_description}, {forecast.precipitation}mm")
                        if forecast.precipitation > 0:
                            print(f"  ⚠️  RAIN DETECTED at {forecast.datetime.strftime('%H:%M')}")
            
            print(f"\n=== Selected Comments ===")
            print(f"天気コメント: {result.final_weather_comment}")
            print(f"アドバイス: {result.final_advice_comment}")
            
            # Check if rain-related comment was selected
            rain_keywords = ["雨", "傘", "濡れ", "降水", "にわか雨", "雷雨"]
            if any(keyword in result.final_weather_comment for keyword in rain_keywords):
                print("\n✅ SUCCESS: Rain-related comment was selected!")
            else:
                print("\n❌ FAILURE: No rain-related terms found in weather comment")
                print("This is the issue - rain at 15:00 is not being considered by LLM")
                
            if any(keyword in result.final_advice_comment for keyword in rain_keywords):
                print("✅ Rain-related advice was selected")
            else:
                print("⚠️  No rain-related advice selected")
                
        else:
            print("❌ No result returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rain_comment_selection()