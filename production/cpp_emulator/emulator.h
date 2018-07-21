#ifndef __EMULATOR_H_INCLUDED__
#define __EMULATOR_H_INCLUDED__

#include <vector>
#include <string>
#include "coordinates.h"

struct Command;

class Bot {
public:
	int pid;
	Pos position;
	std::vector<int> seeds;

	Bot(int pid, Pos position, std::vector<int> seeds);
	Bot();
};


class Emulator {
public:
	int energy;
	bool high_harmonics;
	std::vector<unsigned char> matrix;
	int R;
	std::vector<Bot> bots;

	std::vector<unsigned char> trace;
	int tracepointer;
	int time_step;

	std::vector<unsigned char> floating;
	std::vector<unsigned char> model;
	std::vector<unsigned char> volatiles;
	bool volatile_violation;

	Emulator();

	void read_model(std::string filename);
	void read_trace(std::string filename);
	unsigned char tracebyte();
	bool getbit(const Pos& p, const std::vector<unsigned char>& v) const;
	void setbit(const Pos& p, std::vector<unsigned char>& v, bool bit);

	void run(std::string modelfile, std::string tracefile);
};


#endif