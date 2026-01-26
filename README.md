# 🐆 Jaguar Re-Identification System

Advanced AI-powered pattern recognition system for identifying individual jaguars from their unique coat patterns using deep learning and computer vision.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![Node](https://img.shields.io/badge/node-20-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## 🌟 Features

- **Advanced AI Detection**: YOLO-based jaguar detection in images
- **Precise Segmentation**: SAM (Segment Anything Model) for accurate coat pattern extraction
- **Re-Identification**: ConvNeXt-based feature extraction for individual identification
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
AI Pipeline: YOLO → SAM → ConvNeXt → Similarity Score
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Running with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/patterns-ai-wildlife.git
cd patterns-ai-wildlife

# Start services (auto port detection)
./start.ps1 --build

# Or using docker-compose directly
docker compose up --build
```

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

### Endpoints

#### `POST /predict`
Compare two jaguar images and return similarity score.

**Request:**
- Multipart form data with:
  - `files`: Two image files, OR
  - `url1` & `url2`: Image URLs

**Response:**
```json
{
  "similarity": 0.8298,
  "image1_name": "jaguar1.jpg",
  "image2_name": "jaguar2.jpg"
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "device": "cpu"
}
```

Full API documentation available at: http://localhost:8000/docs

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

Required models (downloaded automatically on first run):

1. **YOLO**: `yolov8n.pt` (included in repo)
2. **SAM**: `sam_vit_b_01ec64.pth` (included in repo)
3. **ConvNeXt**: Downloaded from PyTorch Hub on startup
4. **Re-ID Model**: `convnext_arcface_jaguar_final.pth` (in `models/` directory)

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

Test the system with example images:

```bash
cd src/backend
python test_jaguar_reid.py
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
