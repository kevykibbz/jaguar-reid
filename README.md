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

# 2. Download pre-trained models (~800MB)
python download_models.py

# 3. Start services (auto port detection)
./start.ps1 --build

# Or using docker-compose directly
docker compose up --build
```

**⚠️ Important**: You must run `python download_models.py` before building Docker images. This downloads the required AI models from Azure Storage.

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd src/backend
pip install -r requirements.txt
python install_torch.py
uvicorn main:app --reload
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
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── install_torch.py     # Auto CPU/GPU detection
│   │   └── Dockerfile
│   └── frontend/
│       ├── src/
│       │   ├── components/      # React components
│       │   ├── lib/             # Utilities
│       │   └── App.tsx
│       ├── package.json
│       ├── nginx.conf           # Reverse proxy config
│       └── Dockerfile
├── docker-compose.yml           # Development setup
├── docker-compose.production.yml # Production setup
├── start.ps1                    # Auto port detection script
├── DOCKER.md                    # Docker documentation
├── PRODUCTION.md                # Production deployment guide
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

#### `POST /identify`
Identify a jaguar from an image. Returns match if found in database, otherwise indicates new jaguar.

**Request:**
- `file`: Image file, OR
- `image_url`: Image URL

**Response (Match Found):**
```json
{
  "match": true,
  "jaguar_id": "JAG_0001",
  "jaguar_name": "Luna",
  "confidence": 0.89,
  "similarity": 0.89,
  "first_seen": "2024-01-15",
  "times_seen": 12
}
```

**Response (No Match):**
```json
{
  "match": false,
  "confidence": 0.0,
  "similarity": 0.62,
  "message": "No matching jaguar found in database"
}
```

**Error (Not a Jaguar):**
```json
{
  "detail": "This image does not appear to be a jaguar. Detected: dog (confidence: 0.95)"
}
```

#### `POST /register`
Register a new jaguar in the database with a name.

**Request:**
- `file`: Image file, OR
- `image_url`: Image URL
- `jaguar_name`: Name for the jaguar

**Response:**
```json
{
  "success": true,
  "jaguar_id": "JAG_0015",
  "jaguar_name": "Shadow",
  "message": "Jaguar registered successfully"
}
```

#### `POST /predict`
Compare two jaguar images and return similarity score.

**Request:**
- `files`: Two image files, OR
- `url1` & `url2`: Image URLs

**Response:**
```json
{
  "similarity": 0.8298,
  "same_jaguar": true,
  "confidence": 0.32
}
```

#### `POST /analyze-species`
Perform comprehensive species analysis including subspecies identification, physical characteristics, and conservation status.

**Request:**
- `file`: Image file, OR
- `image_url`: Image URL

**Response:**
```json
{
  "species": {
    "scientific_name": "Panthera onca",
    "common_name": "Jaguar",
    "detection_confidence": 0.94
  },
  "subspecies_analysis": {
    "most_likely": {
      "name": "Panthera onca onca",
      "common_name": "Amazon Jaguar",
      "confidence": 0.75,
      "region": "Amazon Basin"
    }
  },
  "pattern_analysis": {
    "rosette_density": "medium-high",
    "distinctiveness": "high - suitable for individual ID"
  },
  "physical_characteristics": {
    "body_build": "robust and muscular",
    "estimated_weight_range": "56-96 kg"
  },
  "conservation_status": {
    "iucn_status": "Near Threatened",
    "population_trend": "Decreasing"
  }
}
```

### Database Endpoints

#### `GET /jaguars`
List all registered jaguars.

#### `GET /jaguar/{jaguar_id}`
Get detailed information about a specific jaguar including all images and sighting history.

#### `GET /statistics`
Get database statistics (total jaguars, images, sightings).

#### `GET /recent-activity`
Get recent activity feed (registrations and matches).

#### `GET /gallery`
Get recent images gallery across all jaguars.

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
```

### CPU vs GPU

The system automatically detects CUDA availability:
- **With GPU**: Installs CUDA-enabled PyTorch (~2GB)
- **Without GPU**: Installs CPU-only PyTorch (~800MB)
- **Processing time**: GPU ~1 minute, CPU ~5-10 minutes per comparison

## 📦 Model Files

Required models (downloaded via `download_models.py`):

1. **YOLO**: `yolov8n.pt` - Object detection (~6MB)
2. **SAM**: `sam_vit_b_01ec64.pth` - Segmentation (~375MB)
3. **ConvNeXt Re-ID**: `convnext_arcface_jaguar_final.pth` - Individual identification (~412MB)

Total download size: ~800MB

## 💾 Data Storage

### Local Storage
- **Database**: SQLite (`database/jaguars.db`)
- **Images**: `database/images/` directory

### Azure Blob Storage (Optional)
- Configure in `.env`:
  ```bash
  AZURE_STORAGE_CONNECTION_STRING=your_connection_string
  AZURE_STORAGE_CONTAINER_NAME=jaguar-images
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

See [PRODUCTION.md](PRODUCTION.md) for complete deployment guide including:
- HTTPS setup with Traefik
- Resource limits
- Scaling strategies
- Monitoring and logs
- Backup procedures

## 🧪 Testing

### Test Species Validation

```bash
# Test with jaguar image (should succeed)
curl -X POST "http://localhost:8000/identify" \
  -F "file=@path/to/jaguar.jpg"

# Test with non-jaguar image (should reject)
curl -X POST "http://localhost:8000/identify" \
  -F "file=@path/to/dog.jpg"
# Expected: {"detail": "This image does not appear to be a jaguar..."}
```

### Test Registration

```bash
curl -X POST "http://localhost:8000/register" \
  -F "file=@path/to/jaguar.jpg" \
  -F "jaguar_name=Luna"
```

### Test Image Comparison

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"
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

- [Docker Documentation](DOCKER.md)
- [Production Deployment Guide](PRODUCTION.md)
- [API Documentation](http://localhost:8000/docs)

---

Made with ❤️ for wildlife conservation
