import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.web_search_analysis.enhanced_llm_client import EnhancedLLMClient
from services.web_search_analysis.models import WebSearchAnalysis, WebSearchTrigger
from models.llm_message import LLMMessage, LLMUserMessage


class TestEnhancedLLMClientIntegration:
    """Тесты интеграции EnhancedLLMClient"""
    
    @pytest.fixture
    def enhanced_client(self):
        """Фикстура для создания расширенного клиента"""
        return EnhancedLLMClient()
    
    @pytest.fixture
    def sample_messages(self):
        """Фикстура для тестовых сообщений"""
        return [LLMUserMessage(role="user", content="Test message")]
    
    def test_should_enable_web_grounding_unsupported_provider(self, enhanced_client):
        """Проверка отключения веб-поиска для неподдерживаемых провайдеров"""
        # Мокаем неподдерживаемый провайдер
        with patch.object(enhanced_client, 'enable_web_grounding', return_value=False):
            result = await enhanced_client.should_enable_web_grounding("test query")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_should_enable_web_grounding_success(self, enhanced_client):
        """Проверка успешного определения необходимости веб-поиска"""
        # Мокаем поддерживаемый провайдер
        with patch.object(enhanced_client, 'enable_web_grounding', return_value=True):
            # Мокаем анализатор
            mock_analysis = WebSearchAnalysis(
                needs_web_search=True,
                confidence=0.8,
                triggers=[WebSearchTrigger.TEMPORAL],
                reasoning="Temporal indicators found",
                suggested_queries=["test query 2024"]
            )
            
            with patch.object(enhanced_client.web_search_analyzer, 'analyze_query', 
                            new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = mock_analysis
                
                result = await enhanced_client.should_enable_web_grounding("Latest trends in 2024")
                
                assert result is True
                mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_enable_web_grounding_analyzer_error(self, enhanced_client):
        """Проверка обработки ошибки анализатора"""
        with patch.object(enhanced_client, 'enable_web_grounding', return_value=True):
            with patch.object(enhanced_client.web_search_analyzer, 'analyze_query', 
                            new_callable=AsyncMock) as mock_analyze:
                mock_analyze.side_effect = Exception("Analysis error")
                
                result = await enhanced_client.should_enable_web_grounding("test query")
                
                # Должен вернуться fallback результат
                assert isinstance(result, bool)
    
    def test_fallback_web_search_decision_temporal(self, enhanced_client):
        """Проверка fallback решения с временными ключевыми словами"""
        result = enhanced_client._fallback_web_search_decision("Latest trends in 2024")
        assert result is True
    
    def test_fallback_web_search_decision_news(self, enhanced_client):
        """Проверка fallback решения с новостными ключевыми словами"""
        result = enhanced_client._fallback_web_search_decision("Latest news about AI")
        assert result is True
    
    def test_fallback_web_search_decision_statistics(self, enhanced_client):
        """Проверка fallback решения со статистическими ключевыми словами"""
        result = enhanced_client._fallback_web_search_decision("Statistics about AI usage")
        assert result is True
    
    def test_fallback_web_search_decision_no_keywords(self, enhanced_client):
        """Проверка fallback решения без ключевых слов"""
        result = enhanced_client._fallback_web_search_decision("What is artificial intelligence?")
        assert result is False
    
    def test_fallback_web_search_decision_multilingual(self, enhanced_client):
        """Проверка fallback решения с многоязычными ключевыми словами"""
        # Русские ключевые слова
        result = enhanced_client._fallback_web_search_decision("Последние новости об ИИ")
        assert result is True
        
        # Смешанные языки
        result = enhanced_client._fallback_web_search_decision("Latest статистика по AI")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_with_smart_web_search_needs_search(self, enhanced_client, sample_messages):
        """Проверка генерации с умным веб-поиском когда поиск нужен"""
        with patch.object(enhanced_client, 'should_enable_web_grounding', 
                        new_callable=AsyncMock) as mock_should_enable:
            mock_should_enable.return_value = True
            
            with patch.object(enhanced_client, 'generate', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = "Generated content"
                
                result = await enhanced_client.generate_with_smart_web_search(
                    model="test-model",
                    messages=sample_messages,
                    user_query="Latest AI trends",
                    presentation_context={"topic": "Technology"}
                )
                
                assert result == "Generated content"
                mock_should_enable.assert_called_once_with("Latest AI trends", {"topic": "Technology"})
                mock_generate.assert_called_once()
                
                # Проверяем, что SearchWebTool был добавлен
                call_args = mock_generate.call_args
                assert 'tools' in call_args.kwargs
                tools = call_args.kwargs['tools']
                assert tools is not None
                assert len(tools) > 0
    
    @pytest.mark.asyncio
    async def test_generate_with_smart_web_search_no_search(self, enhanced_client, sample_messages):
        """Проверка генерации с умным веб-поиском когда поиск не нужен"""
        with patch.object(enhanced_client, 'should_enable_web_grounding', 
                        new_callable=AsyncMock) as mock_should_enable:
            mock_should_enable.return_value = False
            
            with patch.object(enhanced_client, 'generate', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = "Generated content"
                
                result = await enhanced_client.generate_with_smart_web_search(
                    model="test-model",
                    messages=sample_messages,
                    user_query="What is machine learning?"
                )
                
                assert result == "Generated content"
                mock_should_enable.assert_called_once()
                mock_generate.assert_called_once()
                
                # Проверяем, что SearchWebTool не был добавлен
                call_args = mock_generate.call_args
                assert 'tools' in call_args.kwargs
                tools = call_args.kwargs['tools']
                assert tools is None or len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_generate_with_smart_web_search_no_user_query(self, enhanced_client, sample_messages):
        """Проверка генерации без пользовательского запроса"""
        with patch.object(enhanced_client, 'should_enable_web_grounding', 
                        new_callable=AsyncMock) as mock_should_enable:
            with patch.object(enhanced_client, 'generate', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = "Generated content"
                
                result = await enhanced_client.generate_with_smart_web_search(
                    model="test-model",
                    messages=sample_messages
                    # Нет user_query
                )
                
                assert result == "Generated content"
                mock_should_enable.assert_not_called()  # Не должен вызываться
                mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_with_smart_web_search(self, enhanced_client, sample_messages):
        """Проверка стриминга с умным веб-поиском"""
        with patch.object(enhanced_client, 'should_enable_web_grounding', 
                        new_callable=AsyncMock) as mock_should_enable:
            mock_should_enable.return_value = True
            
            # Мокаем stream метод
            async def mock_stream(*args, **kwargs):
                yield "chunk1"
                yield "chunk2"
            
            with patch.object(enhanced_client, 'stream', side_effect=mock_stream) as mock_stream_method:
                chunks = []
                async for chunk in enhanced_client.stream_with_smart_web_search(
                    model="test-model",
                    messages=sample_messages,
                    user_query="Latest trends"
                ):
                    chunks.append(chunk)
                
                assert chunks == ["chunk1", "chunk2"]
                mock_should_enable.assert_called_once()
                mock_stream_method.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_structured_with_smart_web_search(self, enhanced_client, sample_messages):
        """Проверка структурированной генерации с умным веб-поиском"""
        with patch.object(enhanced_client, 'should_enable_web_grounding', 
                        new_callable=AsyncMock) as mock_should_enable:
            mock_should_enable.return_value = True
            
            with patch.object(enhanced_client, 'generate_structured', 
                            new_callable=AsyncMock) as mock_generate_structured:
                mock_generate_structured.return_value = {"result": "structured"}
                
                response_format = {"type": "object"}
                result = await enhanced_client.generate_structured_with_smart_web_search(
                    model="test-model",
                    messages=sample_messages,
                    response_format=response_format,
                    user_query="Latest data"
                )
                
                assert result == {"result": "structured"}
                mock_should_enable.assert_called_once()
                mock_generate_structured.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_structured_with_smart_web_search(self, enhanced_client, sample_messages):
        """Проверка структурированного стриминга с умным веб-поиском"""
        with patch.object(enhanced_client, 'should_enable_web_grounding', 
                        new_callable=AsyncMock) as mock_should_enable:
            mock_should_enable.return_value = True
            
            # Мокаем stream_structured метод
            async def mock_stream_structured(*args, **kwargs):
                yield {"chunk": 1}
                yield {"chunk": 2}
            
            with patch.object(enhanced_client, 'stream_structured', 
                            side_effect=mock_stream_structured) as mock_stream_structured_method:
                response_format = {"type": "object"}
                chunks = []
                async for chunk in enhanced_client.stream_structured_with_smart_web_search(
                    model="test-model",
                    messages=sample_messages,
                    response_format=response_format,
                    user_query="Latest trends"
                ):
                    chunks.append(chunk)
                
                assert chunks == [{"chunk": 1}, {"chunk": 2}]
                mock_should_enable.assert_called_once()
                mock_stream_structured_method.assert_called_once()


class TestGeneratePresentationOutlinesIntegration:
    """Тесты интеграции с generate_ppt_outline"""
    
    @pytest.mark.asyncio
    async def test_generate_ppt_outline_with_smart_web_search(self):
        """Проверка интеграции умного веб-поиска в generate_ppt_outline"""
        from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
        
        # Мокаем EnhancedLLMClient
        with patch('utils.llm_calls.generate_presentation_outlines.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.should_enable_web_grounding = AsyncMock(return_value=True)
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "Test Presentation", "slides": []}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Вызываем функцию
            chunks = []
            async for chunk in generate_ppt_outline(
                content="Latest AI trends in 2024",
                n_slides=5,
                web_search=True,
                smart_web_search=True
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 1
            assert chunks[0]["title"] == "Test Presentation"
            
            # Проверяем, что был вызван умный анализ
            mock_client.should_enable_web_grounding.assert_called_once_with(
                "Latest AI trends in 2024"
            )
            mock_client.stream_structured_with_smart_web_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ppt_outline_fallback_to_original(self):
        """Проверка fallback на оригинальную логику при отключенном умном поиске"""
        from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
        
        # Мокаем EnhancedLLMClient
        with patch('utils.llm_calls.generate_presentation_outlines.EnhancedLLMClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.enable_web_grounding.return_value = True
            
            # Мокаем stream_structured_with_smart_web_search
            async def mock_stream_structured(*args, **kwargs):
                yield {"title": "Test Presentation", "slides": []}
            
            mock_client.stream_structured_with_smart_web_search = mock_stream_structured
            mock_client_class.return_value = mock_client
            
            # Вызываем функцию с отключенным умным поиском
            chunks = []
            async for chunk in generate_ppt_outline(
                content="Latest AI trends in 2024",
                n_slides=5,
                web_search=True,
                smart_web_search=False  # Отключен умный поиск
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 1
            assert chunks[0]["title"] == "Test Presentation"
            
            # Проверяем, что умный анализ НЕ был вызван
            mock_client.should_enable_web_grounding.assert_not_called()
            mock_client.stream_structured_with_smart_web_search.assert_called_once()
