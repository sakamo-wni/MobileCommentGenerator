"""Test to reproduce the exact issue in retrieve_past_comments_node"""

from typing import Dict, Any
from src.repositories.lazy_comment_repository import LazyCommentRepository
from src.repositories.local_comment_repository import LocalCommentRepository

def simulate_retrieve_past_comments_node(state: Dict[str, Any]):
    """Simulate the problematic code from retrieve_past_comments_node.py"""
    print("=== Simulating retrieve_past_comments_node ===\n")
    
    # This is the problematic code from the node (lines 34-35)
    use_optimized = getattr(state, 'use_optimized_repository', False)
    use_lazy_loading = getattr(state, 'use_lazy_loading', True)
    
    print(f"1. Using getattr on dict state:")
    print(f"   use_optimized = {use_optimized} (should be False)")
    print(f"   use_lazy_loading = {use_lazy_loading} (should be True but ignores state value)")
    print(f"   Actual state['use_lazy_loading'] = {state.get('use_lazy_loading', 'NOT SET')}")
    
    # Show what happens
    if use_lazy_loading:
        print("\n2. Creating LazyCommentRepository...")
        repository = LazyCommentRepository()
    else:
        print("\n2. Creating LocalCommentRepository...")
        repository = LocalCommentRepository(use_index=False)
    
    # Get comments
    print("\n3. Getting recent comments...")
    try:
        comments = repository.get_recent_comments(limit=10)
        print(f"   Found {len(comments)} comments")
        return comments
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {str(e)}")
        return []

def simulate_fixed_version(state: Dict[str, Any]):
    """Show the fixed version"""
    print("\n=== Fixed version ===\n")
    
    # Fixed code - use dict.get() instead of getattr()
    use_optimized = state.get('use_optimized_repository', False)
    use_lazy_loading = state.get('use_lazy_loading', True)
    
    print(f"1. Using dict.get() on state:")
    print(f"   use_optimized = {use_optimized}")
    print(f"   use_lazy_loading = {use_lazy_loading}")
    print(f"   This correctly reads from the state dictionary!")

if __name__ == "__main__":
    # Create a state dict like the workflow does
    state = {
        "location_name": "東京",
        "use_lazy_loading": False,  # Try to disable lazy loading
        "use_optimized_repository": True,
    }
    
    print("State dictionary:")
    print(f"  use_lazy_loading: {state['use_lazy_loading']} (we want False)")
    print(f"  use_optimized_repository: {state['use_optimized_repository']}")
    print()
    
    # Show the problem
    simulate_retrieve_past_comments_node(state)
    
    # Show the fix
    simulate_fixed_version(state)