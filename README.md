# VolView Insight

<img src="volview-insight/resources/logo-remove-bg.png" alt="VolView Insight logo" width="300"/>

![VolView Insight Screenshot](./volview-insight/resources/example_screenshot.jpg)

---

## 📖 About

**VolView Insight** is an open-source platform that unifies **medical imaging**
and **clinical data** into one extensible interface. It provides researchers
with a realistic testbed for **developing, testing, and extending multimodal
models** in settings that mirror clinical reality.  

### Highlights

- 🔬 Unified access to imaging data (DICOM/DICOMWeb) and clinical records
  (FHIR/EHR).  
- 🧠 Extensible backend for AI/ML pipelines, including deep learning inference.
- ⚡ Web-based UI built on [VolView](https://github.com/KitwareMedical/VolView).
- 🔌 Pluggable integrations — Orthanc, HAPI on FHIR, and MedGemma are examples.
  Users can bring their **own DICOM/FHIR servers or multimodal pipelines**.

---

## 🎥 Video Demonstrations

### Quick Overview

[![VolView Insight Overview](https://img.youtube.com/vi/cfdlmkHQcCI/0.jpg)](https://www.youtube.com/watch?v=cfdlmkHQcCI)

### MedGemma Integration

[![VolView Insight MedGemma Integration](https://img.youtube.com/vi/RZ3OovuXEnk/0.jpg)](https://www.youtube.com/watch?v=RZ3OovuXEnk)

### Comprehensive Webinar

[![VolView Insight Webinar](https://img.youtube.com/vi/wItblBkxJw0/0.jpg)](https://www.youtube.com/watch?v=wItblBkxJw0)

---

## 🚀 Quick Start

### Prerequisites

- **Docker** `20.10.0` or later
- **Docker Compose** v2.0 or later (included with Docker Desktop)

---

### 🐳 **Docker Setup**

The easiest way to get started is using our Docker orchestration setup:

#### 1) Clone and setup
```bash
git clone https://github.com/KitwareMedical/volview-insight.git
cd volview-insight
git submodule update --init

# Apply VolView patches
cat ./core-volview-patches/VOLVIEW_BACKEND.patch | git -C core/VolView apply
# macOS only: cat ./core-volview-patches/MACOS_COMPATIBILITY.patch | git -C core/VolView apply
```

#### 2) Setup volumes and environment
```bash
# Setup data volumes (creates both volumes/ and volumes-db/ structures)
./scripts/setup-volumes.sh

# Create environment file from template
cp env.example .env

# Edit .env file and add your HF_TOKEN for AI models
nano .env
# Add your Hugging Face token for medgemma: HF_TOKEN=hf_your_token_here
```

**Understanding the Volume Structure:**
- **`volumes/`** - Your source data directory (DICOM/FHIR files to import)  
- **`volumes-db/`** - Docker persistent storage (actual database files)

**Volume Structure Overview:**
VolView Insight uses two separate volume directories:

- **`volumes/`** - **Source data** (raw files you want to import)
- **`volumes-db/`** - **Docker persistent volumes** (database storage managed by Docker)

**Directory Organization:**
```
volumes/                        # SOURCE DATA (your raw files)
├── orthanc-data/               # Raw DICOM files to be imported
│   ├── patient_[ID]/           # Patient directories by Patient ID
│   │   ├── study1.dcm         # DICOM files for this patient
│   │   └── study2.dcm
│   └── dicom_metadata.json    # Import metadata (optional)
└── hapi-fhir-data/            # Raw FHIR resources to be imported
    ├── patient_*.json         # Individual FHIR patient resources
    ├── patients.json          # Combined patient list (optional)
    └── [resource_type]/       # Additional FHIR resources by type
        ├── condition/
        ├── observation/
        └── ...

volumes-db/                     # DOCKER VOLUMES (persistent databases)
├── orthanc-data/              # Orthanc database (auto-managed)
├── hapi-fhir-data/           # HAPI FHIR database (auto-managed)
└── model-cache/              # AI model cache (persistent)
    ├── segmentLungsModel-v1.0.ckpt
    └── medgemma/            # Downloaded on first use
```

#### 3) Add your medical data

**For new users cloning from GitHub:**

1. **Prepare your source data** in the `volumes/` directory structure:
   ```bash
   # Place raw DICOM files in volumes/orthanc-data/
   mkdir -p volumes/orthanc-data/patient_[ID]/
   # Copy your .dcm files here
   
   # Place raw FHIR resources in volumes/hapi-fhir-data/
   mkdir -p volumes/hapi-fhir-data/
   # Copy your .json FHIR resources here
   ```

2. **Start the services** (creates empty databases in `volumes-db/`):
   ```bash
   ./scripts/start-dev.sh
   ```

3. **Import your data** from source to databases:
   ```bash
   # Auto-import from volumes/ to running servers
   ./scripts/auto-import-data.sh
   
   # Or import individually:
   python3 ./scripts/import-dicom-to-orthanc.py
   python3 ./scripts/import-fhir-to-hapi.py
   ```

**Alternative: Direct API uploads**
You can also upload data directly through REST APIs:
- **DICOM**: Use Orthanc's REST API at http://localhost:8042
- **FHIR**: Use HAPI FHIR's REST API at http://localhost:3000

**Data Requirements:**
- **DICOM files**: Must contain Patient ID in DICOM headers
- **FHIR data**: Patient resources with matching Patient IDs  
- **Patient matching**: Both datasets should use the same Patient ID system for proper correlation

> **Important**: The application only displays data where Patient IDs match between FHIR and DICOM/Orthanc. If a patient exists in FHIR but has no corresponding DICOM studies with the same Patient ID, or vice versa, that data will not be available in the application interface.

**Volume Persistence:**
- ✅ **`volumes-db/`** data persists across container restarts
- ✅ AI model cache (`volumes-db/model-cache/`) persists downloads  
- ⚠️ **`volumes/`** is your source data (not modified by the application)
- 🗑️ Use `docker-compose down -v` to clear all databases

**🔄 Data Persistence After Initial Setup:**
Once you've completed the initial setup and data import, **future container restarts are simple and require NO re-importing**:

```bash
# After initial setup, future restarts are this simple:

# For Development:
./scripts/stop.sh      # Stop all services
./scripts/start-dev.sh # Start all services in development mode

# For Production:  
./scripts/stop.sh       # Stop all services
./scripts/start-prod.sh # Start all services in production mode

# Your data will be immediately available:
# ✅ All DICOM studies (preserved in Orthanc database)
# ✅ All FHIR resources (preserved in HAPI FHIR database)  
# ✅ All AI models (preserved in model cache)
# ✅ No re-import needed!
```

**Important**: The first time you set up the system, you need to import data once. After that, all data persists automatically across container restarts, system reboots, and Docker updates.

#### 4) Start development environment

**🔧 For Development (Recommended):**
```bash
# Use the development script (handles proper configuration automatically)
./scripts/start-dev.sh

# To stop all services
./scripts/stop.sh
```

**⚠️ Important - Development vs Production:**
```bash
# ✅ CORRECT for development (uses docker-compose.dev.yml overrides):
./scripts/start-dev.sh

# ❌ AVOID this in development (missing dev configuration):
docker-compose up -d

# ✅ If you need manual control, use explicit dev configuration:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**🏗️ For Production:**
```bash
# For production (nginx + optimized build)
./scripts/start-prod.sh
```

**🔄 Development Restarts:**
```bash
# When you make code changes, restart specific services:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart backend volview-insight-web

# Or restart all services (preserves data):
./scripts/stop.sh && ./scripts/start-dev.sh
```

**Access Points:**
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:4014  
- **Orthanc DICOM**: http://localhost:8042
- **HAPI FHIR**: http://localhost:3000
- **Orthanc CORS Proxy**: http://localhost:5173

**Development Features:**
- ✅ Hot reloading with Vite dev server
- ✅ Live code updates with volume mounts  
- ✅ All services orchestrated automatically
- ✅ CORS proxy for DICOM Web API access
- ✅ Environment variables pre-configured
- ✅ Persistent database volumes in `volumes-db/`

**Production Features:**  
- ✅ nginx serving optimized static files
- ✅ API proxying with CORS headers
- ✅ Gzip compression and caching
- ✅ Resource limits and restart policies
- ✅ Persistent data storage across container updates

#### 5) Using the application

Once all services are running:

1. **Open the application**: Navigate to http://localhost:8080
2. **Connect to FHIR**: Click "Connect" in the FHIR Patients section
3. **Select a patient**: Choose from the loaded patient list  
4. **View imaging studies**: Patient images will appear in the DICOM section
5. **Explore AI features**: Use the analysis modules with your medical data

**Expected behavior:**
- ✅ FHIR patients load with proper names
- ✅ DICOM studies match FHIR patients by Patient ID
- ✅ Patient names display correctly even if DICOM files are anonymized
- ✅ Medical images load and display in the 3D viewer

---

### 🔧 Troubleshooting

**"No matching imaging studies found"**
- Ensure Patient IDs exactly match between FHIR and DICOM data (case-sensitive)
- Check that both FHIR patients and DICOM studies were imported successfully
- Verify the Patient ID field exists in DICOM headers and FHIR resources
- Run `./scripts/auto-import-data.sh` to verify import completed successfully
- Verify services are running: `docker-compose ps`
- Check if data exists in source directories: `ls volumes/orthanc-data/` and `ls volumes/hapi-fhir-data/`

**FHIR connection errors**
- Ensure HAPI FHIR server is accessible at http://localhost:3000
- Check that FHIR data was imported correctly
- Restart services: `docker-compose restart`

**Patient names appear blank**
- This can happen with anonymized DICOM datasets
- The application automatically falls back to FHIR patient names when available
- Ensure FHIR data includes patient names in the correct format

**CORS errors accessing DICOM**
- Development mode uses CORS proxy at http://localhost:5173
- Ensure Orthanc proxy service is running
- Check browser developer console for detailed errors

**Docker volume management**
- Data persists in `volumes-db/` across container restarts
- To clear all databases: `docker-compose down -v`
- To backup data: Copy `volumes-db/` directory
- To restore data: Replace `volumes-db/` directory before starting services
- AI models download once to `volumes-db/model-cache/` and persist



---

## 🧩 Extending VolView Insight

- **DICOMWeb**: Replace Orthanc with your own server.  
- **FHIR/EHR**: Replace HAPI with your own server.  
- **Pipelines**: Extend the Python backend with your custom multimodal methods.  

---

## 🧑‍💻 Contributing

We welcome contributions!

- Add new pipelines or models  
- Add integrations with other EHR/DICOM backends  
- Report bugs and propose features

---

## Disclaimer

This software is provided **solely for research and educational purposes**.  It
is a proof-of-concept research platform and **is not intended for clinical
use**.  

- This software has **not been reviewed or approved by the U.S. Food and Drug
  Administration (FDA)** or any other regulatory authority.  
- It must **not be used for diagnosis, treatment, or any clinical
  decision-making**.  
- No warranties or guarantees of performance, safety, or fitness for medical
  purposes are provided.  

By using this software, you acknowledge that it is for **non-clinical,
investigational research only**.

---

## 📜 License

[Apache 2.0](./LICENSE) © Kitware
