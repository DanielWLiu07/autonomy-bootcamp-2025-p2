"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
        args: dict,  # Put your own arguments here
    ) -> tuple[bool, "Command"]:
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, cls(cls.__private_key, connection, target, local_logger, args)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
        args: dict,  # Put your own arguments here
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self.connection = connection
        self.target = target
        self.logger = local_logger
        self.args = args
        self.velocity_sum = [0.0, 0.0, 0.0]
        self.data_count = 0

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
        args: dict,  # Put your own arguments here
    ) -> list[str]:
        """
        Make a decision based on received telemetry data.
        """
        try:
            self.velocity_sum[0] += telemetry_data.x_velocity
            self.velocity_sum[1] += telemetry_data.y_velocity
            self.velocity_sum[2] += telemetry_data.z_velocity
            self.data_count += 1

            avg_velocity = [
                self.velocity_sum[0] / self.data_count,
                self.velocity_sum[1] / self.data_count,
                self.velocity_sum[2] / self.data_count,
            ]
            self.logger.info(f"Average velocity: {avg_velocity}")

            messages = []

            height_diff = self.target.z - telemetry_data.z
            if abs(height_diff) > args["height_tolerance"]:
                try:
                    self.connection.mav.command_long_send(
                        1,
                        0,
                        mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                        0,
                        self.target.z,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    )
                    messages.append(f"CHANGE ALTITUDE: {height_diff}")
                    self.logger.info(f"CHANGE ALTITUDE: {height_diff}")
                except (ConnectionError, OSError, ValueError) as e:
                    self.logger.error(f"Failed to send altitude command: {e}")

            dx = self.target.x - telemetry_data.x
            dy = self.target.y - telemetry_data.y
            desired_yaw = math.atan2(dy, dx)

            current_yaw = telemetry_data.yaw
            while current_yaw > math.pi:
                current_yaw -= 2 * math.pi
            while current_yaw < -math.pi:
                current_yaw += 2 * math.pi

            yaw_diff = desired_yaw - current_yaw
            while yaw_diff > math.pi:
                yaw_diff -= 2 * math.pi
            while yaw_diff < -math.pi:
                yaw_diff += 2 * math.pi

            yaw_diff_deg = math.degrees(yaw_diff)

            if abs(yaw_diff_deg) > args["angle_tolerance"]:
                direction = -1 if yaw_diff_deg > 0 else 1
                try:
                    self.connection.mav.command_long_send(
                        1,
                        0,
                        mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                        0,
                        yaw_diff_deg,
                        args["turning_speed"],
                        direction,
                        1,
                        0,
                        0,
                        0,
                        0,
                    )
                    messages.append(f"CHANGE YAW: {yaw_diff_deg}")
                    self.logger.info(f"CHANGE YAW: {yaw_diff_deg}")
                except (ConnectionError, OSError, ValueError) as e:
                    self.logger.error(f"Failed to send yaw command: {e}")

            return messages

        except (ConnectionError, OSError, ValueError, TypeError) as e:
            self.logger.error(f"Error in command decision: {e}")
            return []
