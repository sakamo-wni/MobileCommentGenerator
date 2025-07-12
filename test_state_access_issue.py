"""Test to demonstrate the state access issue"""

from typing import Dict, Any

# Simulate the workflow state as a dictionary (like in the workflow)
state_dict = {
    "location_name": "東京",
    "use_lazy_loading": True,
    "use_optimized_repository": False,
}

# Simulate the state as a class (like CommentGenerationState)
class StateClass:
    def __init__(self):
        self.location_name = "東京"
        self.use_lazy_loading = True
        self.use_optimized_repository = False

def test_getattr_on_dict():
    """Test getattr behavior on dict vs object"""
    print("=== Testing getattr behavior ===\n")
    
    # Test with dictionary
    print("1. Using getattr on dictionary:")
    use_lazy = getattr(state_dict, 'use_lazy_loading', True)
    print(f"   getattr(dict, 'use_lazy_loading', True) = {use_lazy}")
    print(f"   (This returns the default value because dict doesn't have attributes)\n")
    
    # Test with object
    print("2. Using getattr on object:")
    state_obj = StateClass()
    use_lazy = getattr(state_obj, 'use_lazy_loading', True)
    print(f"   getattr(object, 'use_lazy_loading', True) = {use_lazy}")
    print(f"   (This returns the actual value from the object)\n")
    
    # Show the correct way for dictionary
    print("3. Correct way to access dictionary with default:")
    use_lazy = state_dict.get('use_lazy_loading', True)
    print(f"   dict.get('use_lazy_loading', True) = {use_lazy}")
    
    # The bug in retrieve_past_comments_node.py
    print("\n=== The Bug ===")
    print("In retrieve_past_comments_node.py, the code uses:")
    print("  use_lazy_loading = getattr(state, 'use_lazy_loading', True)")
    print("\nBut 'state' is a dictionary in the workflow, not an object!")
    print("So it ALWAYS returns the default value (True), ignoring the actual state value.")

if __name__ == "__main__":
    test_getattr_on_dict()