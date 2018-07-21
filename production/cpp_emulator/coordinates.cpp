#include "coordinates.h"

using std::string;


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

bool Diff::is_adjacent() const { return mlen() == 1; }
bool Diff::is_near() const { return (clen() == 1) && (mlen() == 1 || mlen() == 2); }
bool Diff::is_far() const { return (clen() > 0) && (clen() <= 30); }
bool Diff::is_linear() const { return ((dx == 0) + (dy == 0) + (dz == 0)) == 2; }
bool Diff::is_short() const { return is_linear() && mlen() <= 5; }
bool Diff::is_long() const {return is_linear() && mlen() <= 15; }
bool Diff::operator==(const Diff& other) const { return dx == other.dx && dy == other.dy && dz == other.dz; }
bool Diff::operator!=(const Diff& other) const { return !(*this == other); }

string Diff::__str__() const {
	return "[" + std::to_string(dx) + ", " + std::to_string(dy) + ", " + std::to_string(dz) + "]";
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

bool Pos::is_inside(int R) const { return x >= 0 && x < R && y >= 0 && y < R && z >= 0 && z < R; }
Diff Pos::operator-(const Pos& other) const { return Diff(x - other.x, y - other.y, z - other.z); }
Pos Pos::operator+(const Diff& d) const { return Pos(x + d.dx, y + d.dy, z + d.dz); }
Pos Pos::operator-(const Diff& d) const { return Pos(x - d.dx, y - d.dy, z - d.dz); }
bool Pos::operator==(const Pos& other) const { return x == other.x && y == other.y && z == other.z; }
bool Pos::operator!=(const Pos& other) const { return !(*this == other); }

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

string Pos::__str__() const {
	return "[" + std::to_string(x) + ", " + std::to_string(y) + ", " + std::to_string(z) + "]";
}


/*======================== OTHER ========================*/

int region_dimension(const Diff& d) {
	return (d.dx != 0) + (d.dy != 0) + (d.dz != 0);
}

int region_dimension(const Pos& a, const Pos& b) {
	return region_dimension(b - a);
}
