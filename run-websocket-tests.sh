#!/bin/bash

# WebSocket Testing Script for Cacherr
# This script provides easy commands to test the WebSocket functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
}

# Function to run WebSocket signature tests
run_signature_tests() {
    print_info "Running WebSocket signature validation tests..."
    if python3 test_websocket_signatures.py; then
        print_success "WebSocket signature tests PASSED"
    else
        print_error "WebSocket signature tests FAILED"
        exit 1
    fi
}

# Function to start WebSocket server
start_server() {
    print_info "Starting WebSocket server..."
    docker-compose up -d websocket-server
    print_success "WebSocket server started on http://localhost:5445"
}

# Function to stop WebSocket server
stop_server() {
    print_info "Stopping WebSocket server..."
    docker-compose down
    print_success "WebSocket server stopped"
}

# Function to run Playwright tests
run_playwright_tests() {
    print_info "Running Playwright WebSocket tests..."

    # Build the Playwright image if needed
    print_info "Building Playwright test environment..."
    docker-compose build playwright

    # Run the tests
    if docker-compose run --rm playwright npx playwright test e2e/websocket.spec.ts --reporter=line; then
        print_success "Playwright WebSocket tests PASSED"
    else
        print_error "Playwright WebSocket tests FAILED"
        exit 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_info "Running complete WebSocket test suite..."

    # Check prerequisites
    check_docker

    # Run signature tests first
    run_signature_tests

    # Start server
    start_server

    # Wait for server to be ready
    print_info "Waiting for server to be ready..."
    sleep 5

    # Test server health
    if curl -f http://localhost:5445/health > /dev/null 2>&1; then
        print_success "Server is responding"
    else
        print_error "Server is not responding"
        stop_server
        exit 1
    fi

    # Run Playwright tests
    run_playwright_tests

    # Stop server
    stop_server

    print_success "All WebSocket tests completed successfully!"
}

# Function to show help
show_help() {
    echo "WebSocket Testing Script for Cacherr"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  signature    Run WebSocket signature validation tests"
    echo "  server       Start WebSocket server"
    echo "  stop         Stop WebSocket server"
    echo "  playwright   Run Playwright WebSocket tests"
    echo "  all          Run complete test suite (signature + server + playwright)"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 signature    # Test function signatures only"
    echo "  $0 all          # Run full test suite"
}

# Main script logic
case "${1:-all}" in
    "signature")
        run_signature_tests
        ;;
    "server")
        check_docker
        start_server
        ;;
    "stop")
        stop_server
        ;;
    "playwright")
        check_docker
        run_playwright_tests
        ;;
    "all")
        run_all_tests
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