#!/bin/bash

# Playwright Docker Runner for Unraid OS
# This script helps run Playwright tests in Docker to avoid dependency issues

set -e

function show_help() {
    echo "Playwright Docker Runner for Unraid OS"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  test          Run all tests"
    echo "  test-ui       Run tests with UI mode (opens on port 9323)"
    echo "  test-chrome   Run tests only on Chromium"
    echo "  test-firefox  Run tests only on Firefox"
    echo "  test-webkit   Run tests only on WebKit"
    echo "  build         Build the Docker image"
    echo "  clean         Clean up Docker containers and images"
    echo "  shell         Open a shell in the container"
    echo "  help          Show this help message"
    echo ""
}

function build_image() {
    echo "Building Playwright Docker image..."
    docker-compose build
}

function run_tests() {
    echo "Running Playwright tests..."
    docker-compose run --rm playwright
}

function run_tests_ui() {
    echo "Running Playwright tests with UI..."
    echo "UI will be available at http://localhost:9323"
    docker-compose up playwright-ui
}

function run_tests_browser() {
    local browser=$1
    echo "Running Playwright tests on $browser..."
    docker-compose run --rm playwright npx playwright test --project=$browser
}

function run_shell() {
    echo "Opening shell in Playwright container..."
    docker-compose run --rm playwright /bin/bash
}

function clean_up() {
    echo "Cleaning up Docker containers and images..."
    docker-compose down --rmi all --volumes
}

# Main command handling
case "${1:-help}" in
    "test")
        build_image
        run_tests
        ;;
    "test-ui")
        build_image
        run_tests_ui
        ;;
    "test-chrome")
        build_image
        run_tests_browser "chromium"
        ;;
    "test-firefox")
        build_image
        run_tests_browser "firefox"
        ;;
    "test-webkit")
        build_image
        run_tests_browser "webkit"
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
    "help"|*)
        show_help
        ;;
esac
