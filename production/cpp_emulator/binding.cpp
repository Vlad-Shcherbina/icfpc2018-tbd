#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cassert>

#include "coordinates.h"
#include "matrix.h"
#include "commands.h"
#include "emulator.h"
#include "logger.h"
#include "algo.h"

using std::vector;
using std::string;
using std::unique_ptr;
using std::make_unique;

namespace py = pybind11;
PYBIND11_MODULE(emulator, m) {
	m.doc() = "C++ Emulator";

	m.attr("SHORT_DISTANCE") = SHORT_DISTANCE;
	m.attr("LONG_DISTANCE") = LONG_DISTANCE;
	m.attr("FAR_DISTANCE") = FAR_DISTANCE;

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
		.def(py::self < py::self)
		.def("__repr__", &Diff::__repr__)
		.def("__add__", &Diff::operator+, py::is_operator())
		.def_readonly("dx", &Diff::dx)
		.def_readonly("dy", &Diff::dy)
		.def_readonly("dz", &Diff::dz)
	;

	py::class_<Pos> PosClass(m, "Pos");
	PosClass
		.def(py::init<int, int, int>())
		.def(py::self - py::self)
		.def("is_inside_matrix", &Pos::is_inside)
		.def("__add__", &Pos::operator+, py::is_operator())
		.def("__iadd__", &Pos::operator+=, py::is_operator())
		.def(py::self == py::self)
		.def(py::self != py::self)
		.def(py::self < py::self)
		.def("__repr__", &Pos::__repr__)
		.def("pack", &Pos::pack)
		.def("unpack", &Pos::unpack)
		.def_readonly("x", &Pos::x)
		.def_readonly("y", &Pos::y)
		.def_readonly("z", &Pos::z)
	;

	py::class_<Matrix>(m, "Matrix")
		.def(py::init<int>())
		.def("parse", &Matrix::parse)
		.def_readonly("R", &Matrix::R)
		.def("get", &Matrix::get)
		.def("set", &Matrix::set)
		.def("grounded_voxels", &Matrix::grounded_voxels)
		.def("count_inside_region", &Matrix::count_inside_region)
	;

	// TODO
	py::class_<Command>(m, "Command")
	;
	py::class_<Halt>(m, "Halt")
		.def(py::init<>())
		.def("__repr__", &Halt::__repr__)
	;
	py::class_<Wait>(m, "Wait")
		.def(py::init<>())
		.def("__repr__", &Wait::__repr__)
	;
	py::class_<Flip>(m, "Flip")
		.def(py::init<>())
		.def("__repr__", &Flip::__repr__)
	;
	py::class_<SMove>(m, "SMove")
		.def(py::init<Diff>())
		.def("__repr__", &SMove::__repr__)
		.def_readonly("lld", &SMove::lld)
	;
	py::class_<LMove>(m, "LMove")
		.def(py::init<Diff, Diff>())
		.def("__repr__", &LMove::__repr__)
		.def_readonly("sld1", &LMove::sld1)
		.def_readonly("sld2", &LMove::sld2)
	;
	py::class_<FusionP>(m, "FusionP")
		.def(py::init<Diff>())
		.def("__repr__", &FusionP::__repr__)
		.def_readonly("nd", &FusionP::nd)
	;
	py::class_<FusionS>(m, "FusionS")
		.def(py::init<Diff>())
		.def("__repr__", &FusionS::__repr__)
		.def_readonly("nd", &FusionS::nd)
	;
	py::class_<Fission>(m, "Fission")
		.def(py::init<Diff, unsigned>())
		.def("__repr__", &Fission::__repr__)
		.def_readonly("nd", &Fission::nd)
		.def_readonly("m", &Fission::m)
	;
	py::class_<Fill>(m, "Fill")
		.def(py::init<Diff>())
		.def("__repr__", &Fill::__repr__)
		.def_readonly("nd", &Fill::nd)
	;
	py::class_<Void>(m, "Void")
		.def(py::init<Diff>())
		.def("__repr__", &Void::__repr__)
		.def_readonly("nd", &Void::nd)
	;
	py::class_<GFill>(m, "GFill")
		.def(py::init<Diff, Diff>())
		.def("__repr__", &GFill::__repr__)
		.def_readonly("nd", &GFill::nd)
		.def_readonly("fd", &GFill::fd)
	;
	py::class_<GVoid>(m, "GVoid")
		.def(py::init<Diff, Diff>())
		.def("__repr__", &GVoid::__repr__)
		.def_readonly("nd", &GVoid::nd)
		.def_readonly("fd", &GVoid::fd)
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
		.def(py::init<std::optional<Matrix>, std::optional<Matrix>>())
		.def(py::init<std::optional<Matrix>,
					  std::optional<Matrix>,
					  bool,
					  int64_t,
					  std::vector<Bot>>())

		.def_readonly("R", &State::R)
		.def_readonly("high_harmonics", &State::high_harmonics)
		.def_readonly("bots", &State::bots)
		.def_readonly("matrix", &State::matrix)
		.def_readonly("energy", &State::energy)

		.def("__getitem__", &State::__getitem__)
		.def("__setitem__", &State::__setitem__)
		.def("assert_well_formed", &State::assert_well_formed)
	;

	py::class_<Emulator> EmClass(m, "Emulator");
	EmClass
		.def(py::init<std::optional<Matrix>, std::optional<Matrix>>())
		.def(py::init<const State&>())
		.def("set_trace", &Emulator::set_trace)

		.def("set_state", &Emulator::set_state)
		.def("get_state", &Emulator::get_state)

		.def("run_step", &Emulator::run_one_step)
		.def("run", &Emulator::run_full)
		.def("run_commands", &Emulator::run_commands)

		.def("energy", &Emulator::energy)
		.def_readonly("aborted", &Emulator::aborted)

		.def("setproblemname", &Emulator::setproblemname)
		.def("setsolutionname", &Emulator::setsolutionname)
		.def("setlogfile", &Emulator::setlogfile)
	;

	m.def("region_dimension", (int (*)(const Pos&, const Pos&)) &region_dimension);

	m.def("enum_move_commands", &enum_move_commands);

	static py::exception<base_error> base_exc(m, "SimulatorException");
	py::register_exception_translator([](std::exception_ptr p) {
	    try {
	        if (p) std::rethrow_exception(p);
	    } catch (const base_error &e) {
	        base_exc(e.what());
	    }
	});
}
