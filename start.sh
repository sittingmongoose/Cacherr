#!/bin/bash

# PlexCacheUltra Integrated Docker Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  PlexCacheUltra - Integrated Docker Setup${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        echo "Please install Docker Compose first"
        exit 1
    fi

    print_success "Docker and Docker Compose are installed"
}

# Function to check if configuration exists
check_config() {
    if [ ! -f "plexcache_settings.json" ]; then
        print_warning "plexcache_settings.json not found"
        echo "You may need to configure PlexCache settings first"
        echo "Run: python3 plexcache_setup.py"
        return 1
    else
        print_success "PlexCache configuration found"
        return 0
    fi
}

# Function to start web server
start_web() {
    print_info "Starting PlexCacheUltra Web Server..."
    print_info "This will start the web interface with WebSocket support"

    docker-compose up --build -d plexcache

    print_success "Web server started!"
    echo ""
    echo "🌐 Web Interface: http://localhost:5000"
    echo "🔗 API Endpoints: http://localhost:5000/api/*"
    echo "📊 WebSocket: ws://localhost:5000"
    echo ""
    print_info "To view logs: docker-compose logs -f plexcache"
    print_info "To stop: docker-compose down"
}

# Function to start CLI mode
start_cli() {
    print_info "Starting PlexCacheUltra in CLI mode..."
    print_info "This will run a one-time caching operation"

    docker-compose --profile cli up --build plexcache-cli

    print_success "CLI operation completed!"
}

# Function to run tests
run_tests() {
    print_info "Running PlexCacheUltra tests..."

    # Start the web server first
    print_info "Starting web server for testing..."
    docker-compose up -d plexcache

    # Wait for server to be ready
    print_info "Waiting for server to be healthy..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T plexcache curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done

    if [ $timeout -le 0 ]; then
        print_error "Server failed to start within 60 seconds"
        docker-compose logs plexcache
        exit 1
    fi

    print_success "Server is ready, running tests..."

    # Run the tests
    docker-compose --profile test up --build playwright

    print_success "Tests completed!"
}

# Function to show status
show_status() {
    print_info "PlexCacheUltra Status:"

    if docker-compose ps | grep -q "plexcache"; then
        print_success "Web server is running"
        echo "🌐 http://localhost:5000"
    else
        print_warning "Web server is not running"
    fi

    if docker-compose ps | grep -q "plexcache-cli"; then
        print_success "CLI operation in progress"
    else
        print_info "No CLI operations running"
    fi
}

# Function to stop all services
stop_all() {
    print_info "Stopping all PlexCacheUltra services..."
    docker-compose down
    print_success "All services stopped"
}

# Function to show help
show_help() {
    echo "PlexCacheUltra - Integrated Docker Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  web       Start the web server with WebSocket support (default)"
    echo "  cli       Run PlexCache in traditional CLI mode"
    echo "  test      Run the automated test suite"
    echo "  status    Show current status of services"
    echo "  stop      Stop all running services"
    echo "  logs      Show logs from the web server"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 web      # Start web interface"
    echo "  $0 cli      # Run one-time caching"
    echo "  $0 test     # Run tests"
    echo "  $0 status   # Check what's running"
    echo ""
    echo "For more information, see README_DOCKER.md"
}

# Main script logic
print_header()

# Check prerequisites
check_docker

case "${1:-web}" in
    "web")
        check_config
        start_web
        ;;
    "cli")
        check_config
        start_cli
        ;;
    "test")
        run_tests
        ;;
    "status")
        show_status
        ;;
    "stop")
        stop_all
        ;;
    "logs")
        docker-compose logs -f plexcache
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac