/*
cl /EHsc /LD /O2 emulator.cpp C:\Python37\libs\python37.lib /Feemulator.pyd /I C:\Python37\include
cl emulator.cpp && emulator.exe
*/

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cassert>

using std::vector;
using std::string;



int abs(int x) {
	return x >= 0 ? x : -x;
}


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


/*----------------------------------------------------------*/


int main() {
	// testing purposes only
	Pos a(1, 2, 3);
	Pos b(3, 2, 1);
	Diff d = a - b;
	b += d;
	a = b + d;
	std::cout << (int)a.x;
}