from typing import List, Dict, Optional
from services.llm_client import LLMClient
from models.llm_message import LLMMessage
from .llm_analyzer import LLMWebSearchAnalyzer
from .models import QueryAnalysisRequest
import logging

logger = logging.getLogger(__name__)


class EnhancedLLMClient(LLMClient):
    """Расширенный LLM клиент с умным определением веб-поиска"""
    
    def __init__(self):
        super().__init__()
        self.web_search_analyzer = LLMWebSearchAnalyzer()

    async def should_enable_web_grounding(self, user_query: str, presentation_context: Dict = None) -> bool:
        """
        Умное определение необходимости веб-поиска на основе анализа запроса
        
        Args:
            user_query: Пользовательский запрос для анализа
            presentation_context: Контекст презентации
            
        Returns:
            bool: True если нужен веб-поиск, False иначе
        """
        # Если веб-поиск не поддерживается провайдером
        if not self.enable_web_grounding():
            logger.debug(f"Web grounding not supported for provider: {self.llm_provider}")
            return False
        
        try:
            # Анализируем запрос
            analysis_request = QueryAnalysisRequest(
                user_query=user_query,
                presentation_context=presentation_context,
                sensitivity="medium"  # Можно сделать настраиваемым
            )
            
            analysis = await self.web_search_analyzer.analyze_query(analysis_request)
            
            # Логируем решение для отладки
            logger.info(f"Web search analysis for '{user_query[:50]}...': "
                       f"needs_search={analysis.needs_web_search}, "
                       f"confidence={analysis.confidence:.2f}, "
                       f"triggers={[t.value for t in analysis.triggers]}")
            
            return analysis.needs_web_search
            
        except Exception as e:
            logger.error(f"Error in web search analysis: {str(e)}")
            # Fallback на простое правило
            return self._fallback_web_search_decision(user_query)

    def _fallback_web_search_decision(self, user_query: str) -> bool:
        """
        Простое правило для определения веб-поиска при ошибке анализа
        
        Args:
            user_query: Пользовательский запрос
            
        Returns:
            bool: True если нужен веб-поиск по простым правилам
        """
        query_lower = user_query.lower()
        
        # Простые ключевые слова
        temporal_keywords = ['current', 'latest', 'recent', 'today', 'now', '2024', '2025', 
                           'текущий', 'последний', 'недавно', 'сейчас']
        news_keywords = ['news', 'events', 'announcements', 'developments', 
                        'новости', 'события', 'объявления']
        stats_keywords = ['statistics', 'data', 'figures', 'analysis', 'report',
                         'статистика', 'данные', 'анализ', 'отчет', 'стаья',]
        
        has_temporal = any(keyword in query_lower for keyword in temporal_keywords)
        has_news = any(keyword in query_lower for keyword in news_keywords)
        has_stats = any(keyword in query_lower for keyword in stats_keywords)
        
        needs_search = has_temporal or has_news or has_stats
        
        logger.debug(f"Fallback web search decision for '{user_query[:50]}...': {needs_search}")
        
        return needs_search

    async def generate_with_smart_web_search(
        self,
        model: str,
        messages: List[LLMMessage],
        user_query: str = None,
        presentation_context: Dict = None,
        **kwargs
    ):
        """
        Генерация с умным определением веб-поиска
        
        Args:
            model: Модель для генерации
            messages: Сообщения для LLM
            user_query: Пользовательский запрос (для анализа необходимости веб-поиска)
            presentation_context: Контекст презентации
            **kwargs: Дополнительные параметры для generate
            
        Returns:
            Результат генерации
        """
        # Определяем нужен ли веб-поиск
        needs_web_search = False
        if user_query:
            needs_web_search = await self.should_enable_web_grounding(user_query, presentation_context)
        
        # Добавляем SearchWebTool если нужен веб-поиск
        tools = kwargs.get('tools', [])
        if needs_web_search:
            from models.llm_tools import SearchWebTool
            tools = tools + [SearchWebTool] if tools else [SearchWebTool]
            logger.info(f"Added SearchWebTool to generation for query: '{user_query[:50]}...'")
        
        kwargs['tools'] = tools
        
        # Вызываем обычную генерацию
        return await self.generate(model, messages, **kwargs)

    async def stream_with_smart_web_search(
        self,
        model: str,
        messages: List[LLMMessage],
        user_query: str = None,
        presentation_context: Dict = None,
        **kwargs
    ):
        """
        Стриминг с умным определением веб-поиска
        
        Args:
            model: Модель для генерации
            messages: Сообщения для LLM
            user_query: Пользовательский запрос (для анализа необходимости веб-поиска)
            presentation_context: Контекст презентации
            **kwargs: Дополнительные параметры для stream
            
        Returns:
            Асинхронный генератор результатов
        """
        # Определяем нужен ли веб-поиск
        needs_web_search = False
        if user_query:
            needs_web_search = await self.should_enable_web_grounding(user_query, presentation_context)
        
        # Добавляем SearchWebTool если нужен веб-поиск
        tools = kwargs.get('tools', [])
        if needs_web_search:
            from models.llm_tools import SearchWebTool
            tools = tools + [SearchWebTool] if tools else [SearchWebTool]
            logger.info(f"Added SearchWebTool to streaming for query: '{user_query[:50]}...'")
        
        kwargs['tools'] = tools
        
        # Вызываем обычный стриминг
        async for chunk in self.stream(model, messages, **kwargs):
            yield chunk

    async def generate_structured_with_smart_web_search(
        self,
        model: str,
        messages: List[LLMMessage],
        response_format: dict,
        user_query: str = None,
        presentation_context: Dict = None,
        **kwargs
    ):
        """
        Структурированная генерация с умным определением веб-поиска
        
        Args:
            model: Модель для генерации
            messages: Сообщения для LLM
            response_format: Формат ответа
            user_query: Пользовательский запрос (для анализа необходимости веб-поиска)
            presentation_context: Контекст презентации
            **kwargs: Дополнительные параметры для generate_structured
            
        Returns:
            Структурированный результат генерации
        """
        # Определяем нужен ли веб-поиск
        needs_web_search = False
        if user_query:
            needs_web_search = await self.should_enable_web_grounding(user_query, presentation_context)
        
        # Добавляем SearchWebTool если нужен веб-поиск
        tools = kwargs.get('tools', [])
        if needs_web_search:
            from models.llm_tools import SearchWebTool
            tools = tools + [SearchWebTool] if tools else [SearchWebTool]
            logger.info(f"Added SearchWebTool to structured generation for query: '{user_query[:50]}...'")
        
        kwargs['tools'] = tools
        
        # Вызываем обычную структурированную генерацию
        return await self.generate_structured(model, messages, response_format, **kwargs)

    async def stream_structured_with_smart_web_search(
        self,
        model: str,
        messages: List[LLMMessage],
        response_format: dict,
        user_query: str = None,
        presentation_context: Dict = None,
        **kwargs
    ):
        """
        Структурированный стриминг с умным определением веб-поиска
        
        Args:
            model: Модель для генерации
            messages: Сообщения для LLM
            response_format: Формат ответа
            user_query: Пользовательский запрос (для анализа необходимости веб-поиска)
            presentation_context: Контекст презентации
            **kwargs: Дополнительные параметры для stream_structured
            
        Returns:
            Асинхронный генератор структурированных результатов
        """
        # Определяем нужен ли веб-поиск
        needs_web_search = False
        if user_query:
            needs_web_search = await self.should_enable_web_grounding(user_query, presentation_context)
        
        # Добавляем SearchWebTool если нужен веб-поиск
        tools = kwargs.get('tools', [])
        if needs_web_search:
            from models.llm_tools import SearchWebTool
            tools = tools + [SearchWebTool] if tools else [SearchWebTool]
            logger.info(f"Added SearchWebTool to structured streaming for query: '{user_query[:50]}...'")
        
        kwargs['tools'] = tools
        
        # Вызываем обычный структурированный стриминг
        async for chunk in self.stream_structured(model, messages, response_format, **kwargs):
            yield chunk
