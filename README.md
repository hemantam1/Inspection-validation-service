# AI Inspection Validation Service
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![License](https://img.shields.io/badge/License-MIT-orange)

> A modular AI-powered inspection validation microservice built with FastAPI using Strategy Pattern, Factory Pattern, Repository Pattern, SQLAlchemy ORM, and PostgreSQL persistence.

---

# Overview

AI Inspection Validation Service is a FastAPI-based microservice designed to validate inspection evidence submitted by an inspection platform.

The service exposes REST APIs that intelligently route incoming validation requests to the appropriate validator and return a standardized JSON response.

The architecture is modular, extensible, and follows clean software engineering principles, allowing new AI validators to be added with minimal changes.

In addition to performing validations, the service persists validation results using PostgreSQL through SQLAlchemy ORM, enabling audit history, reporting, and future analytics.

Currently supported validations include:

- Blur Validation
- GPS Validation
- Duplicate Image Detection
- Timestamp Anomaly Detection
- OCR Validation

The repository also includes benchmark datasets and ready-to-use Swagger request collections for end-to-end API testing.

---

# Features

- REST API built with FastAPI
- Modular and extensible architecture
- Strategy Pattern for validator implementation
- Factory Pattern for validator selection
- Repository Pattern for database operations
- PostgreSQL persistence using SQLAlchemy ORM
- Validation history retrieval APIs
- Standardized request and response models
- Consistent JSON response contract
- OCR validation using Tesseract OCR and RapidFuzz
- End-to-end testing using Swagger UI

---

# Supported Validators

| Validation | Technique Used | Status |
|------------|----------------|--------|
| Blur Validation | Variance of Laplacian (OpenCV) | ✅ |
| GPS Validation | Haversine Distance | ✅ |
| Duplicate Image Detection | Perceptual Hash (pHash) | ✅ |
| Timestamp Anomaly Detection | Time Difference Analysis | ✅ |
| OCR Validation | Tesseract OCR + RapidFuzz Similarity Matching | ✅ |

---

# Architecture

The service follows a layered architecture with Strategy Pattern, Factory Pattern, and Repository Pattern to keep validators independent, reusable, and easily extensible.

```text
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
      ┌──────────┬──────────┬─────────────┬──────────────┬────────────┐
      ▼          ▼          ▼             ▼              ▼
 Blur Validator GPS Validator Duplicate Validator Timestamp Validator OCR Validator
      │          │          │             │              │
      └──────────┴──────────┴─────────────┴──────────────┘
                              │
                              ▼
                     ValidationResult
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
     Validation Repository          Response Builder
               │                             │
               ▼                             ▼
       PostgreSQL Database         Standardized JSON Response
```

---

# Validation Workflow

```text
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
        ├────────────► Validation Repository
        │                    │
        │                    ▼
        │             PostgreSQL Database
        │
        ▼
Response Builder
        │
        ▼
ValidationResponse
```

---

# Project Structure

```text
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
│   ├── ocr_utils.py
│   └── datetime_utils.py
│
├── validators/
│   ├── base_validator.py
│   ├── blur_validator.py
│   ├── gps_validator.py
│   ├── duplicate_validator.py
│   ├── timestamp_validator.py
│   └── ocr_validator.py
│
└── main.py

samples/
├── blur_benchmark/

tests/

requirements.txt
README.md
```

---

# API Endpoints

## POST `/validate`

Executes the requested validation and persists the validation result in PostgreSQL using SQLAlchemy ORM.

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

Returns complete validation history.

---

## GET `/results/{jobId}`

Returns validation history for a specific Job ID.

---

# Design Principles

The project is built around the following software engineering principles:

- Strategy Pattern
- Factory Pattern
- Repository Pattern
- Single Responsibility Principle (SRP)
- Open/Closed Principle (OCP)
- Separation of Concerns
- Layered Architecture
- Standardized API Contracts

---

# Technology Stack

- Python 3.11
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- OpenCV
- Pillow
- NumPy
- ImageHash
- Tesseract OCR
- pytesseract
- RapidFuzz

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

Calculates the distance between captured and registered GPS coordinates using the Haversine formula and verifies whether the evidence was captured within the configured inspection radius.

---

## Duplicate Image Detection

Uses Perceptual Hashing (pHash) to compare the submitted image against one or more reference images and detect duplicate submissions.

---

## Timestamp Anomaly Detection

Detects suspicious timestamps by validating chronological consistency between task start time, previous step completion time, and current evidence capture time.

---

## OCR Validation

Extracts text from inspection documents using Tesseract OCR and validates it against the expected text using RapidFuzz token-based similarity matching.

The validator returns:

- Extracted Text
- OCR Confidence
- Text Similarity Score
- Match Result
- Fraud Risk Flags (if mismatch detected)

---

# Testing

The repository contains ready-to-use Swagger request collections inside the `swagger_requests/` directory.

These requests can be directly copied into the FastAPI Swagger UI for end-to-end testing.

Available request collections:

- OCR Validation
- Blur Validation
- GPS Validation
- Duplicate Image Validation
- Timestamp Validation

The repository also includes benchmark datasets used to validate OCR and Blur modules during development.

---

# Current Status

- ✅ Modular validation architecture completed
- ✅ FastAPI REST API implemented
- ✅ Validator Factory implemented
- ✅ Validation Service implemented
- ✅ Response Builder implemented
- ✅ Repository Pattern implemented
- ✅ PostgreSQL persistence using SQLAlchemy
- ✅ Validation history APIs implemented
- ✅ Blur Validator implemented and benchmark tested
- ✅ GPS Validator implemented and tested
- ✅ Duplicate Image Validator implemented and tested
- ✅ Timestamp Validator implemented and tested
- ✅ OCR Validator implemented
- ✅ End-to-end testing completed

---

# Future Enhancements

The architecture is designed to support additional validators with minimal changes.

Possible future extensions include:

- Multi-language OCR Support
- Face Match Validation
- Liveness Detection
- Image Tampering Detection
- EXIF Metadata Validation
- Support for additional relational databases (e.g., MySQL)
- Authentication & Authorization
- Validation Dashboard
- Cloud Storage Integration

---

# Author

**Divyansh Gautam**