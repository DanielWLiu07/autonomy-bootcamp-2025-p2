"""
Telemetry gathering logic.
"""

import time

from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most recent attitude and position reading.
    """

    def __init__(
        self,
        time_since_boot: int | None = None,  # ms
        x: float | None = None,  # m
        y: float | None = None,  # m
        z: float | None = None,  # m
        x_velocity: float | None = None,  # m/s
        y_velocity: float | None = None,  # m/s
        z_velocity: float | None = None,  # m/s
        roll: float | None = None,  # rad
        pitch: float | None = None,  # rad
        yaw: float | None = None,  # rad
        roll_speed: float | None = None,  # rad/s
        pitch_speed: float | None = None,  # rad/s
        yaw_speed: float | None = None,  # rad/s
    ) -> None:
        self.time_since_boot = time_since_boot
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.z_velocity = z_velocity
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.roll_speed = roll_speed
        self.pitch_speed = pitch_speed
        self.yaw_speed = yaw_speed

    def __str__(self) -> str:
        return f"""{{
            time_since_boot: {self.time_since_boot},
            x: {self.x},
            y: {self.y},
            z: {self.z},
            x_velocity: {self.x_velocity},
            y_velocity: {self.y_velocity},
            z_velocity: {self.z_velocity},
            roll: {self.roll},
            pitch: {self.pitch},
            yaw: {self.yaw},
            roll_speed: {self.roll_speed},
            pitch_speed: {self.pitch_speed},
            yaw_speed: {self.yaw_speed}
        }}"""


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        args,  # Put your own arguments here
    ):
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        return True, cls(cls.__private_key, connection, local_logger, args)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        args,  # Put your own arguments here
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        self.connection = connection
        self.logger = local_logger
        self.args = args

    def run(
        self,
        args,  # Put your own arguments here
    ):
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        import time

        last_attitude = None
        last_position = None
        start_time = time.time()

        while time.time() - start_time < 1.0:
            try:
                msg = self.connection.recv_match(
                    type=["ATTITUDE", "LOCAL_POSITION_NED"], timeout=0.1
                )
                if msg:
                    if msg.get_type() == "ATTITUDE":
                        last_attitude = msg
                        self.logger.info("Received ATTITUDE message")
                    elif msg.get_type() == "LOCAL_POSITION_NED":
                        last_position = msg
                        self.logger.info("Received LOCAL_POSITION_NED message")

                    if last_attitude and last_position:
                        time_boot = max(last_attitude.time_boot_ms, last_position.time_boot_ms)
                        data = TelemetryData(
                            time_since_boot=time_boot,
                            x=last_position.x,
                            y=last_position.y,
                            z=last_position.z,
                            x_velocity=last_position.vx,
                            y_velocity=last_position.vy,
                            z_velocity=last_position.vz,
                            roll=last_attitude.roll,
                            pitch=last_attitude.pitch,
                            yaw=last_attitude.yaw,
                            roll_speed=last_attitude.rollspeed,
                            pitch_speed=last_attitude.pitchspeed,
                            yaw_speed=last_attitude.yawspeed,
                        )
                        self.logger.info(f"Returning TelemetryData: {data}")
                        return data
            except Exception as e:
                self.logger.error(f"Error receiving message: {e}")
                return None

        self.logger.error(
            "Timeout: Did not receive both ATTITUDE and LOCAL_POSITION_NED within 1 second"
        )
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
