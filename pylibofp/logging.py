import collections
import logging.config
import os
import warnings
import sys


class TailBufferedHandler(logging.Handler):
    """Logging handler that records the last N log records."""

    _singleton = None

    def __init__(self, maxlen=10):
        super().__init__()
        self._tail = collections.deque(maxlen=maxlen)

    def lines(self):
        """Return last N log lines."""
        return self._tail

    def emit(self, record):
        """Log the specified log record."""
        try:
            self._tail.append(self.format(record))
        except Exception: # pylint: disable=broad-except
            self.handleError(record)

    def close(self):
        """Close the log handler."""
        super().close()
        self._tail.clear()

    @staticmethod
    def install():
        """Install tail logging handler."""
        # Only install it once.
        if TailBufferedHandler._singleton:
            return
        handler = TailBufferedHandler()
        root_logger = logging.getLogger()
        handler.setFormatter(root_logger.handlers[0].formatter)
        root_logger.addHandler(handler)
        TailBufferedHandler._singleton = handler

    @staticmethod
    def tail():
        """Return last N lines."""
        return TailBufferedHandler._singleton.lines()


class PatchedConsoleHandler(logging.Handler):
    """Logging handler that writes to stdout EVEN when stdout is patched.

    The normal StreamHandler grabs a reference to `sys.stdout` once at 
    initialization time. This class always logs to the current sys.stdout 
    which may be patched at runtime by prompt_toolkit.
    """

    def emit(self, record):
        try:
            stream = sys.stdout
            stream.write(self.format(record))
            stream.write('\n')
        except Exception: # pylint: disable=broad-except
            self.handleError(record)

    @staticmethod
    def install():
        """Install stdout logging handler."""
        handler = PatchedConsoleHandler()
        root_logger = logging.getLogger()
        handler.setFormatter(root_logger.handlers[0].formatter)
        handler.setLevel('WARNING')
        root_logger.addHandler(handler)


def init_logging(loglevel):
    """Set up logging.

    This routine also enables asyncio debug mode if `loglevel` is 'debug'.
    """
    if loglevel.lower() == 'debug':
        os.environ['PYTHONASYNCIODEBUG'] = '1'

    # Set up basic logging from config.
    logging.config.dictConfig(_logging_config(loglevel))

    # Create two more output handlers at runtime.
    PatchedConsoleHandler.install()
    TailBufferedHandler.install()

    logging.captureWarnings(True)
    warnings.simplefilter('always')


def _logging_config(loglevel):
    """Construct dictionary to configure logging via `dictConfig`.
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'complete': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'logfile': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'complete',
                'filename': 'ofp_app.log',
                'maxBytes': 2**20,
                'backupCount': 20,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            'pylibofp': {
                'level': loglevel.upper()
            },
            'asyncio': {
                'level': 'WARNING'  # avoid polling msgs at 'INFO' level
            }
        },
        'root': {
            'handlers': ['logfile']
        }
    }
