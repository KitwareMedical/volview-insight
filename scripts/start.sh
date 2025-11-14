#!/bin/bash
set -e

# Parse command line arguments
BACKGROUND=false
FORCE_BUILD=false
if [[ "$1" == "-d" ]] || [[ "$1" == "--detach" ]]; then
    BACKGROUND=true
fi
if [[ "$1" == "--build" ]] || [[ "$2" == "--build" ]]; then
    FORCE_BUILD=true
fi

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

# Check if images exist to determine if this is first run
# Look for any of the custom-built images (backend, frontend, or proxy)
IMAGES_EXIST=false
if docker images | grep -q "\-backend.*latest" || \
   docker images | grep -q "\-volview-insight-web.*latest" || \
   docker images | grep -q "\-orthanc-proxy.*latest"; then
    IMAGES_EXIST=true
fi

# Determine if we should build
BUILD_FLAG=""
if [ "$FORCE_BUILD" = true ]; then
    BUILD_FLAG="--build"
    echo "🔨 Building images (--build flag specified)..."
elif [ "$IMAGES_EXIST" = false ]; then
    BUILD_FLAG="--build"
    echo "🔨 Building images (first run detected)..."
else
    echo "♻️  Using existing images (fast start)"
    echo "   To rebuild: ./scripts/start.sh --build"
fi

echo ""

# Show startup information
echo "🌐 Access points (once services are ready):"
echo "   - Frontend (Vite dev): http://localhost:8080"
echo "   - Backend API: http://localhost:4014"
echo "   - Orthanc DICOM: http://localhost:8042"
echo "   - HAPI FHIR: http://localhost:3000/hapi-fhir-jpaserver/fhir/"
echo "   - Orthanc Proxy: http://localhost:5173"
echo ""

# Auto-import data reminder
if [ -d "./volumes/orthanc-data" ] && [ -d "./volumes/hapi-fhir-data" ]; then
    echo "� Data import reminder:"
    echo "   After services start, run: ./scripts/auto-import-data.sh"
    echo ""
fi

# Start services
if [ "$BACKGROUND" = true ]; then
    echo "🐳 Starting Docker services in background..."
    echo ""
    docker-compose up -d $BUILD_FLAG
    echo ""
    echo "✅ Services started in background!"
    echo ""
    echo "📊 Management commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - View specific service: docker-compose logs -f [service-name]"
    echo "   - Stop services: ./scripts/stop.sh"
    echo "   - Check status: docker-compose ps"
else
    echo "🐳 Starting Docker services (foreground mode with live logs)..."
    echo "   Press Ctrl+C to stop all services"
    echo ""
    docker-compose up $BUILD_FLAG
fi
