import os
import sys
import inspect
import contextlib


def magic_extension(*, name, sources, headers):
    '''See examples/cpp_demo/__init__.py.'''

    caller_file = inspect.stack()[1].filename
    assert os.path.basename(caller_file) == '__init__.py', caller_file

    release = os.getenv('TBD_RELEASE', '0')
    assert release in ('0', '1'), release
    release = release == '1'

    method = os.getenv('TBD_BUILD_METHOD', 'manual')
    assert method in ('manual', 'distutils'), method
    if method == 'manual':
        from production.build_cpp_ext.manual import build_extension
    elif method == 'distutils':
        from production.build_cpp_ext.du import build_extension
    else:
        assert False, method

    with contextlib.redirect_stdout(sys.stderr):
        build_extension(caller_file, name, sources, headers, release)
