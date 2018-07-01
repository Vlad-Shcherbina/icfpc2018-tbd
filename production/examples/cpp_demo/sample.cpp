#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include <algorithm>
#include <string>
#include <sstream>
#include <vector>
#include <iostream>
#include <assert.h>

const int N = 42;

template<typename T>
T square(T x) {
    return x*x;
}

std::vector<int> reverse(std::vector<int> xs) {
    auto c_plus_plus = 11;

    std::reverse(xs.begin(), xs.end());
    return xs;
}


class Hz {
public:
    int a;
    std::string b;
    Hz() : a(0) {
        std::cout << "Hz default constructor" << std::endl;
    }
    Hz(const Hz &other) {
        std::cout << "Hz copy constructor" << std::endl;
        a = other.a;
        b = other.b;
    }
    ~Hz() {
        std::cout << "Hz destructor" << std::endl;
    }
    std::string __str__() {
        std::ostringstream out;
        out << "Hz(" << a << ", " << b << ")";
        return out.str();
    }
};


struct Fail {
    static void fail_assert() {
        assert(false);
    }
    static void index_out_of_bounds() {
        std::vector<int> xs(3);
        std::cout << xs[3] << std::endl;
    }
    static void page_fault() {
        *(char*)123456 = 42;
    }
    static void infinite_recursion() {
        infinite_recursion();
    }
};


PYBIND11_PLUGIN(sample) {
    py::module m("sample", "pybind11 example plugin");

    m.attr("N") = N;
    m.def("square", &square<int>);
    m.def("square", &square<float>);
    m.def("reverse", &reverse);

    py::class_<Hz>(m, "Hz")
        .def(py::init<>())
        .def(py::init<const Hz&>())
        .def_readwrite("a", &Hz::a)
        .def_readwrite("b", &Hz::b)
        .def("__str__", &Hz::__str__)
    ;

    py::class_<Fail>(m, "Fail")
        .def_static("fail_assert", &Fail::fail_assert)
        .def_static("index_out_of_bounds", &Fail::index_out_of_bounds)
        .def_static("page_fault", &Fail::page_fault)
        .def_static("infinite_recursion", &Fail::infinite_recursion)
    ;

    return m.ptr();
}
