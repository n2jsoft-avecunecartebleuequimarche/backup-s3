import signal
from .log import logger


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """Set the kill_now flag to True when a signal is received."""
        logger.info("Received signal to exit gracefully.")
        self.kill_now = True
