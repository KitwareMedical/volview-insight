#!/bin/bash
set -e

echo "🚀 Starting VolView Insight..."
echo "   Frontend: Vite dev server with hot reloading"
echo "   API calls: Direct to backend services"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📋 Please run: ./scripts/setup-volumes.sh first"
    exit 1
fi

# Check if volumes are set up
if [ ! -d "volumes/orthanc-data" ]; then
    echo "❌ Volume directories not found!"
    echo "📋 Please run: ./scripts/setup-volumes.sh first"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "📋 Please start Docker first"
    exit 1
fi

echo "✅ Pre-flight checks passed!"
echo ""

# Start services
echo "🐳 Starting Docker services..."
docker-compose up --build

# In development mode, services run in foreground with logs
# The script will continue running and showing logs
# Press Ctrl+C to stop all services

echo ""
echo "🎉 VolView Insight started!"
echo ""
echo "🌐 Access points:"
echo "   - Frontend (Vite dev): http://localhost:8080"
echo "   - Backend API: http://localhost:4014"
echo "   - Orthanc DICOM: http://localhost:8042"
echo "   - HAPI FHIR: http://localhost:3000/hapi-fhir-jpaserver"
echo "   - Orthanc Proxy: http://localhost:5173"
echo ""
echo "🔄 Features:"
echo "   - ✅ Hot reloading enabled"
echo "   - ✅ Source code mounted for live updates"
echo "   - ✅ Direct API access (no proxy)"
echo ""
echo "📊 Management:"
echo "   - Stop: Press Ctrl+C"
echo "   - View specific logs: docker-compose logs -f [service-name]"
echo "   - Run in background: Add -d flag to docker-compose command"

# Note: Removed service health checks since we're running in foreground
# Services will show their startup logs directly

# Auto-import data if available
echo "📥 Checking for data to import..."
if [ -d "./volumes/orthanc-data" ] && [ -d "./volumes/hapi-fhir-data" ]; then
    echo "   Data volumes found with existing data"
    echo "   To import data: ./scripts/auto-import-data.sh"
else
    echo "   No data found in volumes directory"
    echo "   To import data later, run: ./scripts/auto-import-data.sh"
fi
echo ""

# Note: The docker-compose command above will run in foreground
# showing all service logs. The script will block here until Ctrl+C is pressed.
