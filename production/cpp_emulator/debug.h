#pragma once

#include <iostream>

#define debug(x) \
    std::cerr << #x " = " << (x) << std::endl
#define debug2(x, y) \
    std::cerr << #x " = " << (x) \
         << ", " #y " = " << (y) << std::endl
#define debug3(x, y, z) \
    std::cerr << #x " = " << (x) \
         << ", " #y " = " << (y) \
         << ", " #z " = " << (z) << std::endl
