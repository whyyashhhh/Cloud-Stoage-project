# Cloud Storage Application

A secure, cloud-based file storage web application similar to Google Drive. Upload, download, and manage your files with ease.

## Features

✅ **User Authentication**
- Secure signup and login with JWT tokens
- Password hashing with bcrypt
- Session management

✅ **File Management**
- Upload files to Google Cloud Storage
- Download files with one click
- Delete files securely
- View all your files with details (name, size, upload date)

✅ **Cloud Storage**
- Google Cloud Storage integration
- Automatic file organization by user
- Secure file paths

✅ **Modern Frontend**
- Responsive dashboard
- Drag-and-drop file upload
- Real-time file list
- Progress indicators
- Toast notifications

✅ **Scalable Backend**
- FastAPI with high performance
- PostgreSQL database for metadata
- RESTful API design
- JWT authentication

✅ **Docker Deployment**
- Containerized services
- Docker Compose for local development
- Production-ready configuration

## Project Structure

```
cloud project/
├── backend/                 # Python FastAPI backend
│   ├── app.py             # Main FastAPI application
│   ├── models.py          # Database models
│   ├── auth.py            # Authentication logic
│   ├── gcs_service.py     # Google Cloud Storage integration
│   ├── config.py          # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Backend Docker image
│   └── .dockerignore      # Docker ignore rules
├── frontend/              # Frontend web application
│   ├── index.html        # Main HTML file
│   ├── styles.css        # Styling
│   ├── script.js         # JavaScript logic
│   ├── nginx.conf        # Nginx configuration
│   ├── Dockerfile        # Frontend Docker image
│   ├── .dockerignore     # Docker ignore rules
│   └── package.json      # NPM configuration
├── deployment/           # Deployment scripts
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Environment variables template
└── README.md            # This file
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (if not using Docker)
- Google Cloud Storage account and credentials
- Node.js 20+ (optional, for frontend development)

## Quick Start with Docker

### 1. Clone and Setup

```bash
cd "cloud project"
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your settings:

```env
# Database
DB_USER=clouduser
DB_PASSWORD=your-secure-password
DB_NAME=cloud_storage

# JWT Secret
SECRET_KEY=your-very-secret-key-change-this

# Google Cloud Storage
GCS_PROJECT_ID=your-gcs-project-id
GCS_BUCKET_NAME=your-gcs-bucket-name
GCS_CREDENTIALS_PATH=/app/credentials.json
```

### 3. Place Google Cloud Credentials

Copy your GCS credentials JSON file to the project root:

```bash
cp /path/to/your/credentials.json ./gcs-credentials.json
```

### 4. Start Services

```bash
docker-compose up -d
```

Wait for all services to start:
- PostgreSQL: http://localhost:5432
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

### 5. Access the Application

Open your browser and navigate to:

```
http://localhost:3000
```

## Local Development (Without Docker)

### Backend Setup

1. **Create virtual environment:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set environment variables:**

```bash
cp ../.env.example ../.env
# Edit .env with your values
```

4. **Run database migrations:**

```bash
# Make sure PostgreSQL is running
python -c "from models import Base; from config import DATABASE_URL; from sqlalchemy import create_engine; Base.metadata.create_all(create_engine(DATABASE_URL))"
```

5. **Start the backend:**

```bash
uvicorn app:app --reload
```

Backend will be available at: http://localhost:8000

**API Documentation:** http://localhost:8000/docs

### Frontend Setup

1. **Serve static files:**

```bash
cd frontend
python -m http.server 3000
```

Or use any static server:

```bash
npx http-server -p 3000
```

Frontend will be available at: http://localhost:3000

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
  ```json
  {
    "username": "john",
    "email": "john@example.com",
    "password": "securepassword"
  }
  ```

- `POST /api/v1/auth/login` - Login user
  ```json
  {
    "username": "john",
    "password": "securepassword"
  }
  ```

- `GET /api/v1/auth/me` - Get current user info
  - Requires: `Authorization: Bearer <token>`

### File Operations

- `POST /api/v1/files/upload` - Upload file
  - Requires: `Authorization: Bearer <token>`
  - Content-Type: `multipart/form-data`

- `GET /api/v1/files` - List all user files
  - Requires: `Authorization: Bearer <token>`

- `GET /api/v1/files/{file_id}/download` - Download file
  - Requires: `Authorization: Bearer <token>`

- `DELETE /api/v1/files/{file_id}` - Delete file
  - Requires: `Authorization: Bearer <token>`

### Health Check

- `GET /api/v1/health` - API health status

## Database Schema

### Users Table
```sql
- id (Primary Key)
- username (Unique)
- email (Unique)
- hashed_password
- created_at
- updated_at
- is_active
```

### Files Table
```sql
- id (Primary Key)
- filename (GCS path)
- original_filename
- file_size
- mime_type
- gcs_path (Unique)
- owner_id (Foreign Key → users.id)
- created_at
- updated_at
```

## Security Features

🔒 **Password Security**
- Passwords hashed with bcrypt
- Salted and secure

🔒 **Authentication**
- JWT token-based authentication
- 30-minute token expiration
- Secure token validation

🔒 **Authorization**
- Users can only access their own files
- File ownership validation on all operations

🔒 **Data Protection**
- Files stored in secure Google Cloud Storage
- Metadata encrypted in database
- HTTPS recommended for production

🔒 **Container Security**
- Non-root user in containers
- Minimal base images
- Regular security updates

## Deployment to Google Cloud

### 1. Create Google Cloud Project

```bash
gcloud projects create cloud-storage-project
gcloud config set project cloud-storage-project
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudsql.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage-api.googleapis.com
```

### 3. Create Cloud SQL Instance

```bash
gcloud sql instances create cloud-storage-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

### 4. Create Service Account

```bash
gcloud iam service-accounts create cloud-storage-app \
  --display-name="Cloud Storage App"

gcloud projects add-iam-policy-binding cloud-storage-project \
  --member=serviceAccount:cloud-storage-app@cloud-storage-project.iam.gserviceaccount.com \
  --role=roles/cloudsql.client

gcloud projects add-iam-policy-binding cloud-storage-project \
  --member=serviceAccount:cloud-storage-app@cloud-storage-project.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### 5. Create Cloud Storage Bucket

```bash
gsutil mb gs://cloud-storage-files-bucket
```

### 6. Deploy Backend to Cloud Run

```bash
gcloud run deploy cloud-storage-backend \
  --source=./backend \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=...,GCS_BUCKET_NAME=cloud-storage-files-bucket"
```

### 7. Deploy Frontend

Use Firebase Hosting or Cloud Storage + Cloud CDN:

```bash
gsutil -m cp -r ./frontend/* gs://cloud-storage-files-bucket/
```

## Docker Commands

### Build Images

```bash
docker-compose build
```

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f frontend
```

### Stop Services

```bash
docker-compose down
```

### Remove Volumes (Reset Database)

```bash
docker-compose down -v
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_USER` | Database user | `clouduser` |
| `DB_PASSWORD` | Database password | `secure_password` |
| `DB_NAME` | Database name | `cloud_storage` |
| `DATABASE_URL` | Full database URL | `postgresql://user:pass@host/db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key` |
| `GCS_PROJECT_ID` | Google Cloud Project ID | `my-project-123` |
| `GCS_BUCKET_NAME` | GCS bucket name | `my-storage-bucket` |
| `GCS_CREDENTIALS_PATH` | Path to credentials JSON | `/app/credentials.json` |

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose logs postgres

# Verify connection
psql -h localhost -U clouduser -d cloud_storage
```

### Backend Not Starting

```bash
# View detailed logs
docker-compose logs backend

# Rebuild container
docker-compose up -d --build backend
```

### Frontend Not Loading

```bash
# Check nginx configuration
docker-compose logs frontend

# Verify API connectivity
curl http://localhost:8000/api/v1/health
```

### Google Cloud Storage Errors

- Verify credentials file exists and is readable
- Check GCS project ID and bucket name
- Ensure service account has storage permissions
- Verify credentials file path in environment

## Development Tips

### Database Query Tips

```bash
# Access database
docker exec -it cloud_storage_postgres psql -U clouduser -d cloud_storage

# View tables
\dt

# Query users
SELECT * FROM users;

# Query files
SELECT * FROM files;
```

### Backend API Testing

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Interactive docs
# Visit: http://localhost:8000/docs
```

## Performance Optimization

- Implement caching for file listings
- Use CDN for static frontend assets
- Enable database indexing on frequently queried fields
- Implement file chunking for large uploads
- Use compression for API responses

## Scaling Considerations

- Use load balancer for multiple backend instances
- Implement database read replicas
- Use message queue (Redis/RabbitMQ) for async tasks
- Implement rate limiting
- Add monitoring and alerting

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
1. Check troubleshooting section
2. Review logs: `docker-compose logs`
3. Check API documentation: http://localhost:8000/docs

## Roadmap

- [ ] File sharing capabilities
- [ ] File versioning
- [ ] Advanced search
- [ ] Mobile app
- [ ] End-to-end encryption
- [ ] Collaborative editing
- [ ] Activity logs
- [ ] Storage quotas

---

**Built with ❤️ using FastAPI, React, PostgreSQL, and Google Cloud Storage**
# Cloud Storage - Mini Google Drive

A cloud-based file storage web application built with FastAPI, PostgreSQL, and Google Cloud Storage. Features user authentication, file upload/download/delete, and cloud-ready deployment.

## Features

✅ **User Authentication**
- Secure signup and login with JWT tokens
- Password hashing with bcrypt
- User session management

✅ **File Management**
- Upload files to Google Cloud Storage
- Download uploaded files
- Delete files with metadata cleanup
- List all user files with metadata
- Supports files up to 5GB

✅ **Cloud Integration**
- Google Cloud Storage for file storage
- PostgreSQL for metadata
- Scalable cloud-ready architecture

✅ **Modern Frontend**
- Responsive dashboard UI
- Drag-and-drop file upload
- Real-time file listing
- File download/delete operations
- Toast notifications

✅ **Production Ready**
- Docker support for all services
- Docker Compose orchestration
- Health checks for all services
- Security best practices
- CORS middleware enabled

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Nginx)                        │
│                  (HTML/CSS/JavaScript)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│  (REST APIs, Authentication, Business Logic)                │
└────────────────────────┬──────────────┬─────────────────────┘
                         │              │
        ┌────────────────▼─┐  ┌────────▼──────────┐
        │  PostgreSQL      │  │  Google Cloud     │
        │  (Metadata)      │  │  Storage (Files)  │
        └──────────────────┘  └───────────────────┘
```

## Project Structure

```
cloud-project/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── models.py           # SQLAlchemy models
│   ├── auth.py             # Authentication logic
│   ├── gcs_service.py      # Google Cloud Storage service
│   ├── config.py           # Configuration
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Docker image for backend
│   └── .dockerignore
├── frontend/
│   ├── index.html          # Main dashboard
│   ├── styles.css          # Styling
│   ├── script.js           # JavaScript logic
│   ├── nginx.conf          # Nginx configuration
│   ├── Dockerfile          # Frontend container
│   ├── .dockerignore
│   └── package.json
├── docker-compose.yml      # Docker Compose orchestration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Prerequisites

- **Docker & Docker Compose** (for containerized deployment)
- **Python 3.11+** (for local development)
- **PostgreSQL 15+** (for local development)
- **Google Cloud Account** with:
  - GCS bucket created
  - Service account with GCS permissions
  - Credentials JSON file

## Quick Start with Docker (Recommended)

### 1. Clone and Setup

```bash
cd "cloud project"
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your settings:

```env
# Database
DB_USER=clouduser
DB_PASSWORD=cloudpassword
DB_NAME=cloud_storage

# JWT Secret
SECRET_KEY=your-super-secret-key-change-this-in-production

# Google Cloud Storage
GCS_PROJECT_ID=your-gcs-project-id
GCS_BUCKET_NAME=your-gcs-bucket-name
GCS_CREDENTIALS_PATH=/app/credentials.json
```

### 3. Add GCS Credentials

Place your Google Cloud Storage service account credentials:

```bash
# Copy your GCS credentials JSON to the project root
cp ~/path/to/gcs-credentials.json ./gcs-credentials.json
```

### 4. Start Services

```bash
docker-compose up -d
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Stop Services

```bash
docker-compose down

# Remove data volumes too
docker-compose down -v
```

## Local Development Setup

### Prerequisites

```bash
# Install Python 3.11+
python --version

# Install PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql
# Windows: Download from https://www.postgresql.org/download/windows/
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example ../.env

# Update .env with your settings
# DATABASE_URL=postgresql://user:password@localhost:5432/cloud_storage

# Run migrations (if using alembic)
# alembic upgrade head

# Start backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Serve with Python
python -m http.server 3000

# Or use any other HTTP server
# Node.js: npx http-server -p 3000
# PHP: php -S localhost:3000
```

Then open http://localhost:3000 in your browser.

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user info

### File Management

- `POST /api/v1/files/upload` - Upload file
- `GET /api/v1/files` - List user files
- `GET /api/v1/files/{file_id}/download` - Download file
- `DELETE /api/v1/files/{file_id}` - Delete file

### Health & Status

- `GET /api/v1/health` - Health check
- `GET /` - Root endpoint

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Google Cloud Storage Setup

### 1. Create GCS Bucket

```bash
gsutil mb gs://your-bucket-name/
```

### 2. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create cloud-storage-app \
    --display-name="Cloud Storage App"

# Create key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=cloud-storage-app@PROJECT_ID.iam.gserviceaccount.com

# Grant Storage Admin role
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member=serviceAccount:cloud-storage-app@PROJECT_ID.iam.gserviceaccount.com \
    --role=roles/storage.admin
```

### 3. Set Permissions

```bash
gsutil iam ch serviceAccount:cloud-storage-app@PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://your-bucket-name/
```

## Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique, String)
- `email` (Unique, String)
- `hashed_password` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `is_active` (Boolean)

### Files Table
- `id` (Primary Key)
- `filename` (String)
- `original_filename` (String)
- `file_size` (Float)
- `mime_type` (String)
- `gcs_path` (String, Unique)
- `owner_id` (Foreign Key to Users)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## Security Features

✅ **Password Security**
- Bcrypt hashing for password storage
- Secure password verification

✅ **Authentication**
- JWT tokens with expiration
- Bearer token authentication
- Token validation on all protected routes

✅ **API Security**
- CORS middleware for cross-origin requests
- HTTPBearer security scheme
- Input validation with Pydantic

✅ **Database Security**
- Non-root database user
- Parameterized queries (SQLAlchemy ORM)

✅ **Container Security**
- Non-root user in containers
- Health checks on all services
- Minimal attack surface

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL container status
docker-compose ps

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Backend Not Starting

```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
cat .env

# Check port availability
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000
```

### Frontend Not Connecting to Backend

```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check CORS settings in backend/config.py
# Ensure frontend URL is in ALLOWED_ORIGINS
```

### GCS Authentication Error

```bash
# Verify credentials file exists
ls -la gcs-credentials.json

# Check JSON format is valid
cat gcs-credentials.json | python -m json.tool

# Verify environment variable points to correct path
echo $GCS_CREDENTIALS_PATH
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `SECRET_KEY` | JWT signing key | `your-secret-key` |
| `GCS_PROJECT_ID` | Google Cloud project ID | `my-project-123` |
| `GCS_BUCKET_NAME` | GCS bucket name | `cloud-storage-bucket` |
| `GCS_CREDENTIALS_PATH` | Path to GCS credentials JSON | `/app/credentials.json` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `5368709120` (5GB) |

## Performance Optimization

- **Database**: Indexes on `username`, `email`, and `owner_id`
- **Caching**: Static files cached for 30 days in Nginx
- **Storage**: Direct streaming for file downloads
- **Compression**: Nginx gzip compression enabled

## Deployment Options

### Cloud Platforms

1. **Google Cloud Run**
   - Deploy containerized backend
   - Pay-per-request pricing
   - Automatic scaling

2. **Azure Container Instances**
   - ACI for backend and frontend
   - Azure Database for PostgreSQL
   - Azure Blob Storage integration

3. **AWS**
   - ECS for container orchestration
   - RDS for PostgreSQL
   - S3 instead of GCS

4. **Kubernetes**
   - Use Helm charts
   - Auto-scaling and load balancing
   - Rolling updates

### Local Kubernetes

```bash
# Use Docker Desktop Kubernetes or Minikube
kubectl apply -f deployment.yaml
```

## Future Enhancements

- [ ] File sharing with granular permissions
- [ ] File versioning and restore
- [ ] Collaborative file editing
- [ ] Activity logging and audit trail
- [ ] Two-factor authentication (2FA)
- [ ] File encryption at rest
- [ ] Search and filtering
- [ ] Duplicate file detection
- [ ] Quota management per user
- [ ] Admin dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at http://localhost:8000/docs

## Changelog

### Version 1.0.0
- Initial release
- User authentication with JWT
- File upload/download/delete
- Google Cloud Storage integration
- PostgreSQL for metadata
- Docker support
- Responsive web frontend
