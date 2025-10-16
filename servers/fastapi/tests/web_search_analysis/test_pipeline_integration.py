import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.web_search_analysis.enhanced_llm_client import EnhancedLLMClient
from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
from models.llm_message import LLMUserMessage


class TestPipelineIntegration:
    """Тесты интеграции пайплайна без полного запуска приложения"""
    
    @pytest.mark.asyncio
    async def test_generate_ppt_outline_with_smart_web_search_enabled(self):
        """Тест generate_ppt_outline с включенным умным веб-поиском"""
        content = "Latest AI trends in 2024"
        n_slides = 5
        
        with patch('utils.llm_calls.generate_presentation_outlines.EnhancedLLMClient') as mock_client_class:
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
            
            # Вызываем функцию
            chunks = []
            async for chunk in generate_ppt_outline(
                content=content,
                n_slides=n_slides,
                web_search=True,
                smart_web_search=True
            ):
                chunks.append(chunk)
            
            # Проверяем результат
            assert len(chunks) == 1
            assert chunks[0]["title"] == "Latest AI Trends 2024"
            assert len(chunks[0]["slides"]) == 5
            
            # Проверяем, что умный анализ был вызван
            mock_client.should_enable_web_grounding.assert_called_once_with(content)
            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ppt_outline_with_smart_web_search_disabled(self):
        """Тест generate_ppt_outline с отключенным умным веб-поиском"""
        content = "What is machine learning?"
        n_slides = 3
        
        with patch('utils.llm_calls.generate_presentation_outlines.EnhancedLLMClient') as mock_client_class:
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
            
            # Вызываем функцию
            chunks = []
            async for chunk in generate_ppt_outline(
                content=content,
                n_slides=n_slides,
                web_search=True,
                smart_web_search=False  # Отключен умный поиск
            ):
                chunks.append(chunk)
            
            # Проверяем результат
            assert len(chunks) == 1
            assert chunks[0]["title"] == "Machine Learning Basics"
            assert len(chunks[0]["slides"]) == 3
            
            # Проверяем, что умный анализ НЕ был вызван
            mock_client.should_enable_web_grounding.assert_not_called()
            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ppt_outline_without_web_search(self):
        """Тест generate_ppt_outline без веб-поиска"""
        content = "Basic programming concepts"
        n_slides = 4
        
        with patch('utils.llm_calls.generate_presentation_outlines.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "Programming Basics", "slides": [
                    {"title": "Variables", "body": "Understanding variables"},
                    {"title": "Functions", "body": "Creating functions"},
                    {"title": "Loops", "body": "Iteration concepts"},
                    {"title": "Data Structures", "body": "Arrays and objects"}
                ]}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Вызываем функцию
            chunks = []
            async for chunk in generate_ppt_outline(
                content=content,
                n_slides=n_slides,
                web_search=False,  # Веб-поиск отключен
                smart_web_search=True
            ):
                chunks.append(chunk)
            
            # Проверяем результат
            assert len(chunks) == 1
            assert chunks[0]["title"] == "Programming Basics"
            assert len(chunks[0]["slides"]) == 4
            
            # Проверяем, что умный анализ НЕ был вызван (веб-поиск отключен)
            mock_client.should_enable_web_grounding.assert_not_called()
            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhanced_llm_client_integration(self):
        """Тест интеграции EnhancedLLMClient с реальным анализом"""
        client = EnhancedLLMClient()
        
        # Мокаем LLM анализатор
        with patch.object(client.web_search_analyzer, 'analyze_query', new_callable=AsyncMock) as mock_analyze:
            from services.web_search_analysis.models import WebSearchAnalysis, WebSearchTrigger
            
            # Настраиваем мок анализа
            mock_analysis = WebSearchAnalysis(
                needs_web_search=True,
                confidence=0.8,
                triggers=[WebSearchTrigger.TEMPORAL, WebSearchTrigger.TECHNOLOGY],
                reasoning="Query contains temporal indicators and technology keywords",
                suggested_queries=["AI trends 2024", "latest AI technology"],
                alternative_approach=None
            )
            mock_analyze.return_value = mock_analysis
            
            # Тестируем should_enable_web_grounding
            result = await client.should_enable_web_grounding(
                user_query="Latest AI trends in 2024",
                presentation_context={"topic": "Technology"}
            )
            
            assert result is True
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhanced_llm_client_fallback(self):
        """Тест fallback механизма EnhancedLLMClient"""
        client = EnhancedLLMClient()
        
        # Мокаем ошибку анализа
        with patch.object(client.web_search_analyzer, 'analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("LLM analysis failed")
            
            # Тестируем should_enable_web_grounding с ошибкой
            result = await client.should_enable_web_grounding(
                user_query="Latest AI trends in 2024",
                presentation_context={"topic": "Technology"}
            )
            
            # Должен вернуться fallback результат
            assert isinstance(result, bool)
            mock_analyze.assert_called_once()
    
    def test_generate_presentation_request_model_validation(self):
        """Тест валидации модели GeneratePresentationRequest"""
        from models.generate_presentation_request import GeneratePresentationRequest
        
        # Тест с валидными данными
        valid_request = GeneratePresentationRequest(
            content="Test content",
            n_slides=5,
            web_search=True,
            smart_web_search=True,
            language="English"
        )
        
        assert valid_request.content == "Test content"
        assert valid_request.n_slides == 5
        assert valid_request.web_search is True
        assert valid_request.smart_web_search is True
        assert valid_request.language == "English"
        
        # Тест с умолчательными значениями
        default_request = GeneratePresentationRequest(content="Test content")
        
        assert default_request.web_search is False
        assert default_request.smart_web_search is True  # По умолчанию True
        assert default_request.n_slides == 8
        assert default_request.language == "English"
    
    def test_presentation_model_validation(self):
        """Тест валидации модели PresentationModel"""
        from models.sql.presentation import PresentationModel
        import uuid
        
        # Тест с валидными данными
        presentation = PresentationModel(
            id=uuid.uuid4(),
            content="Test content",
            n_slides=5,
            web_search=True,
            smart_web_search=True,
            language="English"
        )
        
        assert presentation.content == "Test content"
        assert presentation.n_slides == 5
        assert presentation.web_search is True
        assert presentation.smart_web_search is True
        assert presentation.language == "English"
        
        # Тест с умолчательными значениями
        default_presentation = PresentationModel(
            id=uuid.uuid4(),
            content="Test content",
            n_slides=8,  # Обязательное поле
            language="English"  # Обязательное поле
        )
        
        assert default_presentation.web_search is False
        assert default_presentation.smart_web_search is True  # По умолчанию True
        assert default_presentation.n_slides == 8
        assert default_presentation.language == "English"
