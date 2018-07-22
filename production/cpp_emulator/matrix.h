#pragma once

#include "coordinates.h"

#include <vector>
#include <stdint.h>
#include <assert.h>

class Matrix {
public:
    int R;
private:
    std::vector<uint8_t> data;
public:
    Matrix(int R) : R(R), data((R * R * R + 7) / 8, 0) { }

    static Matrix parse(const std::vector<uint8_t> &raw) {
        return Matrix(raw);
    }

    bool get(const Pos& p) const {
        assert(p.is_inside(R));
    	int w = p.x*R*R + p.y*R + p.z;
	    return data[w / 8] & (1 << (w % 8));
    }

    void set(const Pos& p, bool value) {
        assert(p.is_inside(R));
    	int w = p.x*R*R + p.y*R + p.z;
	    data[w / 8] &= ~(1 << (w % 8));
        if (value) {
            data[w / 8] |= 1 << (w % 8);
        }
    }

    std::vector<Pos> grounded_voxels() const {
        Matrix visited(R);
        std::vector<Pos> result;
        std::vector<Pos> work;
        for (int x = 0; x < R; x++) {
            for (int z = 0; z < R; z++) {
                work.push_back(Pos(x, 0, z));
            }
        }
        while (!work.empty()) {
            Pos p = work.back();
            work.pop_back();
            if (!p.is_inside(R) || !get(p) || visited.get(p)) {
                continue;
            }
            visited.set(p, true);
            result.push_back(p);
            work.emplace_back(p.x - 1, p.y, p.z);
            work.emplace_back(p.x + 1, p.y, p.z);
            work.emplace_back(p.x, p.y - 1, p.z);
            work.emplace_back(p.x, p.y + 1, p.z);
            work.emplace_back(p.x, p.y, p.z - 1);
            work.emplace_back(p.x, p.y, p.z + 1);
        }
        return result;
    }

private:
    Matrix(const std::vector<uint8_t> &raw)
        : R(raw.at(0)), data(raw.begin() + 1, raw.end()) {
        assert((int)data.size() == (R * R * R + 7) / 8);
    }
};
