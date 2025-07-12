"""Test to reproduce lazy loading issue in workflow"""

import os
from datetime import datetime
from src.workflows.comment_generation_workflow import create_comment_generation_workflow

# Enable lazy loading
os.environ["USE_LAZY_CSV_LOADING"] = "true"

def test_workflow_integration():
    """Test the workflow with lazy loading"""
    print("=== Testing Workflow with Lazy Loading ===\n")
    
    # Create workflow
    workflow = create_comment_generation_workflow()
    
    # Create initial state (as dict like in run_comment_generation)
    initial_state = {
        "location_name": "東京",
        "target_datetime": datetime.now(),
        "llm_provider": "openai",
        "exclude_previous": False,
        "retry_count": 0,
        "errors": [],
        "warnings": [],
        "workflow_start_time": datetime.now(),
        "use_lazy_loading": True,  # Explicitly set this
    }
    
    try:
        # Run workflow
        print("Running workflow...")
        result = workflow.invoke(initial_state)
        
        if result.get("errors"):
            print("Workflow completed with errors:")
            for error in result.get("errors", []):
                print(f"  - {error}")
        else:
            print("Workflow completed successfully!")
            print(f"Final comment: {result.get('final_comment')}")
            
        # Check if past_comments were loaded
        print(f"\nPast comments loaded: {len(result.get('past_comments', []))}")
        
    except Exception as e:
        print(f"Workflow failed with exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow_integration()