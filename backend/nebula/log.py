import enum
import logging
import sys
import traceback


def indent(text: str, level: int = 4) -> str:
    return text.replace("\n", f"\n{' '*level}")


class LogLevel(enum.IntEnum):
    """Log level."""

    TRACE = 0
    DEBUG = 1
    INFO = 2
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class Logger:
    user: str = "nebula"
    level = LogLevel.DEBUG
    user_max_length: int = 16

    def __call__(self, level: LogLevel, *args, **kwargs):
        if level < self.level:
            return

        lvl = level.name.upper()
        usr = kwargs.get("user") or self.user
        usr = usr[: self.user_max_length].ljust(self.user_max_length)
        msg = " ".join([str(arg) for arg in args])

        print(
            f"{lvl:<8} {usr} {msg}",
            file=sys.stderr,
            flush=True,
        )

    def trace(self, *args, **kwargs):
        self(LogLevel.TRACE, *args, **kwargs)

    def debug(self, *args, **kwargs):
        self(LogLevel.DEBUG, *args, **kwargs)

    def info(self, *args, **kwargs):
        self(LogLevel.INFO, *args, **kwargs)

    def success(self, *args, **kwargs):
        self(LogLevel.SUCCESS, *args, **kwargs)

    def warn(self, *args, **kwargs):
        self(LogLevel.WARNING, *args, **kwargs)

    def warning(self, *args, **kwargs):
        self(LogLevel.WARNING, *args, **kwargs)

    def error(self, *args, **kwargs):
        self(LogLevel.ERROR, *args, **kwargs)

    def traceback(self, *args, **kwargs) -> str:
        msg = " ".join([str(arg) for arg in args])
        tb = traceback.format_exc()
        msg = f"{msg}\n\n{indent(tb)}"
        self(LogLevel.ERROR, msg, **kwargs)
        return msg

    def critical(self, *args, **kwargs):
        self(LogLevel.CRITICAL, *args, **kwargs)


log = Logger()

# Add custom logging handler to standard logging module
# This allows us to use the standard logging module with
# the same format, log level and consumers as the primary
# Nebula logger. This is useful for 3rd party libraries.


class CustomHandler(logging.Handler):
    def emit(self, record):
        log_message = self.format(record)
        name = record.name
        log(LogLevel(record.levelno // 10), log_message, user=name)


root_logger = logging.getLogger()
root_logger.setLevel(log.level * 10)

custom_handler = CustomHandler()
root_logger.addHandler(custom_handler)
