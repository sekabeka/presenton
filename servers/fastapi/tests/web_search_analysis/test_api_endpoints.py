import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from services.web_search_analysis.models import (
    QueryAnalysisRequest,
    WebSearchAnalysis,
    WebSearchTrigger,
    BatchAnalysisRequest
)


class TestWebSearchAnalysisEndpoints:
    """Тесты для API эндпоинтов анализа веб-поиска"""
    
    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента"""
        from api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def sample_analysis(self):
        """Фикстура для тестового анализа"""
        return WebSearchAnalysis(
            needs_web_search=True,
            confidence=0.8,
            triggers=[WebSearchTrigger.TEMPORAL, WebSearchTrigger.TECHNOLOGY],
            reasoning="Query contains temporal indicators and technology keywords",
            suggested_queries=["AI trends 2024", "latest AI technology"],
            alternative_approach=None
        )
    
    def test_analyze_endpoint_success(self, client, sample_analysis):
        """Проверка успешного анализа через API"""
        request_data = {
            "user_query": "Latest AI trends in 2024",
            "presentation_context": {"topic": "Technology"},
            "sensitivity": "medium",
            "language": "en"
        }
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze_query.return_value = sample_analysis
            mock_analyzer_class.return_value = mock_analyzer
            
            response = client.post("/api/v1/ppt/web-search-analysis/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["needs_web_search"] is True
            assert data["confidence"] == 0.8
            assert len(data["triggers"]) == 2
            assert "temporal" in data["triggers"]
            assert "technology" in data["triggers"]
            assert len(data["suggested_queries"]) == 2
    
    def test_analyze_endpoint_minimal_request(self, client, sample_analysis):
        """Проверка анализа с минимальными данными"""
        request_data = {
            "user_query": "test query"
        }
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze_query.return_value = sample_analysis
            mock_analyzer_class.return_value = mock_analyzer
            
            response = client.post("/api/v1/ppt/web-search-analysis/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "needs_web_search" in data
            assert "confidence" in data
            assert "triggers" in data
            assert "reasoning" in data
            assert "suggested_queries" in data
    
    def test_analyze_endpoint_validation_error(self, client):
        """Проверка ошибки валидации"""
        # Отсутствует обязательное поле user_query
        request_data = {
            "sensitivity": "medium"
        }
        
        response = client.post("/api/v1/ppt/web-search-analysis/analyze", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_endpoint_analyzer_error(self, client):
        """Проверка ошибки анализатора"""
        request_data = {
            "user_query": "test query"
        }
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze_query.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer
            
            response = client.post("/api/v1/ppt/web-search-analysis/analyze", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "Analysis failed" in data["detail"]
    
    def test_batch_analyze_endpoint_success(self, client):
        """Проверка успешного пакетного анализа"""
        request_data = {
            "queries": [
                {
                    "user_query": "Latest AI trends",
                    "sensitivity": "medium"
                },
                {
                    "user_query": "What is machine learning?",
                    "sensitivity": "low"
                }
            ]
        }
        
        analysis1 = WebSearchAnalysis(
            needs_web_search=True,
            confidence=0.8,
            triggers=[WebSearchTrigger.TEMPORAL],
            reasoning="Temporal indicators",
            suggested_queries=["AI trends 2024"]
        )
        
        analysis2 = WebSearchAnalysis(
            needs_web_search=False,
            confidence=0.3,
            triggers=[],
            reasoning="General knowledge",
            suggested_queries=[]
        )
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.batch_analyze.return_value = [analysis1, analysis2]
            mock_analyzer_class.return_value = mock_analyzer
            
            response = client.post("/api/v1/ppt/web-search-analysis/batch-analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_analyzed"] == 2
            assert data["success_count"] == 2
            assert data["error_count"] == 0
            assert len(data["results"]) == 2
            assert data["results"][0]["needs_web_search"] is True
            assert data["results"][1]["needs_web_search"] is False
    
    def test_batch_analyze_endpoint_empty_queries(self, client):
        """Проверка пакетного анализа с пустым списком запросов"""
        request_data = {
            "queries": []
        }
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.batch_analyze.return_value = []
            mock_analyzer_class.return_value = mock_analyzer
            
            response = client.post("/api/v1/ppt/web-search-analysis/batch-analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_analyzed"] == 0
            assert data["success_count"] == 0
            assert data["error_count"] == 0
            assert len(data["results"]) == 0
    
    def test_batch_analyze_endpoint_error(self, client):
        """Проверка ошибки пакетного анализа"""
        request_data = {
            "queries": [
                {
                    "user_query": "test query"
                }
            ]
        }
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.batch_analyze.side_effect = Exception("Batch analysis failed")
            mock_analyzer_class.return_value = mock_analyzer
            
            response = client.post("/api/v1/ppt/web-search-analysis/batch-analyze", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "Batch analysis failed" in data["detail"]
    
    def test_health_check_endpoint(self, client):
        """Проверка эндпоинта проверки здоровья"""
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer_class.return_value = MagicMock()
            
            response = client.get("/api/v1/ppt/web-search-analysis/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "web_search_analysis"
            assert "operational" in data["message"]
    
    def test_health_check_endpoint_error(self, client):
        """Проверка ошибки в эндпоинте проверки здоровья"""
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer_class.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/v1/ppt/web-search-analysis/health")
            
            assert response.status_code == 503
            data = response.json()
            assert "Service unhealthy" in data["detail"]
    
    def test_get_triggers_endpoint(self, client):
        """Проверка эндпоинта получения списка триггеров"""
        response = client.get("/api/v1/ppt/web-search-analysis/triggers")
        
        assert response.status_code == 200
        data = response.json()
        assert "triggers" in data
        assert "total" in data
        assert data["total"] > 0
        
        # Проверяем, что все триггеры присутствуют
        trigger_values = [trigger["value"] for trigger in data["triggers"]]
        assert "temporal" in trigger_values
        assert "news" in trigger_values
        assert "statistics" in trigger_values
        assert "current_events" in trigger_values
        assert "prices" in trigger_values
        assert "research" in trigger_values
        assert "technology" in trigger_values
        assert "finance" in trigger_values
        assert "general_knowledge" in trigger_values
    
    def test_analyze_endpoint_different_languages(self, client, sample_analysis):
        """Проверка анализа запросов на разных языках"""
        test_cases = [
            {"user_query": "Latest AI trends", "language": "en"},
            {"user_query": "Последние тренды ИИ", "language": "ru"},
            {"user_query": "Tendencias recientes de IA", "language": "es"},
            {"user_query": "Tendances récentes de l'IA", "language": "fr"},
            {"user_query": "Neueste KI-Trends", "language": "de"}
        ]
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze_query.return_value = sample_analysis
            mock_analyzer_class.return_value = mock_analyzer
            
            for test_case in test_cases:
                response = client.post("/api/v1/ppt/web-search-analysis/analyze", json=test_case)
                assert response.status_code == 200
                data = response.json()
                assert "needs_web_search" in data
    
    def test_analyze_endpoint_different_sensitivity_levels(self, client, sample_analysis):
        """Проверка анализа с разными уровнями чувствительности"""
        sensitivity_levels = ["low", "medium", "high"]
        
        with patch('services.web_search_analysis.llm_analyzer.LLMWebSearchAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze_query.return_value = sample_analysis
            mock_analyzer_class.return_value = mock_analyzer
            
            for sensitivity in sensitivity_levels:
                request_data = {
                    "user_query": "test query",
                    "sensitivity": sensitivity
                }
                
                response = client.post("/api/v1/ppt/web-search-analysis/analyze", json=request_data)
                assert response.status_code == 200
                data = response.json()
                assert "needs_web_search" in data
