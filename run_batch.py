#!/usr/bin/env python
"""Convenience script to run batch processing with predefined credentials."""

import subprocess
import sys
from pathlib import Path

# Your Google Sheets credentials
CREDENTIALS = r"C:\Users\TrendAgency\Downloads\claude-agents-487515-27f459372fd6.json"
SHEET_ID = "1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA"

# Optional parameters (customize as needed)
WORKSHEET_NAME = None  # Use first sheet if None
DELAY = 5  # Seconds between brands
UPDATE_SHEET = True  # Update Google Sheet with status

def main():
    """Run batch processing."""
    print("=" * 60)
    print("Brand Intelligence Agent - Batch Processing")
    print("پردازش دسته‌ای برندها")
    print("=" * 60)
    print()

    # Check if credentials file exists
    if not Path(CREDENTIALS).exists():
        print(f"❌ ERROR: Credentials file not found: {CREDENTIALS}")
        print("Please update CREDENTIALS path in run_batch.py")
        sys.exit(1)

    # Build command
    cmd = [
        sys.executable,
        "batch_process_brands.py",
        "--credentials", CREDENTIALS,
        "--sheet-id", SHEET_ID,
        "--delay", str(DELAY)
    ]

    if WORKSHEET_NAME:
        cmd.extend(["--worksheet", WORKSHEET_NAME])

    if not UPDATE_SHEET:
        cmd.append("--no-update")

    # Run batch processing
    try:
        subprocess.run(cmd, check=True)
        print()
        print("=" * 60)
        print("✅ Processing Complete!")
        print("✅ پردازش تکمیل شد!")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print(f"❌ Error occurred: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
