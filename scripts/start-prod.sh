#!/bin/bash
set -e

echo "🚀 Starting VolView Insight in production mode..."
echo "   Frontend: nginx serving optimized static files"
echo "   API calls: Proxied through nginx"

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

# Start services in production mode
echo "🐳 Starting Docker services in production mode..."
echo "   Using: docker-compose.yml + docker-compose.prod.yml"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

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
    echo "✅ HAPI FHIR is running at http://localhost:3000"
else
    echo "⚠️  HAPI FHIR may still be starting..."
fi

# Check Backend
if curl -f http://localhost:4014 >/dev/null 2>&1; then
    echo "✅ Backend is running at http://localhost:4014"
else
    echo "⚠️  Backend may still be starting..."
fi

# Check Frontend (nginx)
if curl -f http://localhost:8080 >/dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:8080"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "🎉 VolView Insight production deployment complete!"
echo ""
echo "🌐 Production access:"
echo "   - Application: http://localhost:8080"
echo "   - All APIs: Proxied through nginx at /api/, /dicom-web/, /fhir/"
echo ""
echo "🏭 Production Features:"
echo "   - ✅ Optimized static file serving"
echo "   - ✅ API proxying with CORS headers"
echo "   - ✅ Gzip compression enabled"
echo "   - ✅ Static asset caching"
echo "   - ✅ Services running in background"
echo ""
echo "📊 Management commands:"
echo "   - View logs: docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "   - Stop services: docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo "   - Restart services: docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart"
echo "   - Import data: ./scripts/auto-import-data.sh"
echo ""
echo "⏳ Services may take a few minutes to fully initialize..."
echo "   Check logs if any service doesn't respond: docker-compose logs [service-name]"
echo ""

# Auto-import data if available
echo "📥 Checking for data to import..."
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
echo "🎯 Production deployment ready! Access your application at:"
echo "   👉 http://localhost:8080"
echo ""
