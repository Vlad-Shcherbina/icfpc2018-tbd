#include <fstream>
#include <iostream>
#include <cassert>
#include <memory>
#include "emulator.h"
#include "commands.h"

using std::vector;
using std::string;
using std::unique_ptr;

/*======================== BOT ==========================*/

Bot::Bot(int pid, Pos position, vector<int> seeds)
: pid(pid)
, position(position)
, seeds(seeds)
{ }

Bot::Bot()
: pid(1)
, position(Pos(0, 0, 0)) 
{
	for (int i = 2; i <= 20; i++) this-> seeds.push_back(i);
}


/*====================== EMULATOR =======================*/

Emulator::Emulator() {
	energy = 0;
	high_harmonics = false;
	R = 0;
	bots.push_back(Bot());
	tracepointer = 0;
	volatile_violation = false;
	time_step = 0;
}


void Emulator::read_model(string filename) {
	std::ifstream f(filename, std::ios::binary);
	unsigned char c;
	f >> c;
	R = (int)c;
	while (f >> c) model.push_back(c);
	f.close();

	int bytes = (R * R * R + 7) / 8;
	matrix = vector<unsigned char>(bytes, 0);
	floating = vector<unsigned char>(bytes, 0);
	volatiles = vector<unsigned char>(bytes, 0);
}

void Emulator::read_trace(string filename) {
	std::ifstream f(filename, std::ios::binary);
	unsigned char c;
	while (f >> c) {
		trace.push_back(c);
	}
	f.close();
}

unsigned char Emulator::tracebyte() {
	return trace[tracepointer++];
}

bool Emulator::getbit(const Pos& p, const vector<unsigned char>& v) const {
	int w = p.x*R*R + p.y*R + p.z;
	// TODO: TEST!
	return v[w / 8] & (1 << (w % 8));
}

void Emulator::setbit(const Pos& p, vector<unsigned char>& v, bool bit) {
	int w = p.x*R*R + p.y*R + p.z;
	// TODO: TEST!
	v[w / 8] ^= (getbit(p, v) == bit) << (w % 8);
}


void Emulator::run(string modelfile, string tracefile) {
	// test run
	read_model(modelfile);
	read_trace(tracefile);
	for (int i = 0; i < 20; i++) {
		std::cout << i << ' ';
		unique_ptr<Command> c = Command::getnextcommand(this);
	}
}