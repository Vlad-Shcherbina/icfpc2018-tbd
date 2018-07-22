#ifndef __EMULATOR_H_INCLUDED__
#define __EMULATOR_H_INCLUDED__

#include <vector>
#include <string>
#include <bitset>

#include "coordinates.h"

struct Command;
class State;
class Logger;

class Bot {
public:
	unsigned char bid;
	Pos position;
	std::vector<unsigned char> seeds;
	std::unique_ptr<Command> command;
	bool active;

	Bot();
	Bot(const Bot&);
	Bot& operator=(const Bot&);
	Bot(unsigned char bid, Pos position, std::vector<unsigned char> seeds, bool active);
	void set_volatiles(State* field);
	void execute(State* field);
};


class State {
public:
	int64_t energy;
	bool high_harmonics;
	std::vector<unsigned char> matrix;
	int R;
	std::vector<Bot> bots;
	bool halted;

	//std::vector<unsigned char> floating;
	std::vector<unsigned char> target;
	std::vector<unsigned char> volatiles;

	State();
	State(unsigned char R);
	void set_size(unsigned char R);
	void set_initials();
	void set_default_bots();
	void set_state(unsigned char R,
				   bool high_harmonics,
				   int64_t energy,
				   std::vector<unsigned char> matrix,
				   std::vector<Bot> bots);

	bool getbit(const Pos& p) const;
	void setbit(const Pos& p, bool value);
	bool getbit(const Pos& p, const std::vector<unsigned char>& v) const;
	void setbit(const Pos& p, bool value, std::vector<unsigned char>& v);

	bool assert_well_formed();

	int count_active();
	void validate_step();
	void run_commands();
	void add_passive_energy();

};


class Emulator {
public:
	State S;
	int time_step;
	std::vector<unsigned char> trace;
	unsigned tracepointer;
	std::unique_ptr<Logger> logger;
	bool aborted;

	
	Emulator();

	void load_model(std::string filename, char dest);
	void set_model(std::vector<unsigned char> bytes, char dest);

	void load_trace(std::string filename);
	void set_trace(std::vector<unsigned char> bytes);

	void set_state(State S);
	State get_state();

	unsigned char getcommand();
	void run_one_step();
	void run_all();
	void run_given(std::vector<unsigned char> newtrace);
	void load(std::string modelfile, std::string tracefile);

	int64_t energy();

	// piping logger options
	void setproblemname(std::string);
	void setsolutionname(std::string);
	void setlogfile(std::string);



private:
	std::vector<unsigned char>* choose_matrix(char c);
};

#endif