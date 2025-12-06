#!/bin/bash
# Запуск агента диагностики / Launch diagnostic agent

cd "$(dirname "$0")"

echo "=================================================="
echo "Запуск Агента Диагностики..."
echo "Launching Diagnostic Agent..."
echo "=================================================="
echo ""
echo "✅ Можно писать на РУССКОМ!"
echo "✅ Russian input works!"
echo ""
echo "Окно откроется через 2 секунды..."
echo "Window will open in 2 seconds..."
echo ""

sleep 2

python3 diagnostic_agent.py &

echo ""
echo "✅ Агент запущен!"
echo "✅ Agent started!"
echo ""
echo "Если окно не появилось, проверьте ошибки выше."
echo "If window didn't appear, check errors above."
echo ""
