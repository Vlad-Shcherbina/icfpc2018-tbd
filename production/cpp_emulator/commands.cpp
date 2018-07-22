#include <cassert>
#include <memory>
#include <vector>
#include <algorithm>
#include "commands.h"
#include "emulator.h"
#include "logger.h"

using std::unique_ptr;
using std::make_unique;
using std::string;
using std::vector;


int min(int x, int y) { return x < y ? x : y; }
int max(int x, int y) { return x > y ? x : y; }


vector<Pos> get_region(const Pos& a, const Pos& b) {
	Pos p (0, 0, 0);
	vector<Pos> result;
	for (p.x = min(a.x, b.x); p.x <= max(a.x, b.x); p.x++)
		for (p.y = min(a.y, b.y); p.y <= max(a.y, b.y); p.y++)
			for (p.z = min(a.z, b.z); p.z <= max(a.z, b.z); p.z++)
				result.push_back(p);
	return result;
}


bool is_void_voxel(State* S, const Pos& p) {
	return !S->matrix.get(p);
}


bool is_void_region(State* S, const Pos& a, const Pos& b) {
	Pos p (0, 0, 0);
	for (p.x = min(a.x, b.x); p.x <= max(a.x, b.x); p.x++)
		for (p.y = min(a.y, b.y); p.y <= max(a.y, b.y); p.y++)
			for (p.z = min(a.z, b.z); p.z <= max(a.z, b.z); p.z++){
				if (S->matrix.get(p)) return false;
			}
	return true;
}

/*======================= COMMAND =======================*/

Diff Command::get_nd(uint8_t byte) {
	byte >>= 3;
	int dz = byte % 3 - 1;
	byte /= 3;
	int dy = byte % 3 - 1;
	byte /= 3;
	int dx = byte % 3 - 1;
	return Diff(dx, dy, dz);
}

Diff Command::get_lld(uint8_t a, uint8_t i) {
	a &= 3;
	int d = (int)(i &= 31) - 15;
	if (a == 1) return Diff(d, 0, 0);
	if (a == 2) return Diff(0, d, 0);
	if (a == 3) return Diff(0, 0, d);
	// TODO : log
	assert (false);
	throw parser_error("Unable to decode trace");
}

Diff Command::get_sld(uint8_t a, uint8_t i) {
	a &= 3;
	int d = (int)(i &= 15) - 5;
	if (a == 1) return Diff(d, 0, 0);
	if (a == 2) return Diff(0, d, 0);
	if (a == 3) return Diff(0, 0, d);
	// TODO : log
	assert (false);
	throw parser_error("Unable to decode trace");
}


Diff Command::get_fd(uint8_t a, uint8_t b, uint8_t c) {
	return Diff((int)a - 30, (int)b - 30, (int)c - 30);
}


unique_ptr<Command> Command::getnextcommand(Emulator* em) {
	uint8_t byte = em->getcommand();
	if (byte == 255) return make_unique<Halt>();
	if (byte == 254) return make_unique<Wait>();
	if (byte == 253) return make_unique<Flip>();
	uint8_t tail = byte & 7;
	if (tail == 3) return make_unique<Fill>(get_nd(byte));
	if (tail == 2) return make_unique<Void>(get_nd(byte));
	if (tail == 6) return make_unique<FusionS>(get_nd(byte));
	if (tail == 7) return make_unique<FusionP>(get_nd(byte));

	uint8_t byte2 = em->getcommand();
	if (tail == 5) return make_unique<Fission>(get_nd(byte), byte2);
	if (tail == 4) {
		if (byte & 8) return make_unique<LMove>(get_sld(byte>>6, byte2>>4),
											   	get_sld(byte>>4, byte2));
		else		  return make_unique<SMove>(get_lld(byte>>4, byte2));
	}

	uint8_t byte3 = em->getcommand();
	uint8_t byte4 = em->getcommand();
	if (tail == 1)
		return make_unique<GFill>(get_nd(byte), get_fd(byte2, byte3, byte4));
	if (tail == 0)
		return make_unique<GVoid>(get_nd(byte), get_fd(byte2, byte3, byte4));
	// TODO : log
	assert (false);
	throw parser_error("Unable to decode trace");
}


/*==================== COMMAND LIST =====================*/


string Halt::check_preconditions(Bot* b, State* S) {
	if (b->position != Pos(0, 0, 0) || S->high_harmonics || S->count_active() != 1) {
		return("Halt pre-conditions not satisfied");
	}
	return "";
}


vector<Pos> Halt::get_volatiles(Bot* b, State* S) {
	return { b->position };
}


void Halt::execute(Bot* b, State* S) {
	b->active = false;
	S->halted = true;
}


string Halt::__repr__() { return "halt"; }

/*-------------------------------------------------------*/

string Wait::check_preconditions(Bot* b, State* S) { return ""; }


vector<Pos> Wait::get_volatiles(Bot* b, State* S) {
	return { b->position };
}


void Wait::execute(Bot* b, State* S) {}


string Wait::__repr__() { return "wait"; }


/*-------------------------------------------------------*/

string Flip::check_preconditions(Bot* b, State* S) { return ""; }


vector<Pos> Flip::get_volatiles(Bot* b, State* S) {
	return { b->position };
}


void Flip::execute(Bot* b, State* S) {
	S->high_harmonics = !(S->high_harmonics);
}


string Flip::__repr__() { return "flip"; }

/*-------------------------------------------------------*/

SMove::SMove(Diff d)
: lld(d)
{
	if (!lld.is_long()) {
		// TODO: log
		assert (false);
		throw emulation_error("SMove parameter is not long");
	}
}


string SMove::check_preconditions(Bot* b, State* S) {
	if (!(b->position + lld).is_inside(S->R))
		return "SMove is out of bounds";
	if (!is_void_region(S, b->position, b->position + lld))
		return "SMove region has full voxels";
	return "";
}


vector<Pos> SMove::get_volatiles(Bot* b, State* S) {
	return get_region(b->position, b->position + lld);
}


void SMove::execute(Bot* b, State* S) {
	b->position += lld;
	S->energy += 2 * lld.mlen();
}


string SMove::__repr__() { return "smove " + lld.__repr__(); }

/*-------------------------------------------------------*/

LMove::LMove(Diff d1, Diff d2)
: sld1(d1)
, sld2(d2)
{
	if (!sld1.is_short() || !sld2.is_short()) {
		// TODO: log
		assert (false);
		throw emulation_error("LMove parameter is not short");
	}
}


string LMove::check_preconditions(Bot* b, State* S) {
	Pos step1 = b->position + sld1;
	Pos step2 = step1 + sld2;
	if (!step1.is_inside(S->R) || !step2.is_inside(S->R))
		return "LMove is out of bounds";
	if (!is_void_region(S, b->position, step1) || 
		!is_void_region(S, step1, step2))
		return "LMove region has full voxels";
	return "";
}


vector<Pos> LMove::get_volatiles(Bot* b, State* S) {
	Pos step1 = b->position + sld1;
	Pos step2 = step1 + sld2;
	vector<Pos> v1 = get_region(b->position, step1);
	vector<Pos> v2 = get_region(step1, step2);
	v1.insert(v1.end(), v2.begin(), v2.end());
	return v1;
}


void LMove::execute(Bot* b, State* S) {
	b->position = (b->position + sld1) + sld2;
	S->energy += 2 * (sld1.mlen() + 2 + sld2.mlen());
}


string LMove::__repr__() { 
	return "lmove " + sld1.__repr__() + " " + sld2.__repr__(); 
}


/*-------------------------------------------------------*/

FusionP::FusionP(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("FusionP parameter is not near");
	}
}


string FusionP::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		return "FusionP is out of bounds";
	return "";
	// TODO: move pair search
	// assert b2 has corresponding FusionP command
}


vector<Pos> FusionP::get_volatiles(Bot* b, State* S) {
	return { b->position };
}


void FusionP::execute(Bot* b, State* S) {
	Pos p = b->position + nd;
	unsigned index;
	for (index = 0; index < S->bots.size(); index++) {
		if (!(S->bots[index].active)) continue;
		if (!(S->bots[index].position == p)) continue;
	}
	if (index == S->bots.size()) 
		// TODO: move to preconditions
		// TODO : log
		assert (false);
		throw emulation_error("FusionP without a pair");

	Bot* b2 = &(S->bots[index]);
	b2->active = false;
	b->seeds.push_back(b2->bid);
	b->seeds.insert(b->seeds.end(), b2->seeds.begin(), b2->seeds.end());
	b2->seeds = vector<uint8_t>();
	std::sort(b->seeds.begin(), b->seeds.end());
	S->energy -= 24;
}


string FusionP::__repr__() { return "fusionP " + nd.__repr__(); }

/*-------------------------------------------------------*/

FusionS::FusionS(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("FusionS parameter is not near");
	}
}


string FusionS::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		return "FusionS is out of bounds";
	return "";
}


vector<Pos> FusionS::get_volatiles(Bot* b, State* S) {
	return { b->position };
}


void FusionS::execute(Bot* b, State* S) {
	// do nothing: all work done by FusionP
}


string FusionS::__repr__() { return "fusionS " + nd.__repr__(); }

/*-------------------------------------------------------*/

Fission::Fission(Diff nd, unsigned m)
: nd(nd)
, m(m)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("Fission parameter is not near");
	}
	// TODO : report m

}


string Fission::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		return "Fission is out of bounds";
	if (!is_void_voxel(S, b->position + nd))
		return "Fission to a full voxel";
	if (m+1 >= b->seeds.size())
		return "Fission asks more seeds that it has";
	return "";
}


vector<Pos> Fission::get_volatiles(Bot* b, State* S) {
	return { b->position, b->position + nd };
}


void Fission::execute(Bot* b, State* S) {
	Bot* b2 = &(S->bots[b->seeds[0]]);
	assert (!(b2->active));
	b2->active = true;
	b2->position = (b->position + nd);
	b2->seeds = std::move(vector<uint8_t>(b->seeds.begin(),
												b->seeds.begin() + m + 1));
	b->seeds = std::move(vector<uint8_t>(b->seeds.begin() + m + 1,
											   b->seeds.end()));
	S->energy += 24;
}


string Fission::__repr__() {
	return "fission " + nd.__repr__() + " " + std::to_string(m);
}

/*-------------------------------------------------------*/

Fill::Fill(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("Fill parameter is not near");
	}
}


string Fill::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		return "Fill is out of bounds";
	return "";
}


vector<Pos> Fill::get_volatiles(Bot* b, State* S) {
	return { b->position, b->position + nd };
}


void Fill::execute(Bot* b, State* S) {
	Pos dest = b->position + nd;
	if (!S->matrix.get(dest)) {
		S->energy += 12;
		S->matrix.set(dest, true);
	} else {
		S->energy += 6;
	}
}


string Fill::__repr__() { return "fill " + nd.__repr__(); }

/*-------------------------------------------------------*/

Void::Void(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("Void parameter is not near");
	}
}


string Void::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		return "Void is out of bounds";
	return "";
}


vector<Pos> Void::get_volatiles(Bot* b, State* S) {
	return { b->position, b->position + nd };
}


void Void::execute(Bot* b, State* S) {
	Pos dest = b->position + nd;
	if (S->matrix.get(dest)) {
		S->energy -= 12;
		S->matrix.set(dest, false);
	} else {
		S->energy += 3;
	}
}


std::string Void::__repr__() { return "void " + nd.__repr__(); }

/*-------------------------------------------------------*/

GFill::GFill(Diff nd, Diff fd)
: nd(nd)
, fd(fd)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("GFill first parameter is not near");
	}
	if (!fd.is_far()) {
		// TODO: log
		assert (false);
		throw emulation_error("Gfill second parameter is not near");
	}
}


string GFill::check_preconditions(Bot* b, State* S) {
	return "";
}


vector<Pos> GFill::get_volatiles(Bot* b, State* S) {
	vector<Pos> result = get_region(b->position + nd, b->position + nd + fd);
	result.push_back(b->position);
	return result;
}


void GFill::execute(Bot* b, State* S) {
	// TODO
	assert (false);
}


std::string GFill::__repr__() { return "gfill"; }

/*-------------------------------------------------------*/

GVoid::GVoid(Diff nd, Diff fd)
: nd(nd)
, fd(fd)
{
	if (!nd.is_near()) {
		// TODO: log
		assert (false);
		throw emulation_error("GVoid first parameter is not near");
	}
	if (!fd.is_far()) {
		// TODO: log
		assert (false);
		throw emulation_error("GVoid second parameter is not near");
	}
}


string GVoid::check_preconditions(Bot* b, State* S) {
	return "";
}


vector<Pos> GVoid::get_volatiles(Bot* b, State* S) {
	vector<Pos> result = get_region(b->position + nd, b->position + nd + fd);
	result.push_back(b->position);
	return result;
}


void GVoid::execute(Bot* b, State* S) {
	// TODO
	assert (false);
}


std::string GVoid::__repr__() { return "gvoid"; }
