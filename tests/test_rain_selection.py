#!/usr/bin/env python
"""Test rain weather comment selection with improved validation and reporting"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set AWS profile if needed
os.environ.setdefault("AWS_PROFILE", "dit-training")

from src.workflows.comment_generation_workflow import run_comment_generation
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.config.weather_config import get_config


class RainCommentTester:
    """Test rain weather comment generation with comprehensive validation"""
    
    def __init__(self):
        self.config = get_config()
        self.validator = WeatherCommentValidator()
        self.test_results = []
        
    def test_location_rain_comment(self, location_name: str, llm_provider: str = "openai") -> Dict:
        """Test rain comment generation for a specific location"""
        print(f"\n{'='*60}")
        print(f"Testing rain comment for: {location_name}")
        print("="*60)
        
        test_result = {
            'location': location_name,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'weather_data': {},
            'comment_data': {},
            'validation': {},
            'errors': []
        }
        
        try:
            # Run comment generation
            result = run_comment_generation(
                location_name=location_name,
                llm_provider=llm_provider
            )
            
            if result.get("success"):
                print(f"✅ Comment generation successful!")
                test_result['success'] = True
                
                # Extract final comment
                final_comment = result.get('final_comment', '')
                print(f"\nFinal comment:\n{final_comment}")
                test_result['comment_data']['final_comment'] = final_comment
                
                # Extract metadata
                metadata = result.get('generation_metadata', {})
                
                # Weather data
                weather_condition = metadata.get('weather_condition', '')
                temperature = metadata.get('temperature')
                test_result['weather_data'] = {
                    'condition': weather_condition,
                    'temperature': temperature,
                    'coordinates': metadata.get('location_coordinates')
                }
                
                print(f"\nWeather data used:")
                print(f"  Condition: {weather_condition}")
                print(f"  Temperature: {temperature}°C")
                
                # Check if it's actually rainy weather
                is_rainy = self._is_rainy_weather(weather_condition)
                test_result['weather_data']['is_rainy'] = is_rainy
                
                if not is_rainy:
                    print(f"⚠️  Warning: Weather condition '{weather_condition}' is not rainy")
                    test_result['errors'].append(f"Non-rainy weather: {weather_condition}")
                
                # Validate comment
                validation_result = self.validator.validate_comment(
                    final_comment,
                    weather_condition,
                    temperature
                )
                
                test_result['validation'] = {
                    'is_valid': validation_result['is_valid'],
                    'issues': validation_result.get('issues', []),
                    'warnings': validation_result.get('warnings', [])
                }
                
                if not validation_result['is_valid']:
                    print(f"\n❌ Validation failed:")
                    for issue in validation_result.get('issues', []):
                        print(f"  - {issue}")
                else:
                    print(f"\n✅ Comment validation passed!")
                
                # Extract selected comments
                selected_comments = metadata.get('selected_past_comments', [])
                test_result['comment_data']['selected_comments'] = []
                
                print(f"\nSelected S3 comments ({len(selected_comments)}):")
                for comment in selected_comments:
                    if comment:
                        comment_info = {
                            'type': comment.get('type'),
                            'text': comment.get('text'),
                            'weather': comment.get('weather_condition')
                        }
                        test_result['comment_data']['selected_comments'].append(comment_info)
                        print(f"  - {comment.get('type')}: {comment.get('text')[:50]}...")
                
                # Selection metadata
                selection_metadata = metadata.get('selection_metadata', {})
                test_result['comment_data']['selection_metadata'] = {
                    'method': selection_metadata.get('selection_method'),
                    'weather_candidates': selection_metadata.get('weather_comments_count', 0),
                    'advice_candidates': selection_metadata.get('advice_comments_count', 0)
                }
                
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Comment generation failed: {error_msg}")
                test_result['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"❌ Error: {error_msg}")
            test_result['errors'].append(error_msg)
            
        return test_result
    
    def _is_rainy_weather(self, weather_condition: str) -> bool:
        """Check if weather condition indicates rain"""
        rain_keywords = ['雨', 'rain', 'shower', 'drizzle', '降水', '降雨']
        return any(keyword in weather_condition.lower() for keyword in rain_keywords)
    
    def test_multiple_locations(self, 
                              locations: List[str], 
                              llm_provider: str = "openai") -> Dict:
        """Test rain comments for multiple locations"""
        print(f"\nTesting rain comments for {len(locations)} locations")
        print("Using LLM provider:", llm_provider)
        
        for location in locations:
            result = self.test_location_rain_comment(location, llm_provider)
            self.test_results.append(result)
            
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict:
        """Generate summary of all test results"""
        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r['success'])
        rainy_weather = sum(1 for r in self.test_results if r['weather_data'].get('is_rainy', False))
        valid_comments = sum(1 for r in self.test_results if r['validation'].get('is_valid', False))
        
        summary = {
            'total_tests': total,
            'successful_generations': successful,
            'rainy_weather_count': rainy_weather,
            'valid_comments': valid_comments,
            'success_rate': successful / total if total > 0 else 0,
            'validation_rate': valid_comments / successful if successful > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Collect all validation issues
        all_issues = []
        for result in self.test_results:
            issues = result['validation'].get('issues', [])
            all_issues.extend(issues)
            
        # Count issue frequencies
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
        summary['common_issues'] = sorted(
            issue_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]  # Top 5 issues
        
        return summary
    
    def print_summary(self):
        """Print test summary"""
        summary = self._generate_summary()
        
        print(f"\n{'='*80}")
        print("RAIN COMMENT TEST SUMMARY")
        print("="*80)
        print(f"Total locations tested: {summary['total_tests']}")
        print(f"Successful generations: {summary['successful_generations']} ({summary['success_rate']:.1%})")
        print(f"Actually rainy weather: {summary['rainy_weather_count']}")
        print(f"Valid comments: {summary['valid_comments']} ({summary['validation_rate']:.1%})")
        
        if summary['common_issues']:
            print(f"\nMost common validation issues:")
            for issue, count in summary['common_issues']:
                print(f"  - {issue}: {count} occurrences")
                
        # Show locations with issues
        locations_with_issues = [
            r['location'] for r in self.test_results 
            if not r['validation'].get('is_valid', False) and r['success']
        ]
        
        if locations_with_issues:
            print(f"\nLocations with validation issues:")
            for location in locations_with_issues[:5]:
                print(f"  - {location}")
            if len(locations_with_issues) > 5:
                print(f"  ... and {len(locations_with_issues) - 5} more")
                
    def save_results(self, output_file: str = "rain_comment_test_results.json"):
        """Save detailed results to JSON file"""
        output_data = {
            'summary': self._generate_summary(),
            'detailed_results': self.test_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"\nDetailed results saved to: {output_file}")


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test rain weather comment selection')
    parser.add_argument(
        '--locations',
        nargs='+',
        default=['東京', '大阪', '福岡', '札幌', '那覇'],
        help='Locations to test (default: major cities)'
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
        help='Save detailed results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = RainCommentTester()
    tester.test_multiple_locations(args.locations, args.provider)
    tester.print_summary()
    
    # Save results if requested
    if args.save_results:
        tester.save_results()
    
    # Return appropriate exit code
    summary = tester._generate_summary()
    return 0 if summary['validation_rate'] >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())