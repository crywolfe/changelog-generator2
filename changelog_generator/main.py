import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from changelog_generator import main as changelog_main

def main():
    changelog_main()

if __name__ == '__main__':
    main()