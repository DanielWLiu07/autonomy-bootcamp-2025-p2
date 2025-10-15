"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import heartbeat_receiver
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_receiver_worker(
    connection: mavutil.mavfile,
    args,  # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (heartbeat_receiver.HeartbeatReceiver)
    result, heartbeat_receiver_obj = heartbeat_receiver.HeartbeatReceiver.create(
        connection, local_logger, args
    )
    if not result:
        local_logger.error("Failed to create HeartbeatReceiver")
        return

    # Main loop: do work.
    controller = args["controller"]
    heartbeat_period = args["heartbeat_period"]
    local_logger.info("Starting heartbeat receiving loop")
    while not controller.is_exit_requested():
        local_logger.info("Attempting to receive heartbeat")
        try:
            working = heartbeat_receiver_obj.run(args)
            if not working:
                local_logger.error("Failed to receive heartbeat")
        except Exception as e:
            local_logger.error(f"Failed to receive heartbeat: {e}", True)

        local_logger.info(f"Sleeping for {heartbeat_period} seconds")
        import time

        time.sleep(heartbeat_period)

    local_logger.info("Heartbeat receiving loop exited")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
