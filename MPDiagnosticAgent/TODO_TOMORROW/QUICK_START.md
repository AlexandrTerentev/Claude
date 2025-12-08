# Quick Start - Продолжение работы

## ⚡ Быстрый старт (5 минут)

### Шаг 1: Открой проект
```bash
cd /home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent
```

### Шаг 2: Проверь что установлено
```bash
# Claude CLI
which claude

# Если нет:
npm install -g @anthropics/claude-cli
claude auth login
```

### Шаг 3: Протестируй текущую версию
```bash
agent_ran
# Задай вопрос в AI Assistant: "анализ"
# Посмотри что отвечает
```

### Шаг 4: Посмотри код AI
```bash
# Основной файл с AI
nano core/unified_agent.py
# Найди метод ask_claude_api (строка ~406)
```

---

## 🎯 Твоя задача на сегодня

**СДЕЛАТЬ AI ASSISTANT УМНЫМ!**

Сейчас он отвечает шаблонами:
```
User: "почему дрон падает?"
AI: "Я могу помочь с: ..."  ← ЭТО ПЛОХО!
```

Нужно чтобы отвечал умно:
```
User: "почему дрон падает?"
AI: "Анализирую логи... Обнаружена проблема с PID настройками.
     Рекомендую снизить P gain на 20%..." ← ЭТО ХОРОШО!
```

---

## 📝 План действий

### 1. Проверь Claude API (5 мин)
```bash
# Тест Claude CLI
echo "Привет, ты работаешь?" | claude

# Должно вернуть умный ответ
```

### 2. Протестируй ask_claude_api() (10 мин)
```python
# В Python console:
from core.unified_agent import UnifiedAgent
from core.config import Config

agent = UnifiedAgent(config=Config())
answer = agent.ask_claude_api("Почему дрон не взлетает?")
print(answer)
```

### 3. Добавь GitHub docs (30 мин)
Создай файл `core/github_dataset.py`:
```python
#!/usr/bin/env python3
import subprocess
from pathlib import Path

class GitHubDataset:
    def __init__(self):
        self.cache_dir = Path.home() / ".mpdiag" / "docs"
        self.wiki_url = "https://github.com/ArduPilot/ardupilot_wiki.git"

    def download_docs(self):
        """Clone ArduPilot Wiki"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not (self.cache_dir / "ardupilot_wiki").exists():
            print("📥 Downloading ArduPilot Wiki...")
            subprocess.run([
                "git", "clone",
                self.wiki_url,
                str(self.cache_dir / "ardupilot_wiki")
            ])
        else:
            print("✓ Wiki already downloaded")

    def search(self, query: str) -> str:
        """Search in docs"""
        result = subprocess.run([
            "grep", "-r", "-i", query,
            str(self.cache_dir / "ardupilot_wiki")
        ], capture_output=True, text=True)

        return result.stdout[:2000]  # Limit output
```

### 4. Интегрируй в AI (15 мин)
Добавь в `unified_agent.py`:
```python
from .github_dataset import GitHubDataset

class UnifiedAgent:
    def __init__(self, config=None):
        # ...existing code...
        self.dataset = GitHubDataset()
        self.dataset.download_docs()  # Скачать при старте

    def ask_claude_api(self, query, context=""):
        # Добавь в контекст:
        docs_context = self.dataset.search(query)

        full_context = f"""
        ...existing context...

        ДОКУМЕНТАЦИЯ ARDUPILOT:
        {docs_context}

        ВОПРОС: {query}
        """
        # ...rest of code...
```

### 5. Тест full integration (10 мин)
```bash
agent_ran

# В AI Assistant:
"Что такое EKF3 variance и как её исправить?"

# Должен:
# 1. Найти в GitHub docs про EKF3
# 2. Проанализировать логи
# 3. Предложить конкретное решение
```

---

## 🔍 Debugging

Если что-то не работает:

### Claude CLI не найден
```bash
npm install -g @anthropics/claude-cli
claude auth login
```

### Ошибка timeout
Увеличь таймаут в unified_agent.py:
```python
result = subprocess.run(
    ["claude", full_context],
    timeout=120  # Было 90
)
```

### AI не вызывается
Добавь debug print в answer_question():
```python
def answer_question(self, question):
    print(f"DEBUG: Question = {question}")
    # ...
    print("DEBUG: Calling ask_claude_api...")
    ai_response = self.ask_claude_api(question)
    print(f"DEBUG: Response = {ai_response[:100]}")
```

---

## 📂 Важные файлы

**Читай в этом порядке:**

1. **TODO_TOMORROW/PLAN.md** - Подробный план
2. **core/unified_agent.py** - AI код (строка 406+)
3. **/home/user_1/missionplanner/diagnostic_agent_pro.py** - Рабочий пример
4. **main.py** - GUI интерфейс

---

## ✅ Критерий успеха

**Сегодня успешен если:**

- ✅ AI отвечает умно (не шаблонами!)
- ✅ Claude API работает
- ✅ GitHub docs загружаются и используются
- ✅ Пользователь получает реальную помощь

---

## 🚀 Начинай!

```bash
cd /home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent
agent_ran
# ТЕСТИРУЙ AI!
```

**Удачи! 💪**
