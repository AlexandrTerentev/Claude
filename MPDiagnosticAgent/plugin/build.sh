#!/bin/bash
#
# Build script для Mission Planner Diagnostic Agent Plugin
# Компилирует C# плагин в DLL
#

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Mission Planner Diagnostic Agent${NC}"
echo -e "${GREEN}Build Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Путь к Mission Planner
MP_PATH="/home/user_1/missionplanner"

# Проверка существования Mission Planner
if [ ! -f "$MP_PATH/MissionPlanner.exe" ]; then
    echo -e "${RED}Error: Mission Planner not found at $MP_PATH${NC}"
    echo "Please update MP_PATH variable in this script"
    exit 1
fi

# Проверка компилятора
if ! command -v mcs &> /dev/null; then
    echo -e "${RED}Error: Mono C# compiler (mcs) not found${NC}"
    echo "Install with: sudo apt-get install mono-devel"
    exit 1
fi

echo -e "${YELLOW}Compiling DiagnosticAgent.dll...${NC}"

# Компиляция
mcs -t:library \
    -r:"$MP_PATH/MissionPlanner.exe" \
    -r:"$MP_PATH/IronPython.dll" \
    -r:"$MP_PATH/Microsoft.Scripting.dll" \
    -r:"$MP_PATH/Interfaces.dll" \
    -r:"$MP_PATH/MissionPlanner.ArduPilot.dll" \
    -r:"$MP_PATH/MissionPlanner.Utilities.dll" \
    -r:"$MP_PATH/MissionPlanner.Controls.dll" \
    -r:"$MP_PATH/MAVLink.dll" \
    -r:System.Windows.Forms.dll \
    -r:System.Drawing.dll \
    -r:System.Core.dll \
    -r:System.dll \
    DiagnosticAgent.cs \
    -out:DiagnosticAgent.dll

# Проверка результата
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Compilation successful!${NC}"
    echo ""

    # Копирование в Mission Planner plugins
    echo -e "${YELLOW}Copying to Mission Planner plugins folder...${NC}"
    cp DiagnosticAgent.dll "$MP_PATH/plugins/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Plugin installed successfully!${NC}"
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Installation Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Restart Mission Planner"
        echo "2. The Diagnostic Agent panel should appear on the right side of Flight Data tab"
        echo "3. Try typing a message to test the connection"
        echo ""
    else
        echo -e "${RED}Error: Failed to copy plugin to Mission Planner${NC}"
        echo "You can manually copy DiagnosticAgent.dll to $MP_PATH/plugins/"
        exit 1
    fi
else
    echo -e "${RED}✗ Compilation failed${NC}"
    echo "Please check the error messages above"
    exit 1
fi
