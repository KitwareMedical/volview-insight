#!/usr/bin/env python3
"""
Script to import DICOM files from volumes/orthanc-data into Orthanc server.
This script reads the DICOM files that were copied by the notebook and 
imports them into Orthanc via its REST API.
"""

import os
import json
import requests
from pathlib import Path
import time

# Configuration
ORTHANC_URL = "http://localhost:8042"
VOLUME_PATH = Path("./volumes/orthanc-data")
METADATA_FILE = VOLUME_PATH / "dicom_metadata.json"

def import_dicom_file(file_path):
    """Import a single DICOM file to Orthanc."""
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{ORTHANC_URL}/instances",
                headers={'Content-Type': 'application/dicom'},
                data=f
            )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def main():
    print("🔄 Importing DICOM files to Orthanc...")
    print(f"📁 Volume path: {VOLUME_PATH}")
    print(f"🌐 Orthanc URL: {ORTHANC_URL}")
    
    # Check if metadata file exists
    if not METADATA_FILE.exists():
        print(f"❌ Metadata file not found: {METADATA_FILE}")
        print("Please run the notebook first to create the DICOM files.")
        return
    
    # Load metadata
    with open(METADATA_FILE, 'r') as f:
        dicom_files = json.load(f)
    
    print(f"📊 Found {len(dicom_files)} DICOM files to import")
    
    # Import files
    successful_imports = 0
    failed_imports = 0
    
    for i, file_info in enumerate(dicom_files):
        file_path = Path(file_info['dest_path'])
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            failed_imports += 1
            continue
        
        print(f"📤 Importing {i+1}/{len(dicom_files)}: {file_path.name}")
        
        success, result = import_dicom_file(file_path)
        
        if success:
            print(f"   ✅ Success: {result.get('ID', 'Unknown ID')}")
            successful_imports += 1
        else:
            print(f"   ❌ Failed: {result}")
            failed_imports += 1
        
        # Small delay to avoid overwhelming Orthanc
        time.sleep(0.1)
    
    print(f"\n🎉 Import complete!")
    print(f"✅ Successful imports: {successful_imports}")
    print(f"❌ Failed imports: {failed_imports}")
    
    # Check final status
    try:
        response = requests.get(f"{ORTHANC_URL}/patients")
        if response.status_code == 200:
            patients = response.json()
            print(f"👥 Total patients in Orthanc: {len(patients)}")
            
            if patients:
                print("📋 Patient IDs:")
                for patient_id in patients:
                    print(f"   - {patient_id}")
        else:
            print(f"⚠️  Could not check patient count: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not check patient count: {e}")

if __name__ == "__main__":
    main()
