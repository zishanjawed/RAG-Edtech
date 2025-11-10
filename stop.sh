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
print_header() { echo ""; echo -e "${GREEN}===== $1 =====${NC}"; echo ""; }

print_header "RAG-Edtech Platform Shutdown"

print_info "Stopping frontend..."

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend stopped"
    fi
    rm .frontend.pid
fi

if lsof -ti:5173 >/dev/null 2>&1; then
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
fi

print_info "Stopping Docker services..."
docker-compose down

print_success "All services stopped"

echo ""
read -p "Remove all data volumes? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Removing volumes..."
    docker-compose down -v
    print_success "Data removed"
else
    print_info "Data preserved"
fi

print_header "Platform Stopped"

echo "To start again: ./start.sh"
echo ""
