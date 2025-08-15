#!/bin/bash

# PlexCacheUltra Startup Script
# This script provides an easy way to start PlexCacheUltra without Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="plexcache-ultra"
IMAGE_NAME="plexcache-ultra"
PORT="5443"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if container exists
container_exists() {
    docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to check if container is running
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to stop and remove existing container
cleanup_container() {
    if container_exists; then
        print_status "Stopping existing container..."
        docker stop ${CONTAINER_NAME} > /dev/null 2>&1 || true
        print_status "Removing existing container..."
        docker rm ${CONTAINER_NAME} > /dev/null 2>&1 || true
        print_success "Existing container cleaned up"
    fi
}

# Function to build image if needed
build_image() {
    if [[ "$1" == "--build" ]] || [[ "$1" == "-b" ]]; then
        print_status "Building Docker image..."
        docker build -t ${IMAGE_NAME} .
        print_success "Image built successfully"
    fi
}

# Function to start container
start_container() {
    print_status "Starting PlexCacheUltra container..."
    
    # Check if .env file exists
    if [[ ! -f .env ]]; then
        print_warning "No .env file found. Please create one from env.example"
        print_status "Creating minimal .env file..."
        cat > .env << EOF
# PlexCacheUltra Environment Variables
# Please update these values with your actual configuration

PLEX_URL=https://plex.yourdomain.com
PLEX_TOKEN=your_plex_token_here
CACHE_DIR=/mnt/cache
REAL_SOURCE=/mnt/user
PLEX_SOURCE=/media

# Copy vs Move behavior (recommended: true for automatic Plex cache usage)
COPY_TO_CACHE=false
DELETE_FROM_CACHE_WHEN_DONE=true
USE_SYMLINKS_FOR_CACHE=true
MOVE_WITH_SYMLINKS=false
EOF
        print_warning "Created minimal .env file. Please edit it with your actual values before starting."
        exit 1
    fi
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)
    
    # Validate required variables
    if [[ -z "$PLEX_URL" ]] || [[ -z "$PLEX_TOKEN" ]]; then
        print_error "PLEX_URL and PLEX_TOKEN are required in .env file"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p data logs
    
    # Start container
    docker run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p ${PORT}:5443 \
        --env-file .env \
        -v ${CACHE_DIR:-/mnt/cache}:${CACHE_DIR:-/mnt/cache} \
        -v ${REAL_SOURCE:-/mnt/user}:${REAL_SOURCE:-/mnt/user} \
        -v ${PLEX_SOURCE:-/media}:${PLEX_SOURCE:-/media} \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        ${IMAGE_NAME}
    
    print_success "Container started successfully"
}

# Function to show status
show_status() {
    if container_running; then
        print_success "Container is running"
        echo
        print_status "Container details:"
        docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo
        print_status "Logs (last 20 lines):"
        docker logs --tail 20 ${CONTAINER_NAME}
        echo
        print_status "Access the web dashboard at: http://localhost:${PORT}"
    else
        print_warning "Container is not running"
        if container_exists; then
            print_status "Container exists but is stopped"
        else
            print_status "No container found"
        fi
    fi
}

# Function to show logs
show_logs() {
    if container_exists; then
        print_status "Showing logs (press Ctrl+C to exit):"
        docker logs -f ${CONTAINER_NAME}
    else
        print_error "Container not found"
    fi
}

# Function to stop container
stop_container() {
    if container_running; then
        print_status "Stopping container..."
        docker stop ${CONTAINER_NAME}
        print_success "Container stopped"
    else
        print_warning "Container is not running"
    fi
}

# Function to remove container
remove_container() {
    if container_exists; then
        print_status "Removing container..."
        docker rm ${CONTAINER_NAME}
        print_success "Container removed"
    else
        print_warning "Container not found"
    fi
}

# Function to show help
show_help() {
    echo "PlexCacheUltra Startup Script"
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start [--build]  Start the container (--build to rebuild image)"
    echo "  stop             Stop the container"
    echo "  restart          Restart the container"
    echo "  status           Show container status"
    echo "  logs             Show container logs"
    echo "  remove           Remove the container"
    echo "  help             Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start         # Start with existing image"
    echo "  $0 start --build # Start and rebuild image"
    echo "  $0 status        # Check container status"
    echo "  $0 logs          # View logs"
}

# Main script logic
case "${1:-start}" in
    "start")
        check_docker
        build_image "$2"
        cleanup_container
        start_container
        ;;
    "stop")
        check_docker
        stop_container
        ;;
    "restart")
        check_docker
        stop_container
        cleanup_container
        start_container
        ;;
    "status")
        check_docker
        show_status
        ;;
    "logs")
        check_docker
        show_logs
        ;;
    "remove")
        check_docker
        stop_container
        remove_container
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
