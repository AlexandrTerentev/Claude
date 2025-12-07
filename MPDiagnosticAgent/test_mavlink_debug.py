#!/usr/bin/env python3
"""
Debug script to test MAVLink log listing
"""

from core.mavlink_interface import MAVLinkInterface
from core.config import Config
import time

# Find available ports
ports = MAVLinkInterface.find_available_ports()
print(f"Available ports: {ports}")

if not ports:
    print("No ports found!")
    exit(1)

# Use first available port
port = ports[0]
print(f"\nUsing port: {port}")

# Connect
config = Config()
mav = MAVLinkInterface(connection_string=port, config=config)

if not mav.connect(verbose=True):
    print("Failed to connect!")
    exit(1)

print("\n" + "="*60)
print("Sending LOG_REQUEST_LIST...")
print("="*60)

# Send log request
mav.master.mav.log_request_list_send(
    mav.target_system,
    mav.target_component,
    0,      # start
    0xFFFF  # end
)

print("\nListening for ALL messages for 5 seconds...")
print("(Looking for LOG_ENTRY messages)")
print("-"*60)

start_time = time.time()
log_entries = []

while time.time() - start_time < 5:
    msg = mav.master.recv_match(blocking=True, timeout=0.5)

    if msg:
        msg_type = msg.get_type()

        if msg_type == 'LOG_ENTRY':
            print(f"✓ LOG_ENTRY: id={msg.id}, size={msg.size}, num_logs={msg.num_logs}")
            log_entries.append(msg)
        elif msg_type in ['HEARTBEAT', 'SYSTEM_TIME', 'GPS_RAW_INT', 'ATTITUDE']:
            # Skip common messages
            pass
        else:
            print(f"  {msg_type}: {msg}")

print("-"*60)
print(f"\nTotal LOG_ENTRY messages received: {len(log_entries)}")

if log_entries:
    print("\nLogs found:")
    for entry in log_entries:
        print(f"  Log {entry.id}: {entry.size} bytes")
else:
    print("\n⚠ No LOG_ENTRY messages received!")
    print("\nPossible reasons:")
    print("  1. Drone has no logs (fly it first)")
    print("  2. ArduPilot version doesn't support log download")
    print("  3. LOG_BACKEND parameter disabled")
    print("\nTry in Mission Planner:")
    print("  Config -> Full Parameter List -> LOG_BACKEND = 1")

mav.disconnect()
