# SatQuery AI — Backend

SatQuery AI is an interactive vision-language assistant for multimodal remote-sensing image analysis through natural-language queries.

This backend provides the API, raster validation, investigation orchestration, model abstraction, evidence collection, confidence calculation, conflict detection, execution tracing, persistence, and reproducible investigation reports required by the SatQuery AI system.

---

## Project

**SIH Problem:** SIH26167  
**Theme:** Space Technology  
**Project:** SatQuery AI  
**Backend:** FastAPI + Python  
**Primary raster format:** GeoTIFF / TIFF

---

# Architecture

The backend follows an investigation-driven architecture:

```text
User Mission
     ↓
Mission Agent
     ↓
Structured Investigation Plan
     ↓
Plan Validator
     ↓
Raster Compatibility Validation
     ↓
Deterministic Execution Engine
     ↓
Specialist Models
     ↓
Evidence Engine
     ↓
Conflict Detection
     ↓
Confidence Engine
     ↓
Investigation Result
     ↓
Reproducible Report
```

The backend is intentionally designed so that real remote-sensing ML models can be connected later without rewriting the API or orchestration layer.

---

# Directory Structure

```text
backend/
│
├── app/
│   ├── api/
│   │   ├── routes_images.py
│   │   ├── routes_compatibility.py
│   │   ├── routes_investigation.py
│   │   └── routes_models.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   └── database.py
│   │
│   ├── models/
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── image.py
│   │   ├── investigation.py
│   │   └── model.py
│   │
│   ├── services/
│   │   ├── raster.py
│   │   ├── image_registry.py
│   │   ├── compatibility.py
│   │   ├── mission_agent.py
│   │   ├── plan_validator.py
│   │   ├── model_registry.py
│   │   ├── model_adapter.py
│   │   ├── reference_model_adapter.py
│   │   ├── execution_engine.py
│   │   ├── mock_models.py
│   │   ├── evidence_engine.py
│   │   ├── confidence_engine.py
│   │   ├── conflict_engine.py
│   │   ├── investigation_pipeline.py
│   │   ├── execution_trace.py
│   │   ├── investigation_repository.py
│   │   └── report_generator.py
│   │
│   └── main.py
│
├── data/
│   ├── uploads/
│   ├── reports/
│   ├── satquery.db
│   └── test rasters
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Main Responsibilities

The backend is responsible for:

- GeoTIFF/TIFF upload
- Raster metadata extraction
- Modality validation
- CRS validation
- Spatial overlap validation
- Resolution compatibility checks
- Pixel-grid alignment checks
- Investigation planning
- Deterministic task validation
- Specialist model execution
- Runtime context passing between dependent tasks
- Evidence collection
- Confidence calculation
- Model conflict detection
- Observable execution traces
- Investigation persistence
- Reproducible investigation reports
- ML model integration through adapters
- Docker deployment

---

# Installation

## 1. Create virtual environment

```powershell
python -m venv .venv
```

## 2. Activate

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

---

# Requirements

Current Python dependencies:

```text
fastapi
uvicorn[standard]
python-multipart
pydantic
pydantic-settings
rasterio
numpy
pytest
httpx
```

Rasterio is used for GeoTIFF inspection and geospatial raster operations.

---

# Environment Configuration

Create a `.env` file:

```env
APP_NAME=SatQuery AI Backend
APP_VERSION=0.1.0
API_PREFIX=/api/v1
DATA_DIR=data
MAX_UPLOAD_MB=512
CORS_ORIGINS=*
```

A template is provided in:

```text
.env.example
```

---

# Running the Backend

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative API documentation:

```text
http://127.0.0.1:8000/redoc
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "satquery-backend"
}
```

---

# API Structure

Base API prefix:

```text
/api/v1
```

Main endpoints:

```text
GET    /health

POST   /api/v1/images/upload

GET    /api/v1/models/

POST   /api/v1/investigations/

GET    /api/v1/investigations/{investigation_id}

GET    /api/v1/investigations/{investigation_id}/report
```

Compatibility functionality is also exposed through the compatibility router.

---

# Image Upload

Endpoint:

```text
POST /api/v1/images/upload
```

The endpoint accepts:

```text
file
modality
```

Supported modalities:

```text
optical
multispectral
sar
```

Supported raster extensions:

```text
.tif
.tiff
```

The backend rejects unsupported file formats before analysis.

---

# Raster Metadata

When a raster is uploaded, the backend extracts:

- Image ID
- Filename
- Modality
- Width
- Height
- Number of bands
- Data type
- CRS
- Resolution
- Bounds
- Affine transform
- File size

Example:

```json
{
  "image_id": "img_123456789abc",
  "filename": "scene.tif",
  "modality": "optical",
  "width": 100,
  "height": 100,
  "bands": 3,
  "dtype": "uint8",
  "crs": "EPSG:4326",
  "resolution_x": 0.001,
  "resolution_y": 0.001,
  "bounds": [
    77.0,
    27.9,
    77.1,
    28.0
  ]
}
```

---

# Image Compatibility

Before multi-image analysis, the backend validates compatibility.

Checks include:

## CRS

Images must use compatible coordinate reference systems.

## Spatial overlap

Images must overlap spatially.

## Resolution

Resolution differences must remain within the configured tolerance.

Current tolerance:

```text
10%
```

## Pixel grid

Images are checked for compatible affine transforms and grid alignment.

## Dimensions

Raster dimensions are checked for compatibility.

---

# Temporal Analysis

Temporal investigations require two images.

Example query:

```text
Compare these two images for new construction.
```

The mission agent can generate:

```text
change_analysis
```

Optionally followed by:

```text
grounding
```

when the query asks where the detected change occurred.

Example plan:

```text
change_analysis
       ↓
grounding
```

The grounding task receives the previous task's result through runtime execution context.

---

# Optical + SAR Analysis

Cross-modal analysis supports:

```text
Optical / Multispectral + SAR
```

The system validates that exactly one optical/multispectral image and one SAR image are supplied.

Example query:

```text
Analyze the optical and SAR images together.
```

The mission agent creates:

```text
optical_sar_fusion
```

A grounding task can optionally follow when the user asks to locate a feature.

---

# Investigation Mode

The main investigation endpoint is:

```text
POST /api/v1/investigations/
```

Request:

```json
{
  "query": "Compare these two images for new construction and tell me where it occurred.",
  "image_ids": [
    "img_before",
    "img_after"
  ]
}
```

The backend performs:

```text
Query
 ↓
Mission Agent
 ↓
Task Plan
 ↓
Plan Validation
 ↓
Compatibility Validation
 ↓
Task Execution
 ↓
Evidence Collection
 ↓
Conflict Detection
 ↓
Confidence Calculation
 ↓
Trace Generation
 ↓
Persistence
 ↓
Report Generation
```

---

# Supported Task Types

The current task schema supports:

```text
vqa
caption
grounding
change_analysis
optical_sar_fusion
```

---

# Mission Agent

File:

```text
app/services/mission_agent.py
```

The Mission Agent converts a natural-language query into structured tasks.

Example:

```text
User:

Compare these two images for new construction
and tell me where it occurred.
```

Produces approximately:

```text
Task 1:
change_analysis

Task 2:
grounding
depends_on = Task 1
```

The backend does not allow arbitrary free-form model/tool calls.

Tasks must conform to the predefined task schema.

---

# Plan Validator

File:

```text
app/services/plan_validator.py
```

The validator ensures that tasks have valid inputs.

Examples:

```text
change_analysis
→ exactly 2 images

optical_sar_fusion
→ exactly 2 images

vqa
→ at least 1 image

grounding
→ at least 1 image
```

Invalid plans are rejected before specialist execution.

---

# Model Registry

File:

```text
app/services/model_registry.py
```

The Model Registry provides a fixed mapping between task types and specialist models.

Current registered specialists:

```text
SatQuery RS-VLM
SatQuery Captioner
SatQuery Grounding
SatQuery Change Model
SatQuery Optical-SAR Fusion
```

Each model has:

- Name
- Task type
- Version
- Description
- Adapter
- Handler

Example:

```python
register_model(
    name="SatQuery RS-VLM",
    task_type="vqa",
    version="0.1.0",
    description="Remote-sensing visual question answering model.",
    handler=mock_vqa_handler,
)
```

---

# ML Adapter Architecture

The backend is designed to be ML-ready.

The main interface is:

```text
app/services/model_adapter.py
```

Base interface:

```python
class ModelAdapter(ABC):

    @abstractmethod
    def predict(
        self,
        task,
        image_paths,
        execution_context=None,
    ):
        raise NotImplementedError
```

A real remote-sensing model should implement this interface.

---

# Real Model Integration

The ML developer does NOT need to rewrite the backend.

They should create an adapter:

```python
from app.services.model_adapter import ModelAdapter


class MyRemoteSensingModel(ModelAdapter):

    def predict(
        self,
        task,
        image_paths,
        execution_context=None,
    ):

        # Load model
        # Load raster
        # Preprocess
        # Run inference
        # Generate evidence

        return {
            "answer": "...",
            "confidence": 0.91,
            "evidence": [
                {
                    "type": "visual",
                    "description": "..."
                }
            ]
        }
```

Then register the adapter:

```python
register_model(
    name="My Remote Sensing VLM",
    task_type="vqa",
    version="1.0.0",
    description="Fine-tuned remote-sensing VLM.",
    adapter=MyRemoteSensingModel(),
)
```

The execution engine will automatically use the adapter.

---

# Standard Model Output

Every specialist should return a dictionary containing:

```json
{
  "confidence": 0.91,
  "evidence": []
}
```

Task-specific outputs can include:

### VQA

```json
{
  "answer": "Urban buildings are visible.",
  "confidence": 0.91,
  "evidence": []
}
```

### Captioning

```json
{
  "caption": "Urban settlement with roads and buildings.",
  "confidence": 0.88,
  "evidence": []
}
```

### Grounding

```json
{
  "regions": [
    {
      "x": 120,
      "y": 80,
      "width": 200,
      "height": 150
    }
  ],
  "confidence": 0.86,
  "evidence": []
}
```

### Change Analysis

```json
{
  "change_detected": true,
  "change_type": "land-cover change",
  "confidence": 0.90,
  "evidence": []
}
```

### Optical-SAR Fusion

```json
{
  "finding": "The observations indicate...",
  "confidence": 0.87,
  "evidence": []
}
```

---

# Runtime Execution Context

Investigation tasks can depend on earlier tasks.

Example:

```text
change_analysis
       ↓
grounding
```

The execution engine passes the previous result to the dependent task:

```python
execution_context = {
    "previous_results": {
        "task_id": dependency_result
    }
}
```

This allows later specialists to use upstream investigation results without modifying the original task definition.

---

# Execution Engine

File:

```text
app/services/execution_engine.py
```

Responsibilities:

- Resolve registered models
- Resolve image file paths
- Execute adapters
- Execute mock handlers
- Pass runtime context
- Resolve dependencies
- Stop dependent tasks when dependencies fail
- Return standardized execution results

The engine supports both:

```text
adapter
```

and:

```text
handler
```

This allows mocks to be used during development while real ML adapters are being prepared.

---

# Mock Models

File:

```text
app/services/mock_models.py
```

Mocks currently exist for:

```text
VQA
Captioning
Grounding
Change Analysis
Optical-SAR Fusion
```

The mocks exist only to verify backend orchestration and API contracts.

They are NOT intended to satisfy the final remote-sensing ML requirement.

Real remote-sensing models should replace the mock handlers before final SIH evaluation.

---

# Evidence Engine

File:

```text
app/services/evidence_engine.py
```

The Evidence Engine collects evidence from successful specialist results.

Evidence categories include:

```text
visual
scene
spatial
temporal
cross_modal
```

Each evidence item stores information such as:

- Evidence type
- Description
- Source model
- Task ID
- Task type
- Model version

Example:

```json
{
  "type": "temporal",
  "description": "Difference detected between the two temporal images.",
  "source": "SatQuery Change Model",
  "metadata": {
    "task_id": "task_12345678",
    "task_type": "change_analysis",
    "model_version": "0.1.0"
  }
}
```

---

# Confidence Engine

File:

```text
app/services/confidence_engine.py
```

Confidence is calculated separately from the language model.

Current factors:

```text
Model Reliability
Temporal Consistency
Spatial Consistency
Cross-Modal Agreement
Evidence Quality
```

Current weighting:

```text
Model                  40%
Temporal Consistency   15%
Spatial Consistency    15%
Cross-Modal Agreement  15%
Evidence Quality       15%
```

The resulting confidence is clamped to:

```text
0.0 → 1.0
```

Labels:

```text
>= 0.80 → high
>= 0.60 → medium
<  0.60 → low
```

The confidence calculation is deterministic and can later be calibrated using validation data.

---

# Conflict Detection

File:

```text
app/services/conflict_engine.py
```

The system can detect disagreements between successful specialist results.

Examples:

```text
Model A:
change_detected = true

Model B:
change_detected = false
```

This produces a conflict instead of silently averaging the results.

Conflict types currently include:

```text
model_disagreement
answer_disagreement
```

This is important because uncertainty should be surfaced rather than hidden.

---

# Execution Trace

File:

```text
app/services/execution_trace.py
```

Every investigation produces an observable execution trace.

Typical steps:

```text
mission_received
plan_created
plan_validation
raster_compatibility
dependency_resolution
model_execution
evidence_collection
conflict_detection
confidence_calculation
investigation_completed
```

Each trace entry contains:

```json
{
  "timestamp": "...",
  "step": "model_execution",
  "status": "completed",
  "details": {}
}
```

This makes the agent's execution observable to the frontend and useful for Judge Mode.

---

# Investigation Persistence

File:

```text
app/services/investigation_repository.py
```

SQLite is currently used for lightweight persistence.

Database:

```text
data/satquery.db
```

The backend stores:

- Investigation ID
- Query
- Status
- Tasks
- Execution results
- Evidence
- Confidence
- Conflicts
- Compatibility information
- Execution trace
- Creation timestamp

---

# Reproducible Reports

File:

```text
app/services/report_generator.py
```

Every completed investigation generates a structured JSON report.

Reports are stored in:

```text
data/reports/
```

Filename:

```text
{investigation_id}.json
```

Example:

```text
inv_123456789abc.json
```

Reports contain:

```text
Report version
Investigation ID
Timestamp
Original query
Tasks
Model results
Evidence
Confidence
Conflicts
Execution trace
```

This provides the foundation for:

```text
One Mission → One Report
```

---

# Error Handling

File:

```text
app/core/errors.py
```

The backend uses structured errors.

Example:

```json
{
  "error": {
    "code": "INVALID_MODALITY",
    "message": "Modality must be optical, multispectral or sar.",
    "details": null
  }
}
```

Examples of backend error conditions:

```text
INVALID_MODALITY
UNSUPPORTED_FORMAT
FILE_TOO_LARGE
INVALID_RASTER
FILE_SAVE_FAILED
IMAGE_REGISTRATION_FAILED
SOURCE_RASTER_NOT_FOUND
REFERENCE_RASTER_NOT_FOUND
INVALID_RESAMPLING_METHOD
SOURCE_CRS_MISSING
REFERENCE_CRS_MISSING
RASTER_ALIGNMENT_FAILED
RASTER_GRID_CHECK_FAILED
```

---

# Raster Alignment

The raster service also provides alignment utilities.

File:

```text
app/services/raster.py
```

Available resampling methods:

```text
nearest
bilinear
cubic
```

Alignment uses the reference raster's:

```text
CRS
width
height
transform
```

The output is validated after alignment.

---

# Compatibility Failure Behavior

The backend deliberately blocks incompatible imagery before specialist execution.

Example:

```text
Input:
Optical image: 1024 × 1024
SAR image: 768 × 768

Result:

Analysis blocked.

Reason:
Images are not spatially compatible.
```

The objective is:

```text
Invalid input
     ↓
Validation
     ↓
Clear failure
     ↓
NO model execution
```

rather than allowing incompatible data to reach a model.

---

# Testing

Tests are located in:

```text
tests/
```

Run the complete test suite:

```powershell
python -m pytest -q
```

Current backend test coverage includes:

```text
Mission planning
Conflict detection
Compatibility validation
Upload validation
Investigation pipeline
Dependency execution context
Investigation API
```

Current test status:

```text
17 passed
```

There are currently two non-failing dependency warnings related to Starlette/httpx.

---

# Development Rules

## 1. Do not bypass validation

No specialist model should receive incompatible imagery.

## 2. Keep API contracts stable

Frontend and ML developers should integrate against the existing schemas rather than changing them casually.

## 3. Use ModelAdapter for real ML

Real models should be integrated through:

```text
ModelAdapter
```

rather than directly modifying the execution engine.

## 4. Keep mocks available

Mocks are useful for testing the backend when the ML models are unavailable.

## 5. Keep execution deterministic

The Mission Agent produces a structured plan and the execution engine follows that plan.

## 6. Surface conflicts

Do not silently average contradictory model outputs.

## 7. Preserve evidence

Every useful model output should provide evidence that can be displayed by the frontend.

---

# ML Developer Handoff

The backend is intentionally designed so the ML developer can work independently.

The ML developer needs to provide:

```text
1. Real RS-VLM
2. VQA inference
3. Captioning OR grounding
4. Bi-temporal change analysis
5. Change description / change VQA
6. SAR specialist
7. Optical-SAR fusion
8. Model versions
9. Confidence values
10. Evidence outputs
```

The backend expects these through the adapter contract.

The backend should not need major architectural changes when the real models arrive.

---

# Frontend Integration

The frontend should use:

```text
POST /api/v1/images/upload
```

to upload imagery.

Then:

```text
POST /api/v1/investigations/
```

to start an investigation.

The returned investigation contains:

```text
investigation_id
status
query
tasks
execution
model_results
evidence
confidence
conflicts
compatibility
trace
```

The frontend can use these to display:

```text
Investigation plan
Findings
Confidence
Evidence
Detected regions
Model information
Conflicts
Execution trace
```

The report can be retrieved using:

```text
GET /api/v1/investigations/{investigation_id}/report
```

---

# Judge Mode Support

The backend exposes enough structured information for a frontend Judge Mode.

A Judge Mode presentation can show:

```text
MISSION
   ↓
PLAN
   ↓
VALIDATION
   ↓
SPECIALIST MODELS
   ↓
EVIDENCE
   ↓
CONFIDENCE
   ↓
FINAL FINDING
```

It can also demonstrate failure handling:

```text
Upload incompatible imagery
        ↓
Compatibility check
        ↓
Analysis blocked
        ↓
Clear reason shown
```

---

# Docker

The backend contains a Dockerfile for containerized deployment.

Build:

```powershell
docker build -t satquery-backend .
```

Run:

```powershell
docker run --rm -p 8000:8000 satquery-backend
```

The application listens on:

```text
0.0.0.0:8000
```

Inside Docker:

```text
/app
├── app
├── data
│   ├── uploads
│   └── reports
└── requirements.txt
```

---

# Current Backend Status

The backend currently provides:

```text
[✓] FastAPI application
[✓] API routing
[✓] Configuration
[✓] Structured error handling
[✓] GeoTIFF validation
[✓] Raster metadata extraction
[✓] Image registry
[✓] SQLite persistence
[✓] Compatibility validation
[✓] Mission planning
[✓] Plan validation
[✓] Model registry
[✓] Model adapter interface
[✓] Reference adapter
[✓] Mock specialist models
[✓] Deterministic execution engine
[✓] Runtime execution context
[✓] Evidence engine
[✓] Confidence engine
[✓] Conflict detection
[✓] Execution trace
[✓] Investigation pipeline
[✓] Investigation persistence
[✓] Reproducible JSON reports
[✓] Investigation API
[✓] Model listing API
[✓] Automated tests
[✓] Dockerfile
[ ] Real remote-sensing ML models
[ ] Final frontend integration
[ ] Final production deployment
```

---

# Important Final Integration Note

The current mock models demonstrate that the backend architecture works.

They do NOT represent the final SIH model contribution.

For final SIH evaluation, the real ML layer must provide the required remote-sensing capabilities and model adaptation described by the problem statement.

The backend's role is to provide the stable connective layer:

```text
Remote-Sensing Data
        ↓
Validation
        ↓
Mission Planning
        ↓
Model Registry
        ↓
Real Specialist Models
        ↓
Evidence
        ↓
Confidence
        ↓
Conflict Detection
        ↓
Trace
        ↓
Reproducible Result
```

---

# Design Principle

> If the input isn't validated, nothing downstream can be trusted.

SatQuery AI is designed as an evidence-driven remote-sensing investigation system rather than a generic chatbot.

The objective is:

```text
Ask the Earth.
Get Evidence.
```
