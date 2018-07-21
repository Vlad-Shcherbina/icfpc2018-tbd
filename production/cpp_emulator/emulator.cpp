#include <fstream>
#include <iostream>
#include <cassert>
#include <memory>
#include "emulator.h"
#include "commands.h"

using std::vector;
using std::string;
using std::unique_ptr;

const int MAXBOTNUMBER = 20;

/*======================== BOT ==========================*/

Bot::Bot(unsigned char pid, Pos position, vector<unsigned char> seeds, bool active)
: pid(pid)
, position(position)
, seeds(seeds)
, active(active)
{ }


void Bot::set_volatiles(Emulator* field) {
	if (!command) {
		// TODO: report
		assert (false);
	}
	(*command).set_volatiles(this, field);
}


void Bot::execute(Emulator* field) {
	assert (command);
	(*command).execute(this, field);
}



/*====================== EMULATOR =======================*/

Emulator::Emulator() {
	energy = 0;
	high_harmonics = false;
	R = 0;

	tracepointer = 0;
	volatile_violation = false;
	time_step = 0;
	halted = 0;
}


void Emulator::read_model(string filename) {
	std::ifstream f(filename, std::ios::binary);
	f >> std::noskipws;
	unsigned char c;
	f >> c;
	R = (int)c;
	model = vector<unsigned char>();
	while (f >> c) model.push_back(c);
	f.close();

	Pos p(0, 0, 0);
	bots.push_back(Bot(1, p, vector<unsigned char>(), true));
	vector<unsigned char> seeds;
	for (unsigned char i = 2; i <= MAXBOTNUMBER; i++) {
		bots[0].seeds.push_back(i);
		bots.push_back(Bot(i, p, vector<unsigned char>(), false));
	}

	int bytes = (R * R * R + 7) / 8;
	matrix = vector<unsigned char>(bytes, 0);
	floating = vector<unsigned char>(bytes, 0);
	volatiles = vector<unsigned char>(bytes, 0);
	//std::cout << model.size() << " " << bytes << "\n";
	assert (model.size() == bytes);

}


void Emulator::read_trace(string filename) {
	std::ifstream f(filename, std::ios::binary);
	f >> std::noskipws;
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
	v[w / 8] ^= (getbit(p, v) != bit) << (w % 8);
}


int Emulator::count_active() {
	int c = 0;
	for (Bot& b : bots) c += (b.active);
	return c;
}


bool Emulator::check_state() {
	// TODO: check floatings
	for (auto& x : volatiles) x = 0;
	for (Bot& b : bots) if (b.active) b.set_volatiles(this);
	if (volatile_violation) {
		// TODO: report
		assert (false);
	}
	// TODO: handle returns
	return true;
}


void Emulator::run_commands() {
	for (Bot& b : bots) if (b.active) b.execute(this);
}


void Emulator::run(string modelfile, string tracefile) {
	// test run
	read_model(modelfile);
	read_trace(tracefile);
	while (!halted)
	{
		time_step++;
		energy += count_active() * 20 + R * R * R * (high_harmonics ? 30 : 3);
		for (Bot& b : bots) {
			if (!b.active) continue;
			b.command = Command::getnextcommand(this);
			//std::cout << (*(b.command)).__str__() << "\n";
		}
		check_state();
		run_commands();
	}
	// int countr = 0;
	// int countw = 0;
	// int countf = 0;
	// for (unsigned i = 0; i < matrix.size(); i++) {
	// 	if (matrix[i] != model[i]) countw ++;
	// 	else countr++;
	// 	if (matrix[i]) countf++;
	// }
	//std::cout << "right: " << countr << " wrong: " << countw << " full: " << countf <<
	//			 '\n' << "energy: " << energy << "\n";
}