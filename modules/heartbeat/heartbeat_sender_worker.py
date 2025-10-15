"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_sender_worker(
    connection: mavutil.mavfile,
    controller: worker_controller.WorkerController,
    heartbeat_period: float,
    args: dict,  # Place your own arguments here
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
    # Instantiate class object (heartbeat_sender.HeartbeatSender)
    result, heartbeat_sender_obj = heartbeat_sender.HeartbeatSender.create(
        connection, local_logger, args
    )
    if not result:
        local_logger.error("Failed to create HeartbeatSender")
        return
    local_logger.info("Yippe bro it creaated the sender")
    # Main loop: do work.
    local_logger.info("Starting heartbeat sending loop")

    while not controller.is_exit_requested():
        local_logger.info("Attempting to send heartbeat")
        try:
            working = heartbeat_sender_obj.run(args)
            if not working:
                local_logger.error("Failed to send heartbeat")
        except (ConnectionError, OSError, ValueError) as e:
            local_logger.error(f"Failed to send heartbeat: {e}", True)

        local_logger.info(f"Sleeping for {heartbeat_period} seconds")
        time.sleep(heartbeat_period)

    local_logger.info("Heartbeat sending loop exited")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
