#include "algo.h"

#include "debug.h"
#include "pretty_printing.h"
#include "coordinates.h"
#include "commands.h"
#include "matrix.h"

#include <vector>
#include <memory>
#include <map>
#include <deque>
#include <functional>
#include <algorithm>

using namespace std;

vector<Diff> enum_near_diffs() {
    vector<Diff> result;
    for (int dx = -1; dx <= 1; dx++) {
        for (int dy = -1; dy <= 1; dy++) {
            for (int dz = -1; dz <= 1; dz++) {
                Diff d(dz, dy, dz);
                if (d.is_near()) {
                    result.push_back(d);
                }
            }
        }
    }
    return result;
}

map<Pos, int> near_neighbors(int R, const vector<Pos> &ps) {
    map<Pos, int> result;
    auto nds = enum_near_diffs();
    for (Diff d : nds) {
        for (Pos p : ps) {
            Pos p2 = p + d;
            if (p2.is_inside(R)) {
                result[p + d]++;
            }
        }
    }
    return result;
}

vector<Diff> enum_linear_diffs(const Matrix& m, Pos start, int max_dist) {
    vector<Diff> result;
    for (Diff dir : DIRS) {
        Pos p = start + dir;
        int dist = 1;
        while (dist <= max_dist && p.is_inside(m.R) && !m.get(p)) {
            result.push_back(p - start);
            dist++;
            p += dir;
        }
    }
    return result;
}

vector<Diff> enum_move_diffs(const Matrix& m, Pos start) {
    vector<Diff> result = enum_linear_diffs(m, start, LONG_DISTANCE);
    for (Diff sld1 : enum_linear_diffs(m, start, SHORT_DISTANCE)) {
        for (Diff sld2 : enum_linear_diffs(m, start + sld1, SHORT_DISTANCE)) {
            Diff d = sld1 + sld2;
            if (d != Diff(0, 0, 0)) {
                result.push_back(d);
            }
        }
    }
    sort(begin(result), end(result), [](Diff d1, Diff d2) { return d1.dy > d2.dy; });
    return result;
}

shared_ptr<Command> recover_move_command(const Matrix &m, Pos src, Pos dst) {
    for (Diff lld : enum_linear_diffs(m, src, LONG_DISTANCE)) {
        if (src + lld == dst) {
            return make_shared<SMove>(lld);
        }
    }
    for (Diff sld1 : enum_linear_diffs(m, src, SHORT_DISTANCE)) {
        for (Diff sld2 : enum_linear_diffs(m, src + sld1, SHORT_DISTANCE)) {
            if (src + sld1 + sld2 == dst) {
                return make_shared<LMove>(sld1, sld2);
            }
        }
    }
    return nullptr;
}

void bfs(const Matrix &m, Pos start, function<bool (Pos, const map<Pos, Pos>&)> visit) {
    assert(!m.get(start));
    map<Pos, Pos> prev;
    if (!visit(start, prev)) {
        return;
    }
    Matrix visited(m.R);
    deque<Pos> work = {{start, start}};
    visited.set(start, true);

    while (!work.empty()) {
        Pos p = work.front();
        work.pop_front();

        for (Diff d : enum_move_diffs(m, p)) {
            Pos p2 = p + d;
            if (!visited.get(p2)) {
                visited.set(p2, true);
                prev[p2] = p;
                work.push_back(p2);
                if (!visit(p2, prev)) {
                    return;
                }
            }
        }
    }
}

vector<shared_ptr<Command>> recover_path(
        const map<Pos, Pos>& prev, const Matrix &m, Pos start, Pos finish) {
    Pos p = finish;
    vector<shared_ptr<Command>> result;
    while (p != start) {
        Pos p1 = prev.at(p);
        result.push_back(recover_move_command(m, p1, p));
        p = p1;
    }
    reverse(begin(result), end(result));
    return result;
}


std::optional<std::pair<Pos, std::vector<std::shared_ptr<Command>>>> path_to_nearest_pred(
    const Matrix &obstacles, Pos src, std::function<bool(Pos)> pred) {
    optional<pair<Pos, vector<shared_ptr<Command>>>> result;
    bfs(obstacles, src, [&](Pos p, const map<Pos, Pos> &prev) {
        if (pred(p)) {
            result = make_pair(p, recover_path(prev, obstacles, src, p));
            return false;
        }
        return true;
    });
    return result;
}

optional<pair<Pos, vector<shared_ptr<Command>>>> path_to_nearest_of(
    const Matrix &obstacles, Pos src, vector<Pos> dsts) {
    optional<pair<Pos, vector<shared_ptr<Command>>>> result;
    sort(begin(dsts), end(dsts));
    return path_to_nearest_pred(obstacles, src, [&](Pos pos) {
        return binary_search(begin(dsts), end(dsts), pos);
    });
}


bool safe_to_change(const Matrix &mat, Pos pos) {
    Matrix &m = const_cast<Matrix&>(mat);

    if (!m.get(pos)) {
        if (pos.y == 0) {
            return true;
        }
        for (Diff d : DIRS) {
            Pos p = pos + d;
            if (p.is_inside(m.R) && m.get(p)) {
                return true;
            }
        }
        return false;
    }

    bool hz[27];
    for (int dx = -1; dx <= 1; dx++) {
        for (int dy = -1; dy <= 1; dy++) {
            for (int dz = -1; dz <= 1; dz++) {
                Pos p = pos + Diff(dx, dy, dz);
                hz[9 * (dx + 1) + 3 * (dy + 1) + (dz + 1)] = p.y < 0 || p.is_inside(m.R) && m.get(p);
            }
        }
    }
    if (can_safely_remove_center(hz)) {
        return true;
    }

    m.set(pos, false);
    if (m.num_full == m.num_grounded_voxels()) {
        m.set(pos, true);
        return true;
    } else {
        m.set(pos, true);
        return false;
    }
}

std::optional<std::pair<Pos, std::vector<std::shared_ptr<Command>>>> path_to_nearest_safe_change_point(
        const Matrix &obstacles, Pos start, const Matrix &src, const Matrix &dst) {
    auto nds = enum_near_diffs();
    return path_to_nearest_pred(obstacles, start, [&](Pos pos) {
        for (Diff nd : nds) {
            Pos p = pos + nd;
            if (!p.is_inside(src.R)) {
                continue;
            }
            if (src.get(p) == dst.get(p)) {
                continue;
            }
            if (!safe_to_change(src, p)) {
                continue;
            }
            return true;
        }
        return false;
    });
}


void _join_roots(uint8_t * pools, uint8_t a, uint8_t b) {
    while (pools[a] != a) a = pools[a];
    while (pools[b] != b) b = pools[b];
    pools[b] = a;

}

int cubic_num_components(bool bytes[27]) {
    uint8_t pools[27];
    for (uint8_t i = 0; i < 27; i++) {
        pools[i] = bytes[i] ? i : 28;
    }

    for(uint8_t x = 0; x < 3; x++) {
        for (uint8_t y = 0; y < 3; y++) {
            for (uint8_t z = 0; z < 3; z++) {
                uint8_t root = x * 9 + y * 3 + z;
                if (!bytes[root]) continue;

                if (x != 2 && bytes[root+9]) 
                    _join_roots(pools, root, root+9);
                if (y != 2 && bytes[root+3])
                    _join_roots(pools, root, root+3);
                if (z != 2 && bytes[root+1]) 
                    _join_roots(pools, root, root+1);
            }
        }
    }

    int count = 0;
    for (uint8_t i = 0; i < 27; i++) if (pools[i] == i) count++;
    return count;
}

int cubic_num_components2(bool q[27]) {
    bool data[27];
    copy(q, q + 27, data);
    int result = 0;
    for (int i = 0; i < 27; i++) {
        if (!data[i]) {
            continue;
        }
        result++;
        Pos p = Pos::unpack(3, i);
        vector<Pos> work = {p};
        while (!work.empty()) {
            Pos p = work.back();
            work.pop_back();
            if (!p.is_inside(3) || !data[p.pack(3)]) {
                continue;
            }
            data[p.pack(3)] = false;
            for (Diff d : DIRS) {
                work.push_back(p + d);
            }
        }
    }
    return result;
}

bool can_safely_remove_center(bool bytes[27]) {
    if (!bytes[13]) return true;
    int components = cubic_num_components2(bytes);
    bytes[13] = false;
    return cubic_num_components2(bytes) == components;
}
