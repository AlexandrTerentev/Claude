# -*- coding: utf-8 -*-
"""
Mission Planner Diagnostic Agent - Core Module
Простая версия для тестирования связи C# <-> Python
"""

def process_query(user_input):
    """
    Главная функция обработки запросов пользователя
    Вызывается из C# плагина

    Args:
        user_input: строка запроса от пользователя

    Returns:
        строка ответа агента
    """
    # На данном этапе просто возвращаем эхо для тестирования
    return "Echo: " + str(user_input) + "\n\nPython agent is working!"

# Для будущего расширения
class DiagnosticAgent:
    def __init__(self, log_path):
        self.log_path = log_path

    def process(self, user_input):
        return process_query(user_input)
