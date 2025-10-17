#!/bin/bash
set -e

echo "🚀 Setting up VolView Insight volumes..."

# Create source data directories (raw files)
echo "📁 Creating source data directories..."
mkdir -p volumes/orthanc-data 2>/dev/null || true
mkdir -p volumes/hapi-fhir-data 2>/dev/null || true

# Create Docker database volume directories
echo "📁 Creating Docker database volume directories..."
mkdir -p volumes-db/orthanc-data 2>/dev/null || true
mkdir -p volumes-db/hapi-fhir-data 2>/dev/null || true
mkdir -p volumes-db/model-cache/{huggingface,monai,medgemma} 2>/dev/null || true

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 volumes/orthanc-data
chmod 755 volumes/hapi-fhir-data
chmod 755 volumes-db/orthanc-data
chmod 755 volumes-db/hapi-fhir-data
chmod 755 volumes-db/model-cache

# Download MONAI lung segmentation model
echo "🤖 Downloading MONAI lung segmentation model..."
MODEL_PATH="volumes-db/model-cache/segmentLungsModel-v1.0.ckpt"
if [ ! -f "$MODEL_PATH" ]; then
    echo "   Downloading segmentLungsModel-v1.0.ckpt (336MB)..."
    curl -L https://data.kitware.com/api/v1/file/65bd8c2f03c3115909f73dd7/download --output "$MODEL_PATH"
    echo "✅ MONAI model downloaded successfully!"
else
    echo "✅ MONAI model already exists, skipping download."
fi

# Setup MedGemma model (gated repository - downloads on first use)
echo "🧠 Setting up MedGemma model..."
MEDGEMMA_DIR="volumes-db/model-cache/medgemma"
if [ ! -d "$MEDGEMMA_DIR/google--medgemma-4b-it" ]; then
    echo "   MedGemma model will be downloaded on first use"
    echo "   Model: google/medgemma-4b-it (~8GB, gated repository)"
    echo "   Make sure to:"
    echo "   1. Set HF_TOKEN in your .env file"
    echo "   2. Request access at: https://huggingface.co/google/medgemma-4b-it"
    echo "   3. Ensure your token has gated repository permissions"
else
    echo "✅ MedGemma model already exists, skipping setup."
fi

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
echo "   📁 volumes/orthanc-data/      - Raw DICOM files (source for import)"
echo "   📁 volumes/hapi-fhir-data/   - Raw FHIR resources (source for import)" 
echo "   📁 volumes-db/orthanc-data/  - Orthanc database (Docker volume)"
echo "   📁 volumes-db/hapi-fhir-data/- HAPI FHIR database (Docker volume)"
echo "   📁 volumes-db/model-cache/   - AI model cache (medGemma, MONAI, etc.)"
echo "      ├── segmentLungsModel-v1.0.ckpt - MONAI lung segmentation model"
echo "      └── medgemma/ - MedGemma multimodal model (downloaded on first use)"
