# observability/logging_metrics.py
import logging
import time
from functools import wraps
from typing import Callable, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MetricsLogger:
    """
    Simple logger with manual timing support.
    """
    def __init__(self, name: str = "DefaultLogger"):
        self.logger = logging.getLogger(name)

    def log(self, msg: str, level: str = "INFO"):
        if level.upper() == "INFO":
            self.logger.info(msg)
        elif level.upper() == "ERROR":
            self.logger.error(msg)
        elif level.upper() == "WARNING":
            self.logger.warning(msg)
        else:
            self.logger.debug(msg)

    # For async functions, use manually in code
    def time_async_operation(self, operation_name: str) -> tuple[Callable, Callable]:
        async def start_timer():
            return time.time()

        def end_timer(start_time: float):
            duration = time.time() - start_time
            self.log(f"{operation_name} completed in {duration:.2f} seconds")
            return duration

        return start_timer, end_timer

    # For sync functions
    def timer_sync(self, operation_name: str):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                self.log(f"{operation_name} completed in {duration:.2f} seconds")
                return result
            return wrapper
        return decorator