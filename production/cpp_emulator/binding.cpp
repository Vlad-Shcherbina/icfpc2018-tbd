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

	py::class_<Bot> BotClass(m, "Bot");
	BotClass
		.def(py::init<unsigned char,
			          unsigned char,
			          unsigned char,
			          unsigned char,
			          std::vector<unsigned char>,
			          bool>())
	;

	py::class_<State> StClass(m, "State");
	StClass
		.def(py::init<int>())
		.def("__setitem__", &State::setmatrixbit)
		.def("__getitem__", &State::getmatrixbit)
		.def("assert_well_formed", &State::assert_well_formed)

		.def_readonly("energy", &State::energy)
	;

	py::class_<Emulator> EmClass(m, "Emulator");
	EmClass
		.def(py::init<>())
		.def("run_step", &Emulator::run_one_step)
		.def("run", &Emulator::run_all)
		.def("run_commands", &Emulator::run_given_step)
		.def("energy", &Emulator::energy)
		.def("reconstruct", &Emulator::reconstruct_state)
		.def("add_bot", &Emulator::add_bot)
		.def("count_active", &Emulator::count_active)
	;

	m.def("region_dimension", &region_dimension);
}


