import logging

logger = logging.getLogger(__name__)


def compute():
    for _ in range(10):
        logger.info('spam')
    logger.warn('warning')
    return 42
