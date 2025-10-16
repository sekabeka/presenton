from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WebSearchTrigger(Enum):
    """Триггеры, указывающие на необходимость веб-поиска"""
    TEMPORAL = "temporal"  # Временные индикаторы
    NEWS = "news"          # Новостные запросы
    STATISTICS = "statistics"  # Статистические данные
    CURRENT_EVENTS = "current_events"  # Текущие события
    PRICES = "prices"      # Цены, курсы
    RESEARCH = "research"  # Исследования, отчеты
    TECHNOLOGY = "technology"  # Технологические новости
    FINANCE = "finance"    # Финансовые данные
    GENERAL_KNOWLEDGE = "general_knowledge"  # Общие знания


class WebSearchAnalysis(BaseModel):
    """Результат анализа необходимости веб-поиска"""
    needs_web_search: bool = Field(description="Нужен ли веб-поиск")
    confidence: float = Field(ge=0.0, le=1.0, description="Уровень уверенности (0.0-1.0)")
    triggers: List[WebSearchTrigger] = Field(description="Триггеры, повлиявшие на решение")
    reasoning: str = Field(description="Объяснение решения")
    suggested_queries: List[str] = Field(description="Предлагаемые поисковые запросы")
    alternative_approach: Optional[str] = Field(default=None, description="Альтернативный подход")


class QueryAnalysisRequest(BaseModel):
    """Запрос на анализ необходимости веб-поиска"""
    user_query: str = Field(description="Пользовательский запрос для анализа")
    presentation_context: Optional[Dict] = Field(default=None, description="Контекст презентации")
    sensitivity: str = Field(default="medium", description="Уровень чувствительности: low, medium, high")
    language: str = Field(default="en", description="Язык запроса")


class BatchAnalysisRequest(BaseModel):
    """Запрос на пакетный анализ"""
    queries: List[QueryAnalysisRequest] = Field(description="Список запросов для анализа")


class BatchAnalysisResponse(BaseModel):
    """Ответ на пакетный анализ"""
    results: List[WebSearchAnalysis] = Field(description="Результаты анализа")
    total_analyzed: int = Field(description="Общее количество проанализированных запросов")
    success_count: int = Field(description="Количество успешно проанализированных запросов")
    error_count: int = Field(description="Количество запросов с ошибками")
