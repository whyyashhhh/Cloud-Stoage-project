#!/bin/bash
# Cloud Storage Application - Setup Script

set -e

echo "================================================"
echo "Cloud Storage Application Setup"
echo "================================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker Compose is installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Build images
echo ""
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# Check health
echo ""
echo "❤️  Checking service health..."

# Backend health check
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Backend API might still be starting..."
fi

# PostgreSQL check
if docker-compose exec postgres pg_isready -U clouduser > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL might still be starting..."
fi

echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "🌐 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "   README.md          - Full documentation"
echo "   QUICK_REFERENCE.md - Quick reference guide"
echo "   SETUP.md           - Detailed setup instructions"
echo "   DEPLOYMENT.md      - Deployment guide"
echo ""
echo "🧪 Test the API:"
echo "   python test_api.py"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "💡 View logs:"
echo "   docker-compose logs -f"
echo ""
