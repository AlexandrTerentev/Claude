#!/bin/bash
# Установка Агента Диагностики v4.0
# Installation script for Diagnostic Agent v4.0

echo "===================================================="
echo "Агент Диагностики Mission Planner v4.0"
echo "Mission Planner Diagnostic Agent v4.0"
echo "===================================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Пути
SOURCE_FILE="/home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent/plugin/DiagnosticAgent_MultiTab.cs"
DEST_DIR="/home/user_1/missionplanner/plugins"
DEST_FILE="$DEST_DIR/DiagnosticAgent_MultiTab.cs"

# Проверка существования исходного файла
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}✗ Ошибка: Файл не найден${NC}"
    echo -e "${RED}✗ Error: Source file not found${NC}"
    echo "  $SOURCE_FILE"
    exit 1
fi

# Проверка существования папки назначения
if [ ! -d "$DEST_DIR" ]; then
    echo -e "${RED}✗ Ошибка: Папка plugins не найдена${NC}"
    echo -e "${RED}✗ Error: Plugins folder not found${NC}"
    echo "  $DEST_DIR"
    echo ""
    echo "Создать папку? (Create folder?) [y/N]"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY]|[дД][аА]|[дД])$ ]]; then
        mkdir -p "$DEST_DIR"
        echo -e "${GREEN}✓ Папка создана / Folder created${NC}"
    else
        exit 1
    fi
fi

echo "Что делать со старыми версиями плагина?"
echo "What to do with old plugin versions?"
echo ""
echo "1) Оставить все версии (Keep all versions)"
echo "2) Сделать резервные копии старых версий (Backup old versions)"
echo "3) Удалить старые версии (Delete old versions)"
echo ""
echo -n "Выбор / Choice [1/2/3]: "
read -r choice

case $choice in
    2)
        echo ""
        echo "Создание резервных копий..."
        echo "Creating backups..."
        if [ -f "$DEST_DIR/DiagnosticAgent_v2.cs" ]; then
            mv "$DEST_DIR/DiagnosticAgent_v2.cs" "$DEST_DIR/DiagnosticAgent_v2.cs.bak"
            echo -e "${GREEN}✓${NC} DiagnosticAgent_v2.cs → .bak"
        fi
        if [ -f "$DEST_DIR/DiagnosticAgent_Python.cs" ]; then
            mv "$DEST_DIR/DiagnosticAgent_Python.cs" "$DEST_DIR/DiagnosticAgent_Python.cs.bak"
            echo -e "${GREEN}✓${NC} DiagnosticAgent_Python.cs → .bak"
        fi
        if [ -f "$DEST_DIR/DiagnosticAgent.cs" ]; then
            mv "$DEST_DIR/DiagnosticAgent.cs" "$DEST_DIR/DiagnosticAgent.cs.bak"
            echo -e "${GREEN}✓${NC} DiagnosticAgent.cs → .bak"
        fi
        ;;
    3)
        echo ""
        echo "Удаление старых версий..."
        echo "Deleting old versions..."
        rm -f "$DEST_DIR/DiagnosticAgent_v2.cs"
        rm -f "$DEST_DIR/DiagnosticAgent_Python.cs"
        rm -f "$DEST_DIR/DiagnosticAgent.cs"
        echo -e "${GREEN}✓${NC} Старые версии удалены / Old versions deleted"
        ;;
    *)
        echo ""
        echo "Оставляем все версии / Keeping all versions"
        ;;
esac

echo ""
echo "Копирование нового плагина..."
echo "Copying new plugin..."

# Копирование файла
cp "$SOURCE_FILE" "$DEST_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Файл успешно скопирован!${NC}"
    echo -e "${GREEN}✓ File copied successfully!${NC}"
    echo ""
    echo "  Откуда / From: $SOURCE_FILE"
    echo "  Куда / To:     $DEST_FILE"
else
    echo -e "${RED}✗ Ошибка копирования!${NC}"
    echo -e "${RED}✗ Copy error!${NC}"
    exit 1
fi

# Проверка размера файла
SIZE=$(stat -f%z "$DEST_FILE" 2>/dev/null || stat -c%s "$DEST_FILE" 2>/dev/null)
echo ""
echo "Размер файла / File size: $(echo "scale=1; $SIZE/1024" | bc) KB"

# Проверка кодировки
echo ""
echo "Проверка кодировки / Checking encoding..."
ENCODING=$(file -b --mime-encoding "$DEST_FILE")
if [[ "$ENCODING" == "utf-8" ]]; then
    echo -e "${GREEN}✓ UTF-8 кодировка (русский язык поддерживается)${NC}"
    echo -e "${GREEN}✓ UTF-8 encoding (Russian supported)${NC}"
else
    echo -e "${YELLOW}⚠ Внимание: кодировка $ENCODING${NC}"
    echo -e "${YELLOW}⚠ Warning: encoding is $ENCODING${NC}"
    echo "  Может потребоваться конвертация в UTF-8"
    echo "  UTF-8 conversion may be needed"
fi

echo ""
echo "===================================================="
echo -e "${GREEN}✓ УСТАНОВКА ЗАВЕРШЕНА / INSTALLATION COMPLETE${NC}"
echo "===================================================="
echo ""
echo "СЛЕДУЮЩИЕ ШАГИ / NEXT STEPS:"
echo ""
echo "1. Закрыть Mission Planner (если открыт)"
echo "   Close Mission Planner (if running)"
echo ""
echo "2. Запустить Mission Planner заново"
echo "   Start Mission Planner again"
echo ""
echo "3. Подождать 1-2 минуты (компиляция плагина)"
echo "   Wait 1-2 minutes (plugin compilation)"
echo ""
echo "4. Перейти на вкладку DATA"
echo "   Go to DATA tab"
echo ""
echo "5. Справа должна появиться панель 'Агент Диагностики'"
echo "   Panel 'Diagnostic Agent' should appear on the right"
echo ""
echo "6. Попробовать команду: 'помощь' или 'help'"
echo "   Try command: 'помощь' or 'help'"
echo ""
echo "===================================================="
echo ""
echo "Если возникли проблемы, проверьте лог:"
echo "If there are issues, check the log:"
echo ""
echo "tail -100 /home/user_1/missionplanner/Mission\\ Planner/MissionPlanner.log | grep -i diagnostic"
echo ""
echo "===================================================="
echo ""
echo "Документация / Documentation:"
echo "  $PWD/README_v4.md"
echo ""
