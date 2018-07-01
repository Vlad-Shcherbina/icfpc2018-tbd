# Magically compile the extension in this package when we try to import it.
from production.cpp_utils import magic_extension
magic_extension(
    name='sample',
    sources=['sample.cpp'],
    headers=[])
