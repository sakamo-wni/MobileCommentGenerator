#!/usr/bin/env python3
"""Test script to debug Nagano rain issue - rain at 15:00 not being considered"""

import logging
from datetime import datetime
from src.workflows.unified_comment_generation_workflow import UnifiedCommentGenerationWorkflow
from src.config.unified_config import UnifiedConfig

# Set up detailed logging for comment selection
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("src.nodes.comment_selector.llm_selector").setLevel(logging.INFO)
logging.getLogger("src.nodes.comment_selector.utils").setLevel(logging.INFO)
logging.getLogger("src.nodes.weather_forecast_node").setLevel(logging.INFO)

def test_nagano_rain():
    """Test comment selection for Nagano - should detect rain at 15:00"""
    
    print("="*80)
    print("Testing Nagano (長野) - Rain at 15:00 issue")
    print("Expected: Should select rain-related comment because of 1mm rain at 15:00")
    print("="*80)
    
    # Initialize workflow
    config = UnifiedConfig()
    workflow = UnifiedCommentGenerationWorkflow(config)
    
    location = "長野"
    
    try:
        result = workflow.invoke({
            "location_name": location,
            "llm_provider": "anthropic"
        })
        
        if result and result.get('generation_result'):
            gen_result = result['generation_result']
            weather = gen_result.weather_forecast
            
            print(f"\n[Base Time Weather - 09:00]")
            print(f"Weather: {weather.weather_description}")
            print(f"Precipitation: {weather.precipitation}mm")
            print(f"Temperature: {weather.temperature}°C")
            
            # Try to access the state metadata to see all 4 time points
            if 'state' in result:
                state = result['state']
                if hasattr(state, 'generation_metadata'):
                    period_forecasts = state.generation_metadata.get('period_forecasts', [])
                    if period_forecasts:
                        print(f"\n[All 4 Time Points]")
                        has_rain = False
                        for forecast in period_forecasts:
                            time_str = forecast.datetime.strftime('%H:%M')
                            precip = forecast.precipitation
                            print(f"{time_str} - {forecast.weather_description}, {precip}mm", end="")
                            if precip > 0:
                                print(" ⚠️  RAIN!")
                                has_rain = True
                            else:
                                print()
                        
                        if has_rain:
                            print("\n⚠️  Rain detected in timeline - should prioritize rain comments!")
            
            print(f"\n[Selected Comments]")
            print(f"Weather comment: {gen_result.final_weather_comment}")
            print(f"Advice comment: {gen_result.final_advice_comment}")
            
            # Check for rain-related terms
            rain_terms = ["雨", "傘", "雷", "にわか雨", "降水", "濡れ"]
            weather_has_rain = any(term in gen_result.final_weather_comment for term in rain_terms)
            advice_has_rain = any(term in gen_result.final_advice_comment for term in rain_terms)
            
            print(f"\n[Analysis]")
            if weather_has_rain:
                print("✅ Weather comment mentions rain - GOOD!")
            else:
                print("❌ Weather comment does NOT mention rain - THIS IS THE BUG!")
                print("   The LLM is not being told about rain at 15:00")
                
            if advice_has_rain:
                print("✅ Advice mentions rain/umbrella")
            else:
                print("⚠️  Advice does not mention rain/umbrella")
            
            print("\n[Root Cause]")
            print("The issue is in src/nodes/comment_selector/llm_selector.py")
            print("The _format_weather_context method only uses weather_data.precipitation")
            print("It doesn't check the period_forecasts for rain at other times!")
                    
        else:
            print("❌ No result returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nagano_rain()