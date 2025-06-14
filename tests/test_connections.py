#!/usr/bin/env python3
"""
Comprehensive connection test script for all external services

Tests S3, LLM providers, and Weather API connections with detailed diagnostics.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()


class ConnectionTester:
    """Manages connection tests for all external services"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        
    def test_weather_api(self) -> Tuple[bool, Dict]:
        """Test weather API connection with detailed diagnostics"""
        print("\n" + "="*60)
        print("【Weather API Connection Test】")
        print("="*60)
        
        result = {
            'service': 'Weather API',
            'status': 'failed',
            'details': {},
            'errors': []
        }
        
        try:
            from src.apis.wxtech_client import WxTechAPIClient
            from src.utils.common_utils import get_season_from_date
            
            api_key = os.getenv("WXTECH_API_KEY")
            if not api_key:
                result['errors'].append("WXTECH_API_KEY environment variable not set")
                print("❌ Error: WXTECH_API_KEY not configured")
                return False, result
            
            print(f"✓ API key found: {api_key[:10]}...")
            result['details']['api_key_configured'] = True
            
            # Test with multiple locations
            test_locations = [
                {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
                {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},
                {"name": "Sapporo", "lat": 43.0642, "lon": 141.3469}
            ]
            
            client = WxTechAPIClient(api_key)
            successful_tests = 0
            
            for loc in test_locations:
                print(f"\nTesting {loc['name']} (lat: {loc['lat']}, lon: {loc['lon']})...")
                
                try:
                    start = time.time()
                    forecast_collection = client.get_forecast(loc['lat'], loc['lon'])
                    response_time = time.time() - start
                    
                    if forecast_collection and forecast_collection.forecasts:
                        current = forecast_collection.get_nearest_forecast(datetime.now())
                        if current:
                            print(f"✅ Success for {loc['name']}!")
                            print(f"  - Weather: {current.weather_description}")
                            print(f"  - Temperature: {current.temperature}°C")
                            print(f"  - Humidity: {current.humidity}%")
                            print(f"  - Wind: {current.wind_speed}m/s")
                            print(f"  - Response time: {response_time:.2f}s")
                            
                            result['details'][loc['name']] = {
                                'success': True,
                                'weather': current.weather_description,
                                'temperature': current.temperature,
                                'response_time': response_time
                            }
                            successful_tests += 1
                        else:
                            error_msg = f"No current forecast data for {loc['name']}"
                            print(f"❌ {error_msg}")
                            result['errors'].append(error_msg)
                    else:
                        error_msg = f"No forecast data returned for {loc['name']}"
                        print(f"❌ {error_msg}")
                        result['errors'].append(error_msg)
                        
                except Exception as e:
                    error_msg = f"API error for {loc['name']}: {str(e)}"
                    print(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    
            client.close()
            
            # Overall success if at least one location worked
            if successful_tests > 0:
                result['status'] = 'success'
                result['details']['tested_locations'] = len(test_locations)
                result['details']['successful_locations'] = successful_tests
                current_season = get_season_from_date(datetime.now())
                result['details']['current_season'] = current_season
                return True, result
            else:
                return False, result
                
        except ImportError as e:
            result['errors'].append(f"Module import error: {str(e)}")
            print(f"❌ Import error: {str(e)}")
            return False, result
        except Exception as e:
            result['errors'].append(f"Unexpected error: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
            return False, result

    def test_s3_connection(self) -> Tuple[bool, Dict]:
        """Test S3 connection using local CSV repository"""
        print("\n" + "="*60)
        print("【S3/Local Repository Connection Test】")
        print("="*60)
        
        result = {
            'service': 'Comment Repository',
            'status': 'failed',
            'details': {},
            'errors': []
        }
        
        try:
            # First try S3
            print("Testing S3 repository connection...")
            try:
                from src.repositories.s3_comment_repository import S3CommentRepository
                
                aws_profile = os.getenv("AWS_PROFILE", "dit-training")
                region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
                bucket_name = os.getenv("S3_COMMENT_BUCKET", "it-literacy-457604437098-ap-northeast-1")
                
                print(f"✓ Using AWS profile '{aws_profile}'")
                print(f"  - Region: {region}")
                print(f"  - Bucket: {bucket_name}")
                
                repo = S3CommentRepository(
                    bucket_name=bucket_name,
                    region_name=region,
                    aws_profile=aws_profile
                )
                
                # Test connection
                if repo.test_connection():
                    print("✅ S3 connection successful!")
                    result['details']['repository_type'] = 'S3'
                    result['details']['bucket'] = bucket_name
                    
                    # Get sample comments
                    comment_collection = repo.get_recent_comments(location="東京", max_comments=5)
                    if comment_collection and comment_collection.comments:
                        result['details']['sample_comments_count'] = len(comment_collection.comments)
                        result['status'] = 'success'
                        return True, result
                        
            except Exception as e:
                print(f"⚠️  S3 connection failed: {str(e)}")
                result['errors'].append(f"S3 error: {str(e)}")
            
            # Fallback to local repository
            print("\nTesting local CSV repository...")
            from src.repositories.local_comment_repository import LocalCommentRepository
            
            repo = LocalCommentRepository()
            
            # Test by getting available seasons
            seasons = repo.get_available_seasons()
            if seasons:
                print(f"✅ Local repository access successful!")
                print(f"  Available seasons: {', '.join(seasons)}")
                result['details']['repository_type'] = 'Local CSV'
                result['details']['available_seasons'] = seasons
                
                # Get sample comments
                sample_comments = repo.get_comments_by_season(seasons[0], limit=5)
                if sample_comments:
                    result['details']['sample_comments_count'] = len(sample_comments)
                    result['status'] = 'success'
                    return True, result
            else:
                error_msg = "No data found in local repository"
                print(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                return False, result
                
        except ImportError as e:
            result['errors'].append(f"Module import error: {str(e)}")
            print(f"❌ Import error: {str(e)}")
            return False, result
        except Exception as e:
            result['errors'].append(f"Unexpected error: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
            return False, result

    def test_llm_connections(self) -> Tuple[bool, Dict]:
        """Test all LLM provider connections"""
        print("\n" + "="*60)
        print("【LLM Provider Connection Tests】")
        print("="*60)
        
        result = {
            'service': 'LLM Providers',
            'status': 'failed',
            'details': {},
            'errors': []
        }
        
        try:
            from src.llm.llm_manager import LLMManager
            
            providers = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY", 
                "gemini": "GOOGLE_API_KEY"
            }
            
            successful_providers = []
            
            for provider, env_var in providers.items():
                print(f"\n--- Testing {provider.upper()} ---")
                
                api_key = os.getenv(env_var)
                if not api_key:
                    print(f"⚠️  {env_var} not configured (skipping)")
                    result['details'][provider] = 'not_configured'
                    continue
                
                print(f"✓ API key found: {api_key[:10]}...")
                
                try:
                    # Initialize LLM manager
                    llm_manager = LLMManager(provider=provider)
                    
                    # Simple test prompt
                    test_prompt = "Respond with exactly: 'Connection successful'"
                    
                    print(f"Sending test prompt...")
                    start = time.time()
                    response = llm_manager.generate(test_prompt, max_tokens=50)
                    response_time = time.time() - start
                    
                    if response and "successful" in response.lower():
                        print(f"✅ {provider.upper()} connection successful!")
                        print(f"  Response time: {response_time:.2f}s")
                        print(f"  Response: {response.strip()}")
                        
                        result['details'][provider] = {
                            'status': 'success',
                            'response_time': response_time,
                            'model': llm_manager.model_name
                        }
                        successful_providers.append(provider)
                    else:
                        error_msg = f"Unexpected response: {response[:100] if response else 'None'}"
                        print(f"❌ {error_msg}")
                        result['errors'].append(f"{provider}: {error_msg}")
                        
                except Exception as e:
                    error_msg = f"{provider} error: {str(e)}"
                    print(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    result['details'][provider] = 'error'
            
            if successful_providers:
                result['status'] = 'partial' if len(successful_providers) < len(providers) else 'success'
                result['details']['working_providers'] = successful_providers
                return True, result
            else:
                return False, result
                
        except ImportError as e:
            result['errors'].append(f"Module import error: {str(e)}")
            print(f"❌ Import error: {str(e)}")
            return False, result
        except Exception as e:
            result['errors'].append(f"Unexpected error: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
            return False, result

    def test_integration(self) -> Tuple[bool, Dict]:
        """Test full workflow integration"""
        print("\n" + "="*60)
        print("【Integration Test - Full Workflow】")
        print("="*60)
        
        result = {
            'service': 'Workflow Integration',
            'status': 'failed',
            'details': {},
            'errors': []
        }
        
        try:
            from src.workflows.comment_generation_workflow import run_comment_generation
            
            # Try with first available LLM provider
            available_providers = []
            for provider, env_var in [("openai", "OPENAI_API_KEY"), 
                                     ("anthropic", "ANTHROPIC_API_KEY"),
                                     ("gemini", "GOOGLE_API_KEY")]:
                if os.getenv(env_var):
                    available_providers.append(provider)
                    
            if not available_providers:
                error_msg = "No LLM providers configured"
                print(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                return False, result
                
            provider = available_providers[0]
            print(f"Running workflow with provider: {provider}")
            print("  Location: Tokyo")
            
            start = time.time()
            workflow_result = run_comment_generation(
                location_name="東京",
                llm_provider=provider
            )
            execution_time = time.time() - start
            
            if workflow_result.get("success"):
                print("✅ Workflow execution successful!")
                print(f"  Final comment: {workflow_result.get('final_comment')}")
                print(f"  Execution time: {execution_time:.2f}s")
                
                result['status'] = 'success'
                result['details']['execution_time'] = execution_time
                result['details']['llm_provider'] = provider
                
                # Extract metadata
                metadata = workflow_result.get("generation_metadata", {})
                if metadata:
                    result['details']['weather_condition'] = metadata.get('weather_condition')
                    result['details']['temperature'] = metadata.get('temperature')
                    
                    selection_metadata = metadata.get('selection_metadata', {})
                    if selection_metadata:
                        result['details']['selection_method'] = selection_metadata.get('selection_method')
                        result['details']['candidates_evaluated'] = selection_metadata.get('weather_comments_count', 0) + selection_metadata.get('advice_comments_count', 0)
                
                return True, result
            else:
                error_msg = workflow_result.get('error', 'Unknown error')
                print(f"❌ Workflow failed: {error_msg}")
                result['errors'].append(error_msg)
                return False, result
                
        except Exception as e:
            error_msg = f"Integration test error: {str(e)}"
            print(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            return False, result

    def run_all_tests(self) -> Dict:
        """Run all connection tests and compile results"""
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("Starting Comprehensive Connection Tests")
        print("="*80)
        
        # Set default AWS profile if not set
        if not os.getenv("AWS_PROFILE"):
            os.environ["AWS_PROFILE"] = "dit-training"
            print(f"AWS_PROFILE set to 'dit-training'")
        
        # Run each test
        tests = [
            ("Weather API", self.test_weather_api),
            ("Repository", self.test_s3_connection),
            ("LLM Providers", self.test_llm_connections),
            ("Integration", self.test_integration)
        ]
        
        for test_name, test_func in tests:
            success, result = test_func()
            self.results[test_name] = {
                'success': success,
                'result': result
            }
        
        # Calculate summary
        total_tests = len(tests)
        successful_tests = sum(1 for r in self.results.values() if r['success'])
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'execution_time': time.time() - self.start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.results

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*80)
        print("【Connection Test Summary】")
        print("="*80)
        
        summary = self.results.get('summary', {})
        print(f"Total tests: {summary.get('total_tests', 0)}")
        print(f"Successful: {summary.get('successful_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Execution time: {summary.get('execution_time', 0):.2f}s")
        
        print("\nTest Results:")
        for test_name, test_result in self.results.items():
            if test_name == 'summary':
                continue
                
            status_icon = "✅" if test_result['success'] else "❌"
            status = test_result['result']['status']
            print(f"  {test_name}: {status_icon} {status}")
            
            # Show errors if any
            errors = test_result['result'].get('errors', [])
            if errors:
                print(f"    Errors:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
                if len(errors) > 3:
                    print(f"      ... and {len(errors) - 3} more")
        
        print("\n" + "="*80)
        overall_success = summary.get('successful_tests', 0) == summary.get('total_tests', 0)
        if overall_success:
            print("✅ All connection tests passed!")
        else:
            print("❌ Some connection tests failed. Check the errors above.")
        print("="*80)

    def save_results(self, output_file: str = "connection_test_results.json"):
        """Save detailed results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\nDetailed results saved to: {output_file}")


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test all external service connections')
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save detailed results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = ConnectionTester()
    results = tester.run_all_tests()
    tester.print_summary()
    
    # Save results if requested
    if args.save_results:
        tester.save_results()
    
    # Return appropriate exit code
    summary = results.get('summary', {})
    return 0 if summary.get('failed_tests', 1) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())