#!python3
import faulthandler
import sys
import pytest

if __name__ == '__main__':
    faulthandler.enable()
    sys.exit(pytest.main(sys.argv[1:]))
