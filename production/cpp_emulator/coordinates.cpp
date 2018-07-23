#include "coordinates.h"

#include <tuple>
#include <vector>

using std::string;
using std::make_tuple;


/*======================== DIFF =========================*/

Diff::Diff(int dx, int dy, int dz)
: dx(dx)
, dy(dy)
, dz(dz)
{}

Diff::Diff(const Diff& other)
: dx(other.dx)
, dy(other.dy)
, dz(other.dz)
{}

int Diff::mlen() const { return abs(dx) + abs(dy) + abs(dz); }

int Diff::clen() const {
	int x = abs(dx);
	int y = abs(dy);
	int z = abs(dz);
	return (x >= y && x >= z) ? x : ((y >= z) ? y : z);
}

bool Diff::is_adjacent() const {
	return mlen() == 1;
}

bool Diff::is_near() const {
	return (clen() == 1) && (mlen() == 1 || mlen() == 2);
}

bool Diff::is_far() const {
	return (clen() > 0) && (clen() <= FAR_DISTANCE);
}

bool Diff::is_linear() const {
	return ((dx == 0) + (dy == 0) + (dz == 0)) == 2;
}

bool Diff::is_short() const {
	return is_linear() && mlen() <= SHORT_DISTANCE;
}

bool Diff::is_long() const {
	return is_linear() && mlen() <= LONG_DISTANCE;
}

bool Diff::operator==(const Diff& other) const {
	return dx == other.dx && dy == other.dy && dz == other.dz;
}

bool Diff::operator!=(const Diff& other) const {
	return !(*this == other);
}

bool Diff::operator<(const Diff& other) const {
	return make_tuple(dx, dy, dz) < make_tuple(other.dx, other.dy, other.dz);
}

int Diff::operator[](int axis) const {
	switch (axis) {
		case 0: return dx;
		case 1: return dy;
		case 2: return dz;
		default: throw std::invalid_argument("axis");
	}
}

Diff Diff::byaxis(int axis, int value) {
	switch (axis) {
		case 0: return Diff(value, 0, 0);
		case 1: return Diff(0, value, 0);
		case 2: return Diff(0, 0, value);
		default: throw std::invalid_argument("axis");
	}
}

string Diff::__repr__() const {
	return "Diff(" + std::to_string(dx) + ", " + std::to_string(dy) + ", " + std::to_string(dz) + ")";
}


/*========================= POS =========================*/

Pos::Pos(int x, int y, int z) {
	this->x = x;
	this->y = y;
	this->z = z;
}

Pos::Pos(const Pos& other) {
	this->x = other.x;
	this->y = other.y;
	this->z = other.z;
}

bool Pos::is_inside(int R) const {
	return x >= 0 && x < R &&
	       y >= 0 && y < R &&
	       z >= 0 && z < R;
}

std::vector<Pos> Pos::enum_adjacent(int R) const {
	std::vector<Pos> res;
	if (x > 0) {
		res.emplace_back(x - 1, y, z);
	}
	if (y > 0) {
		res.emplace_back(x, y - 1, z);
	}
	if (z > 0) {
		res.emplace_back(x, y, z - 1);
	}
	if (x + 1 < R) {
		res.emplace_back(x + 1, y, z);
	}
	if (y + 1 < R) {
		res.emplace_back(x, y + 1, z);
	}
	if (z + 1 < R) {
		res.emplace_back(x, y, z + 1);
	}
	return res;
}

Diff Pos::operator-(const Pos& other) const {
	return Diff(x - other.x, y - other.y, z - other.z);
}

Pos Pos::operator+(const Diff& d) const {
	return Pos(x + d.dx, y + d.dy, z + d.dz);
}

Pos Pos::operator-(const Diff& d) const {
	return Pos(x - d.dx, y - d.dy, z - d.dz);
}

bool Pos::operator==(const Pos& other) const {
	return x == other.x && y == other.y && z == other.z;
}

bool Pos::operator!=(const Pos& other) const {
	return !(*this == other);
}

bool Pos::operator<(const Pos& other) const {
	return make_tuple(x, y, z) < make_tuple(other.x, other.y, other.z);
}

Pos& Pos::operator+= (const Diff& d) {
	x += d.dx;
	y += d.dy;
	z += d.dz;
	return *this;
}

Pos& Pos::operator-= (const Diff& d) {
	x -= d.dx;
	y -= d.dy;
	x -= d.dz;
	return *this;
}

string Pos::__repr__() const {
	return "Pos(" + std::to_string(x) + ", " + std::to_string(y) + ", " + std::to_string(z) + ")";
}

int Pos::__hash__() const {
	return x ^ (y << 8) ^ (z << 16);
}

/*======================== OTHER ========================*/

int region_dimension(const Diff& d) {
	return (d.dx != 0) + (d.dy != 0) + (d.dz != 0);
}

int region_dimension(const Pos& a, const Pos& b) {
	return region_dimension(b - a);
}
