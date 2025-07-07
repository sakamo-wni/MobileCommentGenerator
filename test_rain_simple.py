#!/usr/bin/env python3
"""Simple test to verify rain comment selection"""

import logging
from datetime import datetime
from src.workflows.unified_comment_generation_workflow import UnifiedCommentGenerationWorkflow
from src.config.unified_config import UnifiedConfig

# Set up minimal logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.nodes.comment_selector").setLevel(logging.INFO)

def test_rain_locations():
    """Test comment selection for rainy locations"""
    
    # Initialize workflow
    config = UnifiedConfig()
    workflow = UnifiedCommentGenerationWorkflow(config)
    
    # Test locations with rain
    rainy_locations = ["与那国島", "久米島", "むつ"]
    
    for location in rainy_locations:
        print(f"\n{'='*60}")
        print(f"Testing: {location}")
        print('='*60)
        
        try:
            result = workflow.invoke({
                "location_name": location,
                "llm_provider": "anthropic"
            })
            
            if result and result.get('generation_result'):
                gen_result = result['generation_result']
                weather = gen_result.weather_forecast
                
                print(f"Weather: {weather.weather_description}")
                print(f"Precipitation: {weather.precipitation}mm")
                print(f"Weather comment: {gen_result.final_weather_comment}")
                
                # Check for rain-related terms
                rain_terms = ["雨", "傘", "雷", "にわか雨", "強雨"]
                found_rain_term = any(term in gen_result.final_weather_comment for term in rain_terms)
                
                if weather.precipitation > 0 and found_rain_term:
                    print("✅ SUCCESS: Rain comment selected for rainy weather!")
                elif weather.precipitation > 0 and not found_rain_term:
                    print("❌ FAIL: No rain comment for rainy weather")
                elif weather.precipitation == 0 and not found_rain_term:
                    print("✓ OK: No rain comment for non-rainy weather")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_rain_locations()