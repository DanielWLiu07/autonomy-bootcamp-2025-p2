"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import queue
import time

from pymavlink import mavutil

from modules.common.modules.logger import logger
from modules.common.modules.logger import logger_main_setup
from modules.common.modules.read_yaml import read_yaml
from modules.command import command
from modules.command import command_worker
from modules.heartbeat import heartbeat_receiver_worker
from modules.heartbeat import heartbeat_sender_worker
from modules.telemetry import telemetry_worker
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from utilities.workers import worker_manager


# MAVLink connection
CONNECTION_STRING = "tcp:localhost:12345"

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# Set queue max sizes (<= 0 for infinity)

# Set worker counts
HEARTBEAT_SENDER_COUNT = 1
HEARTBEAT_RECEIVER_COUNT = 1
TELEMETRY_COUNT = 1
COMMAND_COUNT = 1

# Any other constants
TARGET_POSITION = command.Position(10, 20, 30)
HEIGHT_TOLERANCE = 0.5
Z_SPEED = 1  # m/s
ANGLE_TOLERANCE = 5  # deg
TURNING_SPEED = 5  # deg/s
HEARTBEAT_PERIOD = 1  # seconds
MAIN_LOOP_DURATION = 100  # seconds
MAIN_LOOP_SLEEP = 1  # seconds

# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


def main() -> int:
    """
    Main function.
    """
    # Configuration settings
    result, config = read_yaml.open_config(logger.CONFIG_FILE_PATH)
    if not result:
        print("ERROR: Failed to load configuration file")
        return -1

    # Get Pylance to stop complaining
    assert config is not None

    # Setup main logger
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1

    # Get Pylance to stop complaining
    assert main_logger is not None

    # Create a connection to the drone. Assume that this is safe to pass around to all processes
    # In reality, this will not work, but to simplify the bootamp, preetend it is allowed
    # To test, you will run each of your workers individually to see if they work
    # (test "drones" are provided for you test your workers)
    # NOTE: If you want to have type annotations for the connection, it is of type mavutil.mavfile
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat(timeout=30)  # Wait for the "drone" to connect

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Create a worker controller
    controller = worker_controller.WorkerController()
    # Create a multiprocess manager for synchronized queues
    mp_manager = mp.Manager()

    # Create queues
    heartbeat_report_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager)
    telemetry_report_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager)
    command_input_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager)
    command_request_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager)
    command_output_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager)

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    result, heartbeat_sender_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_SENDER_COUNT,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments=(connection, HEARTBEAT_PERIOD, {}),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create heartbeat sender properties")
        return -1

    assert heartbeat_sender_properties is not None
    # Heartbeat receiver
    result, heartbeat_receiver_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_RECEIVER_COUNT,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments=(connection, HEARTBEAT_PERIOD),
        input_queues=[],
        output_queues=[heartbeat_report_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create heartbeat receiver properties")
        return -1

    assert heartbeat_receiver_properties is not None
    # Telemetry
    result, telemetry_properties = worker_manager.WorkerProperties.create(
        count=TELEMETRY_COUNT,
        target=telemetry_worker.telemetry_worker,
        work_arguments=(connection, {}),
        input_queues=[],
        output_queues=[telemetry_report_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create telemetry properties")
        return -1

    assert telemetry_properties is not None
    # Command
    result, command_properties = worker_manager.WorkerProperties.create(
        count=COMMAND_COUNT,
        target=command_worker.command_worker,
        work_arguments=(
            connection,
            TARGET_POSITION,
            {
                "height_tolerance": HEIGHT_TOLERANCE,
                "z_speed": Z_SPEED,
                "angle_tolerance": ANGLE_TOLERANCE,
                "turning_speed": TURNING_SPEED,
            },
        ),
        input_queues=[command_request_queue],
        output_queues=[command_output_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create command properties")
        return -1

    assert command_properties is not None

    # Create the workers (processes) and obtain their managers
    worker_managers = []

    result, heartbeat_sender_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_sender_properties,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create heartbeat sender manager")
        return -1

    assert heartbeat_sender_manager is not None
    worker_managers.append(heartbeat_sender_manager)

    result, heartbeat_receiver_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_receiver_properties,
        local_logger=main_logger,
    )

    if not result:
        main_logger.error("Failed to create heartbeat receiver manager")
        return -1

    assert heartbeat_receiver_manager is not None
    worker_managers.append(heartbeat_receiver_manager)

    result, telemetry_manager = worker_manager.WorkerManager.create(
        worker_properties=telemetry_properties, local_logger=main_logger
    )
    if not result:
        main_logger.error("Failed to create telemetry manager")
        return -1
    assert telemetry_manager is not None
    worker_managers.append(telemetry_manager)

    result, command_manager = worker_manager.WorkerManager.create(
        worker_properties=command_properties, local_logger=main_logger
    )
    if not result:
        main_logger.error("Failed to create command manager")
        return -1
    assert command_manager is not None
    worker_managers.append(command_manager)

    # Start worker processes
    for manager in worker_managers:
        manager.start_workers()

    main_logger.info("Started Worker Processes")

    # Main's work: read from all queues that output to main, and log any commands that we make
    start_time = time.time()
    try:
        while time.time() - start_time < MAIN_LOOP_DURATION:
            # Check if connection is still alive
            if not connection.target_system:
                main_logger.warning("Drone disconnected")
                break

            # Process heartbeat reports
            try:
                while True:
                    heartbeat_data = heartbeat_report_queue.queue.get_nowait()
                    main_logger.info(f"Received heartbeat: {heartbeat_data}")
            except queue.Empty:
                pass

            # Process telemetry reports
            try:
                while True:
                    telemetry_data = telemetry_report_queue.queue.get_nowait()
                    main_logger.info(f"Received telemetry: {telemetry_data}")
            except queue.Empty:
                pass

            # Process command responses
            try:
                while True:
                    command_response = command_output_queue.queue.get_nowait()
                    main_logger.info(f"Received command response: {command_response}")
            except queue.Empty:
                pass

            if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
                try:
                    test_command = {"type": "test", "data": f"command at {time.time()}"}
                    command_request_queue.queue.put_nowait(test_command)
                    main_logger.info(f"Sent command: {test_command}")
                except queue.Full:
                    main_logger.warning("Command queue is full")

            time.sleep(MAIN_LOOP_SLEEP)

    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt received")

    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    command_output_queue.fill_and_drain_queue()
    command_request_queue.fill_and_drain_queue()
    command_input_queue.fill_and_drain_queue()
    telemetry_report_queue.fill_and_drain_queue()
    heartbeat_report_queue.fill_and_drain_queue()

    main_logger.info("Queues cleared")

    # Clean up worker processes
    for manager in worker_managers:
        manager.join_workers()
    main_logger.info("Stopped")

    # We can reset controller in case we want to reuse it
    # Alternatively, create a new WorkerController instance
    controller.clear_exit()
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    return 0


if __name__ == "__main__":
    result_main = main()
    if result_main < 0:
        print(f"Failed with return code {result_main}")
    else:
        print("Success!")
