#!/bin/bash

# Comprehensive Playwright Docker Runner for Cacherr
# Supports multiple browsers, test types, and reporting options

set -e

function show_help() {
    echo "Comprehensive Playwright Docker Runner for Cacherr"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  test              Run all tests"
    echo "  test-ui           Run tests with UI mode (port 9323)"
    echo "  test-chrome       Run tests only on Chromium"
    echo "  test-firefox      Run tests only on Firefox"
    echo "  test-webkit       Run tests only on WebKit"
    echo "  test-mobile       Run tests on mobile browsers"
    echo "  test-accessibility Run accessibility tests"
    echo "  test-dashboard    Run dashboard-specific tests"
    echo "  test-settings     Run settings-specific tests"
    echo "  test-navigation   Run navigation-specific tests"
    echo "  test-responsive   Run responsive design tests"
    echo "  test-performance  Run performance tests"
    echo "  build             Build the Docker image"
    echo "  clean             Clean up containers and images"
    echo "  shell             Open shell in container"
    echo "  debug             Run tests in debug mode"
    echo "  report            Generate and open test report"
    echo "  help              Show this help message"
    echo ""
    echo "Options:"
    echo "  --headed          Run tests in headed mode (visible browser)"
    echo "  --debug           Run tests in debug mode"
    echo "  --trace           Enable tracing for failed tests"
    echo "  --video           Record videos for all tests"
    echo "  --slow            Run tests with slower execution"
    echo "  --grep PATTERN    Run tests matching pattern"
    echo "  --shard INDEX/N   Run shard INDEX of N total shards"
    echo ""
    echo "Examples:"
    echo "  $0 test --headed --trace"
    echo "  $0 test-dashboard --grep 'critical'"
    echo "  $0 test --shard 1/3"
    echo "  $0 test-mobile --video"
    echo ""
}

function build_image() {
    echo "🔨 Building Playwright Docker image..."
    docker-compose --profile testing build cacherr-test
}

function run_tests() {
    local args="$*"
    echo "🧪 Running Playwright tests..."
    echo "📊 Command: docker-compose --profile testing run --rm cacherr-test npx playwright test $args"

    docker-compose --profile testing run --rm cacherr-test npx playwright test $args
}

function run_tests_ui() {
    echo "🎭 Running Playwright tests with UI..."
    echo "🌐 UI will be available at http://localhost:9323"
    echo "📊 Command: docker-compose --profile testing up playwright-ui"

    docker-compose --profile testing up playwright-ui
}

function run_tests_browser() {
    local browser=$1
    local args="${*:2}"
    echo "🌐 Running Playwright tests on $browser..."
    echo "📊 Command: docker-compose --profile testing run --rm cacherr-test npx playwright test --project=$browser $args"

    docker-compose --profile testing run --rm cacherr-test npx playwright test --project=$browser $args
}

function run_tests_type() {
    local test_type=$1
    local args="${*:2}"
    echo "🎯 Running $test_type tests..."
    echo "📊 Command: docker-compose --profile testing run --rm cacherr-test npx playwright test $test_type $args"

    docker-compose --profile testing run --rm cacherr-test npx playwright test $test_type $args
}

function run_shell() {
    echo "🐚 Opening shell in Playwright container..."
    docker-compose --profile testing run --rm cacherr-test /bin/bash
}

function run_debug() {
    local args="${*:2}"
    echo "🐛 Running tests in debug mode..."
    echo "📊 Command: docker-compose --profile testing run --rm cacherr-test npx playwright test --debug $args"

    docker-compose --profile testing run --rm cacherr-test npx playwright test --debug $args
}

function generate_report() {
    echo "📊 Generating test report..."

    # Check if report directory exists
    if [ -d "./playwright-report" ]; then
        echo "📁 Opening test report..."
        if command -v xdg-open &> /dev/null; then
            xdg-open ./playwright-report/index.html
        elif command -v open &> /dev/null; then
            open ./playwright-report/index.html
        else
            echo "📄 Report generated at ./playwright-report/index.html"
        fi
    else
        echo "❌ No test report found. Run tests first."
    fi
}

function clean_up() {
    echo "🧹 Cleaning up Docker containers and images..."
    docker-compose --profile testing down --rmi all --volumes --remove-orphans

    # Clean up test artifacts
    echo "🧹 Cleaning up test artifacts..."
    rm -rf test-results playwright-report

    echo "✅ Cleanup completed"
}

# Parse command line arguments
COMMAND="${1:-help}"
shift

# Build arguments for playwright
PW_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --headed)
            PW_ARGS="$PW_ARGS --headed"
            shift
            ;;
        --debug)
            PW_ARGS="$PW_ARGS --debug"
            shift
            ;;
        --trace)
            PW_ARGS="$PW_ARGS --trace on"
            shift
            ;;
        --video)
            PW_ARGS="$PW_ARGS --video on"
            shift
            ;;
        --slow)
            PW_ARGS="$PW_ARGS --slowMo 1000"
            shift
            ;;
        --grep)
            PW_ARGS="$PW_ARGS --grep '$2'"
            shift 2
            ;;
        --shard)
            PW_ARGS="$PW_ARGS --shard='$2'"
            shift 2
            ;;
        *)
            PW_ARGS="$PW_ARGS $1"
            shift
            ;;
    esac
done

# Main command handling
case "$COMMAND" in
    "test")
        build_image
        run_tests $PW_ARGS
        ;;
    "test-ui")
        build_image
        run_tests_ui
        ;;
    "test-chrome")
        build_image
        run_tests_browser "chromium" $PW_ARGS
        ;;
    "test-firefox")
        build_image
        run_tests_browser "firefox" $PW_ARGS
        ;;
    "test-webkit")
        build_image
        run_tests_browser "webkit" $PW_ARGS
        ;;
    "test-mobile")
        build_image
        run_tests_browser "mobile-chrome" $PW_ARGS
        run_tests_browser "mobile-safari" $PW_ARGS
        ;;
    "test-accessibility")
        build_image
        run_tests_browser "accessibility" $PW_ARGS
        ;;
    "test-dashboard")
        build_image
        run_tests_type "dashboard" $PW_ARGS
        ;;
    "test-settings")
        build_image
        run_tests_type "settings" $PW_ARGS
        ;;
    "test-navigation")
        build_image
        run_tests_type "navigation" $PW_ARGS
        ;;
    "test-responsive")
        build_image
        run_tests_type "responsive" $PW_ARGS
        ;;
    "test-performance")
        build_image
        PW_ARGS="$PW_ARGS --grep 'performance'"
        run_tests $PW_ARGS
        ;;
    "build")
        build_image
        ;;
    "clean")
        clean_up
        ;;
    "shell")
        build_image
        run_shell
        ;;
    "debug")
        build_image
        run_debug $PW_ARGS
        ;;
    "report")
        generate_report
        ;;
    "help"|*)
        show_help
        ;;
esac
