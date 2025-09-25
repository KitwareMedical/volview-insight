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

# Download MONAI lung segmentation model
echo "🤖 Downloading MONAI lung segmentation model..."
MODEL_PATH="volumes/model-cache/segmentLungsModel-v1.0.ckpt"
if [ ! -f "$MODEL_PATH" ]; then
    echo "   Downloading segmentLungsModel-v1.0.ckpt (336MB)..."
    curl -L https://data.kitware.com/api/v1/file/65bd8c2f03c3115909f73dd7/download --output "$MODEL_PATH"
    echo "✅ MONAI model downloaded successfully!"
else
    echo "✅ MONAI model already exists, skipping download."
fi

# Download MedGemma model (requires HF_TOKEN)
echo "🧠 Setting up MedGemma model..."
MEDGEMMA_DIR="volumes/model-cache/medgemma"
if [ ! -d "$MEDGEMMA_DIR/google--medgemma-4b-it" ]; then
    echo "   MedGemma model will be downloaded on first use with HF_TOKEN"
    echo "   Make sure to set HF_TOKEN in your .env file"
    echo "   Model: google/medgemma-4b-it (~8GB)"
else
    echo "✅ MedGemma model already exists, skipping download."
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
echo "   📁 volumes/orthanc-data/     - DICOM files and Orthanc database"
echo "   📁 volumes/hapi-fhir-data/  - FHIR resources and HAPI database"
echo "   📁 volumes/model-cache/     - AI model cache (medGemma, MONAI, etc.)"
echo "      ├── segmentLungsModel-v1.0.ckpt - MONAI lung segmentation model"
echo "      └── medgemma/ - MedGemma multimodal model (downloaded on first use)"
