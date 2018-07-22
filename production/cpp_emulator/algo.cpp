#include "algo.h"

#include "coordinates.h"
#include "commands.h"

#include <vector>
#include <memory>

using namespace std;

vector<Diff> enum_linear_diffs(int max_distance) {
    vector<Diff> result;
    for (int i = 1; i <= max_distance; i++) {
        result.emplace_back(+i, 0, 0);
        result.emplace_back(-i, 0, 0);
        result.emplace_back(0, +i, 0);
        result.emplace_back(0, -i, 0);
        result.emplace_back(0, 0, +i);
        result.emplace_back(0, 0, -i);
    }
    return result;
}

vector<unique_ptr<Command>> enum_move_commands() {
    vector<unique_ptr<Command>> result;
    for (Diff lld : enum_linear_diffs(LONG_DISTANCE)) {
        result.push_back(make_unique<SMove>(lld));
    }
    for (Diff sld1 : enum_linear_diffs(SHORT_DISTANCE)) {
        for (Diff sld2 : enum_linear_diffs(SHORT_DISTANCE)) {
        result.push_back(make_unique<LMove>(sld1, sld2));
        }
    }
    return result;
}