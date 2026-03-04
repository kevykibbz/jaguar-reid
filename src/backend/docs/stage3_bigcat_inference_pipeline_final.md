# BigCat Multi-Stage Inference Pipeline (Stage 3)

## Overview

This document describes the final integrated AI system consisting of:

-   Stage 1: BigCat Binary Filter (BigCat vs NotBigCat)
-   Stage 2: BigCat Species Classifier (Jaguar, Leopard, Tiger, Lion,
    Cheetah)
-   Stage 3: Unified Inference Pipeline (Image + Video + URL Support)
-   REST API Wrapper (FastAPI)

------------------------------------------------------------------------

## System Architecture

### Image Pipeline

Input Image\
→ Stage 1 (Binary Filter)\
→ If Not BigCat → Reject\
→ If BigCat → Stage 2 (Species Classifier)\
→ Return Species + Confidence

### Video Pipeline

Input Video\
→ Frame Extraction\
→ Stage 1 on Each Frame\
→ If Insufficient BigCat Frames → Reject\
→ Stage 2 on BigCat Frames\
→ Majority Vote Species\
→ Return Species + BigCat Frame Ratio

------------------------------------------------------------------------

## Stage 1 Model

Model: EfficientNet-B2\
Task: Binary Classification\
Output: BigCat / NotBigCat\
Validation Accuracy: \~95--96%\
False Positive Rate: \~2%

------------------------------------------------------------------------

## Stage 2 Model

Model: EfficientNet-B2\
Task: 5-Class Species Classification

Classes: - Jaguar - Leopard - Tiger - Lion - Cheetah

Validation Accuracy: \~91%\
Strong real-world generalization confirmed via internet testing.

------------------------------------------------------------------------

## Unified Inference Function

Single entry function:

predict_media(input)

Supports: - Local image files - Local video files - Image URLs

Automatically routes to: - Image pipeline - Video pipeline

Returns structured JSON-style output.

------------------------------------------------------------------------

## API Layer

Framework: FastAPI

Endpoint:

POST /predict

Accepts: - Uploaded file (image or video) - URL (image)

Returns JSON response:

Image Example:

{ "type": "image", "stage1": "BigCat", "species": "jaguar",
"confidence": 0.94 }

Video Example:

{ "type": "video", "stage1": "BigCat", "species": "leopard",
"bigcat_frame_ratio": 0.72 }

------------------------------------------------------------------------

## Project Structure

bigcat_api/ │ ├── app.py ├── utils.py ├── models/ │ ├──
stage1_bigcat_efficientnet_b2.pth │ ├──
stage2_species_efficientnet_b2.pth │ └── stage2_class_mapping.json ├──
requirements.txt

------------------------------------------------------------------------

## Deployment Ready

This system supports:

-   Image inference
-   Short video inference (≤20s)
-   URL-based image prediction
-   REST API integration
-   Swagger documentation (FastAPI auto-generated)

------------------------------------------------------------------------

## Future Improvements

-   Add uncertainty threshold handling
-   Add logging and monitoring
-   Dockerize for cloud deployment
-   Add authentication & rate limiting
-   Extend to Stage 4 (Individual Jaguar Re-ID)

------------------------------------------------------------------------

Final Status: Multi-Stage AI Wildlife Classification System Completed.
