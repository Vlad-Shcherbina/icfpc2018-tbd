#ifndef __EMULATOR_H_INCLUDED__
#define __EMULATOR_H_INCLUDED__

#include <vector>
#include <string>
#include <bitset>

#include "coordinates.h"

struct Command;
class State;

class Bot {
public:
	unsigned char pid;
	Pos position;
	std::vector<unsigned char> seeds;
	std::unique_ptr<Command> command;
	bool active;

	Bot(unsigned char pid, Pos position, std::vector<unsigned char> seeds, bool active);
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


	std::vector<unsigned char> floating;
	std::vector<unsigned char> model;
	std::vector<unsigned char> volatiles;
	bool volatile_violation;

	State();
	State(unsigned char R);

	void read_model(std::string filename);

	bool getmatrixbit(const Pos& p) const;
	void setmatrixbit(const Pos& p, bool value);
	bool getbit(const Pos& p, const std::vector<unsigned char>& v) const;
	void setbit(const Pos& p, bool value, std::vector<unsigned char>& v);

	bool assert_well_formed();

	int count_active();
	bool validate_step();
	void run_commands();
	void add_passive_energy();

private:
	void set_initials();
	void set_matrices(unsigned char R);
};


class Emulator {
public:
	State S;
	int time_step;
	std::vector<unsigned char> trace;
	int tracepointer;
	
	Emulator();

	void read_trace(std::string filename);
	unsigned char getcommand();
	void run_one_step();
	void run_all(std::string modelfile, std::string tracefile);
	void run_given_step(std::vector<unsigned char> newtrace);
	void load(std::string modelfile, std::string tracefile);

	int64_t energy();

};


#endif