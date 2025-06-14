#!/usr/bin/env python
"""Comprehensive weather data flow testing with detailed validation"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set AWS profile if needed
os.environ.setdefault("AWS_PROFILE", "dit-training")

from src.workflows.comment_generation_workflow import run_comment_generation
from src.apis.wxtech_client import WxTechAPIClient
from src.config.weather_config import get_config
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.utils.common_utils import get_season_from_date, get_time_period


class WeatherFlowTester:
    """Test weather data flow through the entire comment generation system"""
    
    def __init__(self):
        self.config = get_config()
        self.validator = WeatherCommentValidator()
        self.test_results = []
        self.weather_client = None
        
    def test_location_weather_flow(self, 
                                 location_name: str, 
                                 llm_provider: str = "openai") -> Dict:
        """Test weather flow for a specific location"""
        print(f"\n{'='*60}")
        print(f"Testing Weather Flow: {location_name}")
        print("="*60)
        
        result = {
            'location': location_name,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'weather_api': {},
            'workflow': {},
            'validation': {},
            'data_consistency': {},
            'errors': []
        }
        
        try:
            # Step 1: Direct weather API test
            print("\n1. Testing direct weather API access...")
            weather_data = self._test_weather_api(location_name)
            result['weather_api'] = weather_data
            
            if not weather_data['success']:
                result['errors'].append("Weather API test failed")
                return result
                
            # Step 2: Run workflow
            print("\n2. Running comment generation workflow...")
            workflow_start = time.time()
            
            workflow_result = run_comment_generation(
                location_name=location_name,
                llm_provider=llm_provider
            )
            
            workflow_time = time.time() - workflow_start
            
            if workflow_result.get("success"):
                print(f"✅ Workflow successful! (took {workflow_time:.2f}s)")
                result['success'] = True
                
                # Extract workflow data
                final_comment = workflow_result.get('final_comment', '')
                metadata = workflow_result.get('generation_metadata', {})
                
                result['workflow'] = {
                    'success': True,
                    'execution_time': workflow_time,
                    'final_comment': final_comment,
                    'llm_provider': llm_provider
                }
                
                # Step 3: Verify data consistency
                print("\n3. Verifying data consistency...")
                consistency = self._verify_data_consistency(
                    weather_data['data'],
                    metadata
                )
                result['data_consistency'] = consistency
                
                # Step 4: Validate generated comment
                print("\n4. Validating generated comment...")
                validation = self._validate_comment(
                    final_comment,
                    metadata.get('weather_condition', ''),
                    metadata.get('temperature')
                )
                result['validation'] = validation
                
                # Step 5: Analyze comment selection
                print("\n5. Analyzing comment selection...")
                selection_analysis = self._analyze_selection(metadata)
                result['workflow']['selection_analysis'] = selection_analysis
                
                # Display results
                self._display_results(result)
                
            else:
                error_msg = workflow_result.get('error', 'Unknown workflow error')
                print(f"❌ Workflow failed: {error_msg}")
                result['errors'].append(f"Workflow: {error_msg}")
                result['workflow'] = {
                    'success': False,
                    'error': error_msg,
                    'execution_time': workflow_time
                }
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            
        return result
    
    def _test_weather_api(self, location_name: str) -> Dict:
        """Test direct weather API access"""
        result = {
            'success': False,
            'data': {},
            'errors': []
        }
        
        try:
            # Get location coordinates
            from src.data.location_manager import LocationManager
            loc_manager = LocationManager()
            location = loc_manager.get_location(location_name)
            
            if not location:
                result['errors'].append(f"Location not found: {location_name}")
                return result
                
            print(f"  Location: {location.name} ({location.latitude}, {location.longitude})")
            
            # Get weather data
            if not self.weather_client:
                api_key = self.config.weather.wxtech_api_key
                if not api_key:
                    result['errors'].append("WXTECH_API_KEY not configured")
                    return result
                self.weather_client = WxTechAPIClient(api_key)
                
            forecast_collection = self.weather_client.get_forecast(
                location.latitude,
                location.longitude
            )
            
            if forecast_collection and forecast_collection.forecasts:
                current = forecast_collection.get_nearest_forecast(datetime.now())
                
                if current:
                    print(f"  ✅ Weather data retrieved successfully")
                    print(f"    Weather: {current.weather_description}")
                    print(f"    Temperature: {current.temperature}°C")
                    print(f"    Humidity: {current.humidity}%")
                    
                    result['success'] = True
                    result['data'] = {
                        'location_name': location_name,
                        'coordinates': (location.latitude, location.longitude),
                        'weather_condition': current.weather_description,
                        'temperature': current.temperature,
                        'humidity': current.humidity,
                        'wind_speed': current.wind_speed,
                        'forecast_count': len(forecast_collection.forecasts)
                    }
                else:
                    result['errors'].append("No current weather data")
            else:
                result['errors'].append("No forecast data returned")
                
        except Exception as e:
            result['errors'].append(f"API error: {str(e)}")
            
        return result
    
    def _verify_data_consistency(self, api_data: Dict, workflow_metadata: Dict) -> Dict:
        """Verify consistency between API data and workflow data"""
        consistency = {
            'is_consistent': True,
            'mismatches': []
        }
        
        # Check temperature
        api_temp = api_data.get('temperature')
        workflow_temp = workflow_metadata.get('temperature')
        
        if api_temp is not None and workflow_temp is not None:
            if abs(api_temp - workflow_temp) > 1.0:  # Allow 1 degree difference
                consistency['is_consistent'] = False
                consistency['mismatches'].append(
                    f"Temperature mismatch: API={api_temp}°C, Workflow={workflow_temp}°C"
                )
                
        # Check weather condition
        api_weather = api_data.get('weather_condition', '').lower()
        workflow_weather = workflow_metadata.get('weather_condition', '').lower()
        
        if api_weather and workflow_weather:
            # Basic similarity check
            if not any(word in workflow_weather for word in api_weather.split()):
                consistency['is_consistent'] = False
                consistency['mismatches'].append(
                    f"Weather mismatch: API='{api_weather}', Workflow='{workflow_weather}'"
                )
                
        # Check coordinates
        api_coords = api_data.get('coordinates')
        workflow_coords = workflow_metadata.get('location_coordinates')
        
        if api_coords and workflow_coords:
            lat_diff = abs(api_coords[0] - workflow_coords['lat'])
            lon_diff = abs(api_coords[1] - workflow_coords['lon'])
            
            if lat_diff > 0.01 or lon_diff > 0.01:
                consistency['is_consistent'] = False
                consistency['mismatches'].append(
                    f"Coordinate mismatch: API={api_coords}, Workflow=({workflow_coords['lat']}, {workflow_coords['lon']})"
                )
                
        if consistency['is_consistent']:
            print("  ✅ Data consistency verified")
        else:
            print("  ❌ Data inconsistencies found:")
            for mismatch in consistency['mismatches']:
                print(f"    - {mismatch}")
                
        return consistency
    
    def _validate_comment(self, comment: str, weather: str, temperature: Optional[float]) -> Dict:
        """Validate generated comment"""
        validation_result = self.validator.validate_comment(comment, weather, temperature)
        
        if validation_result['is_valid']:
            print("  ✅ Comment validation passed")
        else:
            print("  ❌ Comment validation failed:")
            for issue in validation_result.get('issues', []):
                print(f"    - {issue}")
                
        # Additional checks
        current_season = get_season_from_date(datetime.now())
        current_period = get_time_period(datetime.now())
        
        validation_result['context'] = {
            'season': current_season,
            'time_period': current_period,
            'comment_length': len(comment),
            'has_weather_mention': any(w in comment for w in ['晴', '雨', '曇', '雪', '風']),
            'has_temperature_mention': any(w in comment for w in ['暑', '寒', '涼', '暖', '度'])
        }
        
        return validation_result
    
    def _analyze_selection(self, metadata: Dict) -> Dict:
        """Analyze comment selection process"""
        selection_metadata = metadata.get('selection_metadata', {})
        selected_comments = metadata.get('selected_past_comments', [])
        
        analysis = {
            'selection_method': selection_metadata.get('selection_method', 'unknown'),
            'total_candidates': (
                selection_metadata.get('weather_comments_count', 0) + 
                selection_metadata.get('advice_comments_count', 0)
            ),
            'selected_count': len(selected_comments),
            'comment_types': {}
        }
        
        # Count comment types
        for comment in selected_comments:
            if comment:
                ctype = comment.get('type', 'unknown')
                analysis['comment_types'][ctype] = analysis['comment_types'].get(ctype, 0) + 1
                
        print(f"  Selection method: {analysis['selection_method']}")
        print(f"  Candidates evaluated: {analysis['total_candidates']}")
        print(f"  Comments selected: {analysis['selected_count']}")
        
        return analysis
    
    def _display_results(self, result: Dict):
        """Display test results summary"""
        print("\n" + "-"*40)
        print("SUMMARY")
        print("-"*40)
        
        # Weather data
        weather_data = result['weather_api']['data']
        print(f"Weather: {weather_data.get('weather_condition')}")
        print(f"Temperature: {weather_data.get('temperature')}°C")
        
        # Final comment (truncated)
        comment = result['workflow'].get('final_comment', '')
        print(f"\nGenerated comment:")
        print(f"{comment[:200]}..." if len(comment) > 200 else comment)
        
        # Validation status
        if result['validation'].get('is_valid'):
            print(f"\n✅ Comment is valid")
        else:
            print(f"\n❌ Comment has validation issues")
            
        # Data consistency
        if result['data_consistency'].get('is_consistent'):
            print("✅ Data flow is consistent")
        else:
            print("❌ Data consistency issues detected")
    
    def test_multiple_locations(self, 
                              locations: List[str], 
                              llm_provider: str = "openai") -> Dict:
        """Test weather flow for multiple locations"""
        print(f"\nTesting weather flow for {len(locations)} locations")
        print(f"LLM Provider: {llm_provider}")
        
        for location in locations:
            result = self.test_location_weather_flow(location, llm_provider)
            self.test_results.append(result)
            
        # Close weather client
        if self.weather_client:
            self.weather_client.close()
            
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict:
        """Generate test summary"""
        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r['success'])
        
        # Count specific issues
        api_failures = sum(1 for r in self.test_results if not r['weather_api'].get('success', False))
        workflow_failures = sum(1 for r in self.test_results if not r['workflow'].get('success', False))
        validation_failures = sum(1 for r in self.test_results if not r['validation'].get('is_valid', False))
        consistency_issues = sum(1 for r in self.test_results if not r['data_consistency'].get('is_consistent', True))
        
        summary = {
            'total_tests': total,
            'successful': successful,
            'api_failures': api_failures,
            'workflow_failures': workflow_failures,
            'validation_failures': validation_failures,
            'consistency_issues': consistency_issues,
            'success_rate': successful / total if total > 0 else 0
        }
        
        return summary
    
    def print_summary(self):
        """Print test summary"""
        summary = self._generate_summary()
        
        print(f"\n{'='*80}")
        print("WEATHER FLOW TEST SUMMARY")
        print("="*80)
        print(f"Total locations tested: {summary['total_tests']}")
        print(f"Successful flows: {summary['successful']} ({summary['success_rate']:.1%})")
        print(f"\nFailure breakdown:")
        print(f"  Weather API failures: {summary['api_failures']}")
        print(f"  Workflow failures: {summary['workflow_failures']}")
        print(f"  Validation failures: {summary['validation_failures']}")
        print(f"  Data consistency issues: {summary['consistency_issues']}")
        
        # Show locations with issues
        problem_locations = [
            r['location'] for r in self.test_results 
            if not r['success'] or not r['validation'].get('is_valid', False)
        ]
        
        if problem_locations:
            print(f"\nLocations with issues:")
            for location in problem_locations[:5]:
                print(f"  - {location}")
            if len(problem_locations) > 5:
                print(f"  ... and {len(problem_locations) - 5} more")
                
    def save_results(self, output_file: str = "weather_flow_test_results.json"):
        """Save detailed results"""
        output_data = {
            'summary': self._generate_summary(),
            'test_timestamp': datetime.now().isoformat(),
            'detailed_results': self.test_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"\nDetailed results saved to: {output_file}")


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test weather data flow')
    parser.add_argument(
        '--locations',
        nargs='+',
        default=['東京', '大阪', '札幌'],
        help='Locations to test'
    )
    parser.add_argument(
        '--provider',
        default='openai',
        choices=['openai', 'anthropic', 'gemini'],
        help='LLM provider to use'
    )
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save detailed results to JSON'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = WeatherFlowTester()
    tester.test_multiple_locations(args.locations, args.provider)
    tester.print_summary()
    
    # Save results if requested
    if args.save_results:
        tester.save_results()
        
    # Return appropriate exit code
    summary = tester._generate_summary()
    return 0 if summary['success_rate'] >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())