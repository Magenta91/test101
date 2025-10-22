"""
Context Enhancement Configuration
"""

import os
from typing import Literal

# Configuration options
CONTEXT_MODE = os.environ.get("CONTEXT_MODE", "optimized")  # "fast", "optimized", "full", "off"

def get_context_mode() -> Literal["fast", "optimized", "full", "off"]:
    """Get the current context enhancement mode"""
    return CONTEXT_MODE

def set_context_mode(mode: Literal["fast", "optimized", "full", "off"]):
    """Set the context enhancement mode"""
    global CONTEXT_MODE
    CONTEXT_MODE = mode

# Mode descriptions
MODE_DESCRIPTIONS = {
    "fast": "Process only 3-5 most important fields (Revenue, Profit, etc.) - ~10-20 seconds",
    "optimized": "Batch process all fields efficiently - ~30-60 seconds", 
    "full": "Process all fields individually with full context - ~60-120 seconds",
    "off": "Skip context enhancement entirely - ~3-5 seconds"
}

def print_mode_info():
    """Print information about available modes"""
    print("Available Context Enhancement Modes:")
    for mode, description in MODE_DESCRIPTIONS.items():
        current = " (CURRENT)" if mode == CONTEXT_MODE else ""
        print(f"  {mode}: {description}{current}")
    print(f"\nTo change mode: set CONTEXT_MODE environment variable or use set_context_mode()")
    print(f"Current mode: {CONTEXT_MODE}")

if __name__ == "__main__":
    print_mode_info()