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
	bool active;

	Bot(uint8_t bid);
	Bot(uint8_t bid, Pos position, std::vector<uint8_t> seeds, bool active);
	Bot(const Bot&);
	Bot& operator=(const Bot&);
};


class State {
public:
	int R;
	Matrix matrix;
	Matrix target;

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
//	State(const State& S);
	void set_default_bots();

	bool getbit(const Pos& p) const;
	void setbit(const Pos& p, bool value);

	bool assert_well_formed();

	int count_active();
	std::string validate_command(Bot* b, std::shared_ptr<Command> cmd, bool save);
	// void validate_state();
	// void validate_floating();
	void add_passive_energy();

	void run();

	bool __getitem__(const Pos& p) const;
	void __setitem__(const Pos& p, bool value);

	// auxiliaries for move validations
	std::vector<Pos> volatiles;
	std::vector<Pos> filled;
	std::vector<unsigned> fissioned;

};


class Emulator {
public:
	State S;
	int time_step;
	std::vector<std::shared_ptr<Command>> trace;
	unsigned tracepointer;
	std::unique_ptr<Logger> logger;
	bool aborted;

	Emulator(std::optional<Matrix> src, std::optional<Matrix> tgt);
	Emulator(const State& S);

	void set_trace(std::vector<std::shared_ptr<Command>> newtrace);
	void set_state(State S);
	State get_state();

    bool steptrace_is_complete();
    std::string check_command(std::shared_ptr<Command>);
    void add_command(std::shared_ptr<Command>);
    std::string check_add_command(std::shared_ptr<Command>);

	void run_one_step();
	void run_full();
	void run_commands(std::vector<std::shared_ptr<Command>> newtrace);

	bool src_matches_tgt();

	int64_t energy();


	// piping logger options
	void setproblemname(std::string);
	void setsolutionname(std::string);
	void setlogfile(std::string);

private:
	unsigned unchecked;
	unsigned botindex;		// bots starting from bots[botindex] have no checked trace
	Bot* nextbot();

	void reset_assumptions();
	void validate_one_step();
	std::string check_command_inner(std::shared_ptr<Command>, bool save);

};

#endif