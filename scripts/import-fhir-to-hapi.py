#!/usr/bin/env python3
"""
Script to import FHIR resources from volumes/hapi-fhir-data (raw source) into HAPI FHIR server.
This script reads the raw FHIR JSON files and imports them into HAPI FHIR database
(stored in volumes-db/hapi-fhir-data) via its REST API.
"""

import os
import json
import requests
from pathlib import Path
import time

# Configuration
HAPI_FHIR_URL = "http://localhost:3000/hapi-fhir-jpaserver/fhir"
SOURCE_PATH = Path("./volumes/hapi-fhir-data")  # Raw FHIR files (source)

def import_fhir_resource(resource_json):
    """Import a single FHIR resource to HAPI FHIR."""
    try:
        resource_type = resource_json.get('resourceType')
        resource_id = resource_json.get('id')
        
        if not resource_type or not resource_id:
            return False, "Missing resourceType or id"
        
        # Use PUT to create/update with specific ID
        url = f"{HAPI_FHIR_URL}/{resource_type}/{resource_id}"
        
        response = requests.put(
            url,
            headers={
                'Content-Type': 'application/fhir+json',
                'Accept': 'application/fhir+json'
            },
            json=resource_json
        )
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def main():
    print("🔄 Importing FHIR resources to HAPI FHIR server...")
    print(f"📁 Source path: {SOURCE_PATH}")
    print(f"🌐 HAPI FHIR URL: {HAPI_FHIR_URL}")
    
    if not SOURCE_PATH.exists():
        print(f"❌ Source path not found: {SOURCE_PATH}")
        return
    
    # Import patients first
    patients_file = SOURCE_PATH / "patients.json"
    if patients_file.exists():
        print(f"📤 Importing patients from {patients_file.name}")
        
        with open(patients_file, 'r') as f:
            patients = json.load(f)
        
        successful_patients = 0
        failed_patients = 0
        
        for i, patient in enumerate(patients):
            print(f"   📤 Importing patient {i+1}/{len(patients)}: {patient.get('id', 'Unknown ID')}")
            
            success, result = import_fhir_resource(patient)
            
            if success:
                print(f"      ✅ Success")
                successful_patients += 1
            else:
                print(f"      ❌ Failed: {result}")
                failed_patients += 1
            
            time.sleep(0.1)  # Small delay
        
        print(f"👥 Patients: {successful_patients} successful, {failed_patients} failed")
    
    # Import other resources
    resource_dirs = [d for d in SOURCE_PATH.iterdir() if d.is_dir()]
    
    total_resources_saved = 0
    total_resources_failed = 0
    
    for resource_dir in resource_dirs:
        resource_type = resource_dir.name
        resource_file = resource_dir / f"{resource_type}.json"
        
        if not resource_file.exists():
            continue
        
        print(f"\n📤 Importing {resource_type} from {resource_file.name}")
        
        with open(resource_file, 'r') as f:
            resources = json.load(f)
        
        successful_resources = 0
        failed_resources = 0
        
        for i, resource in enumerate(resources):
            if i % 100 == 0:  # Progress every 100 resources
                print(f"   📤 Importing {resource_type} {i+1}/{len(resources)}")
            
            success, result = import_fhir_resource(resource)
            
            if success:
                successful_resources += 1
            else:
                failed_resources += 1
                if failed_resources <= 5:  # Show first 5 errors
                    print(f"      ❌ Failed: {result}")
            
            time.sleep(0.01)  # Small delay
        
        print(f"   ✅ {resource_type}: {successful_resources} successful, {failed_resources} failed")
        total_resources_saved += successful_resources
        total_resources_failed += failed_resources
    
    print(f"\n🎉 Import complete!")
    print(f"✅ Total successful imports: {total_resources_saved}")
    print(f"❌ Total failed imports: {total_resources_failed}")
    
    # Check final status
    try:
        response = requests.get(f"{HAPI_FHIR_URL}/Patient")
        if response.status_code == 200:
            bundle = response.json()
            patient_count = bundle.get('total', 0)
            print(f"👥 Total patients in HAPI FHIR: {patient_count}")
        else:
            print(f"⚠️  Could not check patient count: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not check patient count: {e}")

if __name__ == "__main__":
    main()
