# AI Inspection Validation Service

## Overview

AI Inspection Validation Service is a FastAPI-based microservice that performs automated validation on inspection evidence submitted by an inspection platform.

The service is designed with a modular and extensible architecture so that new validation types can be added with minimal changes.

Current implementation focuses on building a clean validation framework and implementing the first validator (Blur Validation).

---

## Architecture

The service follows a layered architecture using the Strategy Pattern and Factory Pattern.

```
Inspection Platform
        │
        ▼
 POST /validate
        │
        ▼
 FastAPI API Layer
        │
        ▼
 Validation Service
        │
        ▼
 Validator Factory
        │
 ┌──────┼────────────┬──────────────┬
 ▼      ▼            ▼              ▼
Blur   GPS     Duplicate     Timestamp
Validator Validator Validator   Validator
        │
        ▼
 Validation Result
        │
        ▼
 Response Builder
        │
        ▼
 Standardized JSON Response
```

---

## Project Structure

```
inspection-validation-service/

app/
├── api/
├── builders/
├── core/
├── factory/
├── models/
├── services/
├── utils/
├── validators/
└── main.py

samples/
requirements.txt
```

---

## Implemented Features

- FastAPI REST API
- Standardized Request & Response Models
- Validation Service
- Validator Factory
- Base Validator (Strategy Pattern)
- Response Builder
- Blur Validation (Variance of Laplacian)
- Swagger API Documentation

---

## Planned Validators

- ✅ Blur Validation
- 🚧 GPS Validation
- 🚧 Duplicate Image Validation
- 🚧 Timestamp Anomaly Validation

---

## Technology Stack

- Python 3.11
- FastAPI
- Pydantic
- OpenCV
- NumPy
- ImageHash

---

## Running the Project

Install dependencies

```bash
pip install -r requirements.txt
```

Start the application

```bash
python -m uvicorn app.main:app --reload
```

Swagger UI

```
http://127.0.0.1:8000/docs
```

---

## Sample API

```
POST /validate
```

Returns a standardized validation response for the requested validation job.

---

## Current Status

- Architecture completed
- Validation framework completed
- Blur validator implemented and tested
- Remaining validators are currently under development
