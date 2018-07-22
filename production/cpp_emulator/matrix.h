#pragma once

#include "coordinates.h"

#include <vector>
#include <stdint.h>
#include <assert.h>

class Matrix {
private:
    std::vector<uint8_t> data;
public:
    const int R;

    Matrix(int R) : R(R), data((R * R * R + 7) / 8, 0) {}

    static Matrix parse(const std::vector<uint8_t> &raw) {
        return Matrix(raw);
    }

    bool get(Pos p) const {
        assert(p.is_inside(R));
    	int w = p.x*R*R + p.y*R + p.z;
	    return data[w / 8] & (1 << (w % 8));
    }

    void set(Pos p, bool value) {
        assert(p.is_inside(R));
    	int w = p.x*R*R + p.y*R + p.z;
	    data[w / 8] &= ~(1 << (w % 8));
        if (value) {
            data[w / 8] |= 1 << (w % 8);
        }
    }

private:
    Matrix(const std::vector<uint8_t> &raw)
        : R(raw.at(0)), data(raw.begin() + 1, raw.end()) {
        assert(data.size() == (R * R * R + 7) / 8);
    }
};
