#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>

#include "coordinates.h"
#include "matrix.h"
#include "commands.h"

namespace py = pybind11;

void init_ex2(py::module &m) {
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
		.def("__getitem__", &Diff::operator[], py::is_operator())
		.def("byaxis", &Diff::byaxis)
		.def("__mul__", &Diff::operator*, py::is_operator())
	;

	py::class_<Pos> PosClass(m, "Pos");
	PosClass
		.def(py::init<int, int, int>())
		.def(py::self - py::self)
		.def("is_inside_matrix", &Pos::is_inside)
		.def("enum_adjacent", &Pos::enum_adjacent)
		.def("__add__", &Pos::operator+, py::is_operator())
		.def("__iadd__", &Pos::operator+=, py::is_operator())
		.def(py::self == py::self)
		.def(py::self != py::self)
		.def(py::self < py::self)
		.def("__hash__", &Pos::__hash__)
		.def("__repr__", &Pos::__repr__)
		.def("pack", &Pos::pack)
		.def("unpack", &Pos::unpack)
		.def("is_inside", &Pos::is_inside)
		.def_readonly("x", &Pos::x)
		.def_readonly("y", &Pos::y)
		.def_readonly("z", &Pos::z)
	;

	py::class_<Matrix>(m, "Matrix")
		.def(py::init<int>())
		.def(py::init<const Matrix&>())
		.def("parse", &Matrix::parse)
		.def_readonly("num_full", &Matrix::num_full)
		.def_readonly("R", &Matrix::R)
		.def("__getitem__", &Matrix::get)
		.def("__setitem__", &Matrix::set)
		.def(py::self == py::self)
		.def("num_grounded_voxels", &Matrix::num_grounded_voxels)
		.def("grounded_voxels", &Matrix::grounded_voxels)
		.def("count_inside_region", &Matrix::count_inside_region)
	;

	// TODO
	py::class_<Command, std::shared_ptr<Command>>(m, "Command")
	;
	py::class_<Halt, std::shared_ptr<Halt>, Command>(m, "Halt")
		.def(py::init<>())
		.def("__repr__", &Halt::__repr__)
	;
	py::class_<Wait, std::shared_ptr<Wait>, Command>(m, "Wait")
		.def(py::init<>())
		.def("__repr__", &Wait::__repr__)
	;
	py::class_<Flip, std::shared_ptr<Flip>, Command>(m, "Flip")
		.def(py::init<>())
		.def("__repr__", &Flip::__repr__)
	;
	py::class_<SMove, std::shared_ptr<SMove>, Command>(m, "SMove")
		.def(py::init<Diff>())
		.def("__repr__", &SMove::__repr__)
		.def_readonly("lld", &SMove::lld)
		.def("move_offset", &Halt::move_offset)
	;
	py::class_<LMove, std::shared_ptr<LMove>, Command>(m, "LMove")
		.def(py::init<Diff, Diff>())
		.def("__repr__", &LMove::__repr__)
		.def_readonly("sld1", &LMove::sld1)
		.def_readonly("sld2", &LMove::sld2)
		.def("move_offset", &Halt::move_offset)
	;
	py::class_<FusionP, std::shared_ptr<FusionP>, Command>(m, "FusionP")
		.def(py::init<Diff>())
		.def("__repr__", &FusionP::__repr__)
		.def_readonly("nd", &FusionP::nd)
	;
	py::class_<FusionS, std::shared_ptr<FusionS>, Command>(m, "FusionS")
		.def(py::init<Diff>())
		.def("__repr__", &FusionS::__repr__)
		.def_readonly("nd", &FusionS::nd)
	;
	py::class_<Fission, std::shared_ptr<Fission>, Command>(m, "Fission")
		.def(py::init<Diff, unsigned>())
		.def("__repr__", &Fission::__repr__)
		.def_readonly("nd", &Fission::nd)
		.def_readonly("m", &Fission::m)
	;
	py::class_<Fill, std::shared_ptr<Fill>, Command>(m, "Fill")
		.def(py::init<Diff>())
		.def("__repr__", &Fill::__repr__)
		.def_readonly("nd", &Fill::nd)
	;
	py::class_<Void, std::shared_ptr<Void>, Command>(m, "Void")
		.def(py::init<Diff>())
		.def("__repr__", &Void::__repr__)
		.def_readonly("nd", &Void::nd)
	;
	py::class_<GFill, std::shared_ptr<GFill>, Command>(m, "GFill")
		.def(py::init<Diff, Diff>())
		.def("__repr__", &GFill::__repr__)
		.def_readonly("nd", &GFill::nd)
		.def_readonly("fd", &GFill::fd)
	;
	py::class_<GVoid, std::shared_ptr<GVoid>, Command>(m, "GVoid")
		.def(py::init<Diff, Diff>())
		.def("__repr__", &GVoid::__repr__)
		.def_readonly("nd", &GVoid::nd)
		.def_readonly("fd", &GVoid::fd)
	;
}
