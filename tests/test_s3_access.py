#!/usr/bin/env python3
"""S3 and Local Repository Access Test Script

Tests both S3 access (when available) and local CSV repository as fallback.
Provides comprehensive diagnostics for troubleshooting access issues.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RepositoryTester:
    """Tests comment repository access (S3 and local)"""
    
    def __init__(self):
        self.results = {
            's3': {'tested': False, 'success': False, 'details': {}},
            'local': {'tested': False, 'success': False, 'details': {}}
        }
        
    def test_s3_access(self, use_profile: bool = True) -> Tuple[bool, Dict]:
        """Test S3 repository access with detailed diagnostics"""
        print("=== S3 Repository Access Test ===\n")
        
        result = {
            'success': False,
            'connection_method': 'profile' if use_profile else 'credentials',
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            import boto3
            from src.repositories.s3_comment_repository import S3CommentRepository
            
            bucket_name = os.getenv('S3_COMMENT_BUCKET', 'it-literacy-457604437098-ap-northeast-1')
            region_name = os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-1')
            
            if use_profile:
                profile_name = os.getenv('AWS_PROFILE', 'dit-training')
                print(f"🔑 Using AWS Profile: {profile_name}")
                
                # Create session with profile
                try:
                    session = boto3.Session(profile_name=profile_name)
                    
                    # Test credentials
                    sts_client = session.client('sts')
                    identity = sts_client.get_caller_identity()
                    
                    print("✅ AWS Authentication successful:")
                    print(f"  Account: {identity['Account']}")
                    print(f"  ARN: {identity['Arn']}")
                    
                    result['details']['aws_identity'] = {
                        'account': identity['Account'],
                        'arn': identity['Arn']
                    }
                    
                except Exception as e:
                    error_msg = f"AWS profile authentication failed: {str(e)}"
                    print(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    return False, result
                    
            else:
                print("🔑 Using environment variable credentials")
                
                # Check environment variables
                required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
                missing_vars = [var for var in required_vars if not os.getenv(var)]
                
                if missing_vars:
                    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
                    print(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    return False, result
                    
                print("✅ AWS credentials found in environment")
            
            print(f"\n📦 S3 Bucket: {bucket_name}")
            print(f"🌏 Region: {region_name}")
            
            # Initialize repository
            repo = S3CommentRepository(
                bucket_name=bucket_name,
                region_name=region_name,
                aws_profile=profile_name if use_profile else None
            )
            
            # Test connection
            print("\n2. Testing S3 connection...")
            start_time = time.time()
            
            if repo.test_connection():
                connection_time = time.time() - start_time
                print(f"✅ S3 connection successful! (took {connection_time:.2f}s)")
                result['details']['connection_time'] = connection_time
                
                # List available periods
                print("\n3. Checking available data periods...")
                periods = repo.list_available_periods()
                
                if periods:
                    print(f"✅ Found {len(periods)} data periods")
                    print(f"  Latest: {periods[0]}")
                    print(f"  Oldest: {periods[-1]}")
                    
                    result['details']['data_periods'] = {
                        'count': len(periods),
                        'latest': periods[0],
                        'oldest': periods[-1],
                        'sample': periods[:5]
                    }
                    
                    # Fetch sample data
                    print("\n4. Fetching sample data...")
                    latest_period = periods[0]
                    
                    start_time = time.time()
                    collection = repo.fetch_comments_by_period(latest_period)
                    fetch_time = time.time() - start_time
                    
                    if collection and collection.comments:
                        print(f"✅ Retrieved {len(collection.comments)} comments (took {fetch_time:.2f}s)")
                        
                        # Analyze comment types
                        comment_types = {}
                        locations = set()
                        
                        for comment in collection.comments:
                            comment_type = comment.comment_type.value
                            comment_types[comment_type] = comment_types.get(comment_type, 0) + 1
                            locations.add(comment.location)
                            
                        result['details']['sample_data'] = {
                            'period': latest_period,
                            'total_comments': len(collection.comments),
                            'fetch_time': fetch_time,
                            'comment_types': comment_types,
                            'unique_locations': len(locations),
                            'sample_locations': list(locations)[:5]
                        }
                        
                        # Show sample comment
                        sample = collection.comments[0]
                        print(f"\n📝 Sample comment:")
                        print(f"  Date: {sample.datetime}")
                        print(f"  Location: {sample.location}")
                        print(f"  Weather: {sample.weather_condition}")
                        print(f"  Type: {sample.comment_type.value}")
                        print(f"  Text: {sample.comment_text[:100]}...")
                        
                        result['success'] = True
                    else:
                        warning = f"No comments found in period {latest_period}"
                        print(f"⚠️  {warning}")
                        result['warnings'].append(warning)
                else:
                    error_msg = "No data periods found in S3 bucket"
                    print(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
            else:
                error_msg = "S3 bucket connection test failed"
                print(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                
        except ImportError as e:
            error_msg = f"Failed to import required modules: {str(e)}"
            print(f"❌ {error_msg}")
            result['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            
        self.results['s3'] = {
            'tested': True,
            'success': result['success'],
            'details': result
        }
        
        return result['success'], result
    
    def test_local_access(self) -> Tuple[bool, Dict]:
        """Test local CSV repository access"""
        print("\n=== Local CSV Repository Access Test ===\n")
        
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            from src.repositories.local_comment_repository import LocalCommentRepository
            
            print("1. Initializing local repository...")
            repo = LocalCommentRepository()
            
            # Check data directory
            data_dir = repo.data_dir
            if os.path.exists(data_dir):
                print(f"✅ Data directory found: {data_dir}")
                
                # List CSV files
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                print(f"✅ Found {len(csv_files)} CSV files")
                
                result['details']['data_directory'] = data_dir
                result['details']['csv_files'] = csv_files
                
                # Get available seasons
                print("\n2. Checking available seasons...")
                seasons = repo.get_available_seasons()
                
                if seasons:
                    print(f"✅ Found {len(seasons)} seasons: {', '.join(seasons)}")
                    result['details']['seasons'] = seasons
                    
                    # Test each season
                    season_stats = {}
                    
                    for season in seasons:
                        print(f"\n3. Testing season: {season}")
                        
                        # Get comments for season
                        comments = repo.get_comments_by_season(season, limit=100)
                        
                        if comments:
                            # Analyze comments
                            comment_types = {}
                            for comment in comments:
                                ctype = comment.comment_type.value
                                comment_types[ctype] = comment_types.get(ctype, 0) + 1
                                
                            season_stats[season] = {
                                'total_comments': len(comments),
                                'comment_types': comment_types
                            }
                            
                            print(f"  ✅ Found {len(comments)} comments")
                            print(f"  Types: {comment_types}")
                            
                            # Show sample
                            sample = comments[0]
                            print(f"\n  📝 Sample from {season}:")
                            print(f"    Type: {sample.comment_type.value}")
                            print(f"    Text: {sample.comment_text[:80]}...")
                        else:
                            warning = f"No comments found for season: {season}"
                            print(f"  ⚠️  {warning}")
                            result['warnings'].append(warning)
                            
                    result['details']['season_statistics'] = season_stats
                    result['success'] = True
                    
                    # Test search functionality
                    print("\n4. Testing search functionality...")
                    search_results = repo.search_comments("雨", limit=5)
                    
                    if search_results:
                        print(f"✅ Search found {len(search_results)} results for '雨'")
                        result['details']['search_test'] = {
                            'query': '雨',
                            'results_count': len(search_results)
                        }
                    else:
                        print("⚠️  No search results found")
                        
                else:
                    error_msg = "No seasons found in repository"
                    print(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
            else:
                error_msg = f"Data directory not found: {data_dir}"
                print(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                
        except ImportError as e:
            error_msg = f"Failed to import local repository: {str(e)}"
            print(f"❌ {error_msg}")
            result['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            
        self.results['local'] = {
            'tested': True,
            'success': result['success'],
            'details': result
        }
        
        return result['success'], result
    
    def print_recommendations(self):
        """Print recommendations based on test results"""
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        s3_result = self.results['s3']
        local_result = self.results['local']
        
        if s3_result['success'] and local_result['success']:
            print("✅ Both S3 and local repositories are working!")
            print("   You can use either data source.")
            
        elif local_result['success'] and not s3_result['success']:
            print("✅ Local repository is working, S3 is not accessible.")
            print("   The system will automatically use local CSV files.")
            
            if s3_result['tested']:
                print("\nTo fix S3 access:")
                errors = s3_result['details'].get('errors', [])
                if any('profile' in e.lower() for e in errors):
                    print("  1. Configure AWS profile 'dit-training':")
                    print("     aws configure --profile dit-training")
                elif any('credential' in e.lower() for e in errors):
                    print("  1. Set AWS credentials in .env file:")
                    print("     AWS_ACCESS_KEY_ID=your_key")
                    print("     AWS_SECRET_ACCESS_KEY=your_secret")
                    
        elif s3_result['success'] and not local_result['success']:
            print("⚠️  S3 is working but local repository has issues.")
            print("   Check that CSV files exist in the output directory.")
            
        else:
            print("❌ Both repositories have issues!")
            print("   The system needs at least one working data source.")
            
    def save_results(self, output_file: str = "repository_test_results.json"):
        """Save test results to file"""
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"\nDetailed results saved to: {output_file}")


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test S3 and local repository access',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with AWS profile (default)
  python test_s3_access.py
  
  # Test with environment credentials
  python test_s3_access.py --no-profile
  
  # Test only local repository
  python test_s3_access.py --local-only
  
  # Save detailed results
  python test_s3_access.py --save-results
        """
    )
    
    parser.add_argument(
        '--no-profile',
        action='store_true',
        help='Use environment credentials instead of AWS profile'
    )
    parser.add_argument(
        '--local-only',
        action='store_true',
        help='Test only local repository'
    )
    parser.add_argument(
        '--s3-only',
        action='store_true',
        help='Test only S3 repository'
    )
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save detailed results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = RepositoryTester()
    
    # Test S3 unless local-only
    if not args.local_only:
        tester.test_s3_access(use_profile=not args.no_profile)
        
    # Test local unless s3-only
    if not args.s3_only:
        tester.test_local_access()
        
    # Print recommendations
    tester.print_recommendations()
    
    # Save results if requested
    if args.save_results:
        tester.save_results()
        
    # Return appropriate exit code
    s3_success = tester.results['s3']['success'] if tester.results['s3']['tested'] else True
    local_success = tester.results['local']['success'] if tester.results['local']['tested'] else True
    
    return 0 if (s3_success or local_success) else 1


if __name__ == "__main__":
    sys.exit(main())