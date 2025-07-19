import logging

logger = logging.getLogger(__name__)


def safe_block(block_name: str = "operation"):
    """Context manager for safely executing a block of code"""

    class SafeBlock:
        def __init__(self, name: str):
            self.name = name

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                logger.warning(f"Safe block '{self.name}' failed: {exc_val}")
                return True  # Suppress the exception
            return False

    return SafeBlock(block_name)
