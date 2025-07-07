#!/usr/bin/env python3
"""Test script to verify rain comment selection"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.workflows.comment_generation_workflow import run_comment_generation

# Set up logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.nodes.comment_selector.llm_selector").setLevel(logging.INFO)
logging.getLogger("src.nodes.comment_selector.validation").setLevel(logging.INFO)

def test_rain_comment():
    """Test rain comment selection"""
    
    print("Testing rain comment selection after LLM bias fix...")
    
    # Test with a location that has rain
    location = "与那国島"
    
    print(f"\nGenerating comment for {location}...")
    
    try:
        result = run_comment_generation(
            location_name=location,
            target_datetime=datetime.now(),
            llm_provider="anthropic"
        )
        
        if result:
            print(f"\n✓ Weather: {result.weather_forecast.weather_description}")
            print(f"✓ Precipitation: {result.weather_forecast.precipitation}mm")
            print(f"\n天気コメント: {result.final_weather_comment}")
            
            # Check for rain-related terms
            rain_terms = ["雨", "傘", "雷", "にわか雨", "強雨"]
            if any(term in result.final_weather_comment for term in rain_terms):
                print("\n✅ SUCCESS: Rain-related comment was selected!")
                return True
            else:
                print("\n❌ FAIL: No rain-related comment selected")
                return False
        else:
            print("❌ No result returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rain_comment()
    sys.exit(0 if success else 1)