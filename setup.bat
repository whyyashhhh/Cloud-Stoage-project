@echo off
REM Cloud Storage Application - Setup Script for Windows

echo ================================================
echo Cloud Storage Application Setup
echo ================================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)
echo ✅ Docker is installed

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)
echo ✅ Docker Compose is installed

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    copy .env.example .env
    echo ✅ .env file created. Please edit it with your configuration.
) else (
    echo ✅ .env file already exists
)

REM Build images
echo.
echo 🔨 Building Docker images...
docker-compose build

REM Start services
echo.
echo 🚀 Starting services...
docker-compose up -d

REM Wait for services to start
echo.
echo ⏳ Waiting for services to start (30 seconds)...
timeout /t 30 /nobreak

REM Check health
echo.
echo ❤️  Checking service health...

REM Backend health check
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if errorlevel 0 (
    echo ✅ Backend API is running
) else (
    echo ⚠️  Backend API might still be starting...
)

echo.
echo ================================================
echo ✅ Setup Complete!
echo ================================================
echo.
echo 🌐 Access your application:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo 📚 Documentation:
echo    README.md          - Full documentation
echo    QUICK_REFERENCE.md - Quick reference guide
echo    SETUP.md           - Detailed setup instructions
echo    DEPLOYMENT.md      - Deployment guide
echo.
echo 🧪 Test the API:
echo    python test_api.py
echo.
echo 🛑 Stop services:
echo    docker-compose down
echo.
echo 💡 View logs:
echo    docker-compose logs -f
echo.
