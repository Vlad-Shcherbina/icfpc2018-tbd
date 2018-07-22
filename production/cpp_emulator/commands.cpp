#include <cassert>
#include <memory>
#include <vector>
#include <algorithm>
#include "commands.h"
#include "emulator.h"

using std::unique_ptr;
using std::make_unique;
using std::string;
using std::vector;


int min(int x, int y) { return x < y ? x : y; }
int max(int x, int y) { return x > y ? x : y; }


void set_volatile_voxel(State* S, const Pos& p) {
	if (S->getbit(p, S->volatiles)) {
		// TODO: report
		S->volatile_violation = true;
	}
	else S->setbit(p, true, S->volatiles);
}

void set_volatile_region(State* S, const Pos& a, const Pos& b) {
	// TODO is_inside
	Pos p (0, 0, 0);
	for (p.x = min(a.x, b.x); p.x <= max(a.x, b.x); p.x++) 
		for (p.y = min(a.y, b.y); p.y <= max(a.y, b.y); p.y++) 
			for (p.z = min(a.z, b.z); p.z <= max(a.z, b.z); p.z++) 
				set_volatile_voxel(S, p);
}

/*======================= COMMAND =======================*/

Diff Command::get_nd(unsigned char byte) {
	byte >>= 3;
	int dz = byte % 3 - 1;
	byte /= 3;
	int dy = byte % 3 - 1;
	byte /= 3;
	int dx = byte % 3 - 1;
	return Diff(dx, dy, dz);
}

Diff Command::get_lld(unsigned char a, unsigned char i) {
	a &= 3;
	int d = (int)(i &= 31) - 15;
	if (a == 1) return Diff(d, 0, 0);
	if (a == 2) return Diff(0, d, 0);
	if (a == 3) return Diff(0, 0, d);
	// TODO: report ill-formed model
}

Diff Command::get_sld(unsigned char a, unsigned char i) {
	a &= 3;
	int d = (int)(i &= 15) - 5;
	if (a == 1) return Diff(d, 0, 0);
	if (a == 2) return Diff(0, d, 0);
	if (a == 3) return Diff(0, 0, d);
	// TODO: report ill-formed model
}

unique_ptr<Command> Command::getnextcommand(Emulator* em) {
	unsigned char byte = em->getcommand();
	if (byte == 255) return make_unique<Halt>();
	if (byte == 254) return make_unique<Wait>();
	if (byte == 253) return make_unique<Flip>();
	unsigned char tail = byte & 7;
	if (tail == 3) return make_unique<Fill>(get_nd(byte));
	if (tail == 6) return make_unique<FusionS>(get_nd(byte));
	if (tail == 7) return make_unique<FusionP>(get_nd(byte));

	unsigned char byte2 = em->getcommand();
	if (tail == 5) return make_unique<Fission>(get_nd(byte), byte2);
	if (tail == 4) {
		if (byte & 8) return make_unique<LMove>(get_sld(byte>>6, byte2>>4),
											   	get_sld(byte>>4, byte2));
		else		  return make_unique<SMove>(get_lld(byte>>4, byte2));
	}
	// TODO: report ill-formed model
	return unique_ptr<Command>(nullptr);
}


/*==================== COMMAND LIST =====================*/

void Halt::execute(Bot* b, State* S) {
	if (b->position != Pos(0, 0, 0) || S->high_harmonics || S->count_active() != 1) {
		// TODO: report
		assert (false);
	}
	b->active = false;
	S->halted = true;
}

void Halt::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}

string Halt::__str__() { return "halt"; }


/*-------------------------------------------------------*/

void Wait::execute(Bot* b, State* S) {}

void Wait::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}

string Wait::__str__() { return "wait"; }


/*-------------------------------------------------------*/

void Flip::execute(Bot* b, State* S) {
	S->high_harmonics = !(S->high_harmonics);
}

void Flip::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
}

string Flip::__str__() { return "flip"; }


/*-------------------------------------------------------*/

SMove::SMove(Diff d)
: lld(d)
{
	// TODO: report wrong command
	//assert (lld.is_long());
}

void SMove::execute(Bot* b, State* S) {
	b->position += lld;
	S->energy += 2 * lld.mlen();
}

void SMove::set_volatiles(Bot* b, State* S) {
	set_volatile_region(S, b->position, b->position + lld);
}

string SMove::__str__() { return "smove " + lld.__str__(); }


/*-------------------------------------------------------*/

LMove::LMove(Diff d1, Diff d2)
: sld1(d1)
, sld2(d2)
{
	// TODO: report
}

void LMove::execute(Bot* b, State* S) {
	b->position = (b->position + sld1) + sld2;
	S->energy += 2 * (sld1.mlen() + 2 + sld2.mlen());
}

void LMove::set_volatiles(Bot* b, State* S) {
	// TODO:: check is_inside
	set_volatile_region(S, b->position, b->position + sld1);
	set_volatile_region(S, b->position + sld1, (b->position + sld1) + sld2);
}

string LMove::__str__() { return "lmove " + sld1.__str__() + " " + sld2.__str__(); }


/*-------------------------------------------------------*/

FusionP::FusionP(Diff nd)
: nd(nd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void FusionP::execute(Bot* b, State* S) {
	Pos p = b->position + nd;
	unsigned index;
	for (index = 0; index < S->bots.size(); index++) {
		if (!(S->bots[index].active)) continue;
		if (!(S->bots[index].position == p)) continue;
	}
	if (index == S->bots.size()) {
		// TODO: report - no bot found
		assert (false);
	}

	Bot* b2 = &(S->bots[index]);
	// assert b2 has corresponding FusionP command
	b2->active = false;
	b->seeds.push_back(b2->bid);
	b->seeds.insert(b->seeds.end(), b2->seeds.begin(), b2->seeds.end());
	b2->seeds = vector<unsigned char>();
	std::sort(b->seeds.begin(), b->seeds.end());
	S->energy -= 24;
}

void FusionP::set_volatiles(Bot* b, State* S) {
	// TODO:: check is_inside
	set_volatile_voxel(S, b->position);
}

string FusionP::__str__() { return "fusionP " + nd.__str__(); }


/*-------------------------------------------------------*/

FusionS::FusionS(Diff nd)
: nd(nd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
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
	// TODO: report wrong command
	//assert(nd.is_near());

}
void Fission::execute(Bot* b, State* S) {
	assert (m + 1 <= b->seeds.size());
	Bot* b2 = &(S->bots[b->seeds[0]]);
	assert (!(b2->active));
	b2->active = true;
	b2->position = (b->position + nd);
	b2->seeds = std::move(vector<unsigned char>(b->seeds.begin(), b->seeds.begin() + m + 1));
	b->seeds = std::move(vector<unsigned char>(b->seeds.begin() + m + 1, b->seeds.end()));
	S->energy += 24;
}

void Fission::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
	set_volatile_voxel(S, b->position + nd);
	if (m >= b->seeds.size()) {
		// TODO: report
		S->volatile_violation = true;
	}
}

string Fission::__str__() { return "fission " + nd.__str__() + " " + std::to_string(m); }


/*-------------------------------------------------------*/

Fill::Fill(Diff nd)
: nd(nd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void Fill::execute(Bot* b, State* S) {
	S->energy += 6;
	if (!(S->getbit(b->position + nd, S->matrix))) {
		S->energy += 6;
	}
	S->setbit(b->position + nd, true, S->matrix);
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
	// TODO: report wrong command
	//assert(nd.is_near());
}

void Void::execute(Bot* b, State* S) {
	if (S->getbit(b->position + nd, S->matrix)) {
		S->energy -= 12;
		S->setbit(b->position + nd, false, S->matrix);
	}
	else { S->energy += 3; }
}

void Void::set_volatiles(Bot* b, State* S) {
	set_volatile_voxel(S, b->position);
	set_volatile_voxel(S, b->position + nd);
}

std::string Void::__str__() { return "void " + nd.__str__(); }

/*-------------------------------------------------------*/

GFill::GFill(Diff nd, Diff fd)
: nd(nd)
, fd(fd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void GFill::execute(Bot* b, State* S) {
	// TODO
	assert (false);
}

void GFill::set_volatiles(Bot* b, State* S) {
	// TODO
	assert (false);
}

std::string GFill::__str__() { return "gfill"; }

/*-------------------------------------------------------*/

GVoid::GVoid(Diff nd, Diff fd)
: nd(nd)
, fd(fd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void GVoid::execute(Bot* b, State* S) {
	// TODO
	assert (false);
}

void GVoid::set_volatiles(Bot* b, State* S) {
	// TODO
	assert (false);
}

std::string GVoid::__str__() { return "gvoid"; }
