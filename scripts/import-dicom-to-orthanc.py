#!/usr/bin/env python3
"""
Script to import DICOM files from volumes/orthanc-data (raw source) into Orthanc server.
This script reads the raw DICOM files and imports them into Orthanc database 
(stored in volumes-db/orthanc-data) via its REST API.
"""

import os
import json
import requests
from pathlib import Path
import time

# Configuration
ORTHANC_URL = "http://localhost:8042"
SOURCE_PATH = Path("./volumes/orthanc-data")  # Raw DICOM files (source)
METADATA_FILE = SOURCE_PATH / "dicom_metadata.json"

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

def discover_dicom_files(source_path):
    """Discover all DICOM files in the source directory."""
    dicom_files = []
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if file.endswith('.dcm'):
                file_path = Path(root) / file
                dicom_files.append({'filename': str(file_path.relative_to(source_path))})
    return dicom_files

def main():
    print("🔄 Importing DICOM files to Orthanc...")
    print(f"📁 Source path: {SOURCE_PATH}")
    print(f"🌐 Orthanc URL: {ORTHANC_URL}")
    
    # Try to load metadata file, or discover files if it doesn't exist
    if METADATA_FILE.exists():
        print(f"📋 Loading metadata from: {METADATA_FILE}")
        try:
            with open(METADATA_FILE, 'r') as f:
                dicom_files = json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading metadata file: {e}")
            print("🔍 Falling back to directory scan...")
            dicom_files = discover_dicom_files(SOURCE_PATH)
    else:
        print(f"ℹ️  Metadata file not found, scanning directory for DICOM files...")
        dicom_files = discover_dicom_files(SOURCE_PATH)
    
    if not dicom_files:
        print("❌ No DICOM files found to import")
        return
    
    print(f"📊 Found {len(dicom_files)} DICOM files to import")
    
    # Import each DICOM file
    total_files = len(dicom_files)
    successful_imports = 0
    failed_imports = 0
    
    for i, dicom_info in enumerate(dicom_files, 1):
        # Handle both 'filename' and 'dest_path' metadata formats
        if 'filename' in dicom_info:
            file_path = SOURCE_PATH / dicom_info['filename']
        elif 'dest_path' in dicom_info:
            dest_path = Path(dicom_info['dest_path'])
            # If dest_path is absolute, try to make it relative to SOURCE_PATH
            if dest_path.is_absolute():
                # Extract the relative part after 'volumes/orthanc-data'
                try:
                    # Find where 'volumes/orthanc-data' or 'orthanc-data' appears in the path
                    path_parts = dest_path.parts
                    if 'orthanc-data' in path_parts:
                        orthanc_idx = path_parts.index('orthanc-data')
                        relative_parts = path_parts[orthanc_idx + 1:]
                        file_path = SOURCE_PATH / Path(*relative_parts)
                    else:
                        # Fall back to using filename from path
                        file_path = SOURCE_PATH / dest_path.name
                except Exception as e:
                    print(f"⚠️  Could not convert absolute path, using filename: {e}")
                    file_path = SOURCE_PATH / dest_path.name
            else:
                file_path = SOURCE_PATH / dest_path
        else:
            print(f"❌ No filename or dest_path in metadata entry: {dicom_info}")
            failed_imports += 1
            continue
            
        print(f"📤 [{i}/{total_files}] Importing: {file_path.name}")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            failed_imports += 1
            continue
        
        # Import the DICOM file
        success, result = import_dicom_file(file_path)
        if success:
            successful_imports += 1
            print(f"✅ Imported successfully")
        else:
            failed_imports += 1
            print(f"❌ Import failed: {result}")
    
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
