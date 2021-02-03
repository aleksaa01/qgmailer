import logging
import sys


TESTING = True
TESTING_LOG_LEVEL = logging.DEBUG
PRODUCTION_LOG_LEVEL = logging.WARNING


def default_logger(stream=sys.stdout, file='./logs/log.log'):
    """
    First call to default_logger will create and setup the logger.
    Future calls will just return this logger.
    :param stream - Type of stream(stdout, stderr).
    :param file - Path to and name of the log file.
    """
    default_logger = logging.getLogger('qgmailer-default')

    if len(default_logger.handlers) != 0:
        return default_logger

    if TESTING:
        handler = logging.StreamHandler(stream=stream)
        handler.setLevel(TESTING_LOG_LEVEL)
        default_logger.setLevel(TESTING_LOG_LEVEL)
    else:
        handler = logging.FileHandler(file)
        handler.setLevel(PRODUCTION_LOG_LEVEL)
        default_logger.setLevel(PRODUCTION_LOG_LEVEL)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
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
