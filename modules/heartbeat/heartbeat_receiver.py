"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger,
        args,  # Put your own arguments here
    ):
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            receiver = cls(cls.__private_key, connection, local_logger, args)
            return True, receiver
        except Exception as e:
            local_logger.error(f"Failed to create HeartbeatReceiver: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger,
        args,  # Put your own arguments here
    ):
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.logger = local_logger
        self.consecutive_failures = 0

    def run(
        self,
        args,  # Put your own arguments here
    ):
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            msg = self.connection.recv_match(type="HEARTBEAT", blocking=False, timeout=1.0)
            if msg:
                self.consecutive_failures = 0
                self.logger.info("Heartbeat received successfully")
            else:
                self.consecutive_failures += 1
                self.logger.warning(
                    f"No heartbeat received, consecutive failures: {self.consecutive_failures}"
                )

            # Determine current state
            threshold = args.get("disconnect_threshold", 5)
            if self.consecutive_failures < threshold:
                state = "Connected"
            else:
                state = "Disconnected"
                self.logger.error("Connection considered disconnected")

            # Report state every second
            args["output_queue"].put(state)

            return self.consecutive_failures <= args.get("disconnect_threshold", 5)
        except Exception as e:
            self.logger.error(f"Error receiving heartbeat: {e}")
            return False


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
