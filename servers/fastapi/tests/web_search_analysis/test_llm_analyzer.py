import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.web_search_analysis.llm_analyzer import LLMWebSearchAnalyzer
from services.web_search_analysis.models import (
    QueryAnalysisRequest, 
    WebSearchAnalysis, 
    WebSearchTrigger
)


class TestLLMWebSearchAnalyzer:
    """Тесты для LLMWebSearchAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Фикстура для создания анализатора"""
        return LLMWebSearchAnalyzer()
    
    @pytest.fixture
    def sample_request(self):
        """Фикстура для тестового запроса"""
        return QueryAnalysisRequest(
            user_query="Latest AI trends in 2024",
            presentation_context={"topic": "Technology"},
            sensitivity="medium",
            language="en"
        )
    
    def test_analysis_schema_structure(self, analyzer):
        """Проверка структуры схемы анализа"""
        schema = analyzer.analysis_schema
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "needs_web_search" in schema["properties"]
        assert "confidence" in schema["properties"]
        assert "triggers" in schema["properties"]
        assert "reasoning" in schema["properties"]
        assert "suggested_queries" in schema["properties"]
        assert "alternative_approach" in schema["properties"]
        
        # Проверка типов
        assert schema["properties"]["needs_web_search"]["type"] == "boolean"
        assert schema["properties"]["confidence"]["type"] == "number"
        assert schema["properties"]["triggers"]["type"] == "array"
        assert schema["properties"]["reasoning"]["type"] == "string"
        assert schema["properties"]["suggested_queries"]["type"] == "array"
    
    def test_create_system_prompt(self, analyzer):
        """Проверка создания системного промпта"""
        prompt = analyzer._create_system_prompt("medium", "en")
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "expert AI assistant" in prompt
        assert "web search" in prompt
        assert "TEMPORAL INDICATORS" in prompt
        assert "STATISTICS & DATA" in prompt
        assert "CURRENT EVENTS" in prompt
    
    def test_create_user_prompt(self, analyzer, sample_request):
        """Проверка создания пользовательского промпта"""
        prompt = analyzer._create_user_prompt(sample_request)
        
        assert isinstance(prompt, str)
        assert "Latest AI trends in 2024" in prompt
        assert "Language: en" in prompt
        assert "Sensitivity level: medium" in prompt
        assert "Presentation topic: Technology" in prompt
    
    def test_create_user_prompt_without_context(self, analyzer):
        """Проверка создания промпта без контекста"""
        request = QueryAnalysisRequest(user_query="test query")
        prompt = analyzer._create_user_prompt(request)
        
        assert "test query" in prompt
        assert "Language: en" in prompt
        assert "Sensitivity level: medium" in prompt
        assert "Context:" not in prompt
    
    def test_parse_llm_response_valid(self, analyzer):
        """Проверка парсинга валидного ответа LLM"""
        response = {
            "needs_web_search": True,
            "confidence": 0.8,
            "triggers": ["temporal", "news"],
            "reasoning": "Query contains temporal indicators",
            "suggested_queries": ["AI trends 2024", "latest AI news"],
            "alternative_approach": "Use general AI knowledge"
        }
        
        analysis = analyzer._parse_llm_response(response)
        
        assert isinstance(analysis, WebSearchAnalysis)
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.8
        assert len(analysis.triggers) == 2
        assert WebSearchTrigger.TEMPORAL in analysis.triggers
        assert WebSearchTrigger.NEWS in analysis.triggers
        assert analysis.reasoning == "Query contains temporal indicators"
        assert len(analysis.suggested_queries) == 2
        assert analysis.alternative_approach == "Use general AI knowledge"
    
    def test_parse_llm_response_invalid_triggers(self, analyzer):
        """Проверка парсинга с невалидными триггерами"""
        response = {
            "needs_web_search": True,
            "confidence": 0.8,
            "triggers": ["invalid_trigger", "temporal"],
            "reasoning": "Test reasoning",
            "suggested_queries": []
        }
        
        analysis = analyzer._parse_llm_response(response)
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.8
        assert len(analysis.triggers) == 1  # Только валидный триггер
        assert WebSearchTrigger.TEMPORAL in analysis.triggers
    
    def test_parse_llm_response_missing_fields(self, analyzer):
        """Проверка парсинга с отсутствующими полями"""
        response = {
            "needs_web_search": True,
            "confidence": 0.8
            # Отсутствуют обязательные поля
        }
        
        analysis = analyzer._parse_llm_response(response)
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.8
        assert analysis.triggers == []
        assert analysis.reasoning == ""
        assert analysis.suggested_queries == []
        assert analysis.alternative_approach is None
    
    def test_fallback_analysis_temporal_keywords(self, analyzer):
        """Проверка fallback анализа с временными ключевыми словами"""
        request = QueryAnalysisRequest(user_query="Latest trends in 2024")
        analysis = analyzer._fallback_analysis(request)
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.6
        assert WebSearchTrigger.TEMPORAL in analysis.triggers
        assert "Fallback analysis" in analysis.reasoning
        assert len(analysis.suggested_queries) == 1
        assert analysis.suggested_queries[0] == "Latest trends in 2024"
    
    def test_fallback_analysis_news_keywords(self, analyzer):
        """Проверка fallback анализа с новостными ключевыми словами"""
        request = QueryAnalysisRequest(user_query="Latest news about AI")
        analysis = analyzer._fallback_analysis(request)
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.6
        assert WebSearchTrigger.NEWS in analysis.triggers
    
    def test_fallback_analysis_statistics_keywords(self, analyzer):
        """Проверка fallback анализа со статистическими ключевыми словами"""
        request = QueryAnalysisRequest(user_query="Statistics about AI usage")
        analysis = analyzer._fallback_analysis(request)
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.6
        assert WebSearchTrigger.STATISTICS in analysis.triggers
    
    def test_fallback_analysis_no_keywords(self, analyzer):
        """Проверка fallback анализа без ключевых слов"""
        request = QueryAnalysisRequest(user_query="What is artificial intelligence?")
        analysis = analyzer._fallback_analysis(request)
        
        assert analysis.needs_web_search is False
        assert analysis.confidence == 0.4
        assert len(analysis.triggers) == 0
        assert len(analysis.suggested_queries) == 0
    
    def test_fallback_analysis_multiple_keywords(self, analyzer):
        """Проверка fallback анализа с несколькими типами ключевых слов"""
        request = QueryAnalysisRequest(user_query="Latest statistics and news about AI in 2024")
        analysis = analyzer._fallback_analysis(request)
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.6
        assert len(analysis.triggers) == 3
        assert WebSearchTrigger.TEMPORAL in analysis.triggers
        assert WebSearchTrigger.NEWS in analysis.triggers
        assert WebSearchTrigger.STATISTICS in analysis.triggers
    
    @pytest.mark.asyncio
    async def test_analyze_query_success(self, analyzer, sample_request):
        """Проверка успешного анализа запроса"""
        # Мокаем LLM клиент
        mock_response = {
            "needs_web_search": True,
            "confidence": 0.8,
            "triggers": ["temporal", "technology"],
            "reasoning": "Query contains temporal indicators and technology keywords",
            "suggested_queries": ["AI trends 2024", "latest AI technology"],
            "alternative_approach": None
        }
        
        with patch.object(analyzer.llm_client, 'generate_structured', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response
            
            analysis = await analyzer.analyze_query(sample_request)
            
            assert analysis.needs_web_search is True
            assert analysis.confidence == 0.8
            assert len(analysis.triggers) == 2
            assert WebSearchTrigger.TEMPORAL in analysis.triggers
            assert WebSearchTrigger.TECHNOLOGY in analysis.triggers
            assert len(analysis.suggested_queries) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_query_llm_error(self, analyzer, sample_request):
        """Проверка обработки ошибки LLM"""
        with patch.object(analyzer.llm_client, 'generate_structured', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("LLM error")
            
            analysis = await analyzer.analyze_query(sample_request)
            
            # Должен вернуться fallback анализ
            assert isinstance(analysis, WebSearchAnalysis)
            assert "Fallback analysis" in analysis.reasoning
    
    @pytest.mark.asyncio
    async def test_batch_analyze_success(self, analyzer):
        """Проверка успешного пакетного анализа"""
        requests = [
            QueryAnalysisRequest(user_query="Latest AI trends"),
            QueryAnalysisRequest(user_query="What is machine learning?"),
            QueryAnalysisRequest(user_query="Current market statistics")
        ]
        
        # Мокаем analyze_query для каждого запроса
        with patch.object(analyzer, 'analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = [
                WebSearchAnalysis(
                    needs_web_search=True,
                    confidence=0.8,
                    triggers=[WebSearchTrigger.TEMPORAL],
                    reasoning="Temporal indicators",
                    suggested_queries=["AI trends 2024"]
                ),
                WebSearchAnalysis(
                    needs_web_search=False,
                    confidence=0.3,
                    triggers=[],
                    reasoning="General knowledge",
                    suggested_queries=[]
                ),
                WebSearchAnalysis(
                    needs_web_search=True,
                    confidence=0.9,
                    triggers=[WebSearchTrigger.STATISTICS],
                    reasoning="Statistics needed",
                    suggested_queries=["market data 2024"]
                )
            ]
            
            results = await analyzer.batch_analyze(requests)
            
            assert len(results) == 3
            assert results[0].needs_web_search is True
            assert results[1].needs_web_search is False
            assert results[2].needs_web_search is True
    
    @pytest.mark.asyncio
    async def test_batch_analyze_with_errors(self, analyzer):
        """Проверка пакетного анализа с ошибками"""
        requests = [
            QueryAnalysisRequest(user_query="Valid query"),
            QueryAnalysisRequest(user_query="Error query")
        ]
        
        with patch.object(analyzer, 'analyze_query', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = [
                WebSearchAnalysis(
                    needs_web_search=True,
                    confidence=0.8,
                    triggers=[WebSearchTrigger.TEMPORAL],
                    reasoning="Valid analysis",
                    suggested_queries=[]
                ),
                Exception("Analysis error")
            ]
            
            results = await analyzer.batch_analyze(requests)
            
            assert len(results) == 2
            assert results[0].needs_web_search is True
            assert "Fallback analysis" in results[1].reasoning  # Fallback для ошибки
