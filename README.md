# VolView Insight

![A screenshot of a sample VolView Insight
session](./volview-insight/resources/example_screenshot.jpg)

## Usage

Following are instructions to build and run an instance of the VolView Insight
web application with a locally hosted DICOMWeb server, electronic health records
(EHR) server, and VolView's backend Python server for a connected deep learning
pipeline.

### Prerequisites

- _Node-js_
- _nvm_ (for switching _Node-js_ versions)
- _Python_ >= `3.10` (might work with lower versions, but not tested)
- _Poetry_ == `2.1.2`
- _Docker_ == `28.0.04`
- Download and install [Orthanc
  Server](https://www.orthanc-server.com/download.php) with the DICOMWeb plugin
  for locally hosting DICOM images. You should start the _Orthanc_ server at
  `http://localhost:8042/`.
  - **Linux:** On Linux, you can instead run the _Orthanc_ server using Docker
    following [this guide](/volview-insight/orthanc-docker-quickstart.md). For
    instructions on how to install Docker Engine in Linux, please follow the
    guide [here](https://docs.docker.com/engine/install/ubuntu/). Note that by
    default, the Orthanc Docker image has authentication enabled (username &
    password), and so for a seamless server-side experience, you may want to run
    the docker container with this disabled (`docker run (...) -e
    ORTHANC__AUTHENTICATION_ENABLED=false (...) orthancteam/orthanc`).
    Furthermore, the `orthancteam/orthanc` only loads the DicomWeb plugin if
    `DICOM_WEB_PLUGIN_ENABLED=true` (the documentation has a confusing way of
    describing that it is **not** enabled by default).

  - **macOS:** On macOS, you can install _Orthanc_
    [here](https://www.orthanc-server.com/static.php?page=download-mac). Once
    installed, there should be a file called `startOrthanc.command` in the
    downloaded _Orthanc_ files which you can run using your terminal or by
    double-clicking. This starts the _Orthanc_ server at
    `http://localhost:8042/`.

---

### Build and run the web app

#### Clone the repository to your local drive

```bash
git clone https://www.github.com/KitwareMedical/volview-insight.git
cd volview-insight
git submodule update --init
```

#### Apply patches to VolView `6f3685db`

- All operating systems:

  ```bash
  cat ./core-volview-patches/VOLVIEW_BACKEND.patch | git -C core/VolView apply
  ```

- macOS only:

  ```bash
  cat ./core-volview-patches/MACOS_COMPATIBILITY.patch | git -C core/VolView apply
  ```

#### Build and run VolView Insight on `http://localhost:4173/`

```bash
nvm use 18.17.1
npm install --force
npm run setup-project
npm run build
npm run preview
```

---

### Build and run the _Orthanc_ proxy server to bypass CORS restrictions (for testing only)

```bash
cd volview-insight/orthanc-proxy
nvm use 23.10.0
npm install
npm run dev
```

This should start a _Vite_ http server at port 5173 as a proxy to the _Orthanc_
DICOMWeb server already running on your machine.

> Warning: You must use Node.js version `23.10.0` for running the proxy server.
> Requests are not properly forwarded to the Orthanc server otherwise.

---

### Build and run the Python backend server

VolView's Python server is used to run backend jobs such as deep learning
inference pipelines. For details about the core VolView server, see the
[quick-start
guide](./core/VolView/documentation/content/doc/server.md#starting-the-server).
Note that you need to point _Poetry_ to Python 3.9.12. You can install versions
of Python in many ways, but one way could be using
[pyenv](https://github.com/pyenv/pyenv).

```bash
cd volview-insight/server
poetry env use /path/to/bin/python3.10
poetry install
poetry run python -m volview_server -P 4014 -H 0.0.0.0 volview_insight_methods.py
```

> NOTE: If you have errors, remove the `-P 4014` (port) argument. Sometimes, the
> port is not parsed properly by a downstream file.

#### (Optional) Download the lung segmentation model

The lung segmentation model is optional for VolView Insight. The lung
segmentation model will only work with the checkpoint file installed.

```bash
curl https://data.kitware.com/api/v1/file/65bd8c2f03c3115909f73dd7/download --output segmentLungsModel-v1.0.ckpt
```

---

### Build and run the HAPI FHIR server

Download the empty [hapi r4
container](https://hub.docker.com/layers/hapi-5/smartonfhir/hapi-5/r4-empty/images/sha256-42d138f85967cbcde9ed4f74d8cd57adf9f0b057e9c45ba6a8e1713d3f9e1cea?context=explore)
by the SMART on FHIR team and run the Docker container.

```bash
docker pull smartonfhir/hapi-5:r4-empty
docker run -dp 3000:8080 smartonfhir/hapi-5:r4-empty
```

The port "3000" may be replaced by your choice of port; just replace appearances
of "3000" by your choice in the rest of the instructions. Verify that the server
is working by visiting `http://localhost:3000/hapi-fhir-jpaserver/fhir/Patient`.
This should display some json.

> The VolView Insight web application can interact with EHR in a few different
> ways. In the VolView Insight app, you can see the EHR endpoint by clicking on
> "LOGIN" in the Patients tab when the Source is Remote. However, integrating this
> with a specific EHR endpoint will require manual engineering and customization
> within the VolView Insight custom app. For more details, see the file
> `volview-insight/src/components/fhir/RemoteFHIR.vue` and the directory
> `volview-insight/fhir-login/`. Therefore, for demoing and development, use the
> HAPI FHIR server.

---

### Add example data to VolView Insight

VolView Insight is meant to use images only alongside patient medical records,
so any custom DICOM data that is uploaded needs to contain patient IDs that
match the IDs in the EHR system. You can either find your own data and study the
protocols to send them to the servers or try using the example in
`notebooks/02-load-pt-matched-data-into-volview-insight.ipynb`. The example in
`notebooks/02-load-pt-matched-data-into-volview-insight.ipynb` works if all the
servers are running and you have access to example data. Please read the
notebook for more context.

---

### MedGemma Access

It is possible that when trying to use the Python backend to run inference using MedGemma, you will run into authorization issues. This is because the repositories are public, but gated. To have access to download the models, you need to make a Hugging Face account, accept the terms & conditions of each model repository (4B and 27B), and then make an access token that gives access to those repositories. Copy the access token and then provide the access token to a program like `huggingface-cli`, which is available on most package managers. See this tutorial for more assistance: https://huggingface.co/docs/hub/en/models-gated

---

<img src="volview-insight/resources/logo-remove-bg.png" alt="VolView Insight logo" width="300"/>
