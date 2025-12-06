# MPDiagnosticAgent - Troubleshooting Guide

## Руководство по устранению проблем / Troubleshooting Guide

Common issues and solutions for MPDiagnosticAgent.

---

## Installation Issues

### Python Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'pymavlink'
```

**Solution:**
```bash
pip3 install -r requirements.txt
```

**Verify:**
```bash
pip3 list | grep -E 'pymavlink|pyyaml|requests'
```

---

### Permission Denied on Serial Port (Linux)

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/dev/ttyACM0'
```

**Solution:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in
# Verify:
groups | grep dialout
```

**Alternative (temporary):**
```bash
sudo chmod 666 /dev/ttyACM0
```

---

### GUI Won't Start (Linux)

**Error:**
```
ModuleNotFoundError: No module named 'tkinter'
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

---

## Connection Issues

### Can't Connect to Drone

**Error:**
```
✗ Failed to connect to drone
```

**Troubleshooting steps:**

**1. Check drone is connected:**
```bash
# Linux
ls /dev/ttyACM* /dev/ttyUSB*
dmesg | grep -i usb | tail -20

# Windows
# Check Device Manager > Ports (COM & LPT)
```

**2. Try different ports:**
```bash
python3 -m interfaces.cli download --list --port /dev/ttyUSB0
python3 -m interfaces.cli download --list --port /dev/ttyACM1
```

**3. Check baudrate:**
```yaml
# config/config.yaml
mavlink:
  baudrate: 115200  # Try lower baudrate
```

**4. Verify heartbeat:**
```bash
# Use MAVProxy to test
mavproxy.py --master=/dev/ttyACM0 --baudrate=921600
```

---

### No Heartbeat Received

**Error:**
```
✗ No heartbeat received within 30 seconds
```

**Causes:**
1. Drone not powered on
2. Wrong baudrate
3. Wrong port
4. USB cable issue

**Solutions:**

```bash
# Check power
# - Connect battery or USB power to drone
# - Check LED status on flight controller

# Try lower baudrate
python3 -m interfaces.cli download --list --port /dev/ttyACM0
# Edit config.yaml: baudrate: 115200

# Test cable
# - Try different USB cable
# - Try different USB port on computer
```

---

## Log Download Issues

### No Logs Found on Drone

**Message:**
```
⚠ No logs found on drone
```

**Causes:**
1. Drone hasn't flown yet (no logs created)
2. Logs were erased
3. SD card not present (some flight controllers)

**Solutions:**

- Fly/arm drone to create logs
- Check SD card is inserted (for controllers with SD)
- Verify logging is enabled:
  - Mission Planner > Config > Full Parameter List
  - `LOG_BACKEND_TYPE` should be > 0

---

### Download Times Out

**Error:**
```
✗ Timeout waiting for data at offset XXXX
```

**Causes:**
1. Poor USB connection
2. Large log file
3. Timeout too short

**Solutions:**

```yaml
# config/config.yaml
mavlink:
  timeout: 600  # Increase to 10 minutes
```

```bash
# Try smaller log first
python3 -m interfaces.cli download --log-id 0
```

---

## Diagnostic Issues

### Mission Planner Not Found

**Error:**
```
⚠ Mission Planner not found
```

**Solution:**

```yaml
# config/config.yaml
mission_planner:
  auto_detect: false
  manual_path: /home/user/missionplanner  # Linux
  # manual_path: C:\Program Files\Mission Planner  # Windows
```

**Verify path exists:**
```bash
ls -la /home/user/missionplanner
# Should contain: Mission Planner/MissionPlanner.log
```

---

### Log File Not Found

**Error:**
```
❌ Папка с логами не найдена
```

**Causes:**
1. Mission Planner not run yet (no logs created)
2. Wrong path
3. Permissions issue

**Solutions:**

**1. Check Mission Planner was run:**
```bash
# Log file should exist
ls ~/missionplanner/Mission\ Planner/MissionPlanner.log
```

**2. Run Mission Planner to create log:**
- Start Mission Planner
- Close it
- Run diagnostic agent again

**3. Set manual path:**
```yaml
log_locations:
  mission_planner_log: /full/path/to/MissionPlanner.log
```

---

### No Diagnostic Results

**Issue:** Agent returns no errors but drone still has problems

**Causes:**
1. Logs don't contain recent data
2. Log lines limit too small
3. Different error pattern

**Solutions:**

```yaml
# config/config.yaml
diagnostics:
  log_lines_to_analyze: 500  # Increase from 300
```

```bash
# View raw logs
python3 -m interfaces.cli logs

# Use specific diagnostics
python3 -m interfaces.cli motors
python3 -m interfaces.cli prearm
```

---

## GUI Issues

### Window Doesn't Appear

**Causes:**
1. Tkinter not installed
2. Display issue (headless system)
3. Python error on startup

**Solutions:**

```bash
# Check Tkinter
python3 -c "import tkinter; print('Tkinter OK')"

# Run from terminal to see errors
python3 -m interfaces.gui_standalone

# Check DISPLAY (Linux)
echo $DISPLAY
# Should show :0 or similar
```

---

### GUI Freezes on Download

**Cause:** Long download blocks UI thread

**Workaround:**
- Use CLI for large downloads
- Progress bar still updates

```bash
python3 -m interfaces.cli download --latest
```

---

## Configuration Issues

### Config Not Loaded

**Error:**
```
⚠ Configuration file not found
```

**Solution:**

```bash
# Create default config
cp config/config.yaml ~/.config/mpdiagnostic/config.yaml

# Or use project config
cd /path/to/MPDiagnosticAgent
python3 -m interfaces.cli config
```

---

### Invalid YAML Syntax

**Error:**
```
yaml.scanner.ScannerError: ...
```

**Solution:**

- Check YAML syntax (indentation, colons, no tabs)
- Use YAML validator: http://www.yamllint.com/
- Restore from backup:

```bash
cp config/config.yaml.backup config/config.yaml
```

---

## Performance Issues

### Slow Startup

**Cause:** Loading large log files

**Solution:**

```yaml
# config/config.yaml
diagnostics:
  log_lines_to_analyze: 100  # Reduce from 300
```

---

### High Memory Usage

**Cause:** Large logs in memory

**Solution:**
- Close other applications
- Use CLI instead of GUI
- Analyze logs in smaller chunks

---

## Platform-Specific Issues

### Windows: COM Port Not Found

**Error:**
```
✗ Failed to connect to COM3
```

**Solution:**

**1. Check Device Manager:**
- Open Device Manager
- Expand "Ports (COM & LPT)"
- Note correct COM number

**2. Update config:**
```yaml
mavlink:
  default_port: COM4  # Use correct number
```

**3. Install drivers:**
- Some flight controllers need FTDI or CH340 drivers
- Download from manufacturer website

---

### Linux: Port Changes on Reconnect

**Issue:** `/dev/ttyACM0` becomes `/dev/ttyACM1` after reconnect

**Solution:**

**Create udev rule:**
```bash
# Create file: /etc/udev/rules.d/99-ardupilot.rules
sudo nano /etc/udev/rules.d/99-ardupilot.rules

# Add rule (replace XXXX with your vendor:product)
SUBSYSTEM=="tty", ATTRS{idVendor}=="XXXX", ATTRS{idProduct}=="YYYY", SYMLINK+="drone0"

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Now use /dev/drone0 as port
```

**Find vendor:product:**
```bash
lsusb
# Look for drone, note ID XXXX:YYYY
```

---

### macOS: Permission Issues

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/dev/cu.usbserial-XXX'
```

**Solution:**

```bash
# Add user to dialout group (if exists)
sudo dseditgroup -o edit -a $USER -t user dialout

# Or use sudo (not recommended for regular use)
sudo python3 -m interfaces.cli download --list
```

---

## Error Messages Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `Module not found` | Missing dependency | `pip3 install -r requirements.txt` |
| `Permission denied /dev/tty*` | No serial permissions | `sudo usermod -a -G dialout $USER` |
| `No heartbeat` | Drone not connected | Check power, cable, port |
| `Timeout` | Slow connection | Increase timeout in config |
| `No logs found` | Drone not flown | Arm/fly drone first |
| `Mission Planner not found` | Wrong path | Set `manual_path` in config |
| `Config file not found` | Missing config | Copy default config |
| `GUI won't start` | Missing Tkinter | `apt-get install python3-tk` |

---

## Getting More Help

### 1. Check Logs

**Mission Planner log:**
```bash
tail -100 ~/missionplanner/Mission\ Planner/MissionPlanner.log
```

**Agent errors:**
```bash
python3 -m interfaces.cli status 2>&1 | tee diagnostic.log
```

### 2. Enable Debug Mode

```bash
# Add to start of script
export PYTHONVERBOSE=1
python3 -m interfaces.cli status
```

### 3. Test Components

```python
# Test MAVLink connection
python3 -c "
from core.mavlink_interface import MAVLinkInterface
mav = MAVLinkInterface()
print('Connecting...')
if mav.connect():
    print('✓ Connected')
    print('Status:', mav.get_system_status())
else:
    print('✗ Failed')
"
```

### 4. Community Support

- **GitHub Issues:** [Report bugs](https://github.com/YOUR_USERNAME/MPDiagnosticAgent/issues)
- **ArduPilot Forum:** [Ask questions](https://discuss.ardupilot.org/)
- **Discord:** ArduPilot community Discord

### 5. Provide Debug Info

When reporting issues, include:

```bash
# System info
python3 --version
pip3 list | grep -E 'pymavlink|pyyaml'
uname -a  # Linux
# Or: systeminfo  # Windows

# Agent info
python3 -m interfaces.cli config

# Error output
python3 -m interfaces.cli status 2>&1 | tee error.log
```

---

## Still Having Issues?

If none of these solutions work:

1. **Check prerequisites:** Python 3.8+, all dependencies installed
2. **Verify paths:** Mission Planner installed, logs exist
3. **Test connection:** Drone powered, correct port/baudrate
4. **Read documentation:** [Installation](installation.md), [User Guide](user_guide.md)
5. **Ask for help:** GitHub issues with full error log

---

**Most issues are solved by:**
1. ✅ Installing dependencies: `pip3 install -r requirements.txt`
2. ✅ Setting serial permissions: `sudo usermod -a -G dialout $USER`
3. ✅ Using correct port: `/dev/ttyACM0` or `COM3`

Good luck! Удачи! 🍀
