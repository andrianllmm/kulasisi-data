import signal
import sys
from utils.logger import logger


def on_exit(callback, message="Process interrupted. Exiting..."):
    """Handles interruption."""

    def handle_signal(*_):
        logger.info(message)
        try:
            callback()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
