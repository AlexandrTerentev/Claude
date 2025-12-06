# MPDiagnosticAgent - Installation Guide

## Руководство по установке / Installation Guide

This guide covers installation on both Linux and Windows systems.

## Table of Contents / Содержание

- [Prerequisites](#prerequisites--требования)
- [Installation (Linux)](#installation-linux)
- [Installation (Windows)](#installation-windows)
- [Verification](#verification--проверка)
- [Troubleshooting](#troubleshooting--устранение-проблем)

---

## Prerequisites / Требования

### Linux

- **Python 3.8+**
- **Mission Planner** (running under Mono)
- **USB cable** for drone connection
- **Serial port permissions**

### Windows

- **Python 3.8+**
- **Mission Planner**
- **USB cable** for drone connection

---

## Installation (Linux)

### 1. Install Python Dependencies

```bash
cd /path/to/MPDiagnosticAgent
pip3 install -r requirements.txt
```

**Required packages:**
- `pymavlink>=2.4.0` - MAVLink protocol
- `pyyaml>=6.0` - Configuration files
- `requests>=2.28.0` - Wiki fetching

### 2. Configure Serial Port Permissions

Add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

**Important:** Log out and log back in for changes to take effect!

### 3. Verify Mission Planner Installation

The agent will auto-detect Mission Planner in these locations:
- `~/missionplanner`
- `/opt/missionplanner`

If installed elsewhere, specify path in `config/config.yaml`:

```yaml
mission_planner:
  auto_detect: false
  manual_path: /your/custom/path
```

### 4. Test Installation

```bash
cd MPDiagnosticAgent
python3 -m interfaces.cli config
```

You should see:
```
✓ Configuration loaded from: ...
✓ Auto-detected Mission Planner at: ...
✓ Loaded 9 motor diagnostic rules
```

---

## Installation (Windows)

### 1. Install Python

Download from [python.org](https://www.python.org/downloads/)

**Important:** Check "Add Python to PATH" during installation!

### 2. Install Dependencies

Open Command Prompt or PowerShell:

```cmd
cd C:\path\to\MPDiagnosticAgent
pip install -r requirements.txt
```

### 3. Verify Mission Planner Installation

The agent will auto-detect Mission Planner in these locations:
- `C:\Program Files\Mission Planner`
- `%APPDATA%\Mission Planner`

### 4. Test Installation

```cmd
cd MPDiagnosticAgent
python -m interfaces.cli config
```

---

## Verification / Проверка

### Test Core Functionality

**1. Check configuration:**
```bash
python3 -m interfaces.cli config
```

**2. Test diagnostic engine:**
```bash
python3 -m interfaces.cli status
```

**3. Test log analysis:**
```bash
python3 -m interfaces.cli prearm
```

### Test GUI (Optional)

```bash
python3 -m interfaces.gui_standalone
```

A window should appear with three tabs: Chat, Download Logs, Settings.

### Test Drone Connection (If drone available)

**1. Connect drone via USB**

**2. List logs on drone:**
```bash
python3 -m interfaces.cli download --list --port /dev/ttyACM0
```
(Windows: use `COM3`, `COM4`, etc.)

**3. Expected output:**
```
✓ Connected to drone
Found N logs:
  1. Log ID 0: XX.X KB
  ...
```

---

## Configuration / Конфигурация

### Config File Location

- **Linux:** `~/.config/mpdiagnostic/config.yaml` or `./config/config.yaml`
- **Windows:** `%APPDATA%\mpdiagnostic\config.yaml` or `.\config\config.yaml`

### Important Settings

```yaml
mission_planner:
  auto_detect: true          # Auto-find Mission Planner
  manual_path: null          # Override if auto-detect fails

mavlink:
  default_port: /dev/ttyACM0  # Linux
  # default_port: COM3        # Windows
  baudrate: 921600            # Standard ArduPilot
  timeout: 300                # 5 minutes

diagnostics:
  language: auto              # 'ru', 'en', or 'auto'
  log_lines_to_analyze: 300   # Recent lines to check
  wiki_integration: true      # Enable Wiki search
```

---

## Troubleshooting / Устранение проблем

### "Module not found" errors

**Solution:**
```bash
pip3 install -r requirements.txt
```

### "Permission denied" on /dev/ttyACM0 (Linux)

**Solution:**
```bash
sudo usermod -a -G dialout $USER
# Then log out and log back in
```

### "Mission Planner not found"

**Solution:**

1. Check Mission Planner is installed
2. Specify manual path in `config/config.yaml`:

```yaml
mission_planner:
  auto_detect: false
  manual_path: /path/to/missionplanner
```

### "No logs found on drone"

**Possible causes:**
1. Drone not armed/flown yet (no logs created)
2. Wrong port - check `dmesg | grep tty` (Linux) or Device Manager (Windows)
3. Baudrate mismatch - try 115200 if 921600 fails

**Solution:**
```bash
# Check available ports (Linux)
ls /dev/ttyACM* /dev/ttyUSB*

# Try different port
python3 -m interfaces.cli download --list --port /dev/ttyUSB0
```

### GUI doesn't start

**Solution (Linux):**
```bash
sudo apt-get install python3-tk
```

**Solution (Windows):**

Tkinter is usually included. If not, reinstall Python with Tk/Tcl option checked.

### Import errors in Python

**Solution:**

Make sure you run commands from the project root:
```bash
cd /path/to/MPDiagnosticAgent
python3 -m interfaces.cli status  # Correct
# NOT: cd interfaces && python3 cli.py
```

---

## Optional: Create Command Alias

### Linux/macOS

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias mpdiag='python3 /path/to/MPDiagnosticAgent/interfaces/cli.py'
```

Then reload:
```bash
source ~/.bashrc
```

Now you can use:
```bash
mpdiag status
mpdiag download --latest
```

### Windows

Create a batch file `mpdiag.bat`:

```batch
@echo off
python C:\path\to\MPDiagnosticAgent\interfaces\cli.py %*
```

Place in a directory in your PATH (e.g., `C:\Windows\System32`).

---

## Next Steps

- Read [User Guide](user_guide.md) to learn all features
- Check [Troubleshooting Guide](troubleshooting.md) for common issues
- See [README.md](../README.md) for project overview

---

## Support / Поддержка

- **GitHub Issues:** [Report bugs](https://github.com/YOUR_USERNAME/MPDiagnosticAgent/issues)
- **ArduPilot Forum:** [Ask questions](https://discuss.ardupilot.org/)
- **Documentation:** See `docs/` directory

---

**Installation complete! Ready to diagnose your drone.** ✅

Установка завершена! Готов к диагностике вашего дрона. ✅
