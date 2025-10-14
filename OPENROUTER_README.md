# OpenRouter Integration for Presenton

This document describes the OpenRouter integration for the Presenton project, including setup, configuration, and testing.

## Overview

OpenRouter is integrated into Presenton as a custom LLM provider, allowing you to use various AI models through a single API. This integration provides access to models from OpenAI, Anthropic, Google, Meta, and other providers.

## Files Created

### Start Script
- `start_openrouter.sh` - Main start script for running Presenton with OpenRouter

### Test Files
- `test_openrouter_simple.py` - Simple test script (no external dependencies)
- `tests/test_openrouter.py` - Comprehensive pytest test suite
- `run_tests.sh` - Test runner script

## Quick Start

### 1. Start Presenton with OpenRouter

```bash
# Make the script executable (if not already done)
chmod +x start_openrouter.sh

# Start Presenton with OpenRouter
./start_openrouter.sh
```

### 2. Test the Integration

```bash
# Run all tests
./run_tests.sh

# Run only simple tests
./run_tests.sh --simple

# Test only the start script
./run_tests.sh --start
```

## Configuration

The OpenRouter configuration is stored in `/tmp/presenton_data/userConfig.json`:

```json
{
    "LLM": "custom",
    "CUSTOM_LLM_URL": "https://openrouter.ai/api/v1",
    "CUSTOM_LLM_API_KEY": "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",
    "CUSTOM_MODEL": "openai/gpt-4o-mini",
    "TOOL_CALLS": false,
    "DISABLE_THINKING": false,
    "EXTENDED_REASONING": false,
    "WEB_GROUNDING": false
}
```

## Available Models

OpenRouter supports many models. Here are some popular ones:

### OpenAI Models
- `openai/gpt-4o-mini` (cost-effective)
- `openai/gpt-4o`
- `openai/gpt-4-turbo`

### Anthropic Models
- `anthropic/claude-3.5-sonnet`
- `anthropic/claude-3.5-haiku`
- `anthropic/claude-3-opus`

### Google Models
- `google/gemini-pro-1.5`
- `google/gemini-pro-vision`

### Meta Models
- `meta-llama/llama-3.1-405b-instruct`
- `meta-llama/llama-3.1-70b-instruct`

### Other Models
- `mistralai/mistral-7b-instruct`
- `microsoft/phi-3-medium-128k-instruct`

## Changing Models

To change the model, edit the `CUSTOM_MODEL` field in the configuration file:

```bash
# Edit the configuration
nano /tmp/presenton_data/userConfig.json

# Or use sed to change the model
sed -i 's/"CUSTOM_MODEL": ".*"/"CUSTOM_MODEL": "anthropic\/claude-3.5-sonnet"/' /tmp/presenton_data/userConfig.json
```

## Start Script Options

The start script supports several options:

```bash
# Show help
./start_openrouter.sh --help

# Test connection only
./start_openrouter.sh --test-only

# Skip dependency installation
./start_openrouter.sh --no-install
```

## Environment Variables

You can override the default configuration using environment variables:

```bash
export OPENROUTER_API_KEY="your-api-key"
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
export FASTAPI_PORT=8000
export NEXTJS_PORT=3000

./start_openrouter.sh
```

## Testing

### Simple Tests

The simple test script (`test_openrouter_simple.py`) tests:
- Configuration creation and loading
- OpenRouter API connection
- Different model support
- Presentation generation
- Error handling

```bash
python3 test_openrouter_simple.py
```

### Comprehensive Tests

The pytest test suite (`tests/test_openrouter.py`) includes:
- Unit tests for configuration management
- Integration tests for API calls
- Model switching tests
- Error handling tests
- Mock tests for offline testing

```bash
# Install pytest if not already installed
pip install pytest

# Run the tests
pytest tests/test_openrouter.py -v
```

### Test Runner

Use the test runner script for comprehensive testing:

```bash
# Run all tests
./run_tests.sh

# Run specific test suites
./run_tests.sh --simple
./run_tests.sh --pytest
./run_tests.sh --start
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Verify your OpenRouter API key is correct
   - Check that the key has sufficient credits
   - Ensure the key is properly set in the configuration

2. **Connection Issues**
   - Check your internet connection
   - Verify OpenRouter API is accessible
   - Check firewall settings

3. **Model Issues**
   - Ensure the model name is correct
   - Check if the model is available on OpenRouter
   - Try a different model

4. **Port Conflicts**
   - Change the ports if 8000 or 3000 are in use
   - Use environment variables to set custom ports

### Debug Mode

To run in debug mode:

```bash
# Enable debug logging
export DEBUG=1
./start_openrouter.sh
```

### Logs

Check the application logs for errors:

```bash
# Check FastAPI logs
tail -f /tmp/presenton_data/fastapi.log

# Check Next.js logs
tail -f /tmp/presenton_data/nextjs.log
```

## API Usage

Once running, you can access:

- **Web Interface**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Security Notes

- Keep your API key secure and never commit it to version control
- Use environment variables for production deployments
- Regularly rotate your API keys
- Monitor your API usage and costs

## Support

For issues related to:
- **Presenton**: Check the main project documentation
- **OpenRouter**: Visit https://openrouter.ai/docs
- **This Integration**: Check the test output and logs

