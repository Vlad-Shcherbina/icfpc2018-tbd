#ifndef __EMULATOR_H_INCLUDED__
#define __EMULATOR_H_INCLUDED__

#include <vector>
#include <string>
#include <bitset>

#include "coordinates.h"

struct Command;
class Emulator;

class Bot {
public:
	unsigned char pid;
	Pos position;
	std::vector<unsigned char> seeds;
	std::unique_ptr<Command> command;
	bool active;

	Bot(unsigned char pid, Pos position, std::vector<unsigned char> seeds, bool active);
	void set_volatiles(Emulator* field);
	void execute(Emulator* field);
};


class Emulator {
public:
	int64_t energy;
	bool high_harmonics;
	std::vector<unsigned char> matrix;
	int R;
	std::vector<Bot> bots;

	std::vector<unsigned char> trace;
	int tracepointer;
	int time_step;
	bool halted;

	std::vector<unsigned char> floating;
	std::vector<unsigned char> model;
	std::vector<unsigned char> volatiles;
	bool volatile_violation;

	Emulator();

	bool getbit(const Pos& p, const std::vector<unsigned char>& v) const;
	void setbit(const Pos& p, std::vector<unsigned char>& v, bool bit);
	int count_active();
	void read_model(std::string filename);
	void read_trace(std::string filename);
	unsigned char tracebyte();
	bool check_state();
	void run_commands();

	void run(std::string modelfile, std::string tracefile);
};


#endif