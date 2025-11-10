#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo ""; echo -e "${GREEN}===== $1 =====${NC}"; echo ""; }

command_exists() { command -v "$1" >/dev/null 2>&1; }
check_port() { lsof -i :$1 >/dev/null 2>&1; }

print_header "RAG-Edtech Platform Startup"

print_info "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not installed."
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 18+."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed."
    exit 1
fi

print_success "Prerequisites verified"

print_header "Environment Setup"

if [ ! -f .env ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'
OPENAI_API_KEY=sk-proj-your-key-here
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=edtech-rag-index
JWT_SECRET=your-super-secure-secret-minimum-32-characters-change-this
MONGO_USERNAME=admin
MONGO_PASSWORD=password123
MONGO_DATABASE=rag_edtech
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=password123
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    print_warning "Please edit .env with your actual API keys!"
    read -p "Press Enter after updating .env, or Ctrl+C to exit..."
fi

source .env 2>/dev/null || true

if [ "$OPENAI_API_KEY" = "sk-proj-your-key-here" ] || [ -z "$OPENAI_API_KEY" ]; then
    print_error "OPENAI_API_KEY not set in .env file."
    exit 1
fi

if [ "$PINECONE_API_KEY" = "your-pinecone-key" ] || [ -z "$PINECONE_API_KEY" ]; then
    print_error "PINECONE_API_KEY not set in .env file."
    exit 1
fi

print_success "Environment configured"

if [ ! -f frontend/.env ]; then
    print_info "Creating frontend/.env..."
    echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env
fi

print_header "Installing Dependencies"

if [ ! -d "frontend/node_modules" ]; then
    print_info "Installing npm packages..."
    cd frontend && npm install && cd ..
    print_success "Dependencies installed"
else
    print_info "Dependencies already installed"
fi

print_header "Starting Backend Services"

print_info "Starting Docker Compose services..."
docker-compose up -d

print_success "Backend services started"

print_header "Waiting for Services"

check_service() {
    local url=$1
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    return 1
}

print_info "Waiting for API Gateway..."
if check_service "http://localhost:8000/health"; then
    print_success "API Gateway ready"
else
    print_warning "API Gateway health check timed out"
fi

print_header "Starting Frontend"

if check_port 5173; then
    print_info "Killing existing process on port 5173..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

print_info "Starting Vite development server..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 5

if ps -p $FRONTEND_PID > /dev/null; then
    print_success "Frontend server started (PID: $FRONTEND_PID)"
    echo $FRONTEND_PID > .frontend.pid
else
    print_error "Frontend failed to start. Check frontend.log"
fi

print_header "Platform Running"

echo ""
echo "Frontend:         http://localhost:5173"
echo "API Gateway:      http://localhost:8000"
echo "API Docs:         http://localhost:8000/docs"
echo "RabbitMQ UI:      http://localhost:15672 (admin/password123)"
echo ""
echo "Default Login:"
echo "  Student:  tony.stark@avengers.com / TestPass@123"
echo "  Teacher:  steve.rogers@avengers.com / TestPass@123"
echo ""
echo "Commands:"
echo "  View logs:      docker-compose logs -f"
echo "  Stop all:       ./stop.sh"
echo ""

read -p "Watch service logs? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    docker-compose logs -f
fi
