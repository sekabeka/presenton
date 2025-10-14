#!/bin/bash

# Presenton OpenRouter Test Runner
# This script runs all tests for OpenRouter integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}${BOLD}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run simple tests
run_simple_tests() {
    print_header "Running Simple OpenRouter Tests"
    echo ""
    
    if command_exists python3; then
        python3 test_openrouter_simple.py
        return $?
    else
        print_error "Python3 not found"
        return 1
    fi
}

# Function to run pytest tests
run_pytest_tests() {
    print_header "Running Comprehensive Pytest Tests"
    echo ""
    
    if command_exists pytest; then
        pytest tests/test_openrouter.py -v --tb=short --color=yes
        return $?
    else
        print_info "Pytest not found, installing..."
        pip install pytest
        if command_exists pytest; then
            pytest tests/test_openrouter.py -v --tb=short --color=yes
            return $?
        else
            print_error "Failed to install pytest"
            return 1
        fi
    fi
}

# Function to run start script test
test_start_script() {
    print_header "Testing Start Script"
    echo ""
    
    if [ -f "start_openrouter.sh" ]; then
        print_info "Testing start script help..."
        ./start_openrouter.sh --help
        
        print_info "Testing connection only..."
        ./start_openrouter.sh --test-only
        
        print_success "Start script tests passed"
        return 0
    else
        print_error "Start script not found"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_header "🧪 Running All OpenRouter Tests"
    echo ""
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Test 1: Simple tests
    echo "Test 1/3: Simple Tests"
    if run_simple_tests; then
        print_success "Simple tests passed"
        ((passed_tests++))
    else
        print_error "Simple tests failed"
        ((failed_tests++))
    fi
    ((total_tests++))
    echo ""
    
    # Test 2: Start script test
    echo "Test 2/3: Start Script Test"
    if test_start_script; then
        print_success "Start script tests passed"
        ((passed_tests++))
    else
        print_error "Start script tests failed"
        ((failed_tests++))
    fi
    ((total_tests++))
    echo ""
    
    # Test 3: Pytest tests (optional)
    echo "Test 3/3: Comprehensive Pytest Tests"
    if run_pytest_tests; then
        print_success "Pytest tests passed"
        ((passed_tests++))
    else
        print_error "Pytest tests failed"
        ((failed_tests++))
    fi
    ((total_tests++))
    echo ""
    
    # Print summary
    print_header "Test Results Summary"
    echo "Total Tests: $total_tests"
    echo -e "Passed: ${GREEN}$passed_tests${NC}"
    echo -e "Failed: ${RED}$failed_tests${NC}"
    
    if [ $failed_tests -eq 0 ]; then
        echo ""
        print_success "🎉 All tests passed! OpenRouter integration is working correctly."
        return 0
    else
        echo ""
        print_error "❌ Some tests failed. Please check the output above."
        return 1
    fi
}

# Main execution
main() {
    case "${1:-all}" in
        --help|-h)
            echo "Presenton OpenRouter Test Runner"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --help, -h     Show this help message"
            echo "  --simple       Run only simple tests"
            echo "  --pytest       Run only pytest tests"
            echo "  --start        Test only the start script"
            echo "  --all          Run all tests (default)"
            echo ""
            exit 0
            ;;
        --simple)
            run_simple_tests
            ;;
        --pytest)
            run_pytest_tests
            ;;
        --start)
            test_start_script
            ;;
        --all|all)
            run_all_tests
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
