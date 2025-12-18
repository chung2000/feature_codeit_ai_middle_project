import sys
import os

print("Sys Path:", sys.path)
import site
print("Site Packages:", site.getsitepackages())

# List all folders in site-packages
for path in site.getsitepackages():
    if os.path.exists(path):
        print(f"Listing {path}:")
        try:
            items = os.listdir(path)
            for item in items:
                if 'hwp' in item:
                    print(f"  Found: {item}")
        except Exception as e:
            print(e)
