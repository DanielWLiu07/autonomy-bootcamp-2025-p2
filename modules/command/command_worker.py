"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib

from pymavlink import mavutil

from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
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
    # Instantiate class object (command.Command)
    result, command_obj = command.Command.create(connection, target, local_logger, args)
    if not result:
        local_logger.error("Failed to create Command")
        return

    # Main loop: do work.
    controller = args["controller"]
    while not controller.is_exit_requested():
        try:
            telemetry_data = args["input_queue"].get(timeout=1)
            messages = command_obj.run(telemetry_data, args)
            for message in messages:
                args["output_queue"].put(message)
        except (ConnectionError, OSError, ValueError, TimeoutError) as e:
            local_logger.error(f"Error in worker loop: {e}")
        except KeyboardInterrupt:
            continue
