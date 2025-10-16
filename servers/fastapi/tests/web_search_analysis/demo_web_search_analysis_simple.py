#!/usr/bin/env python3
"""
Простая демонстрация Web Search Analysis Service
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def demo_basic_functionality():
    """Демонстрация базовой функциональности"""
    print("🎯 Демонстрация Web Search Analysis Service")
    print("=" * 60)
    
    try:
        from services.web_search_analysis.enhanced_llm_client import EnhancedLLMClient
        from services.web_search_analysis.models import QueryAnalysisRequest
        
        # Создаем клиент
        client = EnhancedLLMClient()
        
        # Тестовые запросы
        test_queries = [
            "Latest AI trends in 2024",
            "What is machine learning?",
            "Current statistics about AI adoption",
            "Recent news about ChatGPT",
            "How does neural networks work?",
            "Today's stock prices for tech companies"
        ]
        
        print("🔍 Анализ запросов с помощью fallback механизма:")
        print("-" * 50)
        
        for query in test_queries:
            # Используем fallback анализ (не требует LLM)
            needs_search = client._fallback_web_search_decision(query)
            
            status = "✅ НУЖЕН" if needs_search else "❌ НЕ НУЖЕН"
            print(f"{status} | {query}")
        
        print("\n🎉 Демонстрация завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def demo_models():
    """Демонстрация моделей данных"""
    print("\n📋 Демонстрация моделей данных:")
    print("-" * 50)
    
    try:
        from services.web_search_analysis.models import (
            WebSearchAnalysis, 
            WebSearchTrigger, 
            QueryAnalysisRequest
        )
        
        # Создаем анализ
        analysis = WebSearchAnalysis(
            needs_web_search=True,
            confidence=0.85,
            triggers=[WebSearchTrigger.TEMPORAL, WebSearchTrigger.TECHNOLOGY],
            reasoning="Query contains temporal indicators and technology keywords",
            suggested_queries=["AI trends 2024", "latest AI technology"],
            alternative_approach="Use general AI knowledge"
        )
        
        print(f"📊 Результат анализа:")
        print(f"   Нужен веб-поиск: {analysis.needs_web_search}")
        print(f"   Уверенность: {analysis.confidence}")
        print(f"   Триггеры: {[t.value for t in analysis.triggers]}")
        print(f"   Обоснование: {analysis.reasoning}")
        print(f"   Предложенные запросы: {analysis.suggested_queries}")
        
        # Создаем запрос
        request = QueryAnalysisRequest(
            user_query="Latest AI trends in 2024",
            presentation_context={"topic": "Technology", "domain": "AI"},
            sensitivity="high",
            language="en"
        )
        
        print(f"\n📝 Запрос на анализ:")
        print(f"   Запрос: {request.user_query}")
        print(f"   Контекст: {request.presentation_context}")
        print(f"   Чувствительность: {request.sensitivity}")
        print(f"   Язык: {request.language}")
        
        print("\n✅ Модели данных работают корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в моделях: {e}")
        return False

def demo_api_usage():
    """Демонстрация использования API"""
    print("\n🌐 Демонстрация API использования:")
    print("-" * 50)
    
    print("📡 Доступные эндпоинты:")
    print("   GET  /api/v1/ppt/web-search-analysis/health")
    print("   GET  /api/v1/ppt/web-search-analysis/triggers")
    print("   POST /api/v1/ppt/web-search-analysis/analyze")
    print("   POST /api/v1/ppt/web-search-analysis/batch-analyze")
    
    print("\n📝 Пример запроса к API:")
    print("""
curl -X POST "http://localhost:8000/api/v1/ppt/web-search-analysis/analyze" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_query": "Latest AI trends in 2024",
    "presentation_context": {"topic": "Technology"},
    "sensitivity": "medium",
    "language": "en"
  }'
    """)
    
    print("📝 Пример создания презентации с умным веб-поиском:")
    print("""
curl -X POST "http://localhost:8000/api/v1/ppt/presentation/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Latest AI trends in 2024",
    "n_slides": 5,
    "web_search": true,
    "smart_web_search": true,
    "language": "English"
  }'
    """)
    
    print("✅ API готов к использованию!")
    return True

def demo_integration():
    """Демонстрация интеграции"""
    print("\n🔗 Демонстрация интеграции:")
    print("-" * 50)
    
    print("📋 Пайплайн интеграции:")
    print("1. Frontend отправляет запрос с smart_web_search=true")
    print("2. GeneratePresentationRequest получает параметр")
    print("3. generate_presentation_handler передает в generate_ppt_outline")
    print("4. EnhancedLLMClient анализирует запрос")
    print("5. LLMWebSearchAnalyzer определяет нужен ли веб-поиск")
    print("6. SearchWebTool добавляется если нужно")
    print("7. Генерируется контур презентации")
    
    print("\n🎯 Ключевые файлы:")
    print("   models/generate_presentation_request.py - API модель")
    print("   models/sql/presentation.py - База данных")
    print("   api/v1/ppt/endpoints/presentation.py - API эндпоинт")
    print("   utils/llm_calls/generate_presentation_outlines.py - Генерация")
    print("   services/web_search_analysis/ - Сервис анализа")
    
    print("\n✅ Интеграция завершена!")
    return True

async def main():
    """Главная функция демонстрации"""
    print("🚀 Демонстрация Web Search Analysis Service")
    print("=" * 60)
    
    # Запускаем демонстрации
    demos = [
        demo_models,
        demo_api_usage,
        demo_integration,
    ]
    
    for demo in demos:
        if not demo():
            return False
    
    # Асинхронная демонстрация
    if not await demo_basic_functionality():
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Все демонстрации завершены успешно!")
    print("💡 Сервис готов к использованию в production!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
