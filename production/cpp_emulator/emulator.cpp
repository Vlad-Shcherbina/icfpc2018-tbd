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
using std::shared_ptr;

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


/*======================== STATE ========================*/

State::State(std::optional<Matrix> src, std::optional<Matrix> tgt)
: matrix(0)
, target(0)
, energy(0)
, high_harmonics(false)
, halted(false)
{
	if (!src && !tgt) {
		// TODO : log
		assert (false);
		throw parser_error("Source and target matrices cannot both be None");
	}
	R = src ? src.value().R : tgt.value().R;
	matrix = src ? src.value() : Matrix(R);
	target = tgt ? tgt.value() : Matrix(R);

	volatiles = vector<Pos>();
	set_default_bots();
}


State::State(std::optional<Matrix> src,
		  	 std::optional<Matrix> tgt,
			 bool high_harmonics,
			 int64_t energy,
			 vector<Bot> bots)
: matrix(0)
, target(0)
, energy(energy)
, high_harmonics(high_harmonics)
, halted(false)
{
	if (!src && !tgt) {
		// TODO : log
		assert (false);
		throw parser_error("Source and target matrices cannot both be None");
	}
	R = src ? src.value().R : tgt.value().R;
	matrix = src ? src.value() : Matrix(R);
	target = tgt ? tgt.value() : Matrix(R);

	volatiles = vector<Pos>();
	this->bots = bots;
}

// State::State(const State& S)
// : matrix(0)
// , target(0)
// , energy(0)
// , high_harmonics(S.high_harmonics)
// , halted(S.halted)
// {
// 	std::cout << "Copy constructor, energy = " << energy << "\n";
// 	matrix = S.matrix;
// 	target = S.target;

// 	volatiles = vector<Pos>();
// 	bots = S.bots;
// }


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


string State::validate_command(Bot* b, shared_ptr<Command> cmd) {
	assert (b != nullptr && cmd != nullptr);
	string msg = cmd->check_preconditions(b, this);
	if (!msg.empty()) return msg;

	vector<Pos> v = cmd->get_volatiles(b, this);
	for (Pos& p1 : v)
		for (Pos& p2 : volatiles)
			if (p1 == p2) return "Bot actions interfere";
	volatiles.insert(volatiles.end(), v.begin(), v.end());
	return "";
}


// void State::run() {
// 	for (Bot& b : bots) if (b.active) b.execute(this);
// }


void State::add_passive_energy() {
	energy += count_active() * 20 + R * R * R * (high_harmonics ? 30 : 3);
}


// void State::validate_state() {
// 	if (!high_harmonics) validate_floating();
// }


// void State::validate_floating() {
// }


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
, tracepointer(0)
, aborted(false)
{
	logger = std::make_unique<Logger>();
	logger->em = this;
	reset_assumptions();
}


Emulator::Emulator(const State& S)
: S(S.matrix, S.target, S.high_harmonics, S.energy, S.bots)
, time_step(0)
, aborted(false)
, tracepointer(0)
, unchecked(0)
, botindex(0)
{
	logger = std::make_unique<Logger>();
	logger->em = this;
	reset_assumptions();
}


void Emulator::set_trace(vector<shared_ptr<Command>> bytes) {
	trace = bytes;
	tracepointer = 0;
}


void Emulator::set_state(State S) {
	this->S = S;
}


State Emulator::get_state() {
	return this->S;
}


bool Emulator::step_is_complete() {
    return (unsigned)S.count_active() <= (trace.size() - tracepointer);
}


string Emulator::check_command(std::shared_ptr<Command> cmd) {
	if (step_is_complete()) 
		return "Cannot validate before perfoming current step";

	// if there are unchecked previous commands
	while (unchecked < trace.size()) {
		string msg = S.validate_command(nextbot(), trace[unchecked]);
		if (!msg.empty()) 
			return "Trace already contains invalid commands";
		unchecked++;
	}

	return S.validate_command(nextbot(), cmd);
}


void Emulator::add_command(shared_ptr<Command> cmd) {
    trace.push_back(cmd);
}


string Emulator::check_add_command(std::shared_ptr<Command> cmd) {
    string msg = check_command(cmd);
    if (msg.empty()) {
    	add_command(cmd);
    	unchecked++;
    	assert (unchecked == trace.size());
    }
    return msg;
}


void Emulator::validate_one_step() {
	unsigned temppointer = tracepointer;
	for (Bot& b : S.bots) {
		if (!b.active) continue;
       	if (temppointer == trace.size()) {
            // TODO : log
        	std::cout << "End of trace" << "\n";
            assert (false);
        }
        shared_ptr<Command> cmd = trace[temppointer++];
        // std::cout << (*(b.command)).__repr__() << "\n";

        string msg = S.validate_command(&b, cmd);
        if (!msg.empty()) {
        	// TODO log
        	std::cout << msg << "\n";
        	assert (false);
        }
	}
	// TODO: validate group operations
}


void Emulator::run_one_step() {
	time_step++;
	validate_one_step();

	S.add_passive_energy();
	for (Bot& b : S.bots) {
		if (!b.active) continue;
		shared_ptr<Command> cmd = trace[tracepointer++];
		cmd->execute(&b, &S);
	}

	// S.validate_state()
	reset_assumptions();
}


void Emulator::run_full() {
	logger->mode = "auto";
	logger->start();
	while (!S.halted) run_one_step();
	logger->logsuccess(S.energy);
}


void Emulator::run_commands(vector<shared_ptr<Command>> newtrace) {
	logger->mode = "interactive";
	logger->start();
	trace = newtrace;
	tracepointer = 0;
	while ((tracepointer < trace.size()) && !S.halted) run_one_step();
	logger->logsuccess(S.energy);
}


int64_t Emulator::energy() {
	return S.energy;
}


void Emulator::reset_assumptions() {
	unchecked = 0;
	botindex = 0;
	S.volatiles = vector<Pos>();
}


Bot* Emulator::nextbot() {
	while (botindex < S.bots.size())
		if (S.bots[botindex++].active)
			return &S.bots[botindex - 1];
	botindex = 0;
	return nullptr;
}


//---- Logger stuff ----//

void Emulator::setproblemname(std::string name) { logger->problemname = name; }
void Emulator::setsolutionname(std::string name) { logger->solutionname = name; }
void Emulator::setlogfile(std::string name) { logger->logfile = name; }
