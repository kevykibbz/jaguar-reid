# Production Deployment Guide

## Environment Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Frontend port (default: 80 for production)
FRONTEND_PORT=80

# Optional: Backend configuration
BACKEND_PORT=8000

# Optional: Resource allocation
BACKEND_MEMORY_LIMIT=4G
BACKEND_CPU_LIMIT=2.0
```

### 2. Build for Production

```bash
# Build images without cache
docker compose -f docker-compose.production.yml build --no-cache

# Or use the startup script with auto port detection
./start.ps1 --build
```

### 3. Deploy

```bash
# Start services in detached mode
docker compose -f docker-compose.production.yml up -d

# View logs
docker compose -f docker-compose.production.yml logs -f

# Check service health
docker compose -f docker-compose.production.yml ps
```

### 4. Configuration Details

#### API Routing
- Frontend uses `/api` prefix for all backend requests
- Nginx reverse proxy handles routing: `http://yourdomain.com/api/predict` → `http://backend:8000/predict`
- No CORS issues since requests go through same origin

#### Static Asset Caching
- Static files (JS, CSS, images): 1 year cache
- index.html: No cache (for updates)
- API responses: Not cached

#### Timeouts & Limits
- Max upload size: 50MB (adjust in nginx.conf if needed)
- API timeout: 300 seconds (5 minutes)
- Connection timeout: 300 seconds

### 5. Scaling for Production

#### Add HTTPS with Traefik

```yaml
# Add to docker-compose.production.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.email=your-email@example.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - jaguar-network

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=myresolver"
```

#### External Backend (Cloud)

If deploying backend separately (e.g., Azure, AWS):

1. Update nginx.conf:
```nginx
location /api/ {
    proxy_pass https://your-backend-api.com/;
    # ... rest of proxy settings
}
```

2. Or use environment variable at build time:
```bash
docker build --build-arg BACKEND_URL=https://api.example.com ./src/frontend
```

### 6. Monitoring & Logs

```bash
# View real-time logs
docker compose logs -f backend frontend

# Check container stats
docker stats jaguar-reid-backend jaguar-reid-frontend

# Health checks
curl http://localhost/health
curl http://localhost:8000/health
```

### 7. Updates & Rollback

```bash
# Update application
git pull
docker compose -f docker-compose.production.yml up -d --build

# Rollback to previous version
docker compose -f docker-compose.production.yml down
# Restore previous code version
docker compose -f docker-compose.production.yml up -d
```

### 8. Backup Model Files

```bash
# Backup trained models
docker cp jaguar-reid-backend:/app/models ./backups/models-$(date +%Y%m%d)

# Restore models
docker cp ./backups/models-20260126 jaguar-reid-backend:/app/models
```

## Production Checklist

- [ ] Set environment variables in `.env` file
- [ ] Update nginx.conf with production domain
- [ ] Configure firewall rules (allow 80, 443)
- [ ] Set up SSL/TLS certificates
- [ ] Configure monitoring and alerting
- [ ] Set up automated backups
- [ ] Test health check endpoints
- [ ] Verify API routing through `/api` prefix
- [ ] Test image upload with large files (up to 50MB)
- [ ] Set up log rotation
- [ ] Configure resource limits
- [ ] Test auto-restart on failure

## Architecture

```
Internet → [Port 80/443] → Nginx (Frontend Container)
                              ↓
                         /api/* requests → Backend Container (port 8000)
                              ↓
                         Static files → Served from nginx
```

Benefits:
- ✅ Single port exposed (80/443)
- ✅ No CORS issues
- ✅ SSL termination at nginx
- ✅ Static file caching
- ✅ Load balancing ready
- ✅ Environment agnostic (dev/staging/prod)
