#!/bin/bash

# Advanced Playwright Test Runner for PlexCache
# Provides comprehensive testing capabilities with multiple options

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="$SCRIPT_DIR"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
BROWSERS="all"
WORKERS=""
TIMEOUT=""
TRACE="off"
VIDEO="off"
DEBUG=false
SPECIFIC_FILE=""
UI_MODE=false
REPORTER="html"

# Function to print colored output
print_header() {
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}  PlexCache Advanced Test Runner${NC}"
    echo -e "${CYAN}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "${PURPLE}🔍${NC} $1"
    fi
}

# Function to show usage
usage() {
    cat << EOF
$(print_header)

USAGE: $0 [OPTIONS] [COMMAND]

COMMANDS:
    help                    Show this help message
    test                    Run all tests
    test-ui                 Run tests with Playwright UI mode
    test-chrome             Run tests only on Chromium
    test-firefox            Run tests only on Firefox
    test-webkit             Run tests only on WebKit
    build                   Build the Docker image
    clean                   Clean up Docker containers and images
    shell                   Open a shell in the container
    install                 Install Playwright browsers
    report                  Show test report
    status                  Show system and cache status

OPTIONS:
    -b, --browsers BROWSERS    Specify browsers (all, chrome, firefox, webkit) [default: all]
    -w, --workers WORKERS      Number of parallel workers [default: auto]
    -t, --timeout TIMEOUT      Test timeout in milliseconds [default: 30000]
    --trace [on|off]          Enable/disable tracing [default: off]
    --video [on|off]           Enable/disable video recording [default: off]
    -f, --file FILE           Run specific test file
    -d, --debug               Run in debug mode
    -r, --reporter REPORTER   Test reporter (html, json, line) [default: html]
    -h, --help                Show this help message

EXAMPLES:
    $0 test
    $0 test -b chrome -w 2
    $0 test-ui
    $0 test -f dashboard.spec.ts -d
    $0 test --trace on --video on
    $0 build
    $0 status

DOCKER REQUIREMENTS:
    - Docker must be installed and running
    - docker-compose must be available
    - Sufficient disk space for Docker images (~1.5GB)

For more information, see $SCRIPT_DIR/README.md
EOF
}

# Function to check if Docker is running
check_docker() {
    print_debug "Checking Docker status..."

    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        print_info "Try: sudo systemctl start docker"
        exit 1
    fi

    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed."
        print_info "Try: sudo apt-get install docker-compose"
        exit 1
    fi

    print_success "Docker is running and docker-compose is available"
}

# Function to check if Docker Compose file exists
check_compose_file() {
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        print_info "Please ensure you're running from the project root directory"
        exit 1
    fi
}

# Function to build Docker image
build_image() {
    print_info "Building Playwright Docker image..."

    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" build; then
        print_error "Failed to build Docker image"
        exit 1
    fi

    print_success "Docker image built successfully"
}

# Function to construct Playwright command
construct_playwright_command() {
    local cmd="npx playwright test"

    # Add specific file if provided
    if [ -n "$SPECIFIC_FILE" ]; then
        cmd="$cmd $SPECIFIC_FILE"
    fi

    # Add browser selection
    case $BROWSERS in
        chrome)
            cmd="$cmd --project=chromium"
            ;;
        firefox)
            cmd="$cmd --project=firefox"
            ;;
        webkit)
            cmd="$cmd --project=webkit"
            ;;
        all)
            # Default - run all browsers
            ;;
        *)
            print_error "Invalid browser selection: $BROWSERS"
            exit 1
            ;;
    esac

    # Add workers
    if [ -n "$WORKERS" ]; then
        cmd="$cmd --workers=$WORKERS"
    fi

    # Add timeout
    if [ -n "$TIMEOUT" ]; then
        cmd="$cmd --timeout=$TIMEOUT"
    fi

    # Add tracing
    if [ "$TRACE" = "on" ]; then
        cmd="$cmd --trace=on"
    fi

    # Add video recording
    if [ "$VIDEO" = "on" ]; then
        cmd="$cmd --video=on"
    fi

    # Add reporter
    if [ -n "$REPORTER" ]; then
        cmd="$cmd --reporter=$REPORTER"
    fi

    # Add debug mode
    if [ "$DEBUG" = true ]; then
        cmd="$cmd --debug"
    fi

    echo "$cmd"
}

# Function to run tests
run_tests() {
    local service_name="playwright"
    local command

    if [ "$UI_MODE" = true ]; then
        service_name="playwright-ui"
        command="npx playwright test --ui --ui-host=0.0.0.0"
    else
        command=$(construct_playwright_command)
    fi

    print_info "Running Playwright tests..."
    print_debug "Service: $service_name"
    print_debug "Command: $command"
    print_debug "Browsers: $BROWSERS"
    print_debug "Workers: ${WORKERS:-auto}"
    print_debug "Timeout: ${TIMEOUT:-30000}ms"
    print_debug "Trace: $TRACE"
    print_debug "Video: $VIDEO"

    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm "$service_name" $command; then
        print_error "Tests failed!"
        print_info "Check the test results and logs above for details"
        print_info "You can also view the HTML report with: $0 report"
        exit 1
    fi

    print_success "Tests completed successfully"
}

# Function to clean up Docker resources
cleanup() {
    print_info "Cleaning up Docker resources..."

    # Stop and remove containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true

    # Remove unused images
    docker image prune -f >/dev/null 2>&1 || true

    # Remove unused volumes
    docker volume prune -f >/dev/null 2>&1 || true

    print_success "Cleanup completed"
}

# Function to open shell in container
open_shell() {
    print_info "Opening shell in Playwright container..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm playwright /bin/bash
}

# Function to install Playwright browsers
install_browsers() {
    print_info "Installing Playwright browsers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm playwright npx playwright install --with-deps
    print_success "Playwright browsers installed"
}

# Function to show test report
show_report() {
    local report_dir="$PROJECT_ROOT/playwright-report"

    if [ -d "$report_dir" ]; then
        local report_file="$report_dir/index.html"

        if [ -f "$report_file" ]; then
            print_info "Opening test report..."

            # Try to open with available tools
            if command -v xdg-open >/dev/null 2>&1; then
                xdg-open "$report_file" >/dev/null 2>&1 &
            elif command -v open >/dev/null 2>&1; then
                open "$report_file" >/dev/null 2>&1 &
            elif command -v python3 >/dev/null 2>&1; then
                print_info "Starting local server at http://localhost:8080"
                print_info "Press Ctrl+C to stop"
                cd "$report_dir" && python3 -m http.server 8080
            else
                print_warning "Could not automatically open the report"
                print_info "Please manually open: $report_file"
            fi
        else
            print_warning "Test report file not found: $report_file"
            print_info "Run tests first to generate a report"
        fi
    else
        print_warning "Test report directory not found: $report_dir"
        print_info "Run tests first to generate a report"
    fi
}

# Function to show system status
show_status() {
    print_info "Checking system status..."

    # Check Docker
    if docker info >/dev/null 2>&1; then
        print_success "Docker is running"
    else
        print_warning "Docker is not running"
    fi

    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        print_success "docker-compose is available"
    else
        print_warning "docker-compose is not available"
    fi

    # Check Docker Compose file
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        print_success "Docker Compose file found"
    else
        print_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
    fi

    # Check test files
    local test_files=$(find "$TEST_DIR" -name "*.spec.ts" -o -name "*.spec.js" 2>/dev/null | wc -l)
    if [ "$test_files" -gt 0 ]; then
        print_success "Found $test_files test files"
    else
        print_warning "No test files found in $TEST_DIR"
    fi

    # Check Playwright config
    if [ -f "$PROJECT_ROOT/playwright.config.js" ]; then
        print_success "Playwright configuration found"
    else
        print_warning "Playwright configuration not found"
    fi

    # Check package.json
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        print_success "package.json found"
    else
        print_warning "package.json not found"
    fi
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--browsers)
                BROWSERS="$2"
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
            --trace)
                TRACE="$2"
                shift 2
                ;;
            --video)
                VIDEO="$2"
                shift 2
                ;;
            -f|--file)
                SPECIFIC_FILE="$2"
                shift 2
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            -r|--reporter)
                REPORTER="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done

    COMMAND="${1:-help}"
}

# Main script execution
main() {
    # Change to project root
    cd "$PROJECT_ROOT"

    # Parse command line arguments
    parse_args "$@"

    print_debug "Command: $COMMAND"
    print_debug "Project root: $PROJECT_ROOT"
    print_debug "Test directory: $TEST_DIR"

    case $COMMAND in
        "help"|"-h"|"--help")
            usage
            ;;
        "status")
            show_status
            ;;
        "build")
            check_docker
            check_compose_file
            build_image
            ;;
        "test")
            check_docker
            check_compose_file
            run_tests
            ;;
        "test-ui")
            UI_MODE=true
            check_docker
            check_compose_file
            run_tests
            ;;
        "test-chrome")
            BROWSERS="chrome"
            check_docker
            check_compose_file
            run_tests
            ;;
        "test-firefox")
            BROWSERS="firefox"
            check_docker
            check_compose_file
            run_tests
            ;;
        "test-webkit")
            BROWSERS="webkit"
            check_docker
            check_compose_file
            run_tests
            ;;
        "clean")
            check_docker
            cleanup
            ;;
        "shell")
            check_docker
            check_compose_file
            open_shell
            ;;
        "install")
            check_docker
            check_compose_file
            install_browsers
            ;;
        "report")
            show_report
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"