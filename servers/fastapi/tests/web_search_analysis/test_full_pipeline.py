import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app


class TestFullPipelineIntegration:
    """Тесты полного пайплайна с Web Search Analysis"""
    
    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента"""
        return TestClient(app)
    
    def test_generate_presentation_with_smart_web_search(self, client):
        """Тест генерации презентации с умным веб-поиском через API"""
        request_data = {
            "content": "Latest AI trends in 2024",
            "n_slides": 5,
            "web_search": True,
            "smart_web_search": True,
            "language": "English",
            "tone": "professional",
            "verbosity": "standard"
        }
        
        # Мокаем все зависимости
        with patch('services.web_search_analysis.enhanced_llm_client.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.should_enable_web_grounding = AsyncMock(return_value=True)
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "Latest AI Trends 2024", "slides": [
                    {"title": "Introduction", "body": "AI trends overview"},
                    {"title": "Key Developments", "body": "Major AI breakthroughs"},
                    {"title": "Market Impact", "body": "Economic implications"},
                    {"title": "Future Outlook", "body": "Predictions for 2024"},
                    {"title": "Conclusion", "body": "Summary and next steps"}
                ]}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Мокаем другие зависимости
            with patch('services.database.get_async_session') as mock_db:
                with patch('services.temp_file_service.TEMP_FILE_SERVICE') as mock_temp:
                    with patch('services.pptx_presentation_creator.PptxPresentationCreator') as mock_pptx:
                        with patch('services.concurrent_service.CONCURRENT_SERVICE') as mock_concurrent:
                            
                            # Настраиваем моки
                            mock_temp.create_temp_dir.return_value = "/tmp/test"
                            mock_pptx.return_value.create_presentation.return_value = "test.pptx"
                            mock_concurrent.add_task.return_value = None
                            
                            # Выполняем запрос
                            response = client.post("/api/v1/ppt/presentation/generate", json=request_data)
                            
                            # Проверяем результат
                            assert response.status_code == 200
                            
                            # Проверяем, что умный анализ был вызван
                            mock_client.should_enable_web_grounding.assert_called_once()
                            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    def test_generate_presentation_without_smart_web_search(self, client):
        """Тест генерации презентации без умного веб-поиска"""
        request_data = {
            "content": "What is machine learning?",
            "n_slides": 3,
            "web_search": True,
            "smart_web_search": False,  # Отключен умный поиск
            "language": "English",
            "tone": "educational",
            "verbosity": "standard"
        }
        
        with patch('services.web_search_analysis.enhanced_llm_client.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.enable_web_grounding.return_value = True
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "Machine Learning Basics", "slides": [
                    {"title": "What is ML?", "body": "Definition and concepts"},
                    {"title": "Types of ML", "body": "Supervised, unsupervised, reinforcement"},
                    {"title": "Applications", "body": "Real-world use cases"}
                ]}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Мокаем другие зависимости
            with patch('services.database.get_async_session') as mock_db:
                with patch('services.temp_file_service.TEMP_FILE_SERVICE') as mock_temp:
                    with patch('services.pptx_presentation_creator.PptxPresentationCreator') as mock_pptx:
                        with patch('services.concurrent_service.CONCURRENT_SERVICE') as mock_concurrent:
                            
                            # Настраиваем моки
                            mock_temp.create_temp_dir.return_value = "/tmp/test"
                            mock_pptx.return_value.create_presentation.return_value = "test.pptx"
                            mock_concurrent.add_task.return_value = None
                            
                            # Выполняем запрос
                            response = client.post("/api/v1/ppt/presentation/generate", json=request_data)
                            
                            # Проверяем результат
                            assert response.status_code == 200
                            
                            # Проверяем, что умный анализ НЕ был вызван
                            mock_client.should_enable_web_grounding.assert_not_called()
                            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    def test_generate_presentation_default_smart_web_search(self, client):
        """Тест генерации презентации с умолчательным значением smart_web_search"""
        request_data = {
            "content": "AI technology overview",
            "n_slides": 4,
            "web_search": True,
            # smart_web_search не указан - должен быть True по умолчанию
            "language": "English",
            "tone": "informative",
            "verbosity": "standard"
        }
        
        with patch('services.web_search_analysis.enhanced_llm_client.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.should_enable_web_grounding = AsyncMock(return_value=False)
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "AI Technology Overview", "slides": [
                    {"title": "Introduction", "body": "AI basics"},
                    {"title": "Technologies", "body": "Key AI technologies"},
                    {"title": "Applications", "body": "AI use cases"},
                    {"title": "Future", "body": "AI future trends"}
                ]}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Мокаем другие зависимости
            with patch('services.database.get_async_session') as mock_db:
                with patch('services.temp_file_service.TEMP_FILE_SERVICE') as mock_temp:
                    with patch('services.pptx_presentation_creator.PptxPresentationCreator') as mock_pptx:
                        with patch('services.concurrent_service.CONCURRENT_SERVICE') as mock_concurrent:
                            
                            # Настраиваем моки
                            mock_temp.create_temp_dir.return_value = "/tmp/test"
                            mock_pptx.return_value.create_presentation.return_value = "test.pptx"
                            mock_concurrent.add_task.return_value = None
                            
                            # Выполняем запрос
                            response = client.post("/api/v1/ppt/presentation/generate", json=request_data)
                            
                            # Проверяем результат
                            assert response.status_code == 200
                            
                            # Проверяем, что умный анализ был вызван (по умолчанию True)
                            mock_client.should_enable_web_grounding.assert_called_once()
                            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    def test_outlines_endpoint_with_smart_web_search(self, client):
        """Тест эндпоинта outlines с умным веб-поиском"""
        # Сначала создаем презентацию
        presentation_data = {
            "content": "Latest technology trends",
            "n_slides": 3,
            "web_search": True,
            "smart_web_search": True,
            "language": "English"
        }
        
        with patch('services.web_search_analysis.enhanced_llm_client.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.should_enable_web_grounding = AsyncMock(return_value=True)
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "Technology Trends", "slides": [
                    {"title": "Current Trends", "body": "Latest developments"},
                    {"title": "Impact", "body": "Industry impact"},
                    {"title": "Future", "body": "What's next"}
                ]}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Мокаем базу данных
            with patch('services.database.get_async_session') as mock_db:
                with patch('services.temp_file_service.TEMP_FILE_SERVICE') as mock_temp:
                    
                    # Настраиваем моки
                    mock_temp.create_temp_dir.return_value = "/tmp/test"
                    
                    # Создаем презентацию
                    create_response = client.post("/api/v1/ppt/presentation/generate", json=presentation_data)
                    assert create_response.status_code == 200
                    
                    # Получаем ID презентации из ответа
                    response_data = create_response.json()
                    presentation_id = response_data.get("id")
                    
                    if presentation_id:
                        # Тестируем эндпоинт outlines
                        outlines_response = client.get(f"/api/v1/ppt/outlines/stream/{presentation_id}")
                        assert outlines_response.status_code == 200
                        
                        # Проверяем, что умный анализ был вызван
                        mock_client.should_enable_web_grounding.assert_called()
                        mock_client.stream_structured_with_smart_web_search.assert_called()
    
    def test_api_validation_smart_web_search_parameter(self, client):
        """Тест валидации параметра smart_web_search в API"""
        # Тест с валидным boolean значением
        valid_request = {
            "content": "Test content",
            "n_slides": 3,
            "web_search": True,
            "smart_web_search": True,
            "language": "English"
        }
        
        with patch('services.web_search_analysis.enhanced_llm_client.EnhancedLLMClient'):
            with patch('services.database.get_async_session'):
                with patch('services.temp_file_service.TEMP_FILE_SERVICE'):
                    with patch('services.pptx_presentation_creator.PptxPresentationCreator'):
                        with patch('services.concurrent_service.CONCURRENT_SERVICE'):
                            
                            response = client.post("/api/v1/ppt/presentation/generate", json=valid_request)
                            assert response.status_code == 200
        
        # Тест с невалидным типом
        invalid_request = {
            "content": "Test content",
            "n_slides": 3,
            "web_search": True,
            "smart_web_search": "invalid",  # Должно быть boolean
            "language": "English"
        }
        
        response = client.post("/api/v1/ppt/presentation/generate", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        # Тест без параметра (должен использовать значение по умолчанию)
        default_request = {
            "content": "Test content",
            "n_slides": 3,
            "web_search": True,
            # smart_web_search не указан
            "language": "English"
        }
        
        with patch('services.web_search_analysis.enhanced_llm_client.EnhancedLLMClient'):
            with patch('services.database.get_async_session'):
                with patch('services.temp_file_service.TEMP_FILE_SERVICE'):
                    with patch('services.pptx_presentation_creator.PptxPresentationCreator'):
                        with patch('services.concurrent_service.CONCURRENT_SERVICE'):
                            
                            response = client.post("/api/v1/ppt/presentation/generate", json=default_request)
                            assert response.status_code == 200
