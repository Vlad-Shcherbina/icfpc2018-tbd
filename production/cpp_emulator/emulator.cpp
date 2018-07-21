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


void Bot::set_volatiles(State* S) {
	if (!command) {
		// TODO: report
		assert (false);
	}
	(*command).set_volatiles(this, S);
}


void Bot::execute(State* S) {
	assert (command);
	(*command).execute(this, S);
}



/*====================== EMULATOR =======================*/


State::State() { 
	set_initials();
}

State::State(unsigned char R) {
	set_initials();
	set_matrices(R);
}

void State::set_initials() {
	R = 0;
	energy = 0;
	high_harmonics = false;
	volatile_violation = false;
	halted = false;
}

void State::set_matrices(unsigned char R) {
	this->R = R;
	int bytes = (R * R * R + 7) / 8;
	matrix = vector<unsigned char>(bytes, 0);
	floating = vector<unsigned char>(bytes, 0);
	volatiles = vector<unsigned char>(bytes, 0);
}

void State::read_model(string filename) {
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

	set_matrices(R);
	assert (model.size() == matrix.size());
}


bool State::getmatrixbit(const Pos& p) const {
	int w = p.x*R*R + p.y*R + p.z;
	return matrix[w / 8] & (1 << (w % 8));
}


void State::setmatrixbit(const Pos& p, bool value) {
	int w = p.x*R*R + p.y*R + p.z;
	matrix[w / 8] ^= (getmatrixbit(p) != value) << (w % 8);
}


bool State::getbit(const Pos& p, const vector<unsigned char>& v) const {
	int w = p.x*R*R + p.y*R + p.z;
	// TODO: TEST!
	return v[w / 8] & (1 << (w % 8));
}


void State::setbit(const Pos& p, bool value, vector<unsigned char>& v) {
	int w = p.x*R*R + p.y*R + p.z;
	// TODO: TEST!
	v[w / 8] ^= (getbit(p, v) != value) << (w % 8);
}


bool State::assert_well_formed() {
	// TODO
	return true;
}


int State::count_active() {
	int c = 0;
	for (Bot& b : bots) c += (b.active);
	return c;
}


bool State::validate_step() {
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


void State::run_commands() {
	for (Bot& b : bots) if (b.active) b.execute(this);
}


void State::add_passive_energy() {
	energy += count_active() * 20 + R * R * R * (high_harmonics ? 30 : 3);
}


Emulator::Emulator() {
	tracepointer = 0;
	time_step = 0;
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


unsigned char Emulator::getcommand() {
	return trace[tracepointer++];
}



void Emulator::run_one_step() {
	time_step++;
	S.add_passive_energy();
	for (Bot& b : S.bots) {
		if (!b.active) continue;
		b.command = Command::getnextcommand(this);
		//std::cout << (*(b.command)).__str__() << "\n";
	}
	S.validate_step();
	S.run_commands();
}


void Emulator::run_all(string modelfile, string tracefile) {
	S.read_model(modelfile);
	read_trace(tracefile);
	while (!S.halted) run_one_step();
}

void Emulator::run_given_step(vector<unsigned char> newtrace) {
	// TODO
}

int64_t Emulator::energy() {
	return S.energy;
}
