#!/usr/bin/env python3
"""
Nova Apply - Main Entry Point
Run: python run.py [command] [options]
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.scheduler import main

if __name__ == "__main__":
    main()
