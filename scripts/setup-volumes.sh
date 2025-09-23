#!/bin/bash
set -e

echo "🚀 Setting up VolView Insight volumes..."

# Create volume directories
echo "📁 Creating volume directories..."
mkdir -p volumes/orthanc-data/{db,index,storage}
mkdir -p volumes/hapi-fhir-data/{fhir,database}
mkdir -p volumes/model-cache/{huggingface,monai,medgemma}

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 volumes/orthanc-data
chmod 755 volumes/hapi-fhir-data
chmod 755 volumes/model-cache

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    if [ -f ".env.example" ]; then
        echo "📋 Copying .env.example to .env..."
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your configuration."
    else
        echo "❌ .env.example not found. Please create .env file manually."
    fi
fi

echo "✅ Volume setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your configuration"
echo "   2. Run: ./scripts/start-dev.sh (for development)"
echo "   3. Or run: docker-compose up -d (for production)"
echo ""
echo "📊 Volume structure created:"
echo "   📁 volumes/orthanc-data/     - DICOM files and Orthanc database"
echo "   📁 volumes/hapi-fhir-data/  - FHIR resources and HAPI database"
echo "   📁 volumes/model-cache/     - AI model cache (medGemma, MONAI, etc.)"
