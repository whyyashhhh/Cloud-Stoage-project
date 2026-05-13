# Deployment Guide - Cloud Storage Application

This guide covers deploying the Cloud Storage application to various cloud platforms.

## Table of Contents

1. [Google Cloud Deployment](#google-cloud-deployment)
2. [AWS Deployment](#aws-deployment)
3. [Azure Deployment](#azure-deployment)
4. [DigitalOcean Deployment](#digitalocean-deployment)
5. [Scaling Considerations](#scaling-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Google Cloud Deployment

### Architecture

```
┌─────────────────┐
│   Cloud Load    │
│    Balancer     │
└────────┬────────┘
         │
    ┌────┴─────┐
    │           │
┌───▼──┐  ┌────▼───┐
│Cloud │  │Cloud   │
│Run   │  │Run     │
│(API) │  │(API)   │
└───┬──┘  └────┬───┘
    │           │
    └────┬──────┘
         │
    ┌────▼───────┐
    │  Cloud SQL │
    │(PostgreSQL)│
    └────┬───────┘
         │
    ┌────▼─────────┐
    │ Cloud Storage│
    │   (GCS)      │
    └──────────────┘
```

### Step 1: Prepare for Deployment

```bash
# Set project variables
export PROJECT_ID="cloud-storage-app"
export REGION="us-central1"
export BACKEND_IMAGE="gcr.io/$PROJECT_ID/backend"
export DATABASE_INSTANCE="cloud-storage-db"

# Set Google Cloud project
gcloud config set project $PROJECT_ID
```

### Step 2: Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create $DATABASE_INSTANCE \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=$REGION \
  --availability-type=REGIONAL \
  --backup-start-time=03:00 \
  --enable-bin-log

# Create database
gcloud sql databases create cloud_storage \
  --instance=$DATABASE_INSTANCE

# Create user
gcloud sql users create clouduser \
  --instance=$DATABASE_INSTANCE \
  --password=your-secure-password

# Get instance connection string
gcloud sql instances describe $DATABASE_INSTANCE \
  --format='value(connectionName)'
```

### Step 3: Build and Push Docker Image

```bash
# Configure Docker authentication
gcloud auth configure-docker

# Build backend image
docker build -t $BACKEND_IMAGE:latest ./backend

# Push to Container Registry
docker push $BACKEND_IMAGE:latest
```

### Step 4: Deploy Backend to Cloud Run

```bash
# Deploy backend
gcloud run deploy cloud-storage-backend \
  --image $BACKEND_IMAGE:latest \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --allow-unauthenticated \
  --set-env-vars=\
GCS_PROJECT_ID=$PROJECT_ID,\
GCS_BUCKET_NAME=cloud-storage-files,\
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))"),\
DATABASE_URL=postgresql://clouduser:password@/cloud_storage?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME

# Get service URL
BACKEND_URL=$(gcloud run services describe cloud-storage-backend \
  --region $REGION --format='value(status.url)')
echo $BACKEND_URL
```

### Step 5: Deploy Frontend to Firebase Hosting

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize Firebase project
firebase init hosting

# Build and deploy
firebase deploy --only hosting
```

### Step 6: Set Up Monitoring

```bash
# Create uptime check
gcloud monitoring uptime-checks create \
  --display-name="Cloud Storage Backend Health" \
  --resource-type="uptime-url" \
  --monitored-resource-type="uptime-url" \
  --http-check-path="/api/v1/health" \
  --host=$BACKEND_URL

# Create alerting policy
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Cloud Storage Alert"
```

## AWS Deployment

### Architecture

```
┌──────────────┐
│  CloudFront  │
│(CDN)         │
└──────┬───────┘
       │
  ┌────┴────┐
  │          │
┌─▼──────┐ ┌┴─────────┐
│S3      │ │ ALB      │
│(HTML)  │ │(Load Bal)│
└────────┘ └────┬─────┘
                │
           ┌────┴──────┐
           │            │
        ┌──▼─┐ ┌───────▼──┐
        │ECS │ │ ECS      │
        │    │ │          │
        └────┘ └──────────┘
           │
      ┌────▼──────┐
      │ RDS       │
      │PostgreSQL │
      └───────────┘
```

### Deployment Steps

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name cloud-storage-backend

# 2. Build and push image
docker build -t cloud-storage-backend:latest ./backend
docker tag cloud-storage-backend:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cloud-storage-backend:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cloud-storage-backend:latest

# 3. Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier cloud-storage-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username clouduser \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20

# 4. Create ECS cluster
aws ecs create-cluster --cluster-name cloud-storage

# 5. Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 6. Create ECS service
aws ecs create-service \
  --cluster cloud-storage \
  --service-name backend \
  --task-definition backend:1 \
  --desired-count 2

# 7. Deploy frontend to S3
aws s3 sync ./frontend/ s3://cloud-storage-frontend/

# 8. Set up CloudFront distribution
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json
```

## Azure Deployment

### Architecture

```
┌──────────────┐
│ Azure CDN    │
└──────┬───────┘
       │
  ┌────┴──────┐
  │            │
┌─▼─────┐ ┌──┴──────┐
│App    │ │App      │
│Service│ │Gateway  │
│ (Web) │ │         │
└───────┘ └──┬──────┘
             │
      ┌──────┴─────┐
      │             │
   ┌──▼──┐ ┌──────▼──┐
   │App  │ │App      │
   │Serv │ │Service  │
   │(API)│ │(API)    │
   └─────┘ └─────────┘
      │
   ┌──▼───────────────┐
   │Azure Database    │
   │PostgreSQL        │
   └──────────────────┘
```

### Deployment Steps

```bash
# 1. Create resource group
az group create \
  --name cloud-storage-rg \
  --location eastus

# 2. Create PostgreSQL database
az postgres server create \
  --resource-group cloud-storage-rg \
  --name cloud-storage-db \
  --location eastus \
  --admin-user clouduser \
  --admin-password YOUR_PASSWORD \
  --sku-name B_Gen5_2

# 3. Create Container Registry
az acr create \
  --resource-group cloud-storage-rg \
  --name cloudstorage \
  --sku Basic

# 4. Build and push image
az acr build \
  --registry cloudstorage \
  --image backend:latest \
  ./backend

# 5. Create App Service Plan
az appservice plan create \
  --name cloud-storage-plan \
  --resource-group cloud-storage-rg \
  --is-linux \
  --sku B1

# 6. Create App Service for API
az webapp create \
  --resource-group cloud-storage-rg \
  --plan cloud-storage-plan \
  --name cloud-storage-api \
  --deployment-container-image-name cloudstorage.azurecr.io/backend:latest

# 7. Create App Service for Frontend
az webapp create \
  --resource-group cloud-storage-rg \
  --plan cloud-storage-plan \
  --name cloud-storage-web \
  --runtime "node|20"

# 8. Deploy frontend
az webapp up --name cloud-storage-web --local-git
```

## DigitalOcean Deployment

### Using App Platform

```bash
# 1. Create app.yaml
cat > app.yaml << EOF
name: cloud-storage
services:
- name: backend
  github:
    repo: your-org/cloud-storage
    branch: main
  build_command: pip install -r requirements.txt
  run_command: uvicorn app:app --host 0.0.0.0 --port 8080
  http_port: 8080
  envs:
  - key: DATABASE_URL
    scope: RUN_AND_BUILD_TIME
    value: ${db.connection_string}
  - key: GCS_PROJECT_ID
    scope: RUN_AND_BUILD_TIME
    value: ${GCS_PROJECT_ID}

- name: frontend
  github:
    repo: your-org/cloud-storage
    branch: main
  source_dir: frontend
  http_port: 3000

databases:
- name: db
  engine: PG
  version: "15"
EOF

# 2. Deploy
doctl apps create --spec app.yaml
```

### Using Droplets

```bash
# 1. Create Droplet
doctl compute droplet create cloud-storage \
  --region nyc1 \
  --image ubuntu-22-04-x64 \
  --size s-1vcpu-2gb

# 2. SSH into Droplet
doctl compute ssh cloud-storage

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Clone and deploy
git clone your-repo
cd cloud-storage
docker-compose up -d

# 5. Set up SSL with Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com
```

## Scaling Considerations

### Database Scaling

```sql
-- Create indexes for better performance
CREATE INDEX idx_files_owner_id ON files(owner_id);
CREATE INDEX idx_files_created_at ON files(created_at);
CREATE INDEX idx_users_username ON users(username);

-- Enable connection pooling
ALTER SYSTEM SET max_connections = 200;
```

### Backend Scaling

```bash
# Horizontal Scaling (Multiple Instances)
# Cloud Run - Automatic scaling

# Vertical Scaling (More Resources)
gcloud run deploy cloud-storage-backend \
  --memory 4Gi \
  --cpu 4 \
  --max-instances 100
```

### Caching Strategy

```python
# Add Redis caching
from redis import Redis

redis_client = Redis(host='redis-host', port=6379, db=0)

# Cache file listings
@app.get("/api/v1/files")
def list_files(current_user: str = Depends(get_current_user)):
    cache_key = f"files:{current_user}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    files = db.query(File).filter(File.owner_id == user_id).all()
    redis_client.setex(cache_key, 3600, json.dumps(files))
    return files
```

## Monitoring and Maintenance

### Setup Monitoring

```bash
# Google Cloud Monitoring
gcloud monitoring dashboards create \
  --config-from-file=monitoring-config.yaml

# Set up alerts
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID
```

### Database Backups

```bash
# Cloud SQL automatic backups
gcloud sql backups create \
  --instance=cloud-storage-db

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=cloud-storage-db
```

### Log Analysis

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --format json

# Create log sink
gcloud logging sinks create cloud-storage-sink \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/logs
```

### Regular Maintenance

- [ ] Review and optimize slow queries
- [ ] Monitor resource utilization
- [ ] Update dependencies
- [ ] Backup database regularly
- [ ] Review security logs
- [ ] Update SSL certificates
- [ ] Monitor application performance
- [ ] Clean up old files from storage

---

**For more information, refer to cloud provider documentation**
