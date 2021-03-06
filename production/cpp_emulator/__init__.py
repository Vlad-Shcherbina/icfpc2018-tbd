# Magically compile the extension in this package when we try to import it.
from production.build_cpp_ext import magic_extension
magic_extension(
    name='emulator',
    sources=[
        'algo.cpp',
        'binding.cpp',
        'binding2.cpp',
        'emulator.cpp',
        'coordinates.cpp',
        'commands.cpp',
        'logger.cpp',
        'tests.cpp'
    ],
    headers=[
        'algo.h',
        'emulator.h',
        'coordinates.h',
        'commands.h',
        'logger.h',
        'matrix.h',
        'debug.h',
        'pretty_printing.h',
        'tests.h'
    ],
)
