# Proxmox/Portainer Deployment Guide

## GitHub Integration with Portainer

### Option 1: Auto-build from GitHub (Recommended)

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial Whisper AI service"
   git remote add origin https://github.com/earlysvahn/whisper-transcribe-api.git
   git push -u origin main
   ```

2. **In Portainer**:
   - Go to **Stacks** → **Add Stack**
   - Choose **Repository** method
   - Repository URL: `https://github.com/earlysvahn/whisper-transcribe-api`
   - Compose path: `docker-compose.proxmox.yml`
   - Enable **GitOps updates** for auto-redeploy on push
   - Deploy

### Option 2: Pre-built Docker Images (GitHub Actions)

1. **Create `.github/workflows/docker.yml`**:
   ```yaml
   name: Build and Push Docker Image

   on:
     push:
       branches: [ main ]

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Build and push
           uses: docker/build-push-action@v3
           with:
             file: Dockerfile.cpu
             push: true
             tags: earlysvahn/whisper-transcribe-api:latest
   ```

2. **In Portainer**:
   - Use `image: earlysvahn/whisper-transcribe-api:latest`
   - Enable **Auto-update** for automatic image pulls

### Option 3: Manual Upload

1. **Export/Import Stack**:
   - Copy `docker-compose.proxmox.yml` content
   - Paste into Portainer Stack editor
   - Deploy manually

## Model Recommendations for Low-Resource Hardware

### Performance Comparison (CPU-only):

| Model | Size | RAM Usage | Processing Time* | Quality |
|-------|------|-----------|------------------|---------|
| `tiny` | 39MB | ~200MB | 10-15s | Basic |
| `small` | 244MB | ~500MB | 30-60s | Good |
| `base` | 74MB | ~300MB | 20-40s | Balanced |

*For 10-second audio on 2-core CPU

### Recommended Settings:

- **Ultra-low resources**: `WHISPER_MODEL_SIZE=tiny`
- **Acceptable performance**: `WHISPER_MODEL_SIZE=base`
- **Best quality (if you can wait)**: `WHISPER_MODEL_SIZE=small`

## Deployment Steps

1. **Create GitHub repo** with these files:
   ```
   whisper-transcribe-api/
   ├── main.py
   ├── requirements.txt
   ├── Dockerfile.cpu
   ├── docker-compose.proxmox.yml
   └── README.md
   ```

2. **In Portainer**:
   - Stacks → Add Stack → Repository
   - URL: `https://github.com/earlysvahn/whisper-transcribe-api`
   - Compose file: `docker-compose.proxmox.yml`
   - Environment variables (optional):
     ```
     WHISPER_MODEL_SIZE=tiny
     ```

3. **Test deployment**:
   ```bash
   curl http://your-proxmox-ip:8000/health
   ```

## Troubleshooting

- **Slow startup**: Increase `start_period` in healthcheck
- **Out of memory**: Use `tiny` model or increase RAM limit
- **Port conflicts**: Change `8000:8000` to `8001:8000`
- **Build failures**: Check logs in Portainer, ensure all files are in repo

## Auto-Updates

Enable GitOps in Portainer to automatically redeploy when you push to main branch. Changes will be picked up within 5 minutes.