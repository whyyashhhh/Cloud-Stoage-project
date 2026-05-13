# Setup Guide - Cloud Storage Application

This guide provides step-by-step instructions for setting up and running the Cloud Storage application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Google Cloud Setup](#google-cloud-setup)
3. [Local Development Setup](#local-development-setup)
4. [Docker Setup](#docker-setup)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 10GB minimum

### Required Software
- Docker Desktop (v4.0+)
- Docker Compose (v2.0+)
- Git
- Python 3.11+ (for local development)
- PostgreSQL Client (psql)

### Optional Software
- Visual Studio Code
- Postman (for API testing)
- DBeaver (for database management)

## Google Cloud Setup

### Step 1: Create Google Cloud Project

```bash
# Create a new project
gcloud projects create cloud-storage-app --name="Cloud Storage App"

# Set the project
gcloud config set project cloud-storage-app

# Enable billing
gcloud billing projects link cloud-storage-app \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
  storage-api.googleapis.com \
  cloudresourcemanager.googleapis.com
```

### Step 3: Create GCS Bucket

```bash
# Create bucket
gsutil mb gs://cloud-storage-files-bucket

# Set lifecycle policy (optional - delete old files after 90 days)
gsutil lifecycle set - gs://cloud-storage-files-bucket << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
```

### Step 4: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create cloud-storage-sa \
  --display-name="Cloud Storage Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding cloud-storage-app \
  --member=serviceAccount:cloud-storage-sa@cloud-storage-app.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# Create and download JSON key
gcloud iam service-accounts keys create credentials.json \
  --iam-account=cloud-storage-sa@cloud-storage-app.iam.gserviceaccount.com
```

Place the `credentials.json` file in your project root directory.

## Local Development Setup

### Step 1: Clone Repository

```bash
cd "cloud project"
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
# Windows
notepad .env
# macOS/Linux
nano .env
```

Update the following variables in `.env`:

```env
# Database
DB_USER=clouduser
DB_PASSWORD=changeme123!
DB_NAME=cloud_storage

# JWT Secret (generate a secure one)
SECRET_KEY=your-very-secret-key-here-change-this

# Google Cloud Storage
GCS_PROJECT_ID=cloud-storage-app
GCS_BUCKET_NAME=cloud-storage-files-bucket
GCS_CREDENTIALS_PATH=./credentials.json
```

### Step 3: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Navigate back
cd ..
```

### Step 4: PostgreSQL Setup

```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
# Windows: Services > PostgreSQL start
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Create database and user
psql -U postgres

postgres=# CREATE ROLE clouduser WITH LOGIN PASSWORD 'changeme123!';
postgres=# CREATE DATABASE cloud_storage OWNER clouduser;
postgres=# \q
```

### Step 5: Run Backend

```bash
cd backend

# Activate virtual environment if not active
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Run migrations (creates tables)
python -c "from models import Base; from config import DATABASE_URL; from sqlalchemy import create_engine; engine = create_engine(DATABASE_URL); Base.metadata.create_all(engine)"

# Start backend server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**

### Step 6: Run Frontend

```bash
# In a new terminal
cd frontend

# Option 1: Using Python
python -m http.server 3000

# Option 2: Using Node.js
npx http-server -p 3000

# Option 3: Using Live Server VSCode extension
# Install extension and right-click index.html > Open with Live Server
```

Frontend will be available at: **http://localhost:3000**

### Step 7: Access Application

1. Open browser
2. Navigate to: **http://localhost:3000**
3. Sign up for a new account
4. Upload and manage files!

## Docker Setup

### Step 1: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### Step 2: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Wait for services to initialize (30-60 seconds)
sleep 30

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 3: Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

### Step 4: Verify Installation

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","version":"1.0.0"}
```

## Production Deployment

### Option 1: Google Cloud Run

```bash
# Build and push backend
gcloud builds submit ./backend \
  --tag gcr.io/cloud-storage-app/backend

# Deploy to Cloud Run
gcloud run deploy cloud-storage-backend \
  --image gcr.io/cloud-storage-app/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars \
    GCS_PROJECT_ID=cloud-storage-app,\
    GCS_BUCKET_NAME=cloud-storage-files-bucket

# Get backend URL
gcloud run services describe cloud-storage-backend --region us-central1
```

### Option 2: Google Kubernetes Engine

```bash
# Create GKE cluster
gcloud container clusters create cloud-storage-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-1 \
  --region=us-central1

# Deploy using kubectl
kubectl apply -f deployment/k8s/

# Get service IP
kubectl get services
```

### Option 3: Virtual Machine

```bash
# Create VM instance
gcloud compute instances create cloud-storage-vm \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-medium \
  --zone=us-central1-a

# SSH into VM
gcloud compute ssh cloud-storage-vm --zone=us-central1-a

# On VM:
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repository
git clone https://github.com/your-repo/cloud-storage.git
cd cloud-storage

# Copy credentials
# (Upload credentials.json file)

# Run with Docker Compose
docker-compose up -d
```

### Production Checklist

- [ ] Use strong SECRET_KEY (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure database backups
- [ ] Set up rate limiting
- [ ] Enable CORS for specific domains only
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling
- [ ] Set up health checks
- [ ] Enable audit logging

## Troubleshooting

### Docker Issues

**Error: "Port 5432 already in use"**

```bash
# Kill existing PostgreSQL
# Windows
netstat -ano | findstr :5432
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5432
kill -9 <PID>

# Or use different port in docker-compose.yml
```

**Error: "Cannot connect to Docker daemon"**

```bash
# Start Docker Desktop (Windows/macOS)
# Linux:
sudo systemctl start docker
```

### Database Issues

**Error: "database connection refused"**

```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Restart database
docker-compose down
docker-compose up -d postgres
docker-compose up -d backend
```

**Error: "relation 'users' does not exist"**

```bash
# Recreate tables
docker-compose exec backend python -c \
  "from models import Base; from config import DATABASE_URL; from sqlalchemy import create_engine; engine = create_engine(DATABASE_URL); Base.metadata.create_all(engine)"
```

### Google Cloud Issues

**Error: "Invalid credentials"**

```bash
# Verify credentials file
ls -la credentials.json

# Verify path in .env
cat .env | grep GCS_CREDENTIALS

# Test GCS access
gsutil ls gs://cloud-storage-files-bucket/
```

**Error: "Permission denied" in bucket**

```bash
# Grant permissions
gcloud projects add-iam-policy-binding cloud-storage-app \
  --member=serviceAccount:cloud-storage-sa@cloud-storage-app.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### API Issues

**Error: "CORS origin not allowed"**

- Check `ALLOWED_ORIGINS` in `backend/config.py`
- Add frontend URL to the list
- Restart backend

**Error: "Invalid token"**

```bash
# Token expired or invalid
# Logout and login again in frontend
# Or clear localStorage:
# In browser console:
localStorage.clear();
```

### Performance Issues

**Slow file uploads:**
- Check internet connection
- Increase timeout in frontend
- Use Cloud CDN for faster access

**Database slow queries:**

```bash
# Enable slow query log in PostgreSQL
docker-compose exec postgres psql -U clouduser -d cloud_storage \
  -c "SET log_statement = 'all';"
```

## Getting Help

1. **Check Logs**: `docker-compose logs <service>`
2. **API Documentation**: http://localhost:8000/docs
3. **GitHub Issues**: [Link to issues]
4. **Stack Overflow**: Tag your question with relevant technologies

## Next Steps

- Set up monitoring (Google Cloud Monitoring)
- Configure backups (Cloud SQL automatic backups)
- Set up CI/CD (Cloud Build)
- Configure CDN (Cloud CDN)
- Enable security features (Cloud Armor, Secret Manager)
- Set up logging (Cloud Logging)

---

**For more information, see the main README.md file**
