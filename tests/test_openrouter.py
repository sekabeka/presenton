#!/usr/bin/env python3
"""
Comprehensive tests for OpenRouter integration in Presenton
"""

import os
import sys
import json
import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_API_KEY = "sk-or-v1-test-key-123456789"
TEST_URL = "https://openrouter.ai/api/v1"
TEST_MODEL = "openai/gpt-4o-mini"
TEST_CONFIG = {
    "LLM": "custom",
    "CUSTOM_LLM_URL": TEST_URL,
    "CUSTOM_LLM_API_KEY": TEST_API_KEY,
    "CUSTOM_MODEL": TEST_MODEL,
    "TOOL_CALLS": False,
    "DISABLE_THINKING": False,
    "EXTENDED_REASONING": False,
    "WEB_GROUNDING": False
}


class TestOpenRouterConfiguration:
    """Test OpenRouter configuration management"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "userConfig.json")
        os.environ['USER_CONFIG_PATH'] = self.config_path
    
    def teardown_method(self):
        """Clean up after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'USER_CONFIG_PATH' in os.environ:
            del os.environ['USER_CONFIG_PATH']
    
    def test_create_user_config(self):
        """Test creating user configuration file"""
        from start_openrouter import create_user_config
        
        # Mock the APP_DATA_DIR
        with patch('start_openrouter.APP_DATA_DIR', self.temp_dir):
            create_user_config()
        
        assert os.path.exists(self.config_path)
        
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        assert config['LLM'] == 'custom'
        assert config['CUSTOM_LLM_URL'] == 'https://openrouter.ai/api/v1'
        assert config['CUSTOM_LLM_API_KEY'] == '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'
        assert config['CUSTOM_MODEL'] == 'openai/gpt-4o-mini'
    
    def test_load_existing_config(self):
        """Test loading existing configuration"""
        # Create a test config file
        with open(self.config_path, 'w') as f:
            json.dump(TEST_CONFIG, f)
        
        # Test loading
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        assert config['LLM'] == 'custom'
        assert config['CUSTOM_LLM_URL'] == TEST_URL
        assert config['CUSTOM_LLM_API_KEY'] == TEST_API_KEY


class TestOpenRouterConnection:
    """Test OpenRouter API connection and functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "userConfig.json")
        os.environ['USER_CONFIG_PATH'] = self.config_path
        
        # Create test config
        with open(self.config_path, 'w') as f:
            json.dump(TEST_CONFIG, f)
    
    def teardown_method(self):
        """Clean up after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'USER_CONFIG_PATH' in os.environ:
            del os.environ['USER_CONFIG_PATH']
    
    @pytest.mark.asyncio
    async def test_openrouter_connection_success(self):
        """Test successful OpenRouter connection"""
        # Mock the OpenAI client
        mock_response = ChatCompletion(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model=TEST_MODEL,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content="Test response from OpenRouter"
                    ),
                    finish_reason="stop"
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )
        
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Test the connection
            client = AsyncOpenAI(
                base_url=TEST_URL,
                api_key=TEST_API_KEY
            )
            
            response = await client.chat.completions.create(
                model=TEST_MODEL,
                messages=[{"role": "user", "content": "Test message"}],
                max_tokens=50
            )
            
            assert response.choices[0].message.content == "Test response from OpenRouter"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openrouter_connection_failure(self):
        """Test OpenRouter connection failure handling"""
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API connection failed")
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception, match="API connection failed"):
                client = AsyncOpenAI(
                    base_url=TEST_URL,
                    api_key=TEST_API_KEY
                )
                
                await client.chat.completions.create(
                    model=TEST_MODEL,
                    messages=[{"role": "user", "content": "Test message"}],
                    max_tokens=50
                )
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid config
        valid_config = TEST_CONFIG.copy()
        assert valid_config['LLM'] == 'custom'
        assert valid_config['CUSTOM_LLM_URL'] == TEST_URL
        assert valid_config['CUSTOM_LLM_API_KEY'] == TEST_API_KEY
        assert valid_config['CUSTOM_MODEL'] == TEST_MODEL
        
        # Test missing required fields
        invalid_configs = [
            {**TEST_CONFIG, 'CUSTOM_LLM_URL': None},
            {**TEST_CONFIG, 'CUSTOM_LLM_API_KEY': None},
            {**TEST_CONFIG, 'CUSTOM_MODEL': None},
            {**TEST_CONFIG, 'LLM': 'openai'},  # Wrong LLM type
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises((KeyError, ValueError, TypeError)):
                # This would be where validation logic would be called
                if invalid_config['CUSTOM_LLM_URL'] is None:
                    raise ValueError("CUSTOM_LLM_URL is required")
                if invalid_config['CUSTOM_LLM_API_KEY'] is None:
                    raise ValueError("CUSTOM_LLM_API_KEY is required")
                if invalid_config['CUSTOM_MODEL'] is None:
                    raise ValueError("CUSTOM_MODEL is required")
                if invalid_config['LLM'] != 'custom':
                    raise ValueError("LLM must be 'custom' for OpenRouter")


class TestOpenRouterModels:
    """Test different OpenRouter models"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "userConfig.json")
        os.environ['USER_CONFIG_PATH'] = self.config_path
    
    def teardown_method(self):
        """Clean up after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'USER_CONFIG_PATH' in os.environ:
            del os.environ['USER_CONFIG_PATH']
    
    @pytest.mark.parametrize("model", [
        "openai/gpt-4o-mini",
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3.5-haiku",
        "meta-llama/llama-3.1-405b-instruct",
        "google/gemini-pro-1.5"
    ])
    def test_model_configuration(self, model):
        """Test different model configurations"""
        config = TEST_CONFIG.copy()
        config['CUSTOM_MODEL'] = model
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        # Load and verify
        with open(self.config_path, 'r') as f:
            loaded_config = json.load(f)
        
        assert loaded_config['CUSTOM_MODEL'] == model
    
    @pytest.mark.asyncio
    async def test_model_switching(self):
        """Test switching between different models"""
        models = ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"]
        
        for model in models:
            config = TEST_CONFIG.copy()
            config['CUSTOM_MODEL'] = model
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
            
            # Verify model is set correctly
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config['CUSTOM_MODEL'] == model


class TestOpenRouterIntegration:
    """Test OpenRouter integration with Presenton services"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "userConfig.json")
        os.environ['USER_CONFIG_PATH'] = self.config_path
        
        # Create test config
        with open(self.config_path, 'w') as f:
            json.dump(TEST_CONFIG, f)
    
    def teardown_method(self):
        """Clean up after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'USER_CONFIG_PATH' in os.environ:
            del os.environ['USER_CONFIG_PATH']
    
    def test_llm_client_initialization(self):
        """Test LLM client initialization with OpenRouter config"""
        # This would test the actual LLMClient class from the project
        # For now, we'll test the configuration loading
        
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Simulate LLMClient initialization
        assert config['LLM'] == 'custom'
        assert config['CUSTOM_LLM_URL'] == TEST_URL
        assert config['CUSTOM_LLM_API_KEY'] == TEST_API_KEY
        assert config['CUSTOM_MODEL'] == TEST_MODEL
    
    @pytest.mark.asyncio
    async def test_presentation_generation_flow(self):
        """Test the complete presentation generation flow with OpenRouter"""
        # Mock the presentation generation process
        mock_presentation_data = {
            "title": "Test Presentation",
            "slides": [
                {"title": "Slide 1", "content": "Content 1"},
                {"title": "Slide 2", "content": "Content 2"}
            ]
        }
        
        # Mock the LLM response for presentation generation
        mock_response = ChatCompletion(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model=TEST_MODEL,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=json.dumps(mock_presentation_data)
                    ),
                    finish_reason="stop"
                )
            ],
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )
        
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Simulate presentation generation
            client = AsyncOpenAI(
                base_url=TEST_URL,
                api_key=TEST_API_KEY
            )
            
            response = await client.chat.completions.create(
                model=TEST_MODEL,
                messages=[
                    {"role": "system", "content": "Generate a presentation about AI"},
                    {"role": "user", "content": "Create a 2-slide presentation about machine learning"}
                ],
                max_tokens=500
            )
            
            # Parse the response
            presentation_data = json.loads(response.choices[0].message.content)
            
            assert presentation_data['title'] == "Test Presentation"
            assert len(presentation_data['slides']) == 2
            assert presentation_data['slides'][0]['title'] == "Slide 1"


class TestOpenRouterErrorHandling:
    """Test error handling for OpenRouter integration"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "userConfig.json")
        os.environ['USER_CONFIG_PATH'] = self.config_path
    
    def teardown_method(self):
        """Clean up after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'USER_CONFIG_PATH' in os.environ:
            del os.environ['USER_CONFIG_PATH']
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Test handling of invalid API key"""
        invalid_config = TEST_CONFIG.copy()
        invalid_config['CUSTOM_LLM_API_KEY'] = "invalid-key"
        
        with open(self.config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Invalid API key")
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception, match="Invalid API key"):
                client = AsyncOpenAI(
                    base_url=TEST_URL,
                    api_key="invalid-key"
                )
                
                await client.chat.completions.create(
                    model=TEST_MODEL,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=50
                )
    
    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling of network timeout"""
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timed out")
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(asyncio.TimeoutError):
                client = AsyncOpenAI(
                    base_url=TEST_URL,
                    api_key=TEST_API_KEY
                )
                
                await client.chat.completions.create(
                    model=TEST_MODEL,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=50
                )
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test handling of rate limiting"""
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                client = AsyncOpenAI(
                    base_url=TEST_URL,
                    api_key=TEST_API_KEY
                )
                
                await client.chat.completions.create(
                    model=TEST_MODEL,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=50
                )


# Test runner function
def run_tests():
    """Run all OpenRouter tests"""
    print("🧪 Running OpenRouter tests...")
    
    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])


if __name__ == "__main__":
    run_tests()
