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

optional<pair<Pos, vector<shared_ptr<Command>>>> path_to_nearest_of(
    const Matrix &obstacles, Pos src, vector<Pos> dsts) {
    optional<pair<Pos, vector<shared_ptr<Command>>>> result;
    sort(begin(dsts), end(dsts));
    bfs(obstacles, src, [&](Pos p, const map<Pos, Pos> &prev) {
        if (binary_search(begin(dsts), end(dsts), p)) {
            result = make_pair(p, recover_path(prev, obstacles, src, p));
            return false;
        }
        return true;
    });
    return result;
}

bool safe_to_change(Matrix &matrix, Pos pos) {
    
}