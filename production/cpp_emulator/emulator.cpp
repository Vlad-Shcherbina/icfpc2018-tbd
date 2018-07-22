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

Bot::Bot(uint8_t bid, Pos position, vector<uint8_t> seeds, bool active)
: bid(bid)
, position(position)
, seeds(seeds)
, active(active)
{ }

Bot::Bot()
: bid(0)
, position(Pos(0, 0, 0))
, seeds(vector<uint8_t>())
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

State::State(std::optional<Matrix> src, std::optional<Matrix> tgt)
: matrix(0)
, target(0)
, volatiles(0)
, energy(0)
, high_harmonics(false)
, halted(false)
{
	if (!src && !tgt)
		throw parser_error("Source and target matrices cannot both be None");
	R = src ? src.value().R : tgt.value().R;
	matrix = src ? src.value() : Matrix(R);
	target = tgt ? tgt.value() : Matrix(R);
	volatiles = Matrix(R);

	set_default_bots();
}


State::State(std::optional<Matrix> src,
		  	 std::optional<Matrix> tgt,
			 bool high_harmonics,
			 int64_t energy,
			 vector<Bot> bots)
: matrix(0)
, target(0)
, volatiles(0)
, energy(energy)
, high_harmonics(high_harmonics)
, halted(false)
{ 
	if (!src && !tgt)
		throw parser_error("Source and target matrices cannot both be None");
	R = src ? src.value().R : tgt.value().R;
	matrix = src ? src.value() : Matrix(R);
	target = tgt ? tgt.value() : Matrix(R);
	volatiles = Matrix(R);
	
	this->bots = bots;
}

State::State(const State& S)
: matrix(0)
, target(0)
, volatiles(0)
, energy(S.energy)
, high_harmonics(S.high_harmonics)
, halted(S.halted)
{
	matrix = S.matrix;
	target = S.target;
	volatiles = S.volatiles;
	bots = S.bots;
}


void State::set_default_bots() {
	bots = vector<Bot>();
	Pos p(0, 0, 0);
	bots.push_back(Bot(0, p, vector<uint8_t>(), false));  // zerobot
	bots.push_back(Bot(1, p, vector<uint8_t>(), true));
	vector<uint8_t> seeds;
	for (uint8_t i = 2; i <= MAXBOTNUMBER; i++) {
		bots[0].seeds.push_back(i);
		bots.push_back(Bot(i, p, vector<uint8_t>(), false));
	}
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
	volatiles = Matrix(R);
	for (Bot& b : bots) if (b.active) b.check_preconditions(this);
	for (Bot& b : bots) if (b.active) b.set_volatiles(this);
}


void State::run_commands() {
	for (Bot& b : bots) if (b.active) b.execute(this);
}


void State::add_passive_energy() {
	energy += count_active() * 20 + R * R * R * (high_harmonics ? 30 : 3);
}


bool State::__getitem__(const Pos& p) const {
	return matrix.get(p);
}


void State::__setitem__(const Pos& p, bool value) {
	matrix.set(p, value);
}

/*====================== EMULATOR =======================*/

Emulator::Emulator(std::optional<Matrix> src, std::optional<Matrix> tgt)
: S(src, tgt)
, time_step(0)
, aborted(false)
{
	logger = std::make_unique<Logger>();
	logger->em = this;
}


Emulator::Emulator(const State& S)
: S(S)
, time_step(0)
, aborted(false)
{
	logger = std::make_unique<Logger>();
	logger->em = this;
}


void Emulator::set_trace(vector<unsigned char> bytes) {
	trace = bytes;
	tracepointer = 0;
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
			// std::cout << (*(b.command)).__repr__() << "\n";
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
	trace = newtrace;
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
