# Mission Planner Diagnostic Agent

AI-powered diagnostic assistant integrated directly into Mission Planner to help with drone configuration, troubleshooting, and diagnostics.

## What It Does

The Diagnostic Agent appears as a chat panel in Mission Planner where you can:
- Ask questions about your drone issues ("Why won't my motors spin?")
- Get step-by-step calibration instructions
- Analyze Mission Planner logs for errors
- Diagnose PreArm check failures
- Receive specific troubleshooting guidance

## Current Status

**Version 3.0 (Python-Enhanced)**
- ✅ Chat interface integrated into Mission Planner
- ✅ Log file analysis
- ✅ PreArm error detection
- ✅ Motor/arming diagnostics
- ✅ Calibration guides
- ✅ Knowledge base for common issues
- 🔄 IronPython integration (needs testing)
- ⏳ Claude API integration (planned for future)

## Installation

### Files Created

```
/home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent/
├── plugin/
│   ├── DiagnosticAgent.cs           # Original C# plugin with IronPython
│   └── build.sh                     # Compilation script (if using DLL)
│
├── engine/                           # Python logic
│   ├── agent_core.py                # Main agent processing
│   └── log_analyzer.py              # Log parsing and analysis
│
└── knowledge/                        # Diagnostic rules
    └── motor_issues.json            # Motor troubleshooting database

Also in Mission Planner plugins folder:
/home/user_1/missionplanner/plugins/
├── DiagnosticAgent_v2.cs            # Pure C# version (working)
└── DiagnosticAgent_Python.cs        # Python-enhanced version (to test)
```

### Current Working Version

**DiagnosticAgent_v2.cs** - Pure C# implementation (confirmed working)
- Location: `/home/user_1/missionplanner/plugins/DiagnosticAgent_v2.cs`
- Status: ✅ TESTED and WORKING
- Features: Basic commands (help, status, test, logs)

### Python-Enhanced Version (Ready to Test)

**DiagnosticAgent_Python.cs** - With IronPython integration
- Location: `/home/user_1/missionplanner/plugins/DiagnosticAgent_Python.cs`
- Status: 🔄 READY FOR TESTING
- Features: Full log analysis, PreArm diagnostics, motor troubleshooting

## How to Use

### Testing the Python Version

1. **Remove the old version** (if you want only one agent):
   ```bash
   rm /home/user_1/missionplanner/plugins/DiagnosticAgent_v2.cs
   ```

2. **Restart Mission Planner**
   - Close Mission Planner completely
   - Reopen Mission Planner
   - Wait ~1 minute for plugin to compile
   - Look for "Diagnostic Agent (Python)" panel on right side of DATA tab

3. **Check Python Status**
   - The agent will show either:
     - "Python AI Agent Ready!" (Python loaded successfully)
     - "Basic Agent Ready (Python unavailable)" (fell back to C# mode)

### Using the Agent

**Available Commands:**

```
help              - Show available commands
status            - Show drone connection status
test              - Test agent functionality

show logs         - Display recent log entries
check errors      - Find ERROR/CRITICAL messages in logs
prearm            - Check for PreArm errors

motors not spinning      - Diagnose motor issues
why won't motors spin    - Motor troubleshooting
how to calibrate compass - Calibration guidance
how to calibrate radio   - RC calibration help
```

**Natural Language Questions:**

You can also ask questions naturally:
- "Why won't my motors spin?"
- "How do I calibrate the compass?"
- "What errors are in the logs?"
- "Motors not working"
- "Check for problems"

### Example Interaction

```
You: motors not spinning
Agent:
MOTOR/ARMING DIAGNOSIS:

Found 2 PreArm error(s):

X RC not calibrated
X Compass not calibrated

==================================================
RECOMMENDED ACTIONS:
==================================================

! RC CONTROLLER NOT CALIBRATED

SOLUTION:
1. Go to: Initial Setup > Mandatory Hardware > Radio Calibration
2. Turn on your RC transmitter
3. Move all sticks to their extreme positions
4. Click 'Calibrate Radio' button
5. Verify all channels show GREEN bars
6. Click 'Click when Done'
...
```

## Features in Detail

### Log Analysis
- Reads Mission Planner log file at `/home/user_1/missionplanner/Mission Planner/MissionPlanner.log`
- Parses log format: `YYYY-MM-DD HH:mm:ss,ms LEVEL Logger - Message`
- Finds ERROR and CRITICAL level messages
- Extracts recent log entries

### PreArm Error Detection
- Identifies PreArm check failures
- Matches errors to diagnostic rules
- Provides specific solutions for common issues:
  - RC not calibrated
  - Compass calibration
  - Accelerometer calibration
  - Battery issues
  - GPS problems
  - Safety switch
  - ESC calibration

### Motor Diagnostics
- Analyzes PreArm errors related to motors
- Provides step-by-step troubleshooting
- Links to specific calibration procedures
- Suggests parameter checks

### Knowledge Base
- JSON-based diagnostic rules in `knowledge/motor_issues.json`
- Covers common issues:
  - RC calibration
  - Compass calibration
  - Accelerometer calibration
  - ESC calibration
  - Battery failsafe
  - GPS issues
  - Flight mode problems
  - Safety switch

## Troubleshooting the Plugin

### Plugin Not Appearing

1. **Check logs** for compilation errors:
   ```bash
   tail -50 /home/user_1/missionplanner/Mission\ Planner/MissionPlanner.log | grep -i "plugin\|diagnostic\|error"
   ```

2. **Look for these messages:**
   - `Plugin Load DiagnosticAgent_Python.cs` ✅
   - `CodeGenRoslyn: DiagnosticAgent_Python.cs` ✅
   - `Plugin Init Diagnostic Agent (Python) by Claude` ✅ (means it's working!)

3. **Wait 1-2 minutes** after Mission Planner starts
   - Plugin compilation takes time
   - Panel appears after compilation completes

### Python Not Loading

If you see "Basic Agent Ready (Python unavailable)":

1. **Check Python files exist:**
   ```bash
   ls -la /home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent/engine/
   ```
   Should show: `agent_core.py` and `log_analyzer.py`

2. **Check file permissions:**
   ```bash
   chmod +r /home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent/engine/*.py
   ```

3. **Check IronPython in Mission Planner:**
   - Go to Scripts tab in Mission Planner
   - Try running a simple Python script
   - If this works, IronPython is available

### Log File Not Found

If "logs" command says "Log file not found":

1. **Check log file exists:**
   ```bash
   ls -la /home/user_1/missionplanner/Mission\ Planner/MissionPlanner.log
   ```

2. **Log file should be at:**
   `/home/user_1/missionplanner/Mission Planner/MissionPlanner.log`

3. **If using different Mission Planner location**, update path in:
   - `DiagnosticAgent_Python.cs` line 34
   - `engine/log_analyzer.py` line 17

## Architecture

### Two-Layer Design

**C# Layer (DiagnosticAgent_Python.cs)**
- Handles UI (chat panel, text boxes, buttons)
- Integrates with Mission Planner API
- Loads and calls Python engine via IronPython
- Falls back to basic C# mode if Python unavailable

**Python Layer (engine/)**
- `agent_core.py` - Query processing and response generation
- `log_analyzer.py` - Log file parsing and analysis
- Natural language understanding
- Diagnostic logic

**Knowledge Base (knowledge/)**
- `motor_issues.json` - Diagnostic rules and solutions
- Easily extensible for new issues

### Why This Design?

- **Minimal C# code** - easier for beginners
- **Python for logic** - easier to modify and extend
- **Graceful degradation** - works even if Python fails
- **Easy to add Claude API** - just modify Python layer

## Next Steps (Roadmap)

### Phase 1 (Current - MVP Complete) ✅
- [x] Basic chat UI
- [x] Log analysis
- [x] PreArm error detection
- [x] Motor diagnostics
- [x] Calibration guides

### Phase 2 (Next)
- [ ] Test Python integration fully
- [ ] Add more diagnostic rules
- [ ] Parameter reading from Mission Planner
- [ ] Real-time telemetry analysis
- [ ] Proactive warnings

### Phase 3 (Future)
- [ ] Claude API integration for complex questions
- [ ] Dataflash log (.bin) analysis
- [ ] PID tuning recommendations
- [ ] Flight log visualization
- [ ] Export diagnostic reports

## Development Notes

### Modifying the Agent

**To add new diagnostic rules:**
1. Edit `knowledge/motor_issues.json`
2. Add new rule with keywords, diagnosis, and solution steps
3. No need to recompile - just restart Mission Planner

**To modify Python logic:**
1. Edit `engine/agent_core.py` or `engine/log_analyzer.py`
2. Save changes
3. Restart Mission Planner (IronPython will reload scripts)

**To modify C# UI:**
1. Edit `DiagnosticAgent_Python.cs`
2. Save file
3. Restart Mission Planner (auto-recompiles .cs files)

### Key Files to Understand

**DiagnosticAgent_Python.cs:**
- Lines 26-56: Init() - Python initialization
- Lines 135-163: SendMessage() - Handles Python/C# switching
- Lines 165-186: ProcessBasic() - Fallback C# logic

**engine/agent_core.py:**
- Lines 247-261: process_query() - Entry point from C#
- Lines 25-52: process() - Query routing
- Lines 74-160: diagnose_motors() - Main diagnostic logic

**engine/log_analyzer.py:**
- Lines 33-44: read_last_lines() - Read log file
- Lines 56-76: find_prearm_errors() - Parse PreArm messages
- Lines 78-96: find_errors() - Find ERROR/CRITICAL logs

## Credits

**Project:** Mission Planner Diagnostic Agent
**Version:** 3.0
**Author:** Claude (Anthropic)
**For:** Mission Planner (ArduPilot Ground Control Station)
**Platform:** C# + IronPython + JSON

## License

Created for educational and personal use with Mission Planner.

---

## Quick Start Checklist

- [ ] Python version file exists: `/home/user_1/missionplanner/plugins/DiagnosticAgent_Python.cs`
- [ ] Python engine files exist: `/home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent/engine/`
- [ ] Knowledge base exists: `/home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent/knowledge/motor_issues.json`
- [ ] Mission Planner closed
- [ ] Mission Planner restarted
- [ ] Waited 1-2 minutes for compilation
- [ ] Panel appears on right side of DATA tab
- [ ] Tested with "help" command
- [ ] Tested with "test" command
- [ ] Checked if Python loaded (green message)
- [ ] Tested motor diagnostics command

If all checkmarks are complete, the agent should be working!

**Need help? Check Mission Planner logs:**
```bash
tail -100 /home/user_1/missionplanner/Mission\ Planner/MissionPlanner.log
```
