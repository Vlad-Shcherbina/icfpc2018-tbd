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


void set_volatile_voxel(State* S, const Pos& p) {
	if (S->volatiles.get(p)) {
		throw emulation_error("Volatile interference");
	}
	else S->volatiles.set(p, true);
}


void set_volatile_region(State* S, const Pos& a, const Pos& b) {
	Pos p (0, 0, 0);
	for (p.x = min(a.x, b.x); p.x <= max(a.x, b.x); p.x++)
		for (p.y = min(a.y, b.y); p.y <= max(a.y, b.y); p.y++)
			for (p.z = min(a.z, b.z); p.z <= max(a.z, b.z); p.z++)
				set_volatile_voxel(S, p);
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
	throw parser_error("Unable to decode trace");
}

Diff Command::get_sld(uint8_t a, uint8_t i) {
	a &= 3;
	int d = (int)(i &= 15) - 5;
	if (a == 1) return Diff(d, 0, 0);
	if (a == 2) return Diff(0, d, 0);
	if (a == 3) return Diff(0, 0, d);
	throw parser_error("Unable to decode trace");
}

unique_ptr<Command> Command::getnextcommand(Emulator* em) {
	uint8_t byte = em->getcommand();
	if (byte == 255) return make_unique<Halt>();
	if (byte == 254) return make_unique<Wait>();
	if (byte == 253) return make_unique<Flip>();
	uint8_t tail = byte & 7;
	if (tail == 3) return make_unique<Fill>(get_nd(byte));
	if (tail == 6) return make_unique<FusionS>(get_nd(byte));
	if (tail == 7) return make_unique<FusionP>(get_nd(byte));

	uint8_t byte2 = em->getcommand();
	if (tail == 5) return make_unique<Fission>(get_nd(byte), byte2);
	if (tail == 4) {
		if (byte & 8) return make_unique<LMove>(get_sld(byte>>6, byte2>>4),
											   	get_sld(byte>>4, byte2));
		else		  return make_unique<SMove>(get_lld(byte>>4, byte2));
	}
	throw parser_error("Unable to decode trace");
}


/*==================== COMMAND LIST =====================*/


void Halt::check_preconditions(Bot* b, State* S) {
	if (b->position != Pos(0, 0, 0) || S->high_harmonics || S->count_active() != 1) {
		throw emulation_error("Halt pre-conditions not satisfied");
	}
}


void Halt::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}


void Halt::execute(Bot* b, State* S) {
	b->active = false;
	S->halted = true;
}


string Halt::__str__() { return "halt"; }

/*-------------------------------------------------------*/

void Wait::check_preconditions(Bot* b, State* S) {}


void Wait::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}


void Wait::execute(Bot* b, State* S) {}


string Wait::__str__() { return "wait"; }


/*-------------------------------------------------------*/

void Flip::check_preconditions(Bot* b, State* S) {}


void Flip::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}


void Flip::execute(Bot* b, State* S) {
	S->high_harmonics = !(S->high_harmonics);
}


string Flip::__str__() { return "flip"; }

/*-------------------------------------------------------*/

SMove::SMove(Diff d)
: lld(d)
{
	if (!lld.is_long()) 
		throw emulation_error("SMove parameter is not long");
}


void SMove::check_preconditions(Bot* b, State* S) {
	if (!(b->position + lld).is_inside(S->R))
		throw emulation_error("SMove is out of bounds");
	if (!is_void_region(S, b->position, b->position + lld))
		throw emulation_error("SMove region has full voxels");
}


void SMove::set_volatiles(Bot* b, State* S) {
	set_volatile_region(S, b->position, b->position + lld);
}


void SMove::execute(Bot* b, State* S) {
	b->position += lld;
	S->energy += 2 * lld.mlen();
}


string SMove::__str__() { return "smove " + lld.__str__(); }

/*-------------------------------------------------------*/

LMove::LMove(Diff d1, Diff d2)
: sld1(d1)
, sld2(d2)
{
	if (!sld1.is_short() || !sld2.is_short()) {
		throw emulation_error("LMove parameter is not short");
	}
}


void LMove::check_preconditions(Bot* b, State* S) {
	Pos step1 = b->position + sld1;
	Pos step2 = step1 + sld2;
	if (!step1.is_inside(S->R) || !step2.is_inside(S->R))
		throw emulation_error("LMove is out of bounds");
	if (!is_void_region(S, b->position, step1) || 
		!is_void_region(S, step1, step2))
		throw emulation_error("LMove region has full voxels");
}


void LMove::set_volatiles(Bot* b, State* S) {
	Pos step1 = b->position + sld1;
	Pos step2 = step1 + sld2;
	set_volatile_region(S, b->position, step1);
	set_volatile_region(S, step1, step2);
}


void LMove::execute(Bot* b, State* S) {
	b->position = (b->position + sld1) + sld2;
	S->energy += 2 * (sld1.mlen() + 2 + sld2.mlen());
}


string LMove::__str__() { 
	return "lmove " + sld1.__str__() + " " + sld2.__str__(); 
}


/*-------------------------------------------------------*/

FusionP::FusionP(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) 
		throw emulation_error("FusionP parameter is not near");
}


void FusionP::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R)) {
		throw emulation_error("FusionP is out of bounds");
	}
	// TODO: move pair search
	// assert b2 has corresponding FusionP command
}


void FusionP::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
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
		throw emulation_error("FusionP without a pair");

	Bot* b2 = &(S->bots[index]);
	b2->active = false;
	b->seeds.push_back(b2->bid);
	b->seeds.insert(b->seeds.end(), b2->seeds.begin(), b2->seeds.end());
	b2->seeds = vector<uint8_t>();
	std::sort(b->seeds.begin(), b->seeds.end());
	S->energy -= 24;
}


string FusionP::__str__() { return "fusionP " + nd.__str__(); }

/*-------------------------------------------------------*/

FusionS::FusionS(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) 
		throw emulation_error("FusionS parameter is not near");
}


void FusionS::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		throw emulation_error("FusionS is out of bounds");

}


void FusionS::execute(Bot* b, State* S) {
	// do nothing: all work done by FusionP
}


void FusionS::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}


string FusionS::__str__() { return "fusionS " + nd.__str__(); }

/*-------------------------------------------------------*/

Fission::Fission(Diff nd, unsigned m)
: nd(nd)
, m(m)
{
	if (!nd.is_near()) 
		throw emulation_error("Fission parameter is not near");
	// TODO : report m

}


void Fission::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		throw emulation_error("Fission is out of bounds");
	if (!is_void_voxel(S, b->position + nd))
		throw emulation_error("Fission to a full voxel");
	if (m+1 >= b->seeds.size())
		throw emulation_error("Fission asks more seeds that it has");
}


void Fission::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
	set_volatile_voxel(S, b->position + nd);
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


string Fission::__str__() {
	return "fission " + nd.__str__() + " " + std::to_string(m);
}

/*-------------------------------------------------------*/

Fill::Fill(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) 
		throw emulation_error("Fill parameter is not near");
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


void Fill::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		throw emulation_error("Fill is out of bounds");
}


void Fill::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
	set_volatile_voxel(S, b->position + nd);
}


string Fill::__str__() { return "fill " + nd.__str__(); }

/*-------------------------------------------------------*/

Void::Void(Diff nd)
: nd(nd)
{
	if (!nd.is_near()) 
		throw emulation_error("Void parameter is not near");
}


void Void::check_preconditions(Bot* b, State* S) {
	if (!(b->position + nd).is_inside(S->R))
		throw emulation_error("Void is out of bounds");
}


void Void::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
	set_volatile_voxel(S, b->position + nd);
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


std::string Void::__str__() { return "void " + nd.__str__(); }

/*-------------------------------------------------------*/

GFill::GFill(Diff nd, Diff fd)
: nd(nd)
, fd(fd)
{
	if (!nd.is_near()) 
		throw emulation_error("GFill first parameter is not near");
	if (!fd.is_far()) 
		throw emulation_error("Gfill second parameter is not near");
}


void GFill::check_preconditions(Bot* b, State* S) {

}


void GFill::set_volatiles(Bot* b, State* S) {
	// TODO
	assert (false);
}


void GFill::execute(Bot* b, State* S) {
	// TODO
	assert (false);
}


std::string GFill::__str__() { return "gfill"; }

/*-------------------------------------------------------*/

GVoid::GVoid(Diff nd, Diff fd)
: nd(nd)
, fd(fd)
{
	if (!nd.is_near()) 
		throw emulation_error("GVoid first parameter is not near");
	if (!fd.is_far()) 
		throw emulation_error("GVoid second parameter is not near");
}


void GVoid::check_preconditions(Bot* b, State* S) {

}


void GVoid::set_volatiles(Bot* b, State* S) {
	// TODO
	assert (false);
}


void GVoid::execute(Bot* b, State* S) {
	// TODO
	assert (false);
}


std::string GVoid::__str__() { return "gvoid"; }
