import pytest
from services.web_search_analysis.models import (
    WebSearchAnalysis,
    WebSearchTrigger,
    QueryAnalysisRequest,
    BatchAnalysisRequest,
    BatchAnalysisResponse
)


class TestWebSearchTrigger:
    """Тесты для WebSearchTrigger enum"""
    
    def test_trigger_values(self):
        """Проверка значений триггеров"""
        assert WebSearchTrigger.TEMPORAL.value == "temporal"
        assert WebSearchTrigger.NEWS.value == "news"
        assert WebSearchTrigger.STATISTICS.value == "statistics"
        assert WebSearchTrigger.CURRENT_EVENTS.value == "current_events"
        assert WebSearchTrigger.PRICES.value == "prices"
        assert WebSearchTrigger.RESEARCH.value == "research"
        assert WebSearchTrigger.TECHNOLOGY.value == "technology"
        assert WebSearchTrigger.FINANCE.value == "finance"
        assert WebSearchTrigger.GENERAL_KNOWLEDGE.value == "general_knowledge"
    
    def test_trigger_from_value(self):
        """Проверка создания триггера из значения"""
        assert WebSearchTrigger("temporal") == WebSearchTrigger.TEMPORAL
        assert WebSearchTrigger("news") == WebSearchTrigger.NEWS
        assert WebSearchTrigger("statistics") == WebSearchTrigger.STATISTICS


class TestWebSearchAnalysis:
    """Тесты для WebSearchAnalysis модели"""
    
    def test_valid_analysis(self):
        """Проверка создания валидного анализа"""
        analysis = WebSearchAnalysis(
            needs_web_search=True,
            confidence=0.8,
            triggers=[WebSearchTrigger.TEMPORAL, WebSearchTrigger.NEWS],
            reasoning="Query contains temporal indicators and news keywords",
            suggested_queries=["latest AI trends 2024", "AI news today"],
            alternative_approach="Use general knowledge about AI"
        )
        
        assert analysis.needs_web_search is True
        assert analysis.confidence == 0.8
        assert len(analysis.triggers) == 2
        assert WebSearchTrigger.TEMPORAL in analysis.triggers
        assert WebSearchTrigger.NEWS in analysis.triggers
        assert len(analysis.suggested_queries) == 2
        assert analysis.alternative_approach == "Use general knowledge about AI"
    
    def test_minimal_analysis(self):
        """Проверка создания минимального анализа"""
        analysis = WebSearchAnalysis(
            needs_web_search=False,
            confidence=0.3,
            triggers=[],
            reasoning="No web search needed",
            suggested_queries=[]
        )
        
        assert analysis.needs_web_search is False
        assert analysis.confidence == 0.3
        assert len(analysis.triggers) == 0
        assert len(analysis.suggested_queries) == 0
        assert analysis.alternative_approach is None
    
    def test_confidence_validation(self):
        """Проверка валидации confidence"""
        # Валидные значения
        WebSearchAnalysis(
            needs_web_search=True,
            confidence=0.0,
            triggers=[],
            reasoning="test",
            suggested_queries=[]
        )
        
        WebSearchAnalysis(
            needs_web_search=True,
            confidence=1.0,
            triggers=[],
            reasoning="test",
            suggested_queries=[]
        )
        
        # Невалидные значения
        with pytest.raises(ValueError):
            WebSearchAnalysis(
                needs_web_search=True,
                confidence=-0.1,
                triggers=[],
                reasoning="test",
                suggested_queries=[]
            )
        
        with pytest.raises(ValueError):
            WebSearchAnalysis(
                needs_web_search=True,
                confidence=1.1,
                triggers=[],
                reasoning="test",
                suggested_queries=[]
            )


class TestQueryAnalysisRequest:
    """Тесты для QueryAnalysisRequest модели"""
    
    def test_minimal_request(self):
        """Проверка создания минимального запроса"""
        request = QueryAnalysisRequest(user_query="test query")
        
        assert request.user_query == "test query"
        assert request.presentation_context is None
        assert request.sensitivity == "medium"
        assert request.language == "en"
    
    def test_full_request(self):
        """Проверка создания полного запроса"""
        context = {
            "topic": "AI Technology",
            "domain": "technology",
            "previous_slides": ["slide1", "slide2"]
        }
        
        request = QueryAnalysisRequest(
            user_query="Latest AI trends in 2024",
            presentation_context=context,
            sensitivity="high",
            language="ru"
        )
        
        assert request.user_query == "Latest AI trends in 2024"
        assert request.presentation_context == context
        assert request.sensitivity == "high"
        assert request.language == "ru"
    
    def test_sensitivity_validation(self):
        """Проверка валидации sensitivity"""
        # Валидные значения
        QueryAnalysisRequest(user_query="test", sensitivity="low")
        QueryAnalysisRequest(user_query="test", sensitivity="medium")
        QueryAnalysisRequest(user_query="test", sensitivity="high")
        
        # Любые строки принимаются (нет enum ограничений)
        QueryAnalysisRequest(user_query="test", sensitivity="custom")


class TestBatchAnalysisRequest:
    """Тесты для BatchAnalysisRequest модели"""
    
    def test_empty_batch(self):
        """Проверка пустого пакета"""
        request = BatchAnalysisRequest(queries=[])
        assert len(request.queries) == 0
    
    def test_single_query_batch(self):
        """Проверка пакета с одним запросом"""
        query = QueryAnalysisRequest(user_query="test query")
        request = BatchAnalysisRequest(queries=[query])
        
        assert len(request.queries) == 1
        assert request.queries[0].user_query == "test query"
    
    def test_multiple_queries_batch(self):
        """Проверка пакета с несколькими запросами"""
        queries = [
            QueryAnalysisRequest(user_query="query 1"),
            QueryAnalysisRequest(user_query="query 2"),
            QueryAnalysisRequest(user_query="query 3")
        ]
        request = BatchAnalysisRequest(queries=queries)
        
        assert len(request.queries) == 3
        assert request.queries[0].user_query == "query 1"
        assert request.queries[1].user_query == "query 2"
        assert request.queries[2].user_query == "query 3"


class TestBatchAnalysisResponse:
    """Тесты для BatchAnalysisResponse модели"""
    
    def test_response_creation(self):
        """Проверка создания ответа"""
        analysis = WebSearchAnalysis(
            needs_web_search=True,
            confidence=0.8,
            triggers=[WebSearchTrigger.TEMPORAL],
            reasoning="Test reasoning",
            suggested_queries=["test query"]
        )
        
        results = [analysis]
        
        response = BatchAnalysisResponse(
            results=results,
            total_analyzed=1,
            success_count=1,
            error_count=0
        )
        
        assert len(response.results) == 1
        assert response.total_analyzed == 1
        assert response.success_count == 1
        assert response.error_count == 0
        assert response.results[0].needs_web_search is True
    
    def test_response_validation(self):
        """Проверка валидации ответа"""
        # Валидные значения
        BatchAnalysisResponse(
            results=[],
            total_analyzed=0,
            success_count=0,
            error_count=0
        )
        
        # Проверка, что success_count + error_count может быть <= total_analyzed
        BatchAnalysisResponse(
            results=[],
            total_analyzed=10,
            success_count=8,
            error_count=2
        )
