#include <fstream>
#include <iostream>
#include <cassert>
#include <memory>
#include <cstring>
#include "emulator.h"
#include "commands.h"
#include "logger.h"

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


void Bot::check_preconditions(State* S) {
	if (!command) throw malfunc_error("Active bot without command");
	(*command).check_preconditions(this, S);
}


void Bot::set_volatiles(State* S) {
	if (!command) throw malfunc_error("Active bot without command");
	(*command).set_volatiles(this, S);
}


void Bot::execute(State* S) {
	if (!command) throw malfunc_error("Active bot without command");
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
	return v[w / 8] & (1 << (w % 8));
}


void State::setbit(const Pos& p, bool value, vector<unsigned char>& v) {
	int w = p.x*R*R + p.y*R + p.z;
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


void State::validate_step() {
	// TODO: check floatings
	for (auto& x : volatiles) x = 0;
	for (Bot& b : bots) if (b.active) b.check_preconditions(this);
	for (Bot& b : bots) if (b.active) b.set_volatiles(this);
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
, aborted(false) {
	logger = std::make_unique<Logger>();
	logger->em = this;
}


void Emulator::set_size(unsigned char R) { S.set_size(R); }


void Emulator::set_trace(vector<unsigned char> bytes) {
	trace = std::move(bytes);
	tracepointer = 0;
}


void Emulator::set_src_model(vector<unsigned char> bytes) {
	// TODO: set size
	// 	S.set_size( ... );
	S.matrix = std::move(bytes);
}


void Emulator::set_tgt_model(vector<unsigned char> bytes) {
	// TODO: set size
	// 	S.set_size( ... );
	S.target = std::move(bytes);
}


void Emulator::set_state(State S) {
	this->S = S;
}


State Emulator::get_state() {
	return this->S;
}


unsigned char Emulator::getcommand() {
	if (tracepointer == trace.size()) {
		throw emulation_error("End of trace");
		assert (false);
	}
	return trace[tracepointer++];
}


void Emulator::run_one_step() {
	time_step++;

	try {
		for (Bot& b : S.bots) {
			if (!b.active) continue;
			b.command = Command::getnextcommand(this);
			// std::cout << (*(b.command)).__str__() << "\n";
		}

		S.validate_step();
		S.add_passive_energy();
		S.run_commands();
	}
	catch (base_error& e) {
		logger->logerror(e.what());
		S.halted = aborted = true;
		throw e;
	}
}


void Emulator::run_all() {
	logger->mode = "auto";
	logger->start();
	while (!S.halted) run_one_step();
	logger->logsuccess(S.energy);
}


void Emulator::run_given(vector<unsigned char> newtrace) {
	logger->mode = "interactive";
	logger->start();
	trace = std::move(newtrace);
	tracepointer = 0;
	while (tracepointer < trace.size() && !S.halted) run_one_step();
	logger->logsuccess(S.energy);
}


int64_t Emulator::energy() {
	return S.energy;
}


//---- Logger stuff ----//

void Emulator::setproblemname(std::string name) { logger->problemname = name; }
void Emulator::setsolutionname(std::string name) { logger->solutionname = name; }
void Emulator::setlogfile(std::string name) { logger->logfile = name; }
