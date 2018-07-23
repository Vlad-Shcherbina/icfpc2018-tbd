#pragma once

#include "commands.h"
#include "matrix.h"
#include "coordinates.h"

#include <memory>
#include <vector>
#include <utility>
#include <optional>
#include <map>

std::vector<Diff> enum_near_diffs();

std::map<Pos, int> near_neighbors(int R, const std::vector<Pos> &ps);

std::optional<std::pair<Pos, std::vector<std::shared_ptr<Command>>>> path_to_nearest_of(
    const Matrix &obstacles, Pos src, std::vector<Pos> dsts);

bool safe_to_change(Matrix &matrix, Pos pos);