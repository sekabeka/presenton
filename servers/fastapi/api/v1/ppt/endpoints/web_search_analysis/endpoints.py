from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from services.web_search_analysis.models import (
    QueryAnalysisRequest, 
    WebSearchAnalysis, 
    BatchAnalysisRequest,
    BatchAnalysisResponse
)
from services.web_search_analysis.llm_analyzer import LLMWebSearchAnalyzer

logger = logging.getLogger(__name__)

WEB_SEARCH_ANALYSIS_ROUTER = APIRouter(prefix="/web-search-analysis", tags=["Web Search Analysis"])


@WEB_SEARCH_ANALYSIS_ROUTER.post("/analyze", response_model=WebSearchAnalysis)
async def analyze_web_search_need(request: QueryAnalysisRequest):
    """
    Анализ необходимости веб-поиска для одного запроса
    
    Args:
        request: Запрос с пользовательским запросом и контекстом
        
    Returns:
        WebSearchAnalysis: Результат анализа с рекомендациями
    """
    try:
        analyzer = LLMWebSearchAnalyzer()
        analysis = await analyzer.analyze_query(request)
        
        logger.info(f"Analyzed query: '{request.user_query}' - needs_web_search: {analysis.needs_web_search}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing query '{request.user_query}': {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )


@WEB_SEARCH_ANALYSIS_ROUTER.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_queries(request: BatchAnalysisRequest):
    """
    Пакетный анализ нескольких запросов
    
    Args:
        request: Список запросов для анализа
        
    Returns:
        BatchAnalysisResponse: Результаты анализа всех запросов
    """
    try:
        analyzer = LLMWebSearchAnalyzer()
        
        # Анализируем все запросы
        analyses = await analyzer.batch_analyze(request.queries)
        
        # Формируем результаты
        success_count = 0
        error_count = 0
        
        for analysis in analyses:
            if analysis.reasoning and "Error" not in analysis.reasoning:
                success_count += 1
            else:
                error_count += 1
        
        logger.info(f"Batch analysis completed: {success_count} successful, {error_count} errors")
        
        return BatchAnalysisResponse(
            results=analyses,
            total_analyzed=len(request.queries),
            success_count=success_count,
            error_count=error_count
        )
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Batch analysis failed: {str(e)}"
        )


@WEB_SEARCH_ANALYSIS_ROUTER.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса анализа веб-поиска
    
    Returns:
        dict: Статус сервиса
    """
    try:
        # Простой тест анализатора
        analyzer = LLMWebSearchAnalyzer()
        test_request = QueryAnalysisRequest(
            user_query="test query",
            sensitivity="medium"
        )
        
        # Проверяем, что анализатор может быть создан
        # (не делаем полный анализ для экономии ресурсов)
        
        return {
            "status": "healthy",
            "service": "web_search_analysis",
            "message": "Service is operational"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@WEB_SEARCH_ANALYSIS_ROUTER.get("/triggers")
async def get_available_triggers():
    """
    Получить список доступных триггеров для анализа
    
    Returns:
        dict: Список всех доступных триггеров
    """
    from services.web_search_analysis.models import WebSearchTrigger
    
    triggers = [
        {
            "value": trigger.value,
            "name": trigger.name,
            "description": trigger.value.replace("_", " ").title()
        }
        for trigger in WebSearchTrigger
    ]
    
    return {
        "triggers": triggers,
        "total": len(triggers)
    }
