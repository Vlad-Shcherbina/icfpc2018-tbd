#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cassert>
#include <pybind11/stl.h>
#include <pybind11/pybind11.h>

using std::vector;
using std::string;



// int abs(int x) { return (x >= 0) ? x : -x; }


class Diff {

public:
	int dx, dy, dz;

	Diff(int dx, int dy, int dz) {
		assert(dx > -250 && dy > -250 && dz > -250 && dx < 250 && dy < 250 && dz < 250);
		this->dx = dx;
		this->dy = dy;
		this->dz = dz;
	}

	int mlen() const { return abs(dx) + abs(dy) + abs(dz); }

	int clen() const {
		int x = abs(dx);
		int y = abs(dy);
		int z = abs(dz);
		return (x >= y && x >= z) ? x : ((y >= z) ? y : z);
	}

	bool is_adjacent() const { return mlen() == 1; }
	bool is_near() const { return (clen() == 1) && (mlen() == 1 || mlen() == 2); }
	bool is_linear() const { return ((dx == 0) + (dy == 0) + (dz == 0)) == 2; }
	bool is_short() const { return is_linear() && mlen() <= 5; }
	bool is_long() const {return is_linear() && mlen() <= 15; }

};


/*----------------------------------------------------------*/

class Pos {
public:
	int x, y, z;

	Pos (int x, int y, int z) {
		assert (x >= 0 && y >= 0 && z >= 0 && x < 250 && y < 250 && z < 250);
		this->x = x;
		this->y = y;
		this->z = z;
	}

	Diff operator-(const Pos& other) { return Diff(x - other.x, y - other.y, z - other.z); }
	Pos operator+(const Diff& d) const { return Pos(x + d.dx, y + d.dy, z + d.dz); }
	Pos operator-(const Diff& d) const { return Pos(x - d.dx, y - d.dy, z - d.dz); }

	Pos& operator+= (const Diff& d) {
		x += d.dx;
		y += d.dy;
		x += d.dz;
		return *this;
	}

	Pos& operator-= (const Diff& d) {
		x -= d.dx;
		y -= d.dy;
		x -= d.dz;
		return *this;
	}

};


/*----------------------- BINDING --------------------------*/


namespace py = pybind11;
PYBIND11_MODULE(cpp_emulator, m) {
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
	;

	py::class_<Pos> PosClass(m, "Pos");
	PosClass
		.def(py::init<int, int, int>())
	;

}
