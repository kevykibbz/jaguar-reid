# 🐆 Jaguar Re-Identification System

Advanced AI-powered pattern recognition system for identifying individual jaguars from their unique coat patterns using deep learning and computer vision.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![Node](https://img.shields.io/badge/node-20-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## 🌟 Features

- **Species Validation**: Automatic jaguar detection and validation before processing
- **Advanced AI Detection**: YOLO-based animal detection with species classification
- **Precise Segmentation**: SAM (Segment Anything Model) for accurate coat pattern extraction
- **Individual Re-Identification**: ConvNeXt-based feature extraction to identify individual jaguars
- **Database Management**: SQLite database with Azure Blob Storage support for images
- **Species Analysis**: Comprehensive biological analysis including subspecies, physical traits, and conservation status
- **Gallery & Dashboard**: View all registered jaguars, activity feed, and statistics
- **Web Interface**: Modern React/TypeScript frontend with dark mode support
- **REST API**: FastAPI backend with comprehensive endpoints
- **Docker Ready**: Full containerization for easy deployment
- **CPU Optimized**: Automatic detection and installation of CPU/GPU PyTorch variants

## 🏗️ Architecture

```
Frontend (React + Vite)
    ↓ /api/* requests
Nginx Reverse Proxy
    ↓
Backend (FastAPI)
    ↓
AI Pipeline:
  1. YOLO Detection → Species Validation
  2. SAM Segmentation → Pattern Extraction
  3. ConvNeXt Embedding → Feature Vector (512-dim)
  4. Database Search → Match or Register
    ↓
SQLite Database + Azure Blob Storage
```

## 🔄 Identification Workflow

```
1. Upload Image
   ↓
2. YOLO Detection
   ↓
3. ❓ Is it a jaguar?
   → NO: Reject with error
   → YES: Continue
   ↓
4. SAM Segmentation (optional)
   ↓
5. Extract 512-dim Embedding
   ↓
6. Search Database (Cosine Similarity)
   ↓
7. ✅ Match Found (>75% similarity)
   → Display jaguar info
   OR
   ❌ No Match
   → Prompt to register new jaguar
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Python 3.8+ (for downloading models)

### Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/patterns-ai-wildlife.git
cd patterns-ai-wildlife

# 2. Start services (auto port detection)
./start.ps1 --build

# Or using docker-compose directly
docker compose up --build
```

The application will be available at:
- **Frontend**: http://localhost:3000 (or next available port)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd src/backend
pip install -r requirements.txt
python start_dev.py
```

#### Frontend

```bash
cd src/frontend
npm install
npm run dev
```

## 📁 Project Structure

```
patterns-ai-wildlife/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # AI model loading
│   │   ├── preprocessing.py     # Image processing
│   │   ├── config.py            # Configuration
│   │   ├── animal_filter.py     # Stage 0 animal filter
│   │   ├── species_classifier.py # Stage 2 species classifier
│   │   ├── database/            # SQLite/PostgreSQL data access
│   │   ├── services/            # Azure storage integration
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── _test/               # Organized backend tests
│   │   └── Dockerfile
│   └── frontend/
│       ├── src/
│       │   ├── components/      # React components
│       │   ├── pages/           # Route-level UI pages
│       │   ├── services/        # API service layer
│       │   ├── lib/             # Utilities
│       │   └── App.tsx
│       ├── package.json
│       ├── nginx.conf           # Reverse proxy config
│       ├── nginx.conf.template  # Runtime BACKEND_URL injection
│       ├── entrypoint.sh        # Nginx config substitution
│       └── Dockerfile
├── docker-compose.yml           # Development setup
├── docker-compose.production.yml # Production setup
├── deploy-to-azure.ps1          # Azure Container Apps deploy script
├── start.ps1                    # Auto port detection script
├── AZURE_DEPLOYMENT.md          # Azure deployment notes
└── README.md
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PyTorch**: Deep learning framework
- **Ultralytics YOLO**: Object detection
- **Segment Anything (SAM)**: Image segmentation
- **ConvNeXt**: Feature extraction for re-identification
- **OpenCV**: Image processing
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool
- **TailwindCSS**: Styling
- **Shadcn/ui**: Component library
- **Framer Motion**: Animations

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy & static file serving
- **Docker Compose**: Multi-container orchestration

## 📖 API Documentation

### Core Endpoints

#### `POST /classify`
Classify image or video through the three-stage pipeline.

**Request:**
- `file`: Image file, OR
- `image_url`: Image URL

Also supports JSON body:

```json
{ "image_url": "https://..." }
```

**Response (Animal / BigCat / Species):**
```json
{
  "success": true,
  "input_type": "image",
  "stage0": {
    "is_animal": true,
    "label": "jaguar",
    "confidence": 0.97
  },
  "stage1": {
    "is_bigcat": true,
    "confidence": 0.95
  },
  "stage2": {
    "species": "jaguar",
    "confidence": 0.92
  }
}
```

**Response (Non-animal example):**
```json
{
  "success": true,
  "input_type": "image",
  "stage0": {
    "is_animal": false,
    "label": "dining table, board",
    "confidence": 0.58
  },
  "stage1": null,
  "stage2": null,
  "message": "Image detected as non-animal: dining table, board (confidence: 58.44%)"
}
```

#### `POST /predict`
Compatibility endpoint (delegates to `/classify`).

**Request:**
- `files`: file list (first file is used), OR
- `url1` / `url2` for URL-based compatibility usage

#### `POST /predict/url`
Classify from JSON URL payload.

#### `POST /predict/binary`
Return stage-1 big-cat binary result.

#### `POST /predict/species`
Return stage-2 species result.

### Database Endpoints

#### `GET /jaguars`
List all registered jaguars.

#### `GET /statistics`
Get database statistics (total jaguars, images, sightings).

#### `GET /recent-activity`
Get recent activity feed (registrations and matches).

#### `GET /health`
Health check endpoint.

Full interactive API documentation available at: **http://localhost:8000/docs**

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Frontend port (auto-detected by start.ps1)
FRONTEND_PORT=3000

# Backend configuration
BACKEND_PORT=8000
PYTHONUNBUFFERED=1

# Production DB mode
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://username:password@host/database?sslmode=require

# Optional Azure image storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER=jaguar-images

# Frontend proxy target (containers)
BACKEND_URL=http://backend:8000
```

### CPU vs GPU

The system automatically detects CUDA availability:
- **With GPU**: Installs CUDA-enabled PyTorch (~2GB)
- **Without GPU**: Installs CPU-only PyTorch (~800MB)
- **Processing time**: GPU ~1 minute, CPU ~5-10 minutes per comparison

## 📦 Model Files

Core pipeline models used by backend:

1. `stage1_bigcat_efficientnet_b2.pth` - big cat vs non-big-cat
2. `stage2_species_efficientnet_b2.pth` - species classification (cheetah/jaguar/leopard/lion/tiger)
3. `models/mappings/stage2_class_mapping.json` - label mapping

## 💾 Data Storage

### Local Storage
- **Database**: SQLite (`database/jaguars.db`)
- **Images**: `database/images/` directory

### Azure Blob Storage (Optional)
- Configure in `.env`:
  ```bash
  AZURE_STORAGE_CONNECTION_STRING=your_connection_string
  AZURE_STORAGE_CONTAINER=jaguar-images
  ```
- Automatically uploads images when configured
- Falls back to local storage if unavailable

## 🚢 Deployment

### Development

```bash
docker compose up
```

### Production

```bash
docker compose -f docker-compose.production.yml up -d
```

### Azure Container Apps

```bash
./deploy-to-azure.ps1
```

Important Azure notes:
- Frontend nginx proxy must use internal backend URL: `http://jaguar-reid-backend`
- Backend requires `DATABASE_URL` when `DATABASE_TYPE=postgresql`
- Deployment script now falls back to root `.env` for missing `DATABASE_URL` and `AZURE_STORAGE_CONNECTION_STRING`
- Validate deployment with:
  - `https://<frontend>/api/health`
  - `https://<frontend>/api/statistics`

## 🧪 Testing

### Test Species Validation

```bash
# Test with jaguar image (should succeed)
curl -X POST "http://localhost:8000/classify" \
  -F "file=@path/to/jaguar.jpg"

# Test with non-jaguar image (should reject)
curl -X POST "http://localhost:8000/classify" \
  -F "file=@path/to/dog.jpg"
# Expected: stage0/stage1 result showing non-animal or non-big-cat
```

### Test Image Comparison

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "files=@image1.jpg"
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- YOLO by Ultralytics
- Segment Anything (SAM) by Meta AI
- ConvNeXt architecture by Facebook AI Research
- Wildlife conservation organizations for inspiration

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🔗 Links

- [Azure Deployment Notes](AZURE_DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/docs)

---

Made with ❤️ for wildlife conservation
