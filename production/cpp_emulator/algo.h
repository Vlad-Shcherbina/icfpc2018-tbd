#pragma once

#include "commands.h"
#include "matrix.h"
#include "coordinates.h"

#include <memory>
#include <vector>
#include <utility>
#include <optional>

std::optional<std::pair<Pos, std::vector<std::shared_ptr<Command>>>> path_to_nearest_of(
    const Matrix &obstacles, Pos src, std::vector<Pos> dsts);
