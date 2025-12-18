try:
    from hwp5.hwp5txt import Hwp5Txt
    print("Successfully imported Hwp5Txt")
except ImportError:
    print("Failed to import Hwp5Txt. Trying alternative...")

import sys
import os

# Create a dummy HWP file check or just check imports for now? 
# We don't have a dummy HWP easily created, but we can check existing data if available.

def test_extraction(file_path):
    try:
        # hwp5txt usage usually requires a file object or path
        # It typically prints to stdout, so we might need to capture it if using the class directly
        # Or check if there is a cleaner API.
        pass
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Check if we can access the library
    try:
        import hwp5.utils
        print("hwp5.utils imported")
    except ImportError as e:
        print(f"hwp5 import error: {e}")
