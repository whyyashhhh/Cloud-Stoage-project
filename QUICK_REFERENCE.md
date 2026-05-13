# Quick Reference Guide

## 🚀 Getting Started - 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- Google Cloud credentials (optional)

### Quick Start

```bash
cd "cloud project"
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d
```

Access:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 Common Commands

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Remove volumes (reset database)
docker-compose down -v

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Rebuild images
docker-compose build

# Rebuild and start
docker-compose up -d --build

# Execute command in container
docker-compose exec backend python manage.py migrate
```

### Database Commands

```bash
# Connect to database
docker-compose exec postgres psql -U clouduser -d cloud_storage

# Common psql commands
\dt                    # List tables
SELECT * FROM users;   # Query users
SELECT * FROM files;   # Query files
\q                     # Quit
```

### Backend Commands

```bash
# Install new dependency
docker-compose exec backend pip install package-name

# Run migrations
docker-compose exec backend python -c "from models import Base; from config import DATABASE_URL; from sqlalchemy import create_engine; Base.metadata.create_all(create_engine(DATABASE_URL))"

# Test API
python test_api.py
```

## 🔌 API Endpoints

### Authentication
```
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Files
```
POST   /api/v1/files/upload
GET    /api/v1/files
GET    /api/v1/files/{id}/download
DELETE /api/v1/files/{id}
```

### System
```
GET /api/v1/health
GET /
```

## 🔐 Testing API with curl

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"password123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"password123"}'
```

### Get User Info
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Files
```bash
curl http://localhost:8000/api/v1/files \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Upload File
```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/file.txt"
```

### Download File
```bash
curl http://localhost:8000/api/v1/files/1/download \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded_file.txt
```

### Delete File
```bash
curl -X DELETE http://localhost:8000/api/v1/files/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📂 File Structure Reference

```
cloud project/
├── backend/
│   ├── app.py              → Main FastAPI application
│   ├── models.py           → Database models (User, File)
│   ├── auth.py             → Authentication logic
│   ├── gcs_service.py      → Google Cloud Storage integration
│   ├── config.py           → Configuration
│   ├── requirements.txt     → Python dependencies
│   ├── Dockerfile          → Backend container image
│   └── .dockerignore
├── frontend/
│   ├── index.html          → Main dashboard
│   ├── styles.css          → Responsive styling
│   ├── script.js           → Client-side logic
│   ├── nginx.conf          → Nginx configuration
│   ├── Dockerfile          → Frontend container
│   └── .dockerignore
├── docker-compose.yml      → Service orchestration
├── .env.example            → Environment template
├── .gitignore             → Git ignore rules
├── test_api.py            → API testing script
├── README.md              → Full documentation
├── SETUP.md               → Setup guide
├── DEPLOYMENT.md          → Deployment guide
└── SUMMARY.md             → Project summary
```

## 🔑 Environment Variables

```env
# Database
DB_USER=clouduser
DB_PASSWORD=your_password
DB_NAME=cloud_storage

# JWT
SECRET_KEY=your-secret-key

# Google Cloud Storage
GCS_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=/app/credentials.json
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port
# Windows
netstat -ano | findstr :PORT_NUMBER
taskkill /PID PID_NUMBER /F

# macOS/Linux
lsof -i :PORT_NUMBER
kill -9 PID_NUMBER
```

### Docker Won't Start
```bash
# Check Docker daemon
docker ps

# Restart Docker
# Windows/macOS: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

### Database Connection Error
```bash
# Check logs
docker-compose logs postgres

# Verify connection string in .env
# Format: postgresql://user:password@host:port/database
```

### API Not Responding
```bash
# Check if backend is running
docker-compose ps

# View backend logs
docker-compose logs backend

# Test health check
curl http://localhost:8000/api/v1/health
```

## 📱 Frontend Usage

1. **Sign Up**: Create new account with username, email, password
2. **Login**: Use credentials to login
3. **Upload**: Drag files or click upload area
4. **Download**: Click download button on file
5. **Delete**: Click delete button to remove file
6. **Logout**: Click logout button in header

## 🔄 Development Workflow

### Make Changes to Backend
1. Edit code in `backend/`
2. Changes auto-reload with `--reload` flag
3. Test via http://localhost:8000/docs

### Make Changes to Frontend
1. Edit `frontend/index.html`, `styles.css`, or `script.js`
2. Refresh browser (Ctrl+R or Cmd+R)
3. Check console for errors (F12)

### Add Python Dependency
```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# Rebuild container
docker-compose build backend
docker-compose up -d backend
```

## 🚀 Deployment Quick Commands

### Google Cloud Run
```bash
# Deploy backend
gcloud run deploy cloud-storage \
  --source=./backend \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

### AWS ECS
```bash
# Build and push
docker build -t cloud-storage:latest ./backend
docker tag cloud-storage:latest YOUR_ECR_URL/cloud-storage:latest
docker push YOUR_ECR_URL/cloud-storage:latest
```

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend

# Follow logs
docker-compose logs -f backend

# Last N lines
docker-compose logs --tail=100 backend
```

### Database Queries
```bash
# Connect to database
docker-compose exec postgres psql -U clouduser -d cloud_storage

# Check users
SELECT id, username, email, created_at FROM users;

# Check files
SELECT id, original_filename, file_size, owner_id FROM files;

# Check file count per user
SELECT owner_id, COUNT(*) FROM files GROUP BY owner_id;
```

## 🔒 Security Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Use strong database password
- [ ] Restrict API ALLOWED_ORIGINS
- [ ] Enable HTTPS for production
- [ ] Use service accounts for GCS
- [ ] Rotate credentials regularly
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Review security logs
- [ ] Update dependencies

## 📞 Support Resources

- **API Docs**: http://localhost:8000/docs
- **Main Documentation**: README.md
- **Setup Guide**: SETUP.md
- **Deployment Guide**: DEPLOYMENT.md
- **Docker Logs**: `docker-compose logs`
- **Database**: Direct psql connection

## 🎯 Next Steps

1. ✅ Run `docker-compose up -d`
2. ✅ Configure .env
3. ✅ Add GCS credentials
4. ✅ Open http://localhost:3000
5. ✅ Create account and upload files
6. ✅ Read full documentation for advanced features

---

**Pro Tip**: Always check logs first when troubleshooting!
```bash
docker-compose logs -f
```
