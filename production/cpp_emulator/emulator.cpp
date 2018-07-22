#include <fstream>
#include <iostream>
#include <cassert>
#include <memory>
#include "emulator.h"
#include "commands.h"

using std::vector;
using std::string;
using std::unique_ptr;

const int MAXBOTNUMBER = 40;

/*======================== BOT ==========================*/

Bot::Bot(unsigned char bid, Pos position, vector<unsigned char> seeds, bool active)
: bid(bid)
, position(position)
, seeds(seeds)
, active(active)
{ }

Bot::Bot()
: bid(0)
, position(Pos(0, 0, 0))
, seeds(vector<unsigned char>())
, active(false)
{ }

Bot::Bot(const Bot& other) 
: bid(other.bid)
, position(other.position)
, seeds(other.seeds)
, active(other.active)
{ }

Bot& Bot::operator=(const Bot& other) {
	this->bid = other.bid;
	this->position = other.position;
	this->seeds = other.seeds;
	this->active = other.active;
	return *this;
}



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


/*======================== STATE ========================*/

State::State() { 
	set_initials();
}

State::State(unsigned char R) {
	set_initials();
	set_size(R);
}


void State::set_initials() {
	R = 0;
	energy = 0;
	high_harmonics = false;
	volatile_violation = false;
	halted = false;
	set_default_bots();			// maybe should be moved
}


void State::set_default_bots() {
	Pos p(0, 0, 0);
	bots.push_back(Bot(0, p, vector<unsigned char>(), false));  // zerobot
	bots.push_back(Bot(1, p, vector<unsigned char>(), true));
	vector<unsigned char> seeds;
	for (unsigned char i = 2; i <= MAXBOTNUMBER; i++) {
		bots[0].seeds.push_back(i);
		bots.push_back(Bot(i, p, vector<unsigned char>(), false));
	}
}


void State::set_size(unsigned char R) {
	this->R = R;
	int bytes = (R * R * R + 7) / 8;
	matrix = vector<unsigned char>(bytes, 0);
	target = vector<unsigned char>(bytes, 0);
	//floating = vector<unsigned char>(bytes, 0);
	volatiles = vector<unsigned char>(bytes, 0);
}


void State::set_state(unsigned char R,
					  bool high_harmonics,
					  int64_t energy,
					  vector<unsigned char> matrix,
					  vector<Bot> bots) {
	set_size(R);
	this->matrix = std::move(matrix);
	this->high_harmonics = high_harmonics;
	this->energy = energy;
	this->bots = std::move(bots);
}


bool State::getbit(const Pos& p) const {
	int w = p.x*R*R + p.y*R + p.z;
	return matrix[w / 8] & (1 << (w % 8));
}


void State::setbit(const Pos& p, bool value) {
	int w = p.x*R*R + p.y*R + p.z;
	matrix[w / 8] ^= (getbit(p) != value) << (w % 8);
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


/*====================== EMULATOR =======================*/

Emulator::Emulator() 
: time_step(0) 
{ }


void Emulator::load_trace(string filename) {
	trace = vector<unsigned char>();
	std::ifstream f(filename, std::ios::binary);
	f >> std::noskipws;
	unsigned char c;
	uint32_t i = 0;
	while (f >> c) trace.push_back(c);
	f.close();
	tracepointer = 0;
}


void Emulator::set_trace(vector<unsigned char> bytes) {
	trace = std::move(bytes);
	tracepointer = 0;
}


vector<unsigned char>* Emulator::choose_matrix(char c) {
	switch (c) {
		case 's' : return &S.matrix;
		case 't' : return &S.target;
		case 'v' : return &S.volatiles;
	}
}


void Emulator::load_model(string filename, char dest) {
	std::ifstream f(filename, std::ios::binary);
	f >> std::noskipws;
	unsigned char c;

	f >> c;
	S.set_size((unsigned)c);

	vector<unsigned char>* m = choose_matrix(dest);

	uint32_t i = 0;
	while (f >> c) (*m)[i++] = c;
	f.close();

	assert (S.target.size() == S.matrix.size());
}


void Emulator::set_model(vector<unsigned char> bytes, char dest) {
	vector<unsigned char>* m = choose_matrix(dest);
	*m = std::move(bytes);
}


void Emulator::set_state(State S) {
	this->S = S;
}


State Emulator::get_state() {
	return this->S;
}


unsigned char Emulator::getcommand() {
	return trace[tracepointer++];
}


void Emulator::run_one_step() {
	time_step++;

	for (Bot& b : S.bots) {
		if (!b.active) continue;
		b.command = Command::getnextcommand(this);
		// std::cout << (*(b.command)).__str__() << "\n";
	}

	S.validate_step();
	S.add_passive_energy();
	S.run_commands();
}


void Emulator::run_all() {
	while (!S.halted) run_one_step();
}


void Emulator::run_given(vector<unsigned char> newtrace) {
	trace = std::move(newtrace);
	tracepointer = 0;
	while (tracepointer < trace.size()) run_one_step();
}


int64_t Emulator::energy() {
	return S.energy;
}




// void Emulator::add_bot(unsigned char bid,
// 		 unsigned char x,
// 		 unsigned char y,
// 		 unsigned char z,
// 		 vector<unsigned char> seeds)
// {
// 	Bot& b = S.bots[bid];
// 	b.active = true;
// 	b.position = Pos(x, y, z);
// 	b.seeds = std::move(seeds);
// }



// vector<unsigned char> Emulator::get_state() {
// 	// you'd better never know how it is achieved
// 	vector<unsigned char> result;
// 	result.push_back(S.R);
// 	result.push_back(S.high_harmonics);
// 	for (auto x : S.matrix)  result.push_back(x);
// 	return result;
// }


// vector<unsigned char> Emulator::get_bots() {
// 	// same here
// 	vector<unsigned char> result;
// 	for (Bot& b : S.bots) {
// 		if (!b.active) continue;
// 		result.push_back(b.bid);
// 		result.push_back(b.position.x);
// 		result.push_back(b.position.y);
// 		result.push_back(b.position.z);
// 		result.push_back((unsigned char)b.seeds.size());
// 		for (auto x : b.seeds) result.push_back(x);
// 	}
// 	return result;
// }



int Emulator::count_active() { return S.count_active(); }