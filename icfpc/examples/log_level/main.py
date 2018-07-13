import logging
logger = logging.getLogger(__name__)

from icfpc.examples.log_level import spam


def main():
    logging.getLogger(spam.__name__).setLevel(logging.WARN)
    logger.info(spam.compute())


if __name__ == '__main__':
    main()
