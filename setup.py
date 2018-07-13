from glob import glob
from os import walk
from setuptools import setup

def directory_tree(dir):
    return [x[0] for x in walk(dir)]

setup(
    name='icfpc',
    packages=directory_tree('icfpc'),
    test_suite='nose.collector',
    package_data={'': ['*.dll', '*.so']},
    entry_points={
        'console_scripts': [
            'icfpc-examples-cpp=icfpc.examples.cpp.main:main',
            'icfpc-examples-cpp-debug=icfpc.examples.cpp.debug:main',
            'icfpc-examples-log-level=icfpc.examples.log_level.main:main',
        ],
    },
    install_requires=[],
    tests_require=['nose']
)
