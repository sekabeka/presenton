import json
import logging
from typing import List, Dict, Optional
from services.llm_client import LLMClient
from models.llm_message import LLMMessage, LLMSystemMessage, LLMUserMessage
from .models import WebSearchAnalysis, WebSearchTrigger, QueryAnalysisRequest

logger = logging.getLogger(__name__)


class LLMWebSearchAnalyzer:
    """LLM-анализатор для определения необходимости веб-поиска"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.analysis_schema = self._get_analysis_schema()

    def _get_analysis_schema(self) -> dict:
        """Схема для структурированного ответа LLM"""
        return {
            "type": "object",
            "properties": {
                "needs_web_search": {
                    "type": "boolean",
                    "description": "Whether the query requires web search for accurate, up-to-date information"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence level in the decision (0.0 = not confident, 1.0 = very confident)"
                },
                "triggers": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [trigger.value for trigger in WebSearchTrigger]
                    },
                    "description": "Categories that indicate need for web search"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed explanation of why web search is or isn't needed"
                },
                "suggested_queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Suggested search queries if web search is needed"
                },
                "alternative_approach": {
                    "type": "string",
                    "description": "Alternative approach if web search is not needed"
                }
            },
            "required": ["needs_web_search", "confidence", "triggers", "reasoning", "suggested_queries"]
        }

    async def analyze_query(self, request: QueryAnalysisRequest) -> WebSearchAnalysis:
        """Основной метод анализа запроса с использованием LLM"""
        
        try:
            # Формируем системный промпт
            system_prompt = self._create_system_prompt(request.sensitivity, request.language)
            
            # Формируем пользовательский запрос
            user_prompt = self._create_user_prompt(request)
            
            # Создаем сообщения для LLM
            messages = [
                LLMSystemMessage(content=system_prompt),
                LLMUserMessage(content=user_prompt)
            ]
            
            # Получаем анализ от LLM
            response = await self.llm_client.generate_structured(
                model=self.llm_client.get_model(),
                messages=messages,
                response_format=self.analysis_schema,
                strict=True
            )
            
            # Парсим ответ
            return self._parse_llm_response(response)
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            # Fallback на простое правило
            return self._fallback_analysis(request)

    def _create_system_prompt(self, sensitivity: str, language: str) -> str:
        """Создание системного промпта для анализа"""
        
        sensitivity_instructions = {
            "low": "Be conservative - only recommend web search for clearly time-sensitive queries",
            "medium": "Balance between accuracy and efficiency - recommend web search for queries that likely need current information",
            "high": "Be liberal - recommend web search for most queries that could benefit from current information"
        }
        
        language_instructions = {
            "en": "Analyze English queries",
            "ru": "Analyze Russian queries", 
            "es": "Analyze Spanish queries",
            "fr": "Analyze French queries",
            "de": "Analyze German queries"
        }
        
        return f"""You are an expert AI assistant that determines whether a user query requires web search for accurate, up-to-date information.

{language_instructions.get(language, "Analyze queries in any language")}

{sensitivity_instructions.get(sensitivity, sensitivity_instructions["medium"])}

Consider these factors when determining if web search is needed:

TEMPORAL INDICATORS (High Priority):
- Current year (2024, 2025)
- Time-sensitive words: "current", "latest", "recent", "today", "now", "up-to-date"
- Trend analysis: "trends", "changes", "developments"
- News and events: "news", "events", "announcements"

STATISTICS & DATA (High Priority):
- Statistical queries: "statistics", "data", "figures", "numbers"
- Research requests: "studies", "reports", "analysis"
- Rankings and comparisons: "top", "best", "worst", "rankings"
- Market data: "prices", "rates", "indexes", "performance"

CURRENT EVENTS (High Priority):
- Political events: "elections", "government", "policy"
- Economic events: "market", "economy", "crisis", "recession"
- Social events: "protests", "movements", "social issues"
- Global events: "war", "conflict", "disasters", "pandemic"

TECHNOLOGY & INNOVATION (Medium Priority):
- Latest tech: "AI", "blockchain", "quantum", "latest technology"
- Startups and companies: "startups", "unicorns", "IPO"
- Research and development: "breakthrough", "innovation", "discovery"

FINANCE & BUSINESS (Medium Priority):
- Financial data: "stocks", "bonds", "investments", "earnings"
- Business news: "mergers", "acquisitions", "partnerships"
- Economic indicators: "GDP", "inflation", "unemployment"

GENERAL KNOWLEDGE (Low Priority):
- Historical facts that don't change
- Basic definitions and concepts
- Established scientific principles
- General educational content

For each query, provide:
1. A clear decision (needs_web_search: true/false)
2. Confidence level (0.0-1.0)
3. Specific triggers that influenced your decision
4. Detailed reasoning
5. Suggested search queries (if web search is needed)
6. Alternative approach (if web search is not needed)

Be precise and explain your reasoning clearly."""

    def _create_user_prompt(self, request: QueryAnalysisRequest) -> str:
        """Создание пользовательского промпта"""
        prompt_parts = [
            f"Query to analyze: \"{request.user_query}\"",
            f"Language: {request.language}",
            f"Sensitivity level: {request.sensitivity}"
        ]
        
        if request.presentation_context:
            context_info = []
            if request.presentation_context.get('topic'):
                context_info.append(f"Presentation topic: {request.presentation_context['topic']}")
            if request.presentation_context.get('previous_slides'):
                context_info.append(f"Number of previous slides: {len(request.presentation_context['previous_slides'])}")
            if request.presentation_context.get('domain'):
                context_info.append(f"Domain: {request.presentation_context['domain']}")
            
            if context_info:
                prompt_parts.append("Context:")
                prompt_parts.extend([f"- {info}" for info in context_info])
        
        return "\n".join(prompt_parts)

    def _parse_llm_response(self, response: dict) -> WebSearchAnalysis:
        """Парсинг ответа от LLM"""
        try:
            # Извлекаем триггеры
            triggers = []
            for trigger_value in response.get('triggers', []):
                try:
                    triggers.append(WebSearchTrigger(trigger_value))
                except ValueError:
                    logger.warning(f"Unknown trigger: {trigger_value}")
            
            return WebSearchAnalysis(
                needs_web_search=response.get('needs_web_search', False),
                confidence=response.get('confidence', 0.0),
                triggers=triggers,
                reasoning=response.get('reasoning', ''),
                suggested_queries=response.get('suggested_queries', []),
                alternative_approach=response.get('alternative_approach')
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            # Fallback при ошибке парсинга
            return WebSearchAnalysis(
                needs_web_search=False,
                confidence=0.0,
                triggers=[],
                reasoning=f"Error parsing LLM response: {str(e)}",
                suggested_queries=[]
            )

    def _fallback_analysis(self, request: QueryAnalysisRequest) -> WebSearchAnalysis:
        """Простой fallback анализ при ошибке LLM"""
        query = request.user_query.lower()
        
        # Простые правила
        temporal_keywords = ['current', 'latest', 'recent', 'today', 'now', '2024', '2025', 'текущий', 'последний', 'недавно']
        news_keywords = ['news', 'events', 'announcements', 'developments', 'новости', 'события', 'объявления']
        stats_keywords = ['statistics', 'data', 'figures', 'analysis', 'report', 'статистика', 'данные', 'анализ']
        
        has_temporal = any(keyword in query for keyword in temporal_keywords)
        has_news = any(keyword in query for keyword in news_keywords)
        has_stats = any(keyword in query for keyword in stats_keywords)
        
        needs_search = has_temporal or has_news or has_stats
        confidence = 0.6 if needs_search else 0.4
        
        triggers = []
        if has_temporal:
            triggers.append(WebSearchTrigger.TEMPORAL)
        if has_news:
            triggers.append(WebSearchTrigger.NEWS)
        if has_stats:
            triggers.append(WebSearchTrigger.STATISTICS)
        
        return WebSearchAnalysis(
            needs_web_search=needs_search,
            confidence=confidence,
            triggers=triggers,
            reasoning="Fallback analysis based on simple keyword matching",
            suggested_queries=[request.user_query] if needs_search else []
        )

    async def batch_analyze(self, requests: List[QueryAnalysisRequest]) -> List[WebSearchAnalysis]:
        """Пакетный анализ запросов"""
        results = []
        
        for request in requests:
            try:
                analysis = await self.analyze_query(request)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing query '{request.user_query}': {str(e)}")
                # Добавляем fallback результат
                results.append(self._fallback_analysis(request))
        
        return results
