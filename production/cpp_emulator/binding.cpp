#include <pybind11/stl.h>
#include <pybind11/pybind11.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cassert>

#include "coordinates.h"
#include "emulator.h"
#include "logger.h"
#include "algo.h"
#include "tests.h"

using std::vector;
using std::string;
using std::unique_ptr;
using std::make_unique;

namespace py = pybind11;

void init_ex2(py::module &);

PYBIND11_MODULE(emulator, m) {
	m.doc() = "C++ Emulator";

	init_ex2(m);

	py::class_<Bot> BotClass(m, "Bot");
	BotClass
		.def(py::init<uint8_t>())
		.def(py::init<uint8_t, Pos, std::vector<uint8_t>, bool>())
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
		.def("src_matches_tgt", &Emulator::src_matches_tgt)

		.def("steptrace_is_complete", &Emulator::steptrace_is_complete)
	    .def("check_command", &Emulator::check_command)
    	.def("add_command", &Emulator::add_command)
    	.def("check_add_command", &Emulator::check_add_command)

		.def("setproblemname", &Emulator::setproblemname)
		.def("setsolutionname", &Emulator::setsolutionname)
		.def("setlogfile", &Emulator::setlogfile)
	;

	m.def("region_dimension", (int (*)(const Pos&, const Pos&)) &region_dimension);

	m.def("enum_near_diffs", &enum_near_diffs);
	m.def("near_neighbors", &near_neighbors);
	m.def("path_to_nearest_of", &path_to_nearest_of);
	m.def("path_to_nearest_safe_change_point", &path_to_nearest_safe_change_point);
	m.def("safe_to_change", &safe_to_change);

	m.def("run_tests", &run_tests);

	static py::exception<base_error> base_exc(m, "SimulatorException");
	py::register_exception_translator([](std::exception_ptr p) {
	    try {
	        if (p) std::rethrow_exception(p);
	    } catch (const base_error &e) {
	        base_exc(e.what());
	    }
	});
}
