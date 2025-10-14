#!/bin/bash

# Presenton OpenRouter Start Script
# This script starts Presenton with OpenRouter configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OPENROUTER_API_KEY="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"
OPENROUTER_URL="https://openrouter.ai/api/v1"
DEFAULT_MODEL="openai/gpt-4o-mini"
APP_DATA_DIR="/tmp/presenton_data"
FASTAPI_PORT=8000
NEXTJS_PORT=3000

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i ":$1" >/dev/null 2>&1
}

# Function to create user config
create_user_config() {
    print_status "Creating user configuration for OpenRouter..."
    
    mkdir -p "$APP_DATA_DIR"
    
    cat > "$APP_DATA_DIR/userConfig.json" << EOF
{
    "LLM": "custom",
    "CUSTOM_LLM_URL": "$OPENROUTER_URL",
    "CUSTOM_LLM_API_KEY": "$OPENROUTER_API_KEY",
    "CUSTOM_MODEL": "$DEFAULT_MODEL",
    "TOOL_CALLS": false,
    "DISABLE_THINKING": false,
    "EXTENDED_REASONING": false,
    "WEB_GROUNDING": false
}
EOF
    
    print_success "User configuration created at $APP_DATA_DIR/userConfig.json"
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command_exists node; then
        missing_deps+=("node")
    fi
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if ! command_exists pip; then
        missing_deps+=("pip")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_error "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    cd servers/fastapi
    
    # Install basic dependencies
    pip install fastapi uvicorn openai anthropic google-genai python-multipart python-jose[cryptography] passlib[bcrypt] sqlalchemy aiosqlite
    
    cd ../..
    print_success "Python dependencies installed"
}

# Function to install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    
    cd servers/nextjs
    npm install
    cd ../..
    
    print_success "Node.js dependencies installed"
}

# Function to test OpenRouter connection
test_openrouter_connection() {
    print_status "Testing OpenRouter connection..."
    
    # Install openai if not available
    if ! python3 -c "import openai" 2>/dev/null; then
        print_status "Installing OpenAI package for testing..."
        pip install openai
    fi
    
    python3 << 'EOF'
import os
import json
import asyncio
from openai import AsyncOpenAI

async def test_connection():
    try:
        # Load config
        with open('/tmp/presenton_data/userConfig.json', 'r') as f:
            config = json.load(f)
        
        client = AsyncOpenAI(
            base_url=config['CUSTOM_LLM_URL'],
            api_key=config['CUSTOM_LLM_API_KEY']
        )
        
        response = await client.chat.completions.create(
            model=config['CUSTOM_MODEL'],
            messages=[{"role": "user", "content": "Test connection"}],
            max_tokens=10
        )
        
        print("✅ OpenRouter connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
EOF
    
    if [ $? -eq 0 ]; then
        print_success "OpenRouter connection test passed"
    else
        print_error "OpenRouter connection test failed"
        exit 1
    fi
}

# Function to start FastAPI server
start_fastapi() {
    print_status "Starting FastAPI server on port $FASTAPI_PORT..."
    
    cd servers/fastapi
    
    # Set environment variables
    export USER_CONFIG_PATH="$APP_DATA_DIR/userConfig.json"
    export LLM="custom"
    export CUSTOM_LLM_URL="$OPENROUTER_URL"
    export CUSTOM_LLM_API_KEY="$OPENROUTER_API_KEY"
    export CUSTOM_MODEL="$DEFAULT_MODEL"
    
    # Start FastAPI server in background
    python3 server.py --port $FASTAPI_PORT &
    FASTAPI_PID=$!
    
    cd ../..
    
    # Wait a moment for server to start
    sleep 3
    
    # Check if server is running
    if kill -0 $FASTAPI_PID 2>/dev/null; then
        print_success "FastAPI server started (PID: $FASTAPI_PID)"
    else
        print_error "Failed to start FastAPI server"
        exit 1
    fi
}

# Function to start Next.js server
start_nextjs() {
    print_status "Starting Next.js server on port $NEXTJS_PORT..."
    
    cd servers/nextjs
    
    # Set environment variables
    export USER_CONFIG_PATH="$APP_DATA_DIR/userConfig.json"
    export LLM="custom"
    export CUSTOM_LLM_URL="$OPENROUTER_URL"
    export CUSTOM_LLM_API_KEY="$OPENROUTER_API_KEY"
    export CUSTOM_MODEL="$DEFAULT_MODEL"
    
    # Start Next.js server in background
    npm run dev -- -p $NEXTJS_PORT &
    NEXTJS_PID=$!
    
    cd ../..
    
    # Wait a moment for server to start
    sleep 5
    
    # Check if server is running
    if kill -0 $NEXTJS_PID 2>/dev/null; then
        print_success "Next.js server started (PID: $NEXTJS_PID)"
    else
        print_error "Failed to start Next.js server"
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Presenton with OpenRouter is running!"
    echo ""
    echo -e "${GREEN}🌐 Web Interface:${NC} http://localhost:$NEXTJS_PORT"
    echo -e "${GREEN}🔧 API Server:${NC} http://localhost:$FASTAPI_PORT"
    echo -e "${GREEN}📊 API Docs:${NC} http://localhost:$FASTAPI_PORT/docs"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo "  • LLM Provider: OpenRouter (Custom)"
    echo "  • Model: $DEFAULT_MODEL"
    echo "  • API URL: $OPENROUTER_URL"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down servers..."
    
    if [ ! -z "$FASTAPI_PID" ]; then
        kill $FASTAPI_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$NEXTJS_PID" ]; then
        kill $NEXTJS_PID 2>/dev/null || true
    fi
    
    print_success "Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo -e "${BLUE}🚀 Starting Presenton with OpenRouter${NC}"
    echo ""
    
    # Check if ports are available
    if port_in_use $FASTAPI_PORT; then
        print_warning "Port $FASTAPI_PORT is already in use"
    fi
    
    if port_in_use $NEXTJS_PORT; then
        print_warning "Port $NEXTJS_PORT is already in use"
    fi
    
    # Run setup steps
    check_dependencies
    create_user_config
    install_python_deps
    install_node_deps
    test_openrouter_connection
    
    # Start servers
    start_fastapi
    start_nextjs
    
    # Show status
    show_status
    
    # Wait for user interrupt
    wait
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Presenton OpenRouter Start Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --test-only    Only test OpenRouter connection"
        echo "  --no-install   Skip dependency installation"
        echo ""
        echo "Environment Variables:"
        echo "  OPENROUTER_API_KEY    Your OpenRouter API key"
        echo "  OPENROUTER_MODEL      Model to use (default: openai/gpt-4o-mini)"
        echo "  FASTAPI_PORT          FastAPI port (default: 8000)"
        echo "  NEXTJS_PORT           Next.js port (default: 3000)"
        exit 0
        ;;
    --test-only)
        check_dependencies
        create_user_config
        test_openrouter_connection
        exit 0
        ;;
    --no-install)
        print_warning "Skipping dependency installation"
        check_dependencies
        create_user_config
        test_openrouter_connection
        start_fastapi
        start_nextjs
        show_status
        wait
        ;;
    *)
        main
        ;;
esac
