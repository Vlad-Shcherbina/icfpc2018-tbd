# module runner

from cpp import umvm as external
import logging

logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info(external.top_level_test())
    xo = external.umvm();
    logger.info(external.umvm.test(xo))

if __name__ == "__main__":
    main()
