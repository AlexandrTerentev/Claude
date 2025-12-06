# MPDiagnosticAgent - User Guide

## Руководство пользователя / User Guide

Complete guide to using MPDiagnosticAgent for ArduPilot drone diagnostics.

## Table of Contents

- [Overview](#overview)
- [Interfaces](#interfaces)
- [Core Features](#core-features)
- [Diagnostic Commands](#diagnostic-commands)
- [Log Download](#log-download)
- [Wiki Integration](#wiki-integration)
- [Language Support](#language-support)
- [Advanced Usage](#advanced-usage)

---

## Overview

MPDiagnosticAgent is a unified diagnostic tool for ArduPilot drones that:

✅ Analyzes Mission Planner logs for errors
✅ Downloads dataflash logs from drone via MAVLink
✅ Diagnoses motor/arming issues with smart recommendations
✅ Searches ArduPilot Wiki for solutions
✅ Supports Russian and English languages
✅ Provides 3 interfaces: GUI, CLI, and Plugin

---

## Interfaces

### 1. GUI (Graphical User Interface)

**Launch:**
```bash
python3 -m interfaces.gui_standalone
```

**Features:**
- **Chat Tab:** Ask questions in natural language
- **Download Tab:** Download logs from drone with progress bar
- **Settings Tab:** View and manage configuration

**Example queries:**
- "Почему не крутятся моторы?" (Russian)
- "Why won't my motors spin?" (English)
- "status"
- "wiki prearm"

### 2. CLI (Command Line Interface)

**Launch:**
```bash
python3 -m interfaces.cli COMMAND [OPTIONS]
```

**Available commands:**

| Command | Description |
|---------|-------------|
| `status` | Full drone health check |
| `motors` | Diagnose motor/arming issues |
| `vibrations` | Analyze vibrations |
| `compass` | Diagnose compass |
| `prearm` | Check PreArm errors |
| `errors` | Find errors in logs |
| `logs` | Show recent log entries |
| `calibration` | Calibration instructions |
| `wiki TOPIC` | Search ArduPilot Wiki |
| `query TEXT` | Custom natural language query |
| `download` | Download logs from drone |
| `analyze FILE` | Analyze log file |
| `config` | Show configuration |

**Examples:**
```bash
# Full status check
python3 -m interfaces.cli status

# Download latest log
python3 -m interfaces.cli download --latest --port /dev/ttyACM0

# Search Wiki
python3 -m interfaces.cli wiki prearm

# Custom query
python3 -m interfaces.cli query "compass not working"
```

### 3. Mission Planner Plugin (C#)

**Installation:**
1. Copy `DiagnosticAgent_Unified.cs` to Mission Planner plugins folder
2. Restart Mission Planner
3. Find agent panel in DATA tab

**Note:** C# plugin currently in development. Use GUI or CLI for full functionality.

---

## Core Features

### Smart Diagnostics

The agent uses a knowledge base of common issues and solutions.

**Example 1: Motor Issues**

**User query:** "моторы не крутятся"
**Agent response:**
```
ДИАГНОСТИКА МОТОРОВ И АРМИНГА
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Найдено 1 PreArm ошибок:
  ✗ RC not found

РЕКОМЕНДАЦИИ:
• Подключите RC пульт
• Откалибруйте радио: Initial Setup > Radio Calibration
• Проверьте, что пульт включён
```

**Example 2: Compass Issues**

**User query:** "compass calibration failed"
**Agent response:**
```
COMPASS DIAGNOSTICS
━━━━━━━━━━━━━━━━━━━

RECOMMENDATIONS:
1. CALIBRATION:
   - Perform outdoors away from metal
   - Rotate slowly on all axes
   - Avoid interference sources

2. CHECK PARAMETERS:
   COMPASS_LEARN = 3
   COMPASS_USE = 1
```

### Log Analysis

**Automatic analysis of:**
- Mission Planner logs (`.log`)
- Telemetry logs (`.tlog`)
- Dataflash logs (`.bin`) - basic info

**Detected errors:**
- PreArm failures
- Critical errors
- Connection issues
- Parameter problems

---

## Diagnostic Commands

### Status Check

**CLI:**
```bash
python3 -m interfaces.cli status
```

**GUI:** Type "status" or "статус"

**Output:**
- PreArm error summary
- Recent errors in logs
- Recommendations

### Motor Diagnosis

**CLI:**
```bash
python3 -m interfaces.cli motors
```

**GUI:** Type "motors" or "моторы"

**Diagnoses:**
- RC calibration issues
- ESC problems
- Power issues
- Arming checks

### Vibration Analysis

**CLI:**
```bash
python3 -m interfaces.cli vibrations
```

**GUI:** Type "vibrations" or "вибрации"

**Checks:**
- Propeller balance
- Motor mount tightness
- Anti-vibration dampeners
- INS_ACCEL_FILTER parameter

### Compass Diagnosis

**CLI:**
```bash
python3 -m interfaces.cli compass
```

**GUI:** Type "compass" or "компас"

**Checks:**
- Calibration status
- Interference sources
- COMPASS parameters
- GPS/compass placement

### PreArm Errors

**CLI:**
```bash
python3 -m interfaces.cli prearm
```

**GUI:** Type "prearm"

**Shows:**
- All PreArm errors with timestamps
- Unique error messages
- Frequency of each error

### Recent Logs

**CLI:**
```bash
python3 -m interfaces.cli logs
```

**GUI:** Type "show logs" or "показать логи"

**Displays:**
- Last 15 log entries
- Timestamps
- Log levels (INFO, WARNING, ERROR)

---

## Log Download

Download dataflash logs (`.bin`) directly from drone via MAVLink.

### GUI Method

1. Switch to **"Download Logs"** tab
2. Set port (e.g., `/dev/ttyACM0`)
3. Click **"Connect"**
4. Click **"List Logs"** to see available logs
5. Select log from list
6. Click **"Download Selected"**
7. Progress bar shows download status

### CLI Method

**List logs:**
```bash
python3 -m interfaces.cli download --list --port /dev/ttyACM0
```

**Download latest:**
```bash
python3 -m interfaces.cli download --latest --port /dev/ttyACM0
```

**Download specific log:**
```bash
python3 -m interfaces.cli download --log-id 0 --port /dev/ttyACM0
```

**Output:**
```
Connecting to drone on /dev/ttyACM0...
✓ Connected to drone

Downloading latest log...
  [████████████████████░░░] 87.3% (45678/52341 bytes)

✓ Download successful!
  File: /home/user/missionplanner/logs/QUADCOPTER/log_0_20251206_203941.bin
  Size: 52341 bytes
```

### Downloaded Log Location

Logs are saved to directory specified in config:

**Default locations:**
- **Linux:** `~/missionplanner/logs/QUADCOPTER/`
- **Windows:** `C:\Users\USERNAME\missionplanner\logs\QUADCOPTER\`

**Custom location:**
```yaml
# config/config.yaml
log_locations:
  bin_directory: /path/to/custom/directory
```

---

## Wiki Integration

Search ArduPilot Wiki directly from the agent.

### Available Topics

- `prearm` - PreArm safety checks
- `calibration` - Calibration procedures
- `compass` - Compass setup
- `vibration` - Vibration damping
- `parameters` - Parameter reference
- `motors` - Motor/ESC connection

### Usage

**CLI:**
```bash
python3 -m interfaces.cli wiki prearm
```

**GUI:** Type "wiki prearm"

**Output:**
```
📖 ARDUPILOT WIKI INFORMATION:

PreArm Safety Check

PreArm checks ensure drone is safe to fly...
[Wiki content excerpt]

🔗 Full version: https://ardupilot.org/copter/docs/prearm-safety-check.html
```

### Wiki Cache

Wiki content is cached for 15 minutes to reduce network requests.

---

## Language Support

### Automatic Detection

Language is auto-detected from `config.yaml`:

```yaml
diagnostics:
  language: auto  # 'ru', 'en', or 'auto'
```

### Manual Override

**CLI:**
```bash
python3 -m interfaces.cli --language ru status
python3 -m interfaces.cli --language en status
```

**GUI:** Language set on startup from config

### Supported Languages

- **Russian (ru):** Full support
- **English (en):** Full support

**Bilingual responses:**
Most commands show both Russian and English headings for clarity.

---

## Advanced Usage

### Custom Configuration

**1. Create custom config:**
```yaml
# ~/.config/mpdiagnostic/config.yaml
mission_planner:
  manual_path: /custom/path

mavlink:
  default_port: /dev/ttyUSB0
  baudrate: 115200

diagnostics:
  log_lines_to_analyze: 500
  wiki_integration: false
```

**2. Use custom config:**
```bash
export MPDIAG_CONFIG=/path/to/custom/config.yaml
python3 -m interfaces.cli status
```

### Batch Operations

**Download all logs:**
```bash
# List logs and save IDs
python3 -m interfaces.cli download --list > logs.txt

# Download each one
for id in 0 1 2 3; do
  python3 -m interfaces.cli download --log-id $id
done
```

### Integration with MAVProxy

Use downloaded logs with MAVProxy:
```bash
mavlogdump.py --format json log_0_*.bin > analysis.json
```

### Scripting

Use CLI in scripts:

```bash
#!/bin/bash
# Automatic drone health check

echo "Checking drone health..."
python3 -m interfaces.cli status > health_report.txt

if grep -q "✗" health_report.txt; then
  echo "⚠ Issues found!"
  cat health_report.txt
  exit 1
else
  echo "✓ All systems OK"
  exit 0
fi
```

### Python API

Use diagnostic engine in your code:

```python
from core.diagnostic_engine import DiagnosticEngine

# Create engine
engine = DiagnosticEngine(language='en')

# Process queries
response = engine.process_query('status')
print(response)

# Download logs
from core.log_downloader import LogDownloader
downloader = LogDownloader()
downloader.connect()
logs = downloader.list_logs()
downloader.download_latest()
```

---

## Tips & Best Practices

### 1. Regular Health Checks

Run status check before each flight:
```bash
python3 -m interfaces.cli status
```

### 2. Download Logs After Flights

Always download logs after test flights:
```bash
python3 -m interfaces.cli download --latest
```

### 3. Check PreArm Errors

If can't arm, check PreArm first:
```bash
python3 -m interfaces.cli prearm
```

### 4. Use Wiki for Learning

Learn about ArduPilot features:
```bash
python3 -m interfaces.cli wiki parameters
```

### 5. Save Diagnostics

Save diagnostic output for later:
```bash
python3 -m interfaces.cli status > drone_health_$(date +%Y%m%d).txt
```

### 6. Natural Language Queries

Don't memorize commands - just ask:
- "why won't motors spin?"
- "compass calibration failed"
- "drone vibrating during flight"

---

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.

**Quick fixes:**

| Issue | Solution |
|-------|----------|
| "Permission denied" | `sudo usermod -a -G dialout $USER` |
| "No logs found" | Check drone has flown/logged data |
| "Connection failed" | Verify port with `ls /dev/tty*` |
| GUI won't start | `sudo apt-get install python3-tk` |

---

## Examples Gallery

### Example 1: Full Workflow

```bash
# 1. Connect drone
# 2. Check status
python3 -m interfaces.cli status

# 3. Found PreArm errors - diagnose motors
python3 -m interfaces.cli motors

# 4. Need calibration - show guide
python3 -m interfaces.cli calibration

# 5. After flight - download logs
python3 -m interfaces.cli download --latest

# 6. Analyze vibrations
python3 -m interfaces.cli vibrations
```

### Example 2: Troubleshooting Session

**Problem:** Drone won't arm

**Steps:**
1. `python3 -m interfaces.cli prearm` → Shows "RC not found"
2. `python3 -m interfaces.cli motors` → Recommends RC calibration
3. `python3 -m interfaces.cli wiki calibration` → Shows calibration guide
4. Calibrate RC in Mission Planner
5. `python3 -m interfaces.cli prearm` → No errors, ready to fly!

---

## Next Steps

- Check [Troubleshooting Guide](troubleshooting.md)
- Read [Installation Guide](installation.md)
- See [Project README](../README.md)
- Contribute on [GitHub](https://github.com/YOUR_USERNAME/MPDiagnosticAgent)

---

## Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/MPDiagnosticAgent/issues)
- **Forum:** [ArduPilot Discuss](https://discuss.ardupilot.org/)
- **Wiki:** [ArduPilot Wiki](https://ardupilot.org/copter/)

---

**Happy flying! Fly safe! ✈️**

**Удачных полётов! Летайте безопасно! ✈️**
