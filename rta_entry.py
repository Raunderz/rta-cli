#!/usr/bin/env python3
import sys
import os

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kon.cli import main

if __name__ == '__main__':
    main()
