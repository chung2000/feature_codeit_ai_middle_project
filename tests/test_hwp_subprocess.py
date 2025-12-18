import subprocess
import os

file_path = "data/files/국가과학기술지식정보서비스_통합정보시스템 고도화 용역.hwp"

# Check if file exists
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    # Try finding any hwp file
    files = [f for f in os.listdir("data/files") if f.endswith(".hwp")]
    if files:
        file_path = os.path.join("data/files", files[0])
        print(f"Using alternative file: {file_path}")
    else:
        print("No HWP files found.")
        exit(1)

try:
    print(f"Extracting verification from {file_path}...")
    # Assume hwp5txt is in PATH if running from venv
    # If not, we might need to specify full path. 
    # For this test, let's try just 'hwp5txt'
    result = subprocess.run(
        ["/home/soobeom/SB-venv/bin/hwp5txt", file_path],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    
    if result.returncode == 0:
        print("Success!")
        print("Preview:")
        print(result.stdout[:500])
    else:
        print("Failed with return code", result.returncode)
        print("Stderr:", result.stderr)
        
except Exception as e:
    print(f"Exception: {e}")
