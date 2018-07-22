#pragma once

#include "commands.h"

#include <memory>
#include <vector>

std::vector<std::unique_ptr<Command>> enum_move_commands();
