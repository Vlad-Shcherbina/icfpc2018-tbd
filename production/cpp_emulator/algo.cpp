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


int cubic_num_components(bool bytes[27]) {
    uint8_t pools[27];
    for (uint8_t i = 0; i < 27; i++) {
        pools[i] = bytes[i] ? i : 28;
    }

    for(uint8_t x = 0; x < 3; x++) {
        for (uint8_t y = 0; y < 3; y++) {
            for (uint8_t z = 0; z < 3; z++) {
                uint8_t root_a = x * 9 + y * 3 + z;
                if (!bytes[root_a]) continue;
                
                while(pools[root_a] != root_a) root_a = pools[root_a];
                
                for (uint8_t dx = 0; dx < 2; dx++) {
                    if (x + dx > 2) continue;

                    for (uint8_t dy = 0; dy < 2; dy++) {
                        if (y + dy > 2) continue;

                        for (uint8_t dz = 0; dz < 2; dz++) {
                            if (z + dz > 2) continue;
                            if (dx + dy + dz == 0 || dx + dy + dz == 3) continue;
                            uint8_t root_b = (x+dx) * 9 + (y+dy) * 3 + (z+dz);
                            if (!bytes[(x+dx) * 9 + (y+dy) * 3 + (z+dz)]) continue;

                            while(pools[root_b] != root_b) root_b = pools[root_b];
                            if (root_a == root_b) continue;
                            pools[root_b] = root_a;

                        }
                    }
                }
            }
        }
    }

    int count = 0;
    for (uint8_t i = 0; i < 27; i++) {
        if (pools[i] == i) count++;
    }
    std::cout << " " << count << "\n";
    return count;
}

bool can_safely_remove_center(bool bytes[27]) {
    if (!bytes[13]) return true;
    int components = cubic_num_components(bytes);
    bytes[13] = false;
    return cubic_num_components(bytes) == components;
}
