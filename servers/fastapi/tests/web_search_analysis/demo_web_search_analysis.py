#!/usr/bin/env python3
"""
Демонстрационный скрипт для Web Search Analysis Service

Этот скрипт демонстрирует работу сервиса умного определения веб-поиска.
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.web_search_analysis.llm_analyzer import LLMWebSearchAnalyzer
from services.web_search_analysis.enhanced_llm_client import EnhancedLLMClient
from services.web_search_analysis.models import QueryAnalysisRequest, WebSearchTrigger
from models.llm_message import LLMUserMessage


async def demo_basic_analysis():
    """Демонстрация базового анализа запросов"""
    print("🔍 Демонстрация базового анализа запросов")
    print("=" * 50)
    
    analyzer = LLMWebSearchAnalyzer()
    
    # Тестовые запросы
    test_queries = [
        "Latest AI trends in 2024",
        "What is machine learning?",
        "Current statistics about AI adoption",
        "Recent news about ChatGPT",
        "How does neural networks work?",
        "Today's stock prices for tech companies",
        "Latest research papers on quantum computing"
    ]
    
    for query in test_queries:
        print(f"\n📝 Запрос: '{query}'")
        
        try:
            request = QueryAnalysisRequest(
                user_query=query,
                presentation_context={"topic": "Technology"},
                sensitivity="medium",
                language="en"
            )
            
            analysis = await analyzer.analyze_query(request)
            
            print(f"   ✅ Нужен веб-поиск: {analysis.needs_web_search}")
            print(f"   📊 Уверенность: {analysis.confidence:.2f}")
            print(f"   🎯 Триггеры: {[t.value for t in analysis.triggers]}")
            print(f"   💭 Обоснование: {analysis.reasoning}")
            
            if analysis.suggested_queries:
                print(f"   🔍 Предложенные запросы: {analysis.suggested_queries}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")


async def demo_enhanced_llm_client():
    """Демонстрация расширенного LLM клиента"""
    print("\n\n🚀 Демонстрация расширенного LLM клиента")
    print("=" * 50)
    
    client = EnhancedLLMClient()
    
    # Тестовые запросы для анализа
    test_queries = [
        "Latest AI trends in 2024",
        "What is artificial intelligence?",
        "Current market statistics for AI companies"
    ]
    
    for query in test_queries:
        print(f"\n📝 Анализ запроса: '{query}'")
        
        try:
            # Анализируем нужен ли веб-поиск
            needs_search = await client.should_enable_web_grounding(
                user_query=query,
                presentation_context={"topic": "Technology"}
            )
            
            print(f"   🔍 Нужен веб-поиск: {needs_search}")
            
            # Демонстрируем fallback анализ
            fallback_result = client._fallback_web_search_decision(query)
            print(f"   🔄 Fallback результат: {fallback_result}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")


async def demo_batch_analysis():
    """Демонстрация пакетного анализа"""
    print("\n\n📦 Демонстрация пакетного анализа")
    print("=" * 50)
    
    analyzer = LLMWebSearchAnalyzer()
    
    # Создаем пакет запросов
    queries = [
        QueryAnalysisRequest(
            user_query="Latest AI trends",
            presentation_context={"topic": "Technology"},
            sensitivity="high"
        ),
        QueryAnalysisRequest(
            user_query="What is machine learning?",
            presentation_context={"topic": "Education"},
            sensitivity="low"
        ),
        QueryAnalysisRequest(
            user_query="Current AI market statistics",
            presentation_context={"topic": "Business"},
            sensitivity="medium"
        )
    ]
    
    try:
        print("🔄 Анализируем пакет запросов...")
        analyses = await analyzer.batch_analyze(queries)
        
        print(f"✅ Проанализировано {len(analyses)} запросов")
        
        for i, analysis in enumerate(analyses):
            query_text = queries[i].user_query
            print(f"\n📝 Запрос {i+1}: '{query_text}'")
            print(f"   🔍 Нужен поиск: {analysis.needs_web_search}")
            print(f"   📊 Уверенность: {analysis.confidence:.2f}")
            print(f"   🎯 Триггеры: {[t.value for t in analysis.triggers]}")
            
    except Exception as e:
        print(f"❌ Ошибка пакетного анализа: {str(e)}")


async def demo_multilingual_analysis():
    """Демонстрация многоязычного анализа"""
    print("\n\n🌍 Демонстрация многоязычного анализа")
    print("=" * 50)
    
    analyzer = LLMWebSearchAnalyzer()
    
    # Многоязычные запросы
    multilingual_queries = [
        ("Latest AI trends in 2024", "en"),
        ("Последние тренды ИИ в 2024", "ru"),
        ("Tendencias recientes de IA en 2024", "es"),
        ("Tendances récentes de l'IA en 2024", "fr"),
        ("Neueste KI-Trends 2024", "de")
    ]
    
    for query, language in multilingual_queries:
        print(f"\n📝 Запрос ({language}): '{query}'")
        
        try:
            request = QueryAnalysisRequest(
                user_query=query,
                presentation_context={"topic": "Technology"},
                sensitivity="medium",
                language=language
            )
            
            analysis = await analyzer.analyze_query(request)
            
            print(f"   🔍 Нужен веб-поиск: {analysis.needs_web_search}")
            print(f"   📊 Уверенность: {analysis.confidence:.2f}")
            print(f"   🎯 Триггеры: {[t.value for t in analysis.triggers]}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")


async def demo_sensitivity_levels():
    """Демонстрация разных уровней чувствительности"""
    print("\n\n⚙️ Демонстрация уровней чувствительности")
    print("=" * 50)
    
    analyzer = LLMWebSearchAnalyzer()
    
    query = "AI technology overview"
    sensitivity_levels = ["low", "medium", "high"]
    
    for sensitivity in sensitivity_levels:
        print(f"\n📝 Запрос: '{query}' (чувствительность: {sensitivity})")
        
        try:
            request = QueryAnalysisRequest(
                user_query=query,
                presentation_context={"topic": "Technology"},
                sensitivity=sensitivity,
                language="en"
            )
            
            analysis = await analyzer.analyze_query(request)
            
            print(f"   🔍 Нужен веб-поиск: {analysis.needs_web_search}")
            print(f"   📊 Уверенность: {analysis.confidence:.2f}")
            print(f"   🎯 Триггеры: {[t.value for t in analysis.triggers]}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")


async def demo_trigger_types():
    """Демонстрация разных типов триггеров"""
    print("\n\n🎯 Демонстрация типов триггеров")
    print("=" * 50)
    
    analyzer = LLMWebSearchAnalyzer()
    
    # Запросы для разных типов триггеров
    trigger_examples = [
        ("Latest AI trends in 2024", "temporal"),
        ("Breaking news about AI", "news"),
        ("AI market statistics 2024", "statistics"),
        ("Current events in AI", "current_events"),
        ("AI stock prices today", "prices"),
        ("Recent AI research papers", "research"),
        ("AI technology updates", "technology"),
        ("AI company financial reports", "finance"),
        ("What is artificial intelligence?", "general_knowledge")
    ]
    
    for query, expected_trigger in trigger_examples:
        print(f"\n📝 Запрос: '{query}' (ожидаемый триггер: {expected_trigger})")
        
        try:
            request = QueryAnalysisRequest(
                user_query=query,
                presentation_context={"topic": "Technology"},
                sensitivity="medium",
                language="en"
            )
            
            analysis = await analyzer.analyze_query(request)
            
            print(f"   🔍 Нужен веб-поиск: {analysis.needs_web_search}")
            print(f"   📊 Уверенность: {analysis.confidence:.2f}")
            print(f"   🎯 Триггеры: {[t.value for t in analysis.triggers]}")
            
            # Проверяем, есть ли ожидаемый триггер
            trigger_values = [t.value for t in analysis.triggers]
            if expected_trigger in trigger_values:
                print(f"   ✅ Ожидаемый триггер '{expected_trigger}' найден!")
            else:
                print(f"   ⚠️ Ожидаемый триггер '{expected_trigger}' не найден")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")


async def main():
    """Главная функция демонстрации"""
    print("🎉 Демонстрация Web Search Analysis Service")
    print("=" * 60)
    print("Этот сервис умно определяет, нужен ли веб-поиск для запросов")
    print("на основе анализа с использованием LLM.\n")
    
    try:
        # Запускаем все демонстрации
        await demo_basic_analysis()
        await demo_enhanced_llm_client()
        await demo_batch_analysis()
        await demo_multilingual_analysis()
        await demo_sensitivity_levels()
        await demo_trigger_types()
        
        print("\n\n🎊 Демонстрация завершена!")
        print("=" * 60)
        print("Сервис готов к использованию в production!")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        print("Проверьте настройки и зависимости.")


if __name__ == "__main__":
    # Запускаем демонстрацию
    asyncio.run(main())
