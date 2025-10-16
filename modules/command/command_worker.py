"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib
import queue

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller

from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    height_tolerance: float,
    z_speed: float,
    angle_tolerance: float,
    turning_speed: float,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.
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
    # Instantiate class object (command.Command)
    result, command_obj = command.Command.create(
        connection, target, local_logger, height_tolerance, z_speed, angle_tolerance, turning_speed
    )
    if not result:
        local_logger.error("Failed to create Command")
        return

    # Main loop: do work.
    while not controller.is_exit_requested():
        try:
            command_data = input_queue.queue.get(timeout=1)
            message = command_obj.run(command_data)
            if message:
                output_queue.queue.put(message)
        except (ConnectionError, OSError, ValueError, queue.Empty) as e:
            local_logger.error(f"Error in worker loop: {e}")
        except KeyboardInterrupt:
            continue
