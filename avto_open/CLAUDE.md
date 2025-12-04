# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AvtoOpen is a cross-platform (Windows/Linux) assembly launcher with automation support. Users create "assemblies" - collections of applications that launch together with automated actions (clicks, keystrokes, text input).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
# or
cd src && python main.py
```

## Architecture

### Core Layer (`src/core/`)
- **action.py** - `Action` class with factory methods (`delay()`, `click()`, `type_text()`, `hotkey()`). Uses `ActionType` enum.
- **assembly.py** - `Assembly` (collection of apps) and `AppConfig` (single app with its actions) dataclasses.
- **automation.py** - `AutomationEngine` wraps PyAutoGUI for executing actions.
- **executor.py** - `AssemblyExecutor` launches apps and runs their actions, supports parallel execution.

### Storage Layer (`src/storage/`)
- **config.py** - `ConfigManager` handles JSON serialization to `~/.config/avto_open/` (Linux) or `%APPDATA%/avto_open/` (Windows).

### UI Layer (`src/ui/`)
- **main_window.py** - Main window with assembly list, run button, execution log. Uses `ExecutorThread` for background execution.
- **assembly_editor.py** - Dialog for editing assembly name, description, and app list.
- **action_editor.py** - Dialog for adding/editing actions with mouse position capture helper.

### Data Flow
1. User creates Assembly → adds AppConfigs → adds Actions to each AppConfig
2. ConfigManager saves to JSON
3. AssemblyExecutor launches apps in parallel → AutomationEngine executes actions sequentially per app

## Key Patterns

- Dataclasses with `to_dict()`/`from_dict()` for JSON serialization
- Factory methods for Action creation (e.g., `Action.click(x, y)`)
- QThread for non-blocking execution in GUI
- Platform detection via `platform.system()` for Windows/Linux paths
