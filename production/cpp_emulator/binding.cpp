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
#include "logger.h"

using std::vector;
using std::string;
using std::unique_ptr;
using std::make_unique;


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
		.def_readonly("x", &Pos::x)
		.def_readonly("y", &Pos::y)
		.def_readonly("z", &Pos::z)
	;

	py::class_<Bot> BotClass(m, "Bot");
	BotClass
		.def(py::init<>())
		.def(py::init<unsigned char, Pos, std::vector<unsigned char>, bool>())
		.def_readonly("bid", &Bot::bid)
		.def_readonly("pos", &Bot::position)
		.def_readonly("seeds", &Bot::seeds)
		.def_readonly("active", &Bot::active)
	;

	py::class_<State> StClass(m, "State");
	StClass
		.def(py::init<>())
		.def(py::init<int>())

		.def_readonly("R", &State::R)
		.def_readonly("high_harmonics", &State::high_harmonics)
		.def_readonly("bots", &State::bots)
		.def_readonly("matrix", &State::matrix)
		.def_readonly("energy", &State::energy)

		//.def("__getitem__", (bool (*)(const Pos&)) &State::getbit)
		//.def("__setitem__", (void (*)(const Pos&, bool)) &State::setbit)
		.def("assert_well_formed", &State::assert_well_formed)
		.def("set_state", &State::set_state)
	;

	py::class_<Emulator> EmClass(m, "Emulator");
	EmClass
		.def(py::init<>())
		.def("load_model", &Emulator::load_model)
		.def("set_model", &Emulator::set_model)
		.def("load_trace", &Emulator::load_trace)
		.def("set_trace", &Emulator::set_trace)

		.def("set_state", &Emulator::set_state)
		.def("get_state", &Emulator::get_state)

		.def("run_step", &Emulator::run_one_step)
		.def("run", &Emulator::run_all)
		.def("run_commands", &Emulator::run_given)

		.def("energy", &Emulator::energy)
		.def_readonly("aborted", &Emulator::aborted)

		.def("setproblemname", &Emulator::setproblemname)
		.def("setsolutionname", &Emulator::setsolutionname)
		.def("setlogfile", &Emulator::setlogfile)
	;

	m.def("region_dimension", (int (*)(const Pos&, const Pos&)) &region_dimension);

	static py::exception<base_error> base_exc(m, "SimulatorException");
	py::register_exception_translator([](std::exception_ptr p) {
	    try {
	        if (p) std::rethrow_exception(p);
	    } catch (const base_error &e) {
	        base_exc(e.what());
	    }
	});
}
