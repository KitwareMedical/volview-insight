# VolView Insight

<img src="volview-insight/resources/logo-remove-bg.png" alt="VolView Insight logo" width="300"/>

![VolView Insight Screenshot](./volview-insight/resources/example_screenshot.jpg)

---

## 📖 About

**VolView Insight** is an open-source platform that unifies **medical imaging** and **clinical data** into one extensible interface.  
It provides researchers with a realistic testbed for **developing, testing, and extending multimodal models** in settings that mirror clinical reality.  

Key features:
- 🔬 Unified access to imaging data (DICOMWeb) and clinical records (FHIR/EHR).  
- 🧠 Extensible backend for AI/ML pipelines, including deep learning inference.  
- ⚡ Web-based UI built on top of [VolView](https://github.com/KitwareMedical/VolView).  
- 🛠️ Designed for experimentation, integration, and extension.  

---

## 🚀 Getting Started

### Prerequisites
Make sure you have the following installed:
- **Node.js** (via `nvm`)  
- **Python** ≥ 3.10 (tested with 3.10, may work with lower)  
- **Poetry** 2.1.2  
- **Docker** 28.0.04  
- A DICOM server (e.g., Orthanc)  
- A FHIR server (e.g., HAPI FHIR)  

---

### Clone the Repository

```bash
git clone https://github.com/KitwareMedical/volview-insight.git
cd volview-insight
git submodule update --init
```

---

### Build & Run

#### Apply Patches to VolView
```bash
cat ./core-volview-patches/VOLVIEW_BACKEND.patch | git -C core/VolView apply
# macOS only:
cat ./core-volview-patches/MACOS_COMPATIBILITY.patch | git -C core/VolView apply
```

#### Start the Web App
```bash
nvm use 18.17.1
npm install --force
npm run setup-project
npm run build
npm run preview
```
👉 Access at: [http://localhost:4173/](http://localhost:4173/)

#### Python Backend (Extensible Pipelines)
```bash
cd volview-insight/server
poetry env use /path/to/bin/python3.10
poetry install
poetry run python -m volview_server -P 4014 -H 0.0.0.0 volview_insight_methods.py
```

You can integrate custom multimodal pipelines here (e.g., segmentation, retrieval, or generative models).  

---

## 🔌 Example Integrations

VolView Insight is designed to be **extensible**. You can connect it to different backends for imaging, clinical data, or AI pipelines.  

### Imaging Servers
- **Orthanc (DICOMWeb)** – lightweight DICOM server with plugin support.  
- Other DICOMWeb servers can also be configured.  

### Clinical Data Servers
- **HAPI FHIR** – easy-to-run FHIR server for development/testing.  
- Other FHIR-compliant servers can be integrated.  

### Backend AI/ML Pipelines
- **VolView Python server** – run multimodal models and inference pipelines.  
- **MedGemma** (example gated Hugging Face model) – requires token access.  
- Other models or pipelines can be plugged in.  

---

## 📊 Example Data

VolView Insight uses images alongside patient records.  
Example notebooks for loading matched DICOM + FHIR patient data:  
[`notebooks/02-load-pt-matched-data-into-volview-insight.ipynb`](./notebooks/02-load-pt-matched-data-into-volview-insight.ipynb).  

---

## 🧑‍💻 Contributing

Contributions are welcome! 🎉  

Ways you can help:
- Improve documentation & tutorials  
- Add new AI pipelines or models  
- Extend integrations with EHR / imaging backends  
- Report bugs and suggest features  

See our [CONTRIBUTING.md](./CONTRIBUTING.md).  

---

## 📜 License

[Apache 2.0](./LICENSE) © Kitware  
