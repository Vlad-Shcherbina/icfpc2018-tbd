#ifndef __COORDINATES_H_INCLUDED__
#define __COORDINATES_H_INCLUDED__

#include <string>
#include <vector>
#include <ostream>
#include <assert.h>

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
	int operator[](int axis) const;
	static Diff byaxis(int axis, int value);

	Diff operator+(Diff other) const {
		return Diff(dx + other.dx, dy + other.dy, dz + other.dz);
	}

	Diff operator*(int value) const {
		return Diff(dx * value, dy * value, dz * value);
	}

	std::string __repr__() const;
};

inline std::ostream& operator<<(std::ostream &out, Diff d) {
	return out << d.__repr__().c_str();
}

class Pos {
public:
	int x, y, z;

	Pos () : x(0), y(0), z(0) {}
	Pos (int x, int y, int z);
	Pos (const Pos& other);
	bool is_inside(int R) const;
	std::vector<Pos> enum_adjacent(int R) const;
	Diff operator-(const Pos& other) const;
	Pos operator+(const Diff& d) const;
	Pos operator-(const Diff& d) const;
	bool operator==(const Pos& other) const;
	bool operator!=(const Pos& other) const;
	bool operator<(const Pos& other) const;
	Pos& operator+= (const Diff& d);
	Pos& operator-= (const Diff& d);
	std::string __repr__() const;
	int __hash__() const;

	int pack(int R) const {
		assert(is_inside(R));
		return x * R * R + y * R + z;
	}

	static Pos unpack(int R, int idx) {
		assert(R <= 250);
		assert(idx >= 0);
		assert(idx < R * R * R);
		return Pos(
			idx / (R * R),
			idx / R % R,
			idx % R);
	}
};


inline std::ostream& operator<<(std::ostream &out, Pos d) {
	return out << d.__repr__().c_str();
}

int region_dimension(const Pos& a, const Pos& b);
int region_dimension(const Diff& d);

const Diff DIRS[] = {
    Diff(1, 0, 0),
    Diff(-1, 0, 0),
    Diff(0, 1, 0),
    Diff(0, -1, 0),
    Diff(0, 0, 1),
    Diff(0, 0, -1),
};

#endif