# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ВАЖНО: ЯЗЫК ОБЩЕНИЯ

**ОБЯЗАТЕЛЬНОЕ ТРЕБОВАНИЕ:** При работе с этим проектом Claude ДОЛЖЕН отвечать ТОЛЬКО на русском языке. Все объяснения, комментарии, сообщения об ошибках и техническая документация должны быть написаны на русском языке.

## Обзор проекта

AvtoOpen - это кроссплатформенный (Windows/Linux) лаунчер сборок с поддержкой автоматизации. Пользователи создают "сборки" - коллекции приложений, которые запускаются вместе с автоматическими действиями (клики, нажатия клавиш, ввод текста).

## Команды

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python src/main.py
# или
cd src && python main.py
```

## Архитектура

### Основной слой (`src/core/`)
- **action.py** - Класс `Action` с фабричными методами (`delay()`, `click()`, `type_text()`, `hotkey()`). Использует enum `ActionType`.
- **assembly.py** - Dataclass'ы `Assembly` (коллекция приложений) и `AppConfig` (одно приложение с его действиями).
- **automation.py** - `AutomationEngine` оборачивает PyAutoGUI для выполнения действий.
- **executor.py** - `AssemblyExecutor` запускает приложения и выполняет их действия, поддерживает параллельное выполнение.

### Слой хранения (`src/storage/`)
- **config.py** - `ConfigManager` управляет сериализацией в JSON в `~/.config/avto_open/` (Linux) или `%APPDATA%/avto_open/` (Windows).

### Слой интерфейса (`src/ui/`)
- **main_window.py** - Главное окно со списком сборок, кнопкой запуска, логом выполнения. Использует `ExecutorThread` для фонового выполнения.
- **assembly_editor.py** - Диалог для редактирования названия сборки, описания и списка приложений.
- **action_editor.py** - Диалог для добавления/редактирования действий с помощником захвата позиции мыши.

### Поток данных
1. Пользователь создает Assembly → добавляет AppConfig'и → добавляет Action'ы в каждый AppConfig
2. ConfigManager сохраняет в JSON
3. AssemblyExecutor запускает приложения параллельно → AutomationEngine выполняет действия последовательно для каждого приложения

## Ключевые паттерны

- Dataclass'ы с методами `to_dict()`/`from_dict()` для JSON сериализации
- Фабричные методы для создания Action (например, `Action.click(x, y)`)
- QThread для неблокирующего выполнения в GUI
- Определение платформы через `platform.system()` для путей Windows/Linux
