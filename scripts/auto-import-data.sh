#!/bin/bash

# Auto-import script for VolView Insight
# This script waits for services to be ready and then imports DICOM and FHIR data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ORTHANC_URL="${ORTHANC_URL:-http://localhost:8042}"
HAPI_FHIR_URL="${HAPI_FHIR_URL:-http://localhost:3000/hapi-fhir-jpaserver/fhir}"
HAPI_FHIR_HEALTH_URL="${HAPI_FHIR_HEALTH_URL:-http://localhost:3000/hapi-fhir-jpaserver/fhir/metadata}"
MAX_RETRIES=30
RETRY_INTERVAL=10

echo -e "${BLUE}🚀 Starting VolView Insight Auto-Import Process${NC}"
echo "=================================================="

# Function to check if a service is ready
check_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        echo -e "${YELLOW}   Attempt $retries/$MAX_RETRIES - $service_name not ready yet, waiting ${RETRY_INTERVAL}s...${NC}"
        sleep $RETRY_INTERVAL
    done
    
    echo -e "${RED}❌ $service_name failed to become ready after $MAX_RETRIES attempts${NC}"
    return 1
}

# Function to run import script
run_import_script() {
    local script_name=$1
    local description=$2
    
    echo -e "${BLUE}📤 $description${NC}"
    echo "----------------------------------------"
    
    if python3 "$script_name"; then
        echo -e "${GREEN}✅ $description completed successfully${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Checking service availability...${NC}"
    
    # Check Orthanc
    if ! check_service "$ORTHANC_URL" "Orthanc"; then
        echo -e "${RED}❌ Cannot proceed without Orthanc${NC}"
        exit 1
    fi
    
    # Check HAPI FHIR
    if ! check_service "$HAPI_FHIR_HEALTH_URL" "HAPI FHIR"; then
        echo -e "${RED}❌ Cannot proceed without HAPI FHIR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🎉 All services are ready!${NC}"
    echo ""
    
    # Check if data exists
    if [ ! -d "./volumes/orthanc-data" ] || [ ! -d "./volumes/hapi-fhir-data" ]; then
        echo -e "${YELLOW}⚠️  Volume directories not found. Please run the Jupyter notebook first to generate data.${NC}"
        echo -e "${YELLOW}   Expected directories:${NC}"
        echo -e "${YELLOW}   - ./volumes/orthanc-data${NC}"
        echo -e "${YELLOW}   - ./volumes/hapi-fhir-data${NC}"
        exit 1
    fi
    
    # Count existing data
    dicom_count=$(find ./volumes/orthanc-data -name "*.dcm" 2>/dev/null | wc -l)
    fhir_count=$(find ./volumes/hapi-fhir-data -name "*.json" 2>/dev/null | wc -l)
    
    echo -e "${BLUE}📊 Data Summary:${NC}"
    echo -e "   DICOM files: $dicom_count"
    echo -e "   FHIR files: $fhir_count"
    echo ""
    
    if [ "$dicom_count" -eq 0 ] && [ "$fhir_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No data found in volume directories. Please run the Jupyter notebook first.${NC}"
        exit 1
    fi
    
    # Import DICOM data
    if [ "$dicom_count" -gt 0 ]; then
        run_import_script "./scripts/import-dicom-to-orthanc.py" "Importing DICOM data to Orthanc"
    else
        echo -e "${YELLOW}⚠️  No DICOM files found, skipping DICOM import${NC}"
    fi
    
    # Import FHIR data
    if [ "$fhir_count" -gt 0 ]; then
        run_import_script "./scripts/import-fhir-to-hapi.py" "Importing FHIR data to HAPI FHIR"
    else
        echo -e "${YELLOW}⚠️  No FHIR files found, skipping FHIR import${NC}"
    fi
    
    echo -e "${GREEN}🎉 Auto-import process completed successfully!${NC}"
    echo -e "${BLUE}🌐 You can now access:${NC}"
    echo -e "   VolView Insight: http://localhost:8080/"
    echo -e "   Orthanc: http://localhost:8042/"
    echo -e "   HAPI FHIR: http://localhost:3000/hapi-fhir-jpaserver/fhir/"
}

# Run main function
main "$@"
