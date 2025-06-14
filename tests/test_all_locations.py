#!/usr/bin/env python3
"""Test weather API for all locations in 地点名.csv with improved error handling and reporting"""

import os
import sys
import csv
import time
from typing import List, Dict, Tuple
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.apis.wxtech_client import WxTechAPIClient
from src.config.weather_config import get_config
from src.utils.common_utils import get_season_from_date


class LocationWeatherTester:
    """Improved location weather API tester with better error handling and reporting"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.weather.wxtech_api_key
        self.client = None
        self.results = {
            'success': [],
            'no_data': [],
            'api_error': [],
            'other_error': []
        }
        
    def load_locations(self, csv_path: str) -> List[Dict[str, float]]:
        """Load locations from CSV file with error handling"""
        locations = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        locations.append({
                            'name': row['地点名'],
                            'lat': float(row['緯度']),
                            'lon': float(row['経度'])
                        })
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping invalid row: {row} - {e}")
                        
        except FileNotFoundError:
            print(f"ERROR: CSV file not found: {csv_path}")
            raise
        except Exception as e:
            print(f"ERROR: Failed to read CSV file: {e}")
            raise
            
        return locations
    
    def test_location(self, location: Dict[str, float]) -> Tuple[bool, str]:
        """Test a single location and return success status and message"""
        try:
            forecast_collection = self.client.get_forecast(
                location['lat'], 
                location['lon']
            )
            
            if forecast_collection and forecast_collection.forecasts:
                forecast_count = len(forecast_collection.forecasts)
                
                # Get current weather for verification
                current = forecast_collection.get_nearest_forecast(datetime.now())
                if current:
                    weather_info = (
                        f"{forecast_count} forecasts, "
                        f"current: {current.weather_description}, "
                        f"{current.temperature}°C"
                    )
                    return True, weather_info
                else:
                    return False, f"{forecast_count} forecasts but no current data"
            else:
                return False, "No forecast data returned"
                
        except Exception as e:
            error_type = type(e).__name__
            return False, f"{error_type}: {str(e)}"
    
    def categorize_result(self, location: Dict[str, float], success: bool, message: str):
        """Categorize test result for reporting"""
        result = {
            'location': location['name'],
            'lat': location['lat'],
            'lon': location['lon'],
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.results['success'].append(result)
        elif "No forecast data" in message:
            self.results['no_data'].append(result)
        elif any(err in message for err in ['APIError', 'RequestException', 'Timeout']):
            self.results['api_error'].append(result)
        else:
            self.results['other_error'].append(result)
    
    def run_tests(self, csv_path: str, delay_between_requests: float = 0.1):
        """Run tests for all locations with rate limiting"""
        if not self.api_key:
            print("ERROR: WXTECH_API_KEY environment variable not set")
            return False
            
        print(f"API Key found: {self.api_key[:10]}...")
        
        # Load locations
        locations = self.load_locations(csv_path)
        print(f"\nTesting {len(locations)} locations...")
        print(f"Rate limit delay: {delay_between_requests}s between requests\n")
        
        # Initialize client
        self.client = WxTechAPIClient(self.api_key)
        
        # Test each location
        start_time = time.time()
        
        for i, location in enumerate(locations):
            print(f"[{i+1}/{len(locations)}] Testing {location['name']} "
                  f"(lat={location['lat']:.4f}, lon={location['lon']:.4f})... ", 
                  end='', flush=True)
            
            success, message = self.test_location(location)
            
            if success:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                
            self.categorize_result(location, success, message)
            
            # Rate limiting (except for last request)
            if i < len(locations) - 1:
                time.sleep(delay_between_requests)
        
        # Close client
        if self.client:
            self.client.close()
            
        elapsed_time = time.time() - start_time
        
        # Print summary
        self.print_summary(len(locations), elapsed_time)
        
        return len(self.results['api_error']) == 0
    
    def print_summary(self, total_locations: int, elapsed_time: float):
        """Print detailed test summary"""
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total locations tested: {total_locations}")
        print(f"Total time: {elapsed_time:.2f}s ({elapsed_time/total_locations:.2f}s per location)")
        print(f"\nResults:")
        print(f"  ✅ Success: {len(self.results['success'])}")
        print(f"  ⚠️  No data: {len(self.results['no_data'])}")
        print(f"  ❌ API errors: {len(self.results['api_error'])}")
        print(f"  ❌ Other errors: {len(self.results['other_error'])}")
        
        # Show sample errors
        if self.results['api_error']:
            print(f"\nAPI ERROR SAMPLES (first 5):")
            for error in self.results['api_error'][:5]:
                print(f"  - {error['location']}: {error['message']}")
                
        if self.results['other_error']:
            print(f"\nOTHER ERROR SAMPLES (first 5):")
            for error in self.results['other_error'][:5]:
                print(f"  - {error['location']}: {error['message']}")
                
        # Season analysis
        if self.results['success']:
            current_season = get_season_from_date(datetime.now())
            print(f"\nCurrent season: {current_season}")
            print("Success rate by region would be calculated here...")
            
    def save_results(self, output_file: str = "test_results.json"):
        """Save detailed results to JSON file"""
        import json
        
        output_data = {
            'test_timestamp': datetime.now().isoformat(),
            'summary': {
                'total': sum(len(v) for v in self.results.values()),
                'success': len(self.results['success']),
                'no_data': len(self.results['no_data']),
                'api_error': len(self.results['api_error']),
                'other_error': len(self.results['other_error'])
            },
            'results': self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"\nDetailed results saved to: {output_file}")


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test weather API for all locations')
    parser.add_argument(
        '--csv', 
        default='frontend/public/地点名.csv',
        help='Path to locations CSV file'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.1,
        help='Delay between API requests in seconds (default: 0.1)'
    )
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save detailed results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = LocationWeatherTester()
    success = tester.run_tests(args.csv, args.delay)
    
    # Save results if requested
    if args.save_results:
        tester.save_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())