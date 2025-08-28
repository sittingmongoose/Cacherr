#!/bin/bash

# Comprehensive Playwright Test Runner for PlexCacheUltra WebGUI
# This script provides various options for running end-to-end tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BROWSER="chromium"
HEADLESS="true"
WORKERS="1"
TIMEOUT="30000"
REPORTER="html"
TRACE="off"
VIDEO="off"
SCREENSHOT="off"
PROJECT=""
TEST_FILE=""
DEBUG="false"
UI="false"
COVERAGE="false"
PARALLEL="false"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print usage information
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --browser BROWSER     Browser to use (chromium, firefox, webkit, all)"
    echo "  -h, --headless BOOL       Run in headless mode (true/false)"
    echo "  -w, --workers NUM         Number of workers for parallel execution"
    echo "  -t, --timeout MS          Test timeout in milliseconds"
    echo "  -r, --reporter TYPE       Reporter type (html, json, line, list)"
    echo "  --trace MODE              Trace mode (on, off, on-first-retry, retain-on-failure)"
    echo "  --video MODE              Video recording mode (on, off, on-first-retry, retain-on-failure)"
    echo "  --screenshot MODE         Screenshot mode (on, off, on-first-retry, retain-on-failure)"
    echo "  -p, --project NAME        Run specific project"
    echo "  -f, --file FILE           Run specific test file"
    echo "  -d, --debug               Run in debug mode"
    echo "  -u, --ui                  Run with Playwright UI"
    echo "  -c, --coverage            Generate coverage report"
    echo "  --parallel                Enable parallel test execution"
    echo "  --help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests in Chromium"
    echo "  $0 -b firefox                        # Run all tests in Firefox"
    echo "  $0 -b all -w 4                      # Run all tests in all browsers with 4 workers"
    echo "  $0 -f dashboard.spec.ts             # Run only dashboard tests"
    echo "  $0 -d                               # Run in debug mode"
    echo "  $0 -u                               # Run with Playwright UI"
    echo "  $0 --parallel -w 4                  # Run tests in parallel with 4 workers"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status $BLUE "Checking prerequisites..."
    
    # Check if Node.js is installed
    if ! command_exists node; then
        print_status $RED "Error: Node.js is not installed"
        exit 1
    fi
    
    # Check if npm is installed
    if ! command_exists npm; then
        print_status $RED "Error: npm is not installed"
        exit 1
    fi
    
    # Check if Playwright is installed
    if [ ! -d "node_modules/@playwright" ]; then
        print_status $YELLOW "Warning: Playwright not found, installing..."
        npm install @playwright/test
        npx playwright install
    fi
    
    print_status $GREEN "Prerequisites check passed"
}

# Function to setup test environment
setup_test_environment() {
    print_status $BLUE "Setting up test environment..."
    
    # Create test results directory
    mkdir -p test-results/screenshots
    mkdir -p test-results/videos
    mkdir -p test-results/traces
    
    # Set environment variables
    export PLAYWRIGHT_HTML_REPORT="test-results/playwright-report"
    export PLAYWRIGHT_TEST_RESULTS_DIR="test-results"
    
    print_status $GREEN "Test environment setup complete"
}

# Function to run tests
run_tests() {
    local command="npx playwright test"
    
    # Add browser specification
    if [ "$BROWSER" = "all" ]; then
        command="$command --project=chromium --project=firefox --project=webkit"
    else
        command="$command --project=$BROWSER"
    fi
    
    # Add headless mode
    if [ "$HEADLESS" = "false" ]; then
        command="$command --headed"
    fi
    
    # Add workers
    if [ "$PARALLEL" = "true" ] && [ "$WORKERS" -gt 1 ]; then
        command="$command --workers=$WORKERS"
    fi
    
    # Add timeout
    command="$command --timeout=$TIMEOUT"
    
    # Add reporter
    command="$command --reporter=$REPORTER"
    
    # Add trace mode
    command="$command --trace=$TRACE"
    
    # Add video mode
    command="$command --video=$VIDEO"
    
    # Add screenshot mode
    command="$command --screenshot=$SCREENSHOT"
    
    # Add specific project
    if [ -n "$PROJECT" ]; then
        command="$command --project=$PROJECT"
    fi
    
    # Add specific test file
    if [ -n "$TEST_FILE" ]; then
        command="$command $TEST_FILE"
    fi
    
    # Add debug mode
    if [ "$DEBUG" = "true" ]; then
        command="$command --debug"
    fi
    
    # Add UI mode
    if [ "$UI" = "true" ]; then
        command="$command --ui"
    fi
    
    print_status $BLUE "Running tests with command: $command"
    print_status $BLUE "Test configuration:"
    print_status $BLUE "  Browser: $BROWSER"
    print_status $BLUE "  Headless: $HEADLESS"
    print_status $BLUE "  Workers: $WORKERS"
    print_status $BLUE "  Timeout: ${TIMEOUT}ms"
    print_status $BLUE "  Reporter: $REPORTER"
    print_status $BLUE "  Trace: $TRACE"
    print_status $BLUE "  Video: $VIDEO"
    print_status $BLUE "  Screenshot: $SCREENSHOT"
    
    # Execute the command
    eval $command
}

# Function to run tests with Docker
run_tests_docker() {
    print_status $BLUE "Running tests with Docker..."
    
    # Check if Docker is available
    if ! command_exists docker; then
        print_status $RED "Error: Docker is not installed"
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command_exists docker-compose; then
        print_status $RED "Error: docker-compose is not installed"
        exit 1
    fi
    
    # Build the test image
    print_status $BLUE "Building Docker test image..."
    docker-compose build playwright
    
    # Run tests in Docker
    local docker_command="docker-compose run --rm playwright npx playwright test"
    
    # Add browser specification
    if [ "$BROWSER" = "all" ]; then
        docker_command="$docker_command --project=chromium --project=firefox --project=webkit"
    else
        docker_command="$docker_command --project=$BROWSER"
    fi
    
    # Add other options
    if [ "$HEADLESS" = "false" ]; then
        docker_command="$docker_command --headed"
    fi
    
    if [ -n "$TEST_FILE" ]; then
        docker_command="$docker_command $TEST_FILE"
    fi
    
    if [ "$DEBUG" = "true" ]; then
        docker_command="$docker_command --debug"
    fi
    
    print_status $BLUE "Running Docker command: $docker_command"
    eval $docker_command
}

# Function to show test results
show_test_results() {
    print_status $BLUE "Test execution completed"
    
    # Check if test results exist
    if [ -d "test-results" ]; then
        print_status $GREEN "Test results available in: test-results/"
        
        # Show HTML report location
        if [ -d "test-results/playwright-report" ]; then
            print_status $GREEN "HTML report: test-results/playwright-report/index.html"
        fi
        
        # Show screenshot count
        if [ -d "test-results/screenshots" ]; then
            local screenshot_count=$(find test-results/screenshots -name "*.png" | wc -l)
            print_status $BLUE "Screenshots: $screenshot_count"
        fi
        
        # Show video count
        if [ -d "test-results/videos" ]; then
            local video_count=$(find test-results/videos -name "*.webm" | wc -l)
            print_status $BLUE "Videos: $video_count"
        fi
        
        # Show trace count
        if [ -d "test-results/traces" ]; then
            local trace_count=$(find test-results/traces -name "*.zip" | wc -l)
            print_status $BLUE "Traces: $trace_count"
        fi
    fi
}

# Function to cleanup test environment
cleanup_test_environment() {
    print_status $BLUE "Cleaning up test environment..."
    
    # Remove temporary files
    rm -rf test-results/tmp
    
    print_status $GREEN "Cleanup complete"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -h|--headless)
            HEADLESS="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -r|--reporter)
            REPORTER="$2"
            shift 2
            ;;
        --trace)
            TRACE="$2"
            shift 2
            ;;
        --video)
            VIDEO="$2"
            shift 2
            ;;
        --screenshot)
            SCREENSHOT="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT="$2"
            shift 2
            ;;
        -f|--file)
            TEST_FILE="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG="true"
            shift
            ;;
        -u|--ui)
            UI="true"
            shift
            ;;
        -c|--coverage)
            COVERAGE="true"
            shift
            ;;
        --parallel)
            PARALLEL="true"
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            print_status $RED "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [ "$BROWSER" != "chromium" ] && [ "$BROWSER" != "firefox" ] && [ "$BROWSER" != "webkit" ] && [ "$BROWSER" != "all" ]; then
    print_status $RED "Error: Invalid browser '$BROWSER'. Valid options: chromium, firefox, webkit, all"
    exit 1
fi

if [ "$HEADLESS" != "true" ] && [ "$HEADLESS" != "false" ]; then
    print_status $RED "Error: Invalid headless value '$HEADLESS'. Valid options: true, false"
    exit 1
fi

if ! [[ "$WORKERS" =~ ^[0-9]+$ ]] || [ "$WORKERS" -lt 1 ]; then
    print_status $RED "Error: Invalid workers value '$WORKERS'. Must be a positive integer"
    exit 1
fi

if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [ "$TIMEOUT" -lt 1000 ]; then
    print_status $RED "Error: Invalid timeout value '$TIMEOUT'. Must be at least 1000ms"
    exit 1
fi

# Main execution
main() {
    print_status $GREEN "=== PlexCacheUltra WebGUI Test Runner ==="
    print_status $BLUE "Starting test execution..."
    
    # Check prerequisites
    check_prerequisites
    
    # Setup test environment
    setup_test_environment
    
    # Determine if we should use Docker
    if [ "$USE_DOCKER" = "true" ] || [ -f "docker-compose.yml" ]; then
        run_tests_docker
    else
        run_tests
    fi
    
    # Show results
    show_test_results
    
    # Cleanup
    cleanup_test_environment
    
    print_status $GREEN "Test execution completed successfully!"
}

# Run main function
main "$@"
