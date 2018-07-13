cmake_minimum_required(VERSION 3.0)
project(icfpc_example_cpp)

set(CMAKE_CXX_STANDARD 17)

add_subdirectory(pybind11)
pybind11_add_module(icfpc/examples/cpp/extension icfpc/examples/cpp/extension.cpp)

