#pragma once

#include "commands.h"
#include "matrix.h"
#include "coordinates.h"

#include <memory>
#include <vector>
#include <utility>
#include <optional>
#include <map>
#include <functional>

std::vector<Diff> enum_near_diffs();

std::map<Pos, int> near_neighbors(int R, const std::vector<Pos> &ps);

std::optional<std::pair<Pos, std::vector<std::shared_ptr<Command>>>> path_to_nearest_of(
    const Matrix &obstacles, Pos src, std::vector<Pos> dsts);

std::optional<std::pair<Pos, std::vector<std::shared_ptr<Command>>>> path_to_nearest_safe_change_point(
        const Matrix &obstacles, Pos start, const Matrix &src, const Matrix &dst);

bool safe_to_change(const Matrix &matrix, Pos pos);

bool can_safely_remove_center(bool[27]);