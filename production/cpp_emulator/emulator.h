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
	Bot(	unsigned char pid,
			unsigned char x,
			unsigned char y,
			unsigned char z,
			std::vector<unsigned char> seeds,
			bool active);
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
	bool volatile_violation;

	State();
	State(unsigned char R);
	void set_size(unsigned char R);

	bool getbit(const Pos& p) const;
	void setbit(const Pos& p, bool value);
	bool getbit(const Pos& p, const std::vector<unsigned char>& v) const;
	void setbit(const Pos& p, bool value, std::vector<unsigned char>& v);

	bool assert_well_formed();

	int count_active();
	bool validate_step();
	void run_commands();
	void add_passive_energy();

private:
	void set_initials();
};


class Emulator {
public:
	State S;
	int time_step;
	std::vector<unsigned char> trace;
	unsigned tracepointer;

	Emulator();

	void load_model(std::string filename, char dest);
	void set_model(std::vector<unsigned char> bytes, char dest);

	void load_trace(std::string filename);
	void set_trace(std::vector<unsigned char> bytes);

	unsigned char getcommand();
	void run_one_step();
	void run_all();
	void run_given(std::vector<unsigned char> newtrace);
	void load(std::string modelfile, std::string tracefile);

	void reconstruct_state(
			unsigned char R,
			std::vector<unsigned char> matrix,
			bool harmonics,
			int64_t energy);

	void add_bot(unsigned char pid,
				 unsigned char x,
				 unsigned char y,
				 unsigned char z,
				 std::vector<unsigned char> seeds);

	std::vector<unsigned char> get_state();
	std::vector<unsigned char> get_bots();


	int64_t energy();
	int count_active();

private:
	std::vector<unsigned char>* choose_matrix(char c);
};


#endif