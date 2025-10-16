"""
Heartbeat sending logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        # Put your own arguments here
    ) -> tuple[bool, "HeartbeatSender"]:
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            sender = cls(cls.__private_key, connection, local_logger)
            return True, sender
        except (ConnectionError, ValueError, TypeError) as e:
            local_logger.error(f"Failed to create HeartbeatSender: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.logger = local_logger

    def run(self) -> bool:
        """
        Attempt to send a heartbeat message.
        """
        try:
            self.connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0
            )
            self.logger.info("Heartbeat sent Wahoo")
            return True
        except (ConnectionError, OSError) as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
            return False


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
