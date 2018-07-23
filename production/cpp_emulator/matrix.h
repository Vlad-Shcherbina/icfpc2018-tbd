#pragma once

#include "coordinates.h"

#include <vector>
#include <stdint.h>
#include <assert.h>
#include <algorithm>

class Matrix {
public:
    int num_full = 0;
    int R;
private:
    std::vector<uint8_t> data;
public:
    Matrix(int R) : R(R) {
        assert(0 <= R && R <= 250);
        data.assign((R * R * R + 7) / 8, 0);
    }

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
        if (data[w / 8] & (1 << (w % 8))) {
            if (!value) {
                num_full--;
                data[w / 8] &= ~(1 << (w % 8));
            }
        } else {
            if (value) {
                num_full++;
                data[w / 8] |= 1 << (w % 8);
            }
        }
    }

    bool operator==(const Matrix &other) const {
        assert(R == other.R);
        int q = R * R * R / 8;
        for (int i = 0; i < q; i++) {
            if (data[i] != other.data[i]) {
                return false;
            }
        }
        int garbage = (int)data.size() * 8 - R * R * R;
        if (garbage) {
            int tail = 8 - garbage;
            uint8_t mask = (1 << tail) - 1;
            if ((data.back() & mask) != (other.data.back() & mask)) {
                return false;
            }
        }
        return true;
    }

    int num_grounded_voxels() const {
        return (int)grounded_voxels().size();
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
            for (Diff d : DIRS) {
                work.push_back(p + d);
            }
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
        for (int x = 0; x < R; x++) {
            for (int y = 0; y < R; y++) {
                for (int z = 0; z < R; z++) {
                    if (get(Pos(x, y, z))) {
                        num_full++;
                    }
                }
            }
        }
    }
};
