#!/bin/bash

# Playwright Test Runner for Unraid OS
# This script provides easy access to common Playwright operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to show usage
usage() {
    echo "Playwright Test Runner for Unraid OS"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  help          Show this help message"
    echo "  test          Run all tests"
    echo "  test-ui       Run tests with UI mode (opens on port 9323)"
    echo "  test-chrome   Run tests only on Chromium"
    echo "  test-firefox  Run tests only on Firefox"
    echo "  test-webkit   Run tests only on WebKit"
    echo "  build         Build the Docker image"
    echo "  clean         Clean up Docker containers and images"
    echo "  shell         Open a shell in the container"
    echo "  install       Install Playwright browsers"
    echo "  report        Show test report"
    echo ""
    echo "Examples:"
    echo "  $0 test"
    echo "  $0 test-ui"
    echo "  $0 test-chrome"
    echo ""
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to build Docker image
build_image() {
    print_info "Building Playwright Docker image..."
    docker-compose build
    print_status "Docker image built successfully!"
}

# Function to run tests
run_test() {
    local test_command="$1"
    check_docker

    print_info "Running Playwright tests: $test_command"

    if [ "$test_command" = "test-ui" ]; then
        print_info "UI mode will be available at http://localhost:9323"
        docker-compose run --rm playwright-ui
    else
        docker-compose run --rm playwright $test_command
    fi
}

# Function to clean up Docker resources
cleanup() {
    print_info "Cleaning up Docker resources..."
    docker-compose down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f
    print_status "Cleanup completed!"
}

# Function to open shell in container
open_shell() {
    check_docker
    print_info "Opening shell in Playwright container..."
    docker-compose run --rm playwright /bin/bash
}

# Function to install Playwright browsers
install_browsers() {
    check_docker
    print_info "Installing Playwright browsers..."
    docker-compose run --rm playwright npx playwright install --with-deps
    print_status "Playwright browsers installed!"
}

# Function to show test report
show_report() {
    if [ -d "playwright-report" ]; then
        print_info "Opening test report..."
        if command -v python3 &> /dev/null; then
            cd playwright-report && python3 -m http.server 8080
        else
            print_warning "Python3 not found. Please manually open playwright-report/index.html"
        fi
    else
        print_warning "No test report found. Run tests first with '$0 test'"
    fi
}

# Main script logic
case "${1:-help}" in
    "help"|"-h"|"--help")
        usage
        ;;
    "build")
        build_image
        ;;
    "test")
        run_test "npx playwright test"
        ;;
    "test-ui")
        run_test "test-ui"
        ;;
    "test-chrome")
        run_test "npx playwright test --project=chromium"
        ;;
    "test-firefox")
        run_test "npx playwright test --project=firefox"
        ;;
    "test-webkit")
        run_test "npx playwright test --project=webkit"
        ;;
    "clean")
        cleanup
        ;;
    "shell")
        open_shell
        ;;
    "install")
        install_browsers
        ;;
    "report")
        show_report
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac