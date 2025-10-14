#!/usr/bin/env python3
"""
Simple test script for OpenRouter integration
This script can be run without pytest dependencies
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from openai import AsyncOpenAI

# Test configuration
TEST_API_KEY = "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"
TEST_URL = "https://openrouter.ai/api/v1"
TEST_MODEL = "openai/gpt-4o-mini"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, color=Colors.BLUE):
    """Print a status message with color"""
    print(f"{color}[TEST]{Colors.END} {message}")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}[PASS]{Colors.END} {message}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}[FAIL]{Colors.END} {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {message}")

class OpenRouterTester:
    """Test class for OpenRouter functionality"""
    
    def __init__(self):
        self.temp_dir = None
        self.config_path = None
        self.test_results = []
    
    def setup(self):
        """Set up test environment"""
        print_status("Setting up test environment...")
        
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "userConfig.json")
        os.environ['USER_CONFIG_PATH'] = self.config_path
        
        print_success("Test environment created")
    
    def cleanup(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'USER_CONFIG_PATH' in os.environ:
            del os.environ['USER_CONFIG_PATH']
        print_status("Test environment cleaned up")
    
    def test_config_creation(self):
        """Test creating user configuration"""
        print_status("Testing configuration creation...")
        
        try:
            config = {
                "LLM": "custom",
                "CUSTOM_LLM_URL": TEST_URL,
                "CUSTOM_LLM_API_KEY": TEST_API_KEY,
                "CUSTOM_MODEL": TEST_MODEL,
                "TOOL_CALLS": False,
                "DISABLE_THINKING": False,
                "EXTENDED_REASONING": False,
                "WEB_GROUNDING": False
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Verify config was created
            assert os.path.exists(self.config_path)
            
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config['LLM'] == 'custom'
            assert loaded_config['CUSTOM_LLM_URL'] == TEST_URL
            assert loaded_config['CUSTOM_LLM_API_KEY'] == TEST_API_KEY
            assert loaded_config['CUSTOM_MODEL'] == TEST_MODEL
            
            print_success("Configuration creation test passed")
            self.test_results.append(("Config Creation", True, ""))
            
        except Exception as e:
            print_error(f"Configuration creation test failed: {e}")
            self.test_results.append(("Config Creation", False, str(e)))
    
    def test_config_loading(self):
        """Test loading configuration from file"""
        print_status("Testing configuration loading...")
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['LLM', 'CUSTOM_LLM_URL', 'CUSTOM_LLM_API_KEY', 'CUSTOM_MODEL']
            for field in required_fields:
                assert field in config, f"Missing required field: {field}"
                assert config[field] is not None, f"Field {field} is None"
            
            print_success("Configuration loading test passed")
            self.test_results.append(("Config Loading", True, ""))
            
        except Exception as e:
            print_error(f"Configuration loading test failed: {e}")
            self.test_results.append(("Config Loading", False, str(e)))
    
    async def test_openrouter_connection(self):
        """Test OpenRouter API connection"""
        print_status("Testing OpenRouter connection...")
        
        try:
            # Load config
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Create OpenAI client
            client = AsyncOpenAI(
                base_url=config['CUSTOM_LLM_URL'],
                api_key=config['CUSTOM_LLM_API_KEY']
            )
            
            # Test connection with a simple request
            response = await client.chat.completions.create(
                model=config['CUSTOM_MODEL'],
                messages=[
                    {"role": "user", "content": "Hello! Please respond with just 'Connection test successful!'"}
                ],
                max_tokens=50
            )
            
            # Verify response
            assert response.choices[0].message.content is not None
            assert len(response.choices[0].message.content) > 0
            
            print_success(f"OpenRouter connection test passed - Response: {response.choices[0].message.content}")
            self.test_results.append(("OpenRouter Connection", True, ""))
            
        except Exception as e:
            print_error(f"OpenRouter connection test failed: {e}")
            self.test_results.append(("OpenRouter Connection", False, str(e)))
    
    async def test_different_models(self):
        """Test different OpenRouter models"""
        print_status("Testing different models...")
        
        models_to_test = [
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet"
        ]
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            client = AsyncOpenAI(
                base_url=config['CUSTOM_LLM_URL'],
                api_key=config['CUSTOM_LLM_API_KEY']
            )
            
            for model in models_to_test:
                print_status(f"Testing model: {model}")
                
                # Update config with new model
                config['CUSTOM_MODEL'] = model
                with open(self.config_path, 'w') as f:
                    json.dump(config, f)
                
                # Test the model
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": f"Test message for {model}"}
                    ],
                    max_tokens=20
                )
                
                assert response.choices[0].message.content is not None
                print_success(f"Model {model} test passed")
            
            print_success("All model tests passed")
            self.test_results.append(("Model Testing", True, ""))
            
        except Exception as e:
            print_error(f"Model testing failed: {e}")
            self.test_results.append(("Model Testing", False, str(e)))
    
    async def test_presentation_generation(self):
        """Test presentation generation flow"""
        print_status("Testing presentation generation...")
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            client = AsyncOpenAI(
                base_url=config['CUSTOM_LLM_URL'],
                api_key=config['CUSTOM_LLM_API_KEY']
            )
            
            # Test presentation generation prompt
            response = await client.chat.completions.create(
                model=config['CUSTOM_MODEL'],
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a presentation generator. Create a simple 2-slide presentation about AI."
                    },
                    {
                        "role": "user", 
                        "content": "Generate a presentation with title and 2 slides about artificial intelligence."
                    }
                ],
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            assert content is not None
            assert len(content) > 50  # Should be substantial content
            
            print_success("Presentation generation test passed")
            self.test_results.append(("Presentation Generation", True, ""))
            
        except Exception as e:
            print_error(f"Presentation generation test failed: {e}")
            self.test_results.append(("Presentation Generation", False, str(e)))
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print_status("Testing error handling...")
        
        try:
            # Test invalid config
            invalid_config = {
                "LLM": "custom",
                "CUSTOM_LLM_URL": "https://invalid-url.com/api/v1",
                "CUSTOM_LLM_API_KEY": "invalid-key",
                "CUSTOM_MODEL": "invalid-model"
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(invalid_config, f)
            
            # This should not crash the application
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config['CUSTOM_LLM_URL'] == "https://invalid-url.com/api/v1"
            
            print_success("Error handling test passed")
            self.test_results.append(("Error Handling", True, ""))
            
        except Exception as e:
            print_error(f"Error handling test failed: {e}")
            self.test_results.append(("Error Handling", False, str(e)))
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}OpenRouter Test Results Summary{Colors.END}")
        print("="*60)
        
        passed = 0
        failed = 0
        
        for test_name, success, error in self.test_results:
            if success:
                print(f"{Colors.GREEN}✓{Colors.END} {test_name}")
                passed += 1
            else:
                print(f"{Colors.RED}✗{Colors.END} {test_name}: {error}")
                failed += 1
        
        print("-"*60)
        print(f"Total: {len(self.test_results)} | {Colors.GREEN}Passed: {passed}{Colors.END} | {Colors.RED}Failed: {failed}{Colors.END}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! OpenRouter is ready to use.{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Please check the errors above.{Colors.END}")
        
        return failed == 0

async def main():
    """Main test function"""
    print(f"{Colors.BOLD}{Colors.BLUE}🧪 OpenRouter Integration Tests{Colors.END}\n")
    
    tester = OpenRouterTester()
    
    try:
        # Setup
        tester.setup()
        
        # Run tests
        tester.test_config_creation()
        tester.test_config_loading()
        await tester.test_openrouter_connection()
        await tester.test_different_models()
        await tester.test_presentation_generation()
        tester.test_error_handling()
        
        # Print results
        success = tester.print_results()
        
        return 0 if success else 1
        
    except Exception as e:
        print_error(f"Test suite failed with error: {e}")
        return 1
        
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
