#ifndef __EMULATOR_H_INCLUDED__
#define __EMULATOR_H_INCLUDED__

#include <vector>
#include <string>
#include <optional>

#include "coordinates.h"
#include "matrix.h"

struct Command;
class State;
class Logger;

class Bot {
public:
	uint8_t bid;
	Pos position;
	std::vector<uint8_t> seeds;
	std::unique_ptr<Command> command;
	bool active;

	Bot();
	Bot(const Bot&);
	Bot& operator=(const Bot&);
	Bot(uint8_t bid, Pos position, std::vector<uint8_t> seeds, bool active);
	void check_preconditions(State* field);
	void set_volatiles(State* field);
	void execute(State* field);
};


class State {
public:
	int R;
	Matrix matrix;
	Matrix target;
	Matrix volatiles;

	int64_t energy;
	bool high_harmonics;
	std::vector<Bot> bots;
	bool halted;

	State(std::optional<Matrix> src, std::optional<Matrix> tgt);
	State(std::optional<Matrix> src,
		  std::optional<Matrix> tgt,
		  bool high_harmonics,
		  int64_t energy,
		  std::vector<Bot> bots);
	State(const State& S);
	void set_default_bots();

	bool getbit(const Pos& p) const;
	void setbit(const Pos& p, bool value);

	bool assert_well_formed();

	int count_active();
	void validate_step();
	void run_commands();
	void add_passive_energy();

	bool __getitem__(const Pos& p) const;
	void __setitem__(const Pos& p, bool value);
};


class Emulator {
public:
	State S;
	int time_step;
	std::vector<uint8_t> trace;
	unsigned tracepointer;
	std::unique_ptr<Logger> logger;
	bool aborted;

	
	Emulator(std::optional<Matrix> src, std::optional<Matrix> tgt);
	Emulator(const State& S);

	void set_trace(std::vector<uint8_t> bytes);
	void set_state(State S);				// TODO: take ownership
	State get_state();

	uint8_t getcommand();
	void run_one_step();
	void run_all();
	void run_given(std::vector<uint8_t> newtrace);

	int64_t energy();

	// piping logger options
	void setproblemname(std::string);
	void setsolutionname(std::string);
	void setlogfile(std::string);
};

#endif