#!/usr/bin/env python3
"""
Script to update imports from weather_constants.py to use the new config.py structure.
This script shows what constants are being imported and creates the updated import statements.
"""

import os
from pathlib import Path

# Define the files to update and their current imports
files_to_update = [
    {
        "path": "src/nodes/comment_selector/validation.py",
        "line": 16,
        "current_import": "from src.config.weather_constants import WEATHER_CHANGE_THRESHOLD",
        "constants": ["WEATHER_CHANGE_THRESHOLD"],
        "updated_import": "from src.config.config import get_weather_constants\n\n# At the beginning of the file or in __init__ method:\nweather_constants = get_weather_constants()\nWEATHER_CHANGE_THRESHOLD = weather_constants.WEATHER_CHANGE_THRESHOLD"
    },
    {
        "path": "src/formatters/weather_timeline_formatter.py",
        "line": 12,
        "current_import": "from src.config.weather_constants import WEATHER_CHANGE_THRESHOLD",
        "constants": ["WEATHER_CHANGE_THRESHOLD"],
        "updated_import": "from src.config.config import get_weather_constants\n\n# In __init__ method:\nself.weather_constants = get_weather_constants()\n# Then use: self.weather_constants.WEATHER_CHANGE_THRESHOLD"
    },
    {
        "path": "src/utils/validators/weather_validator.py",
        "line": 6,
        "current_import": "from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS",
        "constants": ["SUNNY_WEATHER_KEYWORDS"],
        "additional_imports": [
            {"line": 178, "import": "from src.config.weather_constants import PrecipitationThresholds", "constants": ["PrecipitationThresholds"]}
        ],
        "updated_import": "from src.config.config import get_weather_constants\n\n# In __init__ method:\nweather_constants = get_weather_constants()\nself.SUNNY_WEATHER_KEYWORDS = weather_constants.SUNNY_WEATHER_KEYWORDS\nself.PrecipitationThresholds = weather_constants.PrecipitationThresholds"
    },
    {
        "path": "src/utils/validators/weather_specific/temperature_condition_validator.py",
        "lines": [7, 8, 9, 10],
        "current_import": """from src.config.weather_constants import (
    HEATSTROKE_WARNING_TEMP,
    HEATSTROKE_SEVERE_TEMP,
    COLD_WARNING_TEMP,
)""",
        "constants": ["HEATSTROKE_WARNING_TEMP", "HEATSTROKE_SEVERE_TEMP", "COLD_WARNING_TEMP"],
        "updated_import": "from src.config.config import get_weather_constants\n\n# In __init__ method:\nweather_constants = get_weather_constants()\nself.HEATSTROKE_WARNING_TEMP = weather_constants.HEATSTROKE_WARNING_TEMP\nself.HEATSTROKE_SEVERE_TEMP = weather_constants.HEATSTROKE_SEVERE_TEMP\nself.COLD_WARNING_TEMP = weather_constants.COLD_WARNING_TEMP"
    },
    {
        "path": "src/utils/validators/weather_specific/weather_condition_validator.py",
        "line": 8,
        "current_import": "from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS",
        "constants": ["SUNNY_WEATHER_KEYWORDS"],
        "updated_import": "from src.config.config import get_weather_constants\n\n# In __init__ method:\nweather_constants = get_weather_constants()\nself.SUNNY_WEATHER_KEYWORDS = weather_constants.SUNNY_WEATHER_KEYWORDS"
    },
    {
        "path": "src/utils/validators/weather_specific/consistency_validator.py",
        "line": 7,
        "current_import": "from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS",
        "constants": ["SUNNY_WEATHER_KEYWORDS"],
        "updated_import": "from src.config.config import get_weather_constants\n\n# In __init__ method:\nweather_constants = get_weather_constants()\nself.SUNNY_WEATHER_KEYWORDS = weather_constants.SUNNY_WEATHER_KEYWORDS"
    }
]

def print_update_details():
    """Print detailed update information for each file"""
    print("=" * 80)
    print("WEATHER CONSTANTS IMPORT UPDATE GUIDE")
    print("=" * 80)
    print()
    
    for file_info in files_to_update:
        print(f"FILE: {file_info['path']}")
        print("-" * 80)
        
        # Print current import information
        if 'line' in file_info:
            print(f"Current import (line {file_info['line']}):")
        else:
            print(f"Current import (lines {file_info['lines']}):")
        print(f"  {file_info['current_import']}")
        print()
        
        # Print constants being imported
        print("Constants being imported:")
        for const in file_info['constants']:
            print(f"  - {const}")
        
        # Print additional imports if any
        if 'additional_imports' in file_info:
            print("\nAdditional imports found:")
            for imp in file_info['additional_imports']:
                print(f"  Line {imp['line']}: {imp['import']}")
                print(f"    Constants: {', '.join(imp['constants'])}")
        
        print()
        
        # Print the updated import statement
        print("Updated import and usage:")
        print("```python")
        print(file_info['updated_import'])
        print("```")
        print()
        
        # Add specific notes for each file
        if "validation.py" in file_info['path']:
            print("Note: Use WEATHER_CHANGE_THRESHOLD directly as a module-level constant")
            print("      or access via self.weather_constants.WEATHER_CHANGE_THRESHOLD in methods")
        elif "weather_timeline_formatter.py" in file_info['path']:
            print("Note: Access via self.weather_constants.WEATHER_CHANGE_THRESHOLD in methods")
        elif "weather_validator.py" in file_info['path']:
            print("Note: This file also imports PrecipitationThresholds - include all constants in __init__")
        elif "temperature_condition_validator.py" in file_info['path']:
            print("Note: Store constants as instance variables for use in validation methods")
        elif "weather_condition_validator.py" in file_info['path'] or "consistency_validator.py" in file_info['path']:
            print("Note: Store SUNNY_WEATHER_KEYWORDS as instance variable")
        
        print()
        print("=" * 80)
        print()

def generate_update_script():
    """Generate a script that can automatically update the files"""
    script_content = '''#!/usr/bin/env python3
"""
Auto-generated script to update weather_constants imports.
Run this script to automatically update all files.
"""

import re
from pathlib import Path

updates = {
    "src/nodes/comment_selector/validation.py": {
        "old": "from src.config.weather_constants import WEATHER_CHANGE_THRESHOLD",
        "new": "from src.config.config import get_weather_constants",
        "additional_code": "\\n# Get weather constants\\nweather_constants = get_weather_constants()\\nWEATHER_CHANGE_THRESHOLD = weather_constants.WEATHER_CHANGE_THRESHOLD\\n"
    },
    # Add more files here...
}

def update_file(filepath, old_import, new_import, additional_code=""):
    """Update a single file"""
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return
    
    content = path.read_text()
    
    # Replace the import
    updated_content = content.replace(old_import, new_import)
    
    # Add additional code if needed
    if additional_code and new_import in updated_content:
        # Find where to insert the additional code
        lines = updated_content.split('\\n')
        for i, line in enumerate(lines):
            if new_import in line:
                # Insert after the import
                lines.insert(i + 1, additional_code)
                break
        updated_content = '\\n'.join(lines)
    
    # Write back
    path.write_text(updated_content)
    print(f"Updated: {filepath}")

# Run updates
for filepath, update_info in updates.items():
    update_file(filepath, update_info["old"], update_info["new"], update_info.get("additional_code", ""))
'''
    
    with open('auto_update_imports.py', 'w') as f:
        f.write(script_content)
    print("\nGenerated auto_update_imports.py for automatic updates")

if __name__ == "__main__":
    print_update_details()
    
    # Optionally generate the auto-update script
    # generate_update_script()