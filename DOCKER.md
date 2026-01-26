# Jaguar Re-ID System - Docker Setup

This project uses Docker Compose to run both the frontend and backend services.

## Prerequisites

- Docker Desktop installed
- Docker Compose installed (included with Docker Desktop)

## Quick Start

Run the entire application with a single command:

```bash
docker-compose up --build
```

The services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Commands

### Build and start all services
```bash
docker-compose up --build
```

### Run in detached mode (background)
```bash
docker-compose up -d
```

### Stop all services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild specific service
```bash
docker-compose build backend
docker-compose build frontend
```

### Stop and remove all containers, networks, and volumes
```bash
docker-compose down -v
```

## Service Details

### Backend (FastAPI)
- Port: 8000
- Features:
  - Automatic GPU/CPU detection
  - YOLO-based jaguar detection
  - ConvNeXT Re-ID model
  - Health check endpoint

### Frontend (React + Vite)
- Port: 3000
- Built with:
  - React 19
  - TypeScript
  - Tailwind CSS v3
  - shadcn/ui components
  - Framer Motion animations

## Environment Variables

You can customize settings by creating a `.env` file:

```env
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## Notes

- The backend will automatically download the YOLO model on first run
- Make sure the `models/convnext_arcface_jaguar_final.pth` file exists in `src/backend/models/`
- Frontend is served via Nginx in production mode
- Both services are connected via a Docker network

## Troubleshooting

### Port already in use
If ports 3000 or 8000 are already in use, modify the `docker-compose.yml` file:

```yaml
ports:
  - "8080:8000"  # Change 8000 to another port
```

### GPU Support
For GPU support, install nvidia-docker and modify `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```
