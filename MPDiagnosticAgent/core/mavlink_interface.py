# -*- coding: utf-8 -*-
"""
MAVLink Interface for MPDiagnosticAgent
Handles connection and communication with ArduPilot drones via MAVLink protocol
"""

import time
from typing import Optional, Callable, Any
from pymavlink import mavutil

# Handle imports for both module and standalone usage
try:
    from .config import Config
except ImportError:
    from config import Config


class MAVLinkInterface:
    """
    MAVLink connection manager

    Provides connection, heartbeat monitoring, and basic MAVLink operations
    for communicating with ArduPilot flight controllers
    """

    def __init__(self, connection_string: Optional[str] = None, baudrate: int = 921600,
                 timeout: int = 30, config: Optional[Config] = None):
        """
        Initialize MAVLink interface

        Args:
            connection_string: Connection string (e.g., '/dev/ttyUSB0', 'COM3', 'udp:127.0.0.1:14550')
            baudrate: Serial baudrate (default: 921600 for ArduPilot)
            timeout: Connection timeout in seconds
            config: Configuration object (optional)
        """
        self.config = config if config else Config()

        # Use connection string from config if not provided
        if connection_string is None:
            connection_string = self.config.mavlink_port

        self.connection_string = connection_string
        self.baudrate = baudrate
        self.timeout = timeout

        # MAVLink connection object
        self.master = None
        self.connected = False

        # System and component IDs (set after connection)
        self.target_system = 1
        self.target_component = 1

    def connect(self, verbose: bool = True) -> bool:
        """
        Establish connection to drone

        Args:
            verbose: Print connection messages

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            if verbose:
                print(f"Connecting to {self.connection_string} at {self.baudrate} baud...")

            # Create MAVLink connection
            self.master = mavutil.mavlink_connection(
                self.connection_string,
                baud=self.baudrate,
                source_system=255,  # Ground station system ID
                source_component=mavutil.mavlink.MAV_COMP_ID_MISSIONPLANNER
            )

            if verbose:
                print("Waiting for heartbeat...")

            # Wait for heartbeat to confirm connection
            heartbeat = self.wait_heartbeat(timeout=self.timeout)

            if heartbeat:
                self.connected = True
                self.target_system = self.master.target_system
                self.target_component = self.master.target_component

                if verbose:
                    print(f"✓ Connected to system {self.target_system}, component {self.target_component}")
                    print(f"  MAVLink version: {heartbeat.mavlink_version}")
                    print(f"  Autopilot: {self._get_autopilot_name(heartbeat.autopilot)}")
                    print(f"  Vehicle type: {self._get_vehicle_type(heartbeat.type)}")
                    print(f"  Flight mode: {heartbeat.custom_mode}")

                return True
            else:
                if verbose:
                    print(f"✗ No heartbeat received within {self.timeout} seconds")
                return False

        except Exception as e:
            if verbose:
                print(f"✗ Connection failed: {e}")
            self.connected = False
            return False

    def wait_heartbeat(self, timeout: Optional[int] = None) -> Optional[Any]:
        """
        Wait for heartbeat message from drone

        Args:
            timeout: Timeout in seconds (uses self.timeout if not specified)

        Returns:
            Heartbeat message or None if timeout
        """
        if timeout is None:
            timeout = self.timeout

        if not self.master:
            return None

        # Wait for heartbeat
        msg = self.master.wait_heartbeat(timeout=timeout)
        return msg

    def disconnect(self):
        """Close MAVLink connection"""
        if self.master:
            try:
                self.master.close()
                self.connected = False
                print("✓ Disconnected from drone")
            except Exception as e:
                print(f"⚠ Error during disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if connected to drone"""
        return self.connected and self.master is not None

    def send_command_long(self, command: int, param1: float = 0, param2: float = 0,
                         param3: float = 0, param4: float = 0, param5: float = 0,
                         param6: float = 0, param7: float = 0, confirmation: int = 0) -> bool:
        """
        Send MAVLink COMMAND_LONG message

        Args:
            command: MAV_CMD command ID
            param1-7: Command parameters
            confirmation: Confirmation counter

        Returns:
            True if sent successfully
        """
        if not self.is_connected():
            print("✗ Not connected to drone")
            return False

        try:
            self.master.mav.command_long_send(
                self.target_system,
                self.target_component,
                command,
                confirmation,
                param1, param2, param3, param4, param5, param6, param7
            )
            return True
        except Exception as e:
            print(f"✗ Error sending command: {e}")
            return False

    def receive_message(self, msg_type: str, timeout: int = 5, blocking: bool = True) -> Optional[Any]:
        """
        Receive specific MAVLink message type

        Args:
            msg_type: Message type to receive (e.g., 'HEARTBEAT', 'GLOBAL_POSITION_INT')
            timeout: Timeout in seconds
            blocking: Wait for message if True, return immediately if False

        Returns:
            MAVLink message or None
        """
        if not self.is_connected():
            return None

        try:
            msg = self.master.recv_match(type=msg_type, blocking=blocking, timeout=timeout)
            return msg
        except Exception as e:
            print(f"✗ Error receiving message: {e}")
            return None

    def get_parameters(self, param_names: Optional[list] = None) -> dict:
        """
        Request and retrieve parameters from drone

        Args:
            param_names: List of parameter names to fetch (None = all parameters)

        Returns:
            Dictionary of parameter name: value
        """
        if not self.is_connected():
            print("✗ Not connected to drone")
            return {}

        params = {}

        try:
            if param_names is None:
                # Request all parameters
                print("Requesting all parameters (this may take a while)...")
                self.master.mav.param_request_list_send(
                    self.target_system,
                    self.target_component
                )

                # Wait for parameters
                timeout = time.time() + 30  # 30 second timeout
                while time.time() < timeout:
                    msg = self.receive_message('PARAM_VALUE', timeout=1, blocking=True)
                    if msg:
                        param_id = msg.param_id.decode('utf-8') if isinstance(msg.param_id, bytes) else msg.param_id
                        params[param_id] = msg.param_value

                        # Check if we've received all parameters
                        if msg.param_index + 1 >= msg.param_count:
                            break

                print(f"✓ Received {len(params)} parameters")
            else:
                # Request specific parameters
                for param_name in param_names:
                    self.master.mav.param_request_read_send(
                        self.target_system,
                        self.target_component,
                        param_name.encode('utf-8'),
                        -1  # Use param_id instead of param_index
                    )

                    msg = self.receive_message('PARAM_VALUE', timeout=5)
                    if msg:
                        param_id = msg.param_id.decode('utf-8') if isinstance(msg.param_id, bytes) else msg.param_id
                        params[param_id] = msg.param_value

        except Exception as e:
            print(f"✗ Error getting parameters: {e}")

        return params

    def set_parameter(self, param_name: str, param_value: float, param_type: int = mavutil.mavlink.MAV_PARAM_TYPE_REAL32) -> bool:
        """
        Set parameter on drone

        Args:
            param_name: Parameter name
            param_value: Parameter value
            param_type: Parameter type (default: REAL32)

        Returns:
            True if successful
        """
        if not self.is_connected():
            print("✗ Not connected to drone")
            return False

        try:
            self.master.mav.param_set_send(
                self.target_system,
                self.target_component,
                param_name.encode('utf-8'),
                param_value,
                param_type
            )

            # Wait for confirmation
            msg = self.receive_message('PARAM_VALUE', timeout=5)
            if msg:
                param_id = msg.param_id.decode('utf-8') if isinstance(msg.param_id, bytes) else msg.param_id
                if param_id == param_name and abs(msg.param_value - param_value) < 0.001:
                    print(f"✓ Parameter {param_name} set to {param_value}")
                    return True

            print(f"✗ Failed to set parameter {param_name}")
            return False

        except Exception as e:
            print(f"✗ Error setting parameter: {e}")
            return False

    @staticmethod
    def _get_autopilot_name(autopilot_id: int) -> str:
        """Get autopilot name from ID"""
        autopilots = {
            mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA: "ArduPilot",
            mavutil.mavlink.MAV_AUTOPILOT_PX4: "PX4",
            mavutil.mavlink.MAV_AUTOPILOT_GENERIC: "Generic",
        }
        return autopilots.get(autopilot_id, f"Unknown ({autopilot_id})")

    @staticmethod
    def _get_vehicle_type(vehicle_type_id: int) -> str:
        """Get vehicle type name from ID"""
        types = {
            mavutil.mavlink.MAV_TYPE_QUADROTOR: "Quadcopter",
            mavutil.mavlink.MAV_TYPE_HEXAROTOR: "Hexacopter",
            mavutil.mavlink.MAV_TYPE_OCTOROTOR: "Octocopter",
            mavutil.mavlink.MAV_TYPE_HELICOPTER: "Helicopter",
            mavutil.mavlink.MAV_TYPE_FIXED_WING: "Fixed Wing",
            mavutil.mavlink.MAV_TYPE_GROUND_ROVER: "Rover",
            mavutil.mavlink.MAV_TYPE_SUBMARINE: "Submarine",
        }
        return types.get(vehicle_type_id, f"Unknown ({vehicle_type_id})")

    def get_system_status(self) -> dict:
        """
        Get current system status

        Returns:
            Dictionary with status information
        """
        if not self.is_connected():
            return {'error': 'Not connected'}

        status = {}

        try:
            # Get SYS_STATUS message
            msg = self.receive_message('SYS_STATUS', timeout=5)
            if msg:
                status['voltage'] = msg.voltage_battery / 1000.0  # mV to V
                status['current'] = msg.current_battery / 100.0   # cA to A
                status['battery_remaining'] = msg.battery_remaining

            # Get GPS status
            gps_msg = self.receive_message('GPS_RAW_INT', timeout=5)
            if gps_msg:
                status['gps_fix'] = gps_msg.fix_type
                status['satellites'] = gps_msg.satellites_visible

            # Get attitude
            attitude_msg = self.receive_message('ATTITUDE', timeout=5)
            if attitude_msg:
                status['roll'] = attitude_msg.roll
                status['pitch'] = attitude_msg.pitch
                status['yaw'] = attitude_msg.yaw

        except Exception as e:
            status['error'] = str(e)

        return status


# Testing
if __name__ == '__main__':
    print("Testing MAVLinkInterface module...\n")
    print("=" * 60)

    # Create interface
    mav = MAVLinkInterface()

    print(f"Connection string: {mav.connection_string}")
    print(f"Baudrate: {mav.baudrate}")
    print(f"Timeout: {mav.timeout}s")
    print()

    # Try to connect
    print("Attempting to connect to drone...")
    print("(Make sure drone is connected to USB port)")
    print()

    if mav.connect(verbose=True):
        print("\n" + "=" * 60)
        print("Connection successful! Testing additional features...")
        print("=" * 60)

        # Get system status
        print("\nGetting system status...")
        status = mav.get_system_status()
        for key, value in status.items():
            print(f"  {key}: {value}")

        # Get some parameters
        print("\nGetting selected parameters...")
        params = mav.get_parameters(['SYSID_THISMAV', 'FRAME_TYPE'])
        for name, value in params.items():
            print(f"  {name}: {value}")

        # Disconnect
        print()
        mav.disconnect()
    else:
        print("\n✗ Failed to connect to drone")
        print("Please check:")
        print("  1. Drone is connected to USB port")
        print("  2. Correct port in config.yaml (default: /dev/ttyUSB0)")
        print("  3. User has permissions to access serial port")
        print("     (run: sudo usermod -a -G dialout $USER)")
