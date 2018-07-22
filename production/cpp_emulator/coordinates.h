#ifndef __COORDINATES_H_INCLUDED__
#define __COORDINATES_H_INCLUDED__

#include <string>

const int SHORT_DISTANCE = 5;
const int LONG_DISTANCE = 15;
const int FAR_DISTANCE = 30;

class Diff {
public:
	int dx, dy, dz;

	Diff(int dx, int dy, int dz);
	Diff(const Diff& other);
	int mlen() const;
	int clen() const;
	bool is_adjacent() const;
	bool is_near() const;
	bool is_far() const;
	bool is_linear() const;
	bool is_short() const;
	bool is_long() const;
	bool operator==(const Diff& other) const;
	bool operator!=(const Diff& other) const;
	bool operator<(const Diff& other) const;

	Diff operator+(Diff other) const {
		return Diff(dx + other.dx, dy + other.dy, dz + other.dz);
	}

	std::string __str__() const;
};


class Pos {
public:
	int x, y, z;

	Pos (int x, int y, int z);
	Pos (const Pos& other);
	bool is_inside(int R) const;
	Diff operator-(const Pos& other) const;
	Pos operator+(const Diff& d) const;
	Pos operator-(const Diff& d) const;
	bool operator==(const Pos& other) const;
	bool operator!=(const Pos& other) const;
	bool operator<(const Pos& other) const;
	Pos& operator+= (const Diff& d);
	Pos& operator-= (const Diff& d);
	std::string __str__() const;

};


int region_dimension(const Pos& a, const Pos& b);
int region_dimension(const Diff& d);

#endif