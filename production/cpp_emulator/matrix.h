#pragma once

#include "coordinates.h"

#include <vector>
#include <stdint.h>
#include <assert.h>
#include <algorithm>

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

    int count_inside_region(Pos p1, Pos p2) const {
        int x1 = std::min(p1.x, p2.x);
        int x2 = std::max(p1.x, p2.x);
        int y1 = std::min(p1.y, p2.y);
        int y2 = std::max(p1.y, p2.y);
        int z1 = std::min(p1.z, p2.z);
        int z2 = std::max(p1.z, p2.z);
        int cnt = 0;
        for (int x = x1; x <= x2; x++) {
            for (int y = y1; y <= y2; y++) {
                for (int z = z1; z <= z2; z++) {
                    if (get(Pos(x, y, z))) {
                        cnt++;
                    }
                }
            }
        }
        return cnt;
    }

private:
    Matrix(const std::vector<uint8_t> &raw)
        : R(raw.at(0)), data(raw.begin() + 1, raw.end()) {
        assert((int)data.size() == (R * R * R + 7) / 8);
    }
};
