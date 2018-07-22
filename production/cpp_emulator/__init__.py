# Magically compile the extension in this package when we try to import it.
from production.cpp_utils import magic_extension
magic_extension(
    name='emulator',
    sources=['binding.cpp', 'emulator.cpp', 'coordinates.cpp', 
             'commands.cpp', 'logger.cpp'],
    headers=[])
