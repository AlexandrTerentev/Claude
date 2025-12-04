# -*- coding: utf-8 -*-
"""
Diagnostic Agent Core
Main logic for processing user queries and providing drone diagnostics
"""

import sys
import os

# Add engine directory to path for imports
engine_dir = os.path.dirname(os.path.abspath(__file__))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from log_analyzer import LogAnalyzer


class DiagnosticAgent:
    """Main diagnostic agent class"""

    def __init__(self, log_path='/home/user_1/missionplanner'):
        self.log_path = log_path
        self.log_analyzer = LogAnalyzer(log_path)

    def process(self, user_input):
        """Process user input and return response"""
        query = user_input.lower().strip()

        # Command detection
        if query in ['help', '?']:
            return self.show_help()

        elif 'motor' in query or 'spin' in query or 'arm' in query or 'propeller' in query:
            return self.diagnose_motors()

        elif 'calibrat' in query:
            return self.show_calibration_info()

        elif 'log' in query and ('show' in query or 'recent' in query or 'check' in query):
            return self.show_recent_logs()

        elif 'error' in query or 'problem' in query or 'issue' in query:
            return self.check_errors()

        elif 'prearm' in query:
            return self.check_prearm()

        elif 'status' in query or 'summary' in query:
            return self.get_status_summary()

        else:
            return self.general_response(query)

    def show_help(self):
        """Show available commands"""
        return """Available commands and questions:

BASIC COMMANDS:
  help         - Show this help
  status       - Show system status summary

DIAGNOSTICS:
  check errors     - Find recent errors in logs
  prearm           - Check PreArm errors
  show logs        - Display recent log entries

TROUBLESHOOTING:
  "Why won't my motors spin?"
  "Motors not working"
  "How to calibrate [compass/radio/etc]?"

Try asking natural questions about your drone!"""

    def diagnose_motors(self):
        """Diagnose motor/arming issues"""
        # Check for PreArm errors
        prearm_errors = self.log_analyzer.find_prearm_errors(num_lines=300)

        if not prearm_errors:
            return """No PreArm errors found in recent logs.

POSSIBLE CAUSES:
1. Drone might not be connected to Mission Planner
2. No arming attempts logged recently
3. All systems might be ready (try arming)

Try: 'show logs' to see recent activity"""

        # Analyze the PreArm errors
        response = ["MOTOR/ARMING DIAGNOSIS:", ""]
        response.append(f"Found {len(prearm_errors)} PreArm error(s):\n")

        # Show unique errors
        unique_errors = {}
        for err in prearm_errors:
            msg = err['message']
            if msg not in unique_errors:
                unique_errors[msg] = err

        for msg, err in list(unique_errors.items())[-5:]:  # Last 5 unique errors
            response.append(f"X {msg}")

        response.append("\n" + "="*50)
        response.append("RECOMMENDED ACTIONS:")
        response.append("="*50 + "\n")

        # Provide specific guidance based on error patterns
        all_errors_text = ' '.join([e['message'] for e in prearm_errors]).lower()

        if 'rc not calibrated' in all_errors_text or 'rc3_min' in all_errors_text:
            response.append("""! RC CONTROLLER NOT CALIBRATED

SOLUTION:
1. Go to: Initial Setup > Mandatory Hardware > Radio Calibration
2. Turn on your RC transmitter
3. Move all sticks to their extreme positions
4. Click 'Calibrate Radio' button
5. Verify all channels show GREEN bars
6. Click 'Click when Done'
""")

        if 'compass' in all_errors_text and ('calibrat' in all_errors_text or 'inconsistent' in all_errors_text):
            response.append("""! COMPASS CALIBRATION NEEDED

SOLUTION:
1. Go to: Initial Setup > Mandatory Hardware > Compass
2. Click 'Onboard Mag Calibration'
3. Take drone outside (away from metal/magnets)
4. Slowly rotate on all axes
5. Wait for 'Calibration successful' message
""")

        if 'accel' in all_errors_text and 'calibrat' in all_errors_text:
            response.append("""! ACCELEROMETER CALIBRATION NEEDED

SOLUTION:
1. Go to: Initial Setup > Mandatory Hardware > Accel Calibration
2. Follow on-screen instructions
3. Place drone in each orientation when prompted
4. Keep drone still during each measurement
""")

        if 'battery' in all_errors_text or 'voltage' in all_errors_text:
            response.append("""! BATTERY ISSUE

CHECK:
1. Is battery connected properly?
2. Is battery voltage sufficient?
3. Check battery parameters in Config/Full Parameter List
""")

        if not any(keyword in all_errors_text for keyword in ['rc', 'compass', 'accel', 'battery']):
            response.append("""For this specific error, please:
1. Check the error message carefully
2. Google: "ArduPilot PreArm [error message]"
3. Check Mission Planner documentation
4. Ask on ArduPilot forums if needed
""")

        return '\n'.join(response)

    def check_prearm(self):
        """Check for PreArm errors"""
        prearm_errors = self.log_analyzer.find_prearm_errors()

        if not prearm_errors:
            return "OK - No PreArm errors found in recent logs"

        response = [f"Found {len(prearm_errors)} PreArm error(s):\n"]

        # Show last 5 unique errors
        unique_errors = {}
        for err in prearm_errors:
            msg = err['message']
            unique_errors[msg] = err

        for msg, err in list(unique_errors.items())[-5:]:
            response.append(f"[{err['timestamp'].split()[1]}] {msg}")

        return '\n'.join(response)

    def check_errors(self):
        """Check for ERROR and CRITICAL messages"""
        errors = self.log_analyzer.find_errors(num_lines=300)

        if not errors:
            return "OK - No critical errors found in recent logs"

        response = [f"Found {len(errors)} error(s):\n"]

        for err in errors[-5:]:  # Last 5 errors
            time_only = err['timestamp'].split()[1]
            response.append(f"[{time_only}] {err['level']}: {err['message']}")

        return '\n'.join(response)

    def show_recent_logs(self):
        """Show recent log entries"""
        logs = self.log_analyzer.get_recent_logs(num_lines=15)
        return "RECENT LOG ENTRIES:\n\n" + logs

    def get_status_summary(self):
        """Get overall status summary"""
        summary = self.log_analyzer.summarize_issues()
        return "SYSTEM STATUS SUMMARY:\n\n" + summary

    def show_calibration_info(self):
        """Show calibration guidance"""
        return """CALIBRATION GUIDE:

COMPASS:
  Initial Setup > Mandatory Hardware > Compass
  - Click 'Onboard Mag Calibration'
  - Take drone outside, rotate slowly on all axes

RADIO (RC):
  Initial Setup > Mandatory Hardware > Radio Calibration
  - Move all sticks to extremes
  - Verify GREEN bars on all channels

ACCELEROMETER:
  Initial Setup > Mandatory Hardware > Accel Calibration
  - Follow on-screen instructions
  - Place drone in each orientation

ESC:
  Initial Setup > Optional Hardware > ESC Calibration
  - CAREFUL: Motors will spin!
  - Follow instructions exactly

Ask: "How to calibrate [compass/radio/accel]?" for specific help"""

    def general_response(self, query):
        """Handle general queries"""
        return f"""I understand you're asking about: "{query}"

I'm still learning! Currently I can help with:
- Motor/arming issues (ask: "why won't motors spin?")
- Calibration guidance
- Log analysis
- Error checking

Try: 'help' to see all commands"""


# Global function for C# to call
def process_query(user_input):
    """
    Main entry point called from C# plugin

    Args:
        user_input: User's question or command

    Returns:
        Response string
    """
    try:
        agent = DiagnosticAgent()
        return agent.process(user_input)
    except Exception as e:
        return f"Error processing query: {str(e)}\n\nPlease check that log files are accessible."
