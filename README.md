# AI Inspection Validation Service

> A modular AI validation microservice for inspection workflows built using FastAPI, Strategy Pattern, Factory Pattern, Repository Pattern, and SQLite persistence.

---

## Overview

AI Inspection Validation Service is a FastAPI-based microservice designed to validate inspection evidence submitted by an inspection platform.

The service exposes REST APIs that route incoming validation requests to the appropriate validator and return a standardized JSON response.

The architecture has been designed to be modular and extensible, allowing new validation types to be added with minimal changes to the overall system.

In addition to executing validations, the service also persists validation results using SQLite through SQLAlchemy, making it possible to maintain validation history for auditing, reporting, and future analysis.

---

# Features

- REST API built with FastAPI
- Modular and extensible architecture
- Strategy Pattern for validator implementation
- Factory Pattern for validator selection
- Repository Pattern for database operations
- SQLite persistence using SQLAlchemy ORM
- Validation history retrieval APIs
- Standardized request and response models
- Consistent JSON response contract
- End-to-end API testing using Swagger UI

---

# Supported Validators

| Validation | Technique Used | Status |
|------------|----------------|--------|
| Blur Validation | Variance of Laplacian (OpenCV) | ✅ |
| GPS Validation | Haversine Distance | ✅ |
| Duplicate Image Detection | Perceptual Hash (pHash) | ✅ |
| Timestamp Anomaly Detection | Time Difference Analysis | ✅ |

---

# Architecture

The service follows a layered architecture with Strategy Pattern, Factory Pattern, and Repository Pattern to keep validators independent, reusable, and easily extensible.

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
      ┌───────────────┬───────────────┬───────────────┬───────────────┐
      ▼               ▼               ▼               ▼
 Blur Validator   GPS Validator  Duplicate Validator Timestamp Validator
      │               │               │               │
      └───────────────┴───────────────┴───────────────┘
                              │
                              ▼
                     ValidationResult
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
     Validation Repository          Response Builder
               │                             │
               ▼                             ▼
       SQLite Database          Standardized JSON Response
```

---

# Validation Workflow

```
Inspection Platform

        │

        ▼

POST /validate

        │

        ▼

Validation Service

        │

        ▼

Validator Factory

        │

        ▼

Selected Validator

        │

        ▼

ValidationResult

        │

        ├──────────────► Validation Repository
        │                       │
        │                       ▼
        │                SQLite Database
        │
        ▼

Response Builder

        │

        ▼

ValidationResponse
```

---

# Project Structure

```
inspection-validation-service/

app/
├── api/
│   └── routes.py
│
├── builders/
│   └── response_builder.py
│
├── core/
│   ├── config.py
│   ├── constants.py
│   ├── exceptions.py
│   └── logger.py
│
├── database/
│   ├── connection.py
│   └── models.py
│
├── factory/
│   └── validator_factory.py
│
├── models/
│   ├── enums.py
│   ├── request.py
│   ├── response.py
│   └── validation_result.py
│
├── repositories/
│   └── validation_repository.py
│
├── services/
│   └── validation_service.py
│
├── utils/
│   ├── image_utils.py
│   ├── gps_utils.py
│   ├── hash_utils.py
│   └── datetime_utils.py
│
├── validators/
│   ├── base_validator.py
│   ├── blur_validator.py
│   ├── gps_validator.py
│   ├── duplicate_validator.py
│   └── timestamp_validator.py
│
└── main.py

samples/
tests/

requirements.txt
README.md
```

---

# API Endpoints

## POST `/validate`

Executes the requested validation and stores the validation result in the SQLite database.

### Example Response

```json
{
  "jobId": "job-001",
  "status": "COMPLETED",
  "resultType": "BLUR_CHECK",
  "confidenceScore": 95,
  "resultJson": {},
  "riskFlags": [],
  "error": null
}
```

---

## GET `/results`

Returns the complete validation history stored in the database.

---

## GET `/results/{jobId}`

Returns the validation record associated with the specified Job ID.

---

# Design Principles

The project is built around the following software engineering principles:

- Strategy Pattern
- Factory Pattern
- Repository Pattern
- Single Responsibility Principle
- Open/Closed Principle
- Layered Architecture
- Separation of Concerns
- Standardized API Contracts

---

# Technology Stack

- Python 3.11
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- OpenCV
- Pillow
- NumPy
- ImageHash

---

# Running the Project

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Start the Server

```bash
python -m uvicorn app.main:app --reload
```

## Swagger Documentation

```
http://127.0.0.1:8000/docs
```

---

# Validation Techniques

## Blur Validation

Detects blurry inspection images using the Variance of Laplacian algorithm provided by OpenCV.

---

## GPS Validation

Calculates the distance between captured and registered GPS coordinates using the Haversine formula and verifies whether the capture occurred within the configured radius.

---

## Duplicate Image Detection

Detects duplicate inspection images using Perceptual Hashing (pHash) by comparing the captured image against previously submitted reference images.

---

## Timestamp Anomaly Detection

Identifies suspicious timestamps by validating chronological consistency between task start time, previous step completion time, and current evidence capture time.

---

# Current Status

- ✅ Modular validation architecture completed
- ✅ FastAPI REST API implemented
- ✅ Request and Response models implemented
- ✅ Validator Factory implemented
- ✅ Validation Service implemented
- ✅ Response Builder implemented
- ✅ Repository Pattern implemented
- ✅ SQLite persistence using SQLAlchemy
- ✅ Validation history retrieval APIs implemented
- ✅ Blur Validator implemented and tested
- ✅ GPS Validator implemented and tested
- ✅ Duplicate Image Validator implemented and tested
- ✅ Timestamp Validator implemented and tested
- ✅ End-to-end testing completed using Swagger
- ✅ Validation results persisted and retrieved using SQLite

---

# Future Enhancements

The current architecture allows additional validators and storage backends to be introduced with minimal changes.

Possible extensions include:

- OCR Validation
- Face Match Validation
- Liveness Detection
- Image Tampering Detection
- EXIF Metadata Validation
- PostgreSQL / MySQL support
- Authentication & Authorization
- Validation Dashboard

---

# Author

**Divyansh Gautam**