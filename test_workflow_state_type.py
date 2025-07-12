"""Test to check what type of state is passed to nodes"""

import logging
from typing import Dict, Any
from src.data.comment_generation_state import CommentGenerationState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_node(state):
    """Test node to check state type"""
    logger.info(f"State type: {type(state)}")
    logger.info(f"Is dict: {isinstance(state, dict)}")
    logger.info(f"Is CommentGenerationState: {isinstance(state, CommentGenerationState)}")
    
    # Test accessing attributes
    if isinstance(state, dict):
        logger.info(f"Dict access - location_name: {state.get('location_name', 'NOT FOUND')}")
        logger.info(f"Dict access - use_lazy_loading: {state.get('use_lazy_loading', 'NOT FOUND')}")
    
    if hasattr(state, 'location_name'):
        logger.info(f"Attribute access - location_name: {state.location_name}")
    
    if hasattr(state, 'use_lazy_loading'):
        logger.info(f"Attribute access - use_lazy_loading: {state.use_lazy_loading}")
    
    # Test getattr
    use_lazy = getattr(state, 'use_lazy_loading', 'DEFAULT')
    logger.info(f"getattr(state, 'use_lazy_loading', 'DEFAULT') = {use_lazy}")
    
    return state

# Test with dict
print("=== Testing with dict ===")
dict_state = {
    "location_name": "東京",
    "use_lazy_loading": False,
}
test_node(dict_state)

print("\n=== Testing with CommentGenerationState ===")
# Test with CommentGenerationState
from datetime import datetime
obj_state = CommentGenerationState(
    location_name="東京",
    target_datetime=datetime.now(),
    use_lazy_loading=False
)
test_node(obj_state)