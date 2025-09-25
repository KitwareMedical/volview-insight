#!/bin/bash
set -e

echo "🚀 Starting VolView Insight in development mode..."

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
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "🔍 Checking service status..."

# Check Orthanc
if curl -f http://localhost:8042/system >/dev/null 2>&1; then
    echo "✅ Orthanc is running at http://localhost:8042"
else
    echo "⚠️  Orthanc may still be starting..."
fi

# Check HAPI FHIR
if curl -f http://localhost:3000/hapi-fhir-jpaserver/fhir/metadata >/dev/null 2>&1; then
    echo "✅ HAPI FHIR is running at http://localhost:3000/hapi-fhir-jpaserver/fhir/"
else
    echo "⚠️  HAPI FHIR may still be starting..."
fi

# Check Backend
if curl -f http://localhost:4014 >/dev/null 2>&1; then
    echo "✅ Backend is running at http://localhost:4014"
else
    echo "⚠️  Backend may still be starting..."
fi

# Check Frontend
if curl -f http://localhost:8080 >/dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:8080"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "🎉 VolView Insight is starting up!"
echo ""
echo "🌐 Access points:"
echo "   - Frontend: http://localhost:8080"
echo "   - Backend: http://localhost:4014"
echo "   - Orthanc: http://localhost:8042"
echo "   - HAPI FHIR: http://localhost:3000/hapi-fhir-jpaserver/fhir/"
echo "   - Orthanc Proxy: http://localhost:5173"
echo ""
echo "📊 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo "   - Import data manually: ./scripts/auto-import-data.sh"
echo ""
echo "⏳ Services may take a few minutes to fully initialize..."
echo "   Check the logs if any service doesn't respond: docker-compose logs [service-name]"
echo ""
echo "📥 Auto-import: Checking for data to import..."

# Check if data exists and run auto-import
if [ -d "./volumes/orthanc-data" ] && [ -d "./volumes/hapi-fhir-data" ]; then
    echo "   Found data in volumes, running auto-import..."
    echo "   This may take a few minutes..."
    ./scripts/auto-import-data.sh
    echo ""
    echo "✅ Auto-import completed!"
else
    echo "   No data found in volumes directory"
    echo "   To import data later, run: ./scripts/auto-import-data.sh"
fi
echo ""
