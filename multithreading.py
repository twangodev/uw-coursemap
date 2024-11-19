import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


def threaded_task_runner(task_function, inputs, max_runtime, max_retries, max_threads, logger, task_description, identifier_function):
    """
    Spawns threads to process inputs, retrying failed tasks up to max_retries.
    Maps inputs to their outputs, excluding tasks that fail all retries or return None.

    Args:
        task_function (callable): The function to execute for each task.
        inputs (list): List of tuples representing input arguments for the tasks.
        max_runtime (int): Maximum runtime for all threads in seconds.
        max_retries (int): Maximum number of retries for failed tasks.
        max_threads (int): Maximum number of threads to run concurrently.
        logger (logging.Logger): Logger instance to log errors and events.
        task_description (str): Description of the task for logging purposes.
        identifier_function (callable): A function that generates a unique identifier for log messages, given input_args.

    Returns:
        dict: Mapping of input values to their outputs for successful tasks.
    """
    results = {}
    lock = threading.Lock()

    def task_wrapper(input_args):
        """Wrapper to execute the task with retries and store results."""
        identifier = identifier_function(input_args)  # Get identifier for logging
        retry_count = 0
        while retry_count <= max_retries:
            logger.debug(f"Starting task for {task_description} with identifier {identifier} (retry {retry_count}/{max_retries})")
            try:
                result = task_function(*input_args)
                if result is not None:
                    with lock:
                        results[input_args] = result
                    logger.debug(f"Task for {task_description} with identifier {identifier} completed successfully.")
                    return
            except Exception as e:
                logger.error(f"Task failed for {task_description} with identifier {identifier}, retry {retry_count + 1}/{max_retries}: {e}")
            retry_count += 1

        # Log failure after exhausting retries
        logger.error(f"Task for {task_description} with identifier {identifier} failed after {max_retries} retries.")

    with ThreadPoolExecutor(max_threads) as executor:  # Control max threads here
        future_to_input = {
            executor.submit(task_wrapper, input_args): input_args for input_args in inputs
        }
        try:
            for future in as_completed(future_to_input, timeout=max_runtime):
                pass  # Results are handled within task_wrapper
        except TimeoutError:
            logger.warning(f"Task execution for {task_description} exceeded the max runtime.")

    return results

def identify_by_first_input(input_args):
    return input_args[0]