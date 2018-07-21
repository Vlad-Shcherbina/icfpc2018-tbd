#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cassert>

#include "coordinates.h"
#include "commands.h"
#include "emulator.h"

using std::vector;
using std::string;
using std::unique_ptr;
using std::make_unique;


// ENERGY CONSTANTS







/*===================== FUNCTIONS =======================*/



/*====================== BINDING ========================*/

namespace py = pybind11;
PYBIND11_MODULE(emulator, m) {
	m.doc() = "C++ Emulator";

	py::class_<Diff> DiffClass(m, "Diff");
	DiffClass
		.def(py::init<int, int, int>())
		.def("mlen", &Diff::mlen)
		.def("clen", &Diff::clen)
		.def("is_linear", &Diff::is_linear)
		.def("is_short_linear", &Diff::is_short)
		.def("is_long_linear", &Diff::is_long)
		.def("is_near", &Diff::is_near)
		.def(py::self == py::self)
		.def(py::self != py::self)
		.def("__str__", &Diff::__str__)
	;

	py::class_<Pos> PosClass(m, "Pos");
	PosClass
		.def(py::init<int, int, int>())
		.def(py::self - py::self)
		.def("is_inside_matrix", &Pos::is_inside)
		.def("__add__", &Pos::operator+, py::is_operator())
		.def("__iadd__", &Pos::operator+=, py::is_operator())
		// .def("__sub__", &Pos::operator-<DiffClass>, py::is_operator())
		// .def("__isub__", &Pos::operator-=<Diff>, py::is_operator())
		.def(py::self == py::self)
		.def(py::self != py::self)
		.def("__str__", &Pos::__str__)
	;

	py::class_<Emulator> EmClass(m, "Emulator");
	EmClass
		.def(py::init<>())
		.def("run", &Emulator::run)
		.def_readonly("energy", &Emulator::energy)
	;

	m.def("region_dimension", &region_dimension);
}
