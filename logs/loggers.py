import logging
import sys


def default_logger(testing=False, stream=sys.stdout, file='./logs/log.log'):
    """
    First call to default_logger will create and setup the logger.
    Future calls will just return this logger.
    :param testing - If True, write logs to stdout. Otherwise it write logs to a file.
    :param stream - Type of stream(stdout, stderr).
    :param file - Path to and name of the log file.
    """
    default_logger = logging.getLogger('qgmailer-default')

    if len(default_logger.handlers) != 0:
        return default_logger

    if testing:
        handler = logging.StreamHandler(stream=stream)
        handler.setLevel(logging.DEBUG)
    else:
        handler = logging.FileHandler(file)
        handler.setLevel(logging.WARNING)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    default_logger.addHandler(handler)
    return default_logger


def clear_log_file(logger):
    for handler in logger.handlers:
        if hasattr(handler, 'baseFilename'):
            filename = handler.baseFilename
            # Open for write, which is going to clear the whole file.
            with open(filename, 'w'):
                pass
