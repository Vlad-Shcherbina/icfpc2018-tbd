#include <cassert>
#include <memory>
#include "commands.h"
#include "emulator.h"

using std::unique_ptr;
using std::make_unique;


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

unique_ptr<Command> Command::getnextcommand(Emulator* field) {
	unsigned char byte = field->tracebyte();
	if (byte == 255) return make_unique<Halt>();
	if (byte == 254) return make_unique<Wait>();
	if (byte == 253) return make_unique<Flip>();
	unsigned char tail = byte & 7;
	if (tail == 3) return make_unique<Fill>(get_nd(byte));
	if (tail == 6) return make_unique<FusionS>(get_nd(byte));
	if (tail == 7) return make_unique<FusionP>(get_nd(byte));

	unsigned char byte2 = field->tracebyte();
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


void Halt::execute(Bot* b, Emulator* f) {
	// TODO
}

void Halt::set_volatiles(Bot* b, Emulator* f) {
}

void Wait::execute(Bot* b, Emulator* f) {
	// TODO
}

void Wait::set_volatiles(Bot* b, Emulator* f) {
}

void Flip::execute(Bot* b, Emulator* f) {
	// TODO
}

void Flip::set_volatiles(Bot* b, Emulator* f) {
}


SMove::SMove(Diff d)
: lld(d)
{
	// TODO: report wrong command
	//assert (lld.is_long());
}

void SMove::execute(Bot* b, Emulator* f) {
	// TODO
}

void SMove::set_volatiles(Bot* b, Emulator* f) {
}


LMove::LMove(Diff d1, Diff d2)
: sld1(d1)
, sld2(d2)
{
	// TODO: report wrong command
	// assert (sld1.is_short() && sld2.is_short());
}

void LMove::execute(Bot* b, Emulator* f) {
	// TODO
}

void LMove::set_volatiles(Bot* b, Emulator* f) {
}


FusionP::FusionP(Diff nd)
: nd(nd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void FusionP::execute(Bot* b, Emulator* f) {
	// TODO
}

void FusionP::set_volatiles(Bot* b, Emulator* f) {
}


FusionS::FusionS(Diff nd)
: nd(nd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void FusionS::execute(Bot* b, Emulator* f) {
	// TODO
}

void FusionS::set_volatiles(Bot* b, Emulator* f) {
}

Fission::Fission(Diff nd, unsigned short m)
: nd(nd)
, m(m)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}
void Fission::execute(Bot* b, Emulator* f) {
	// TODO
}

void Fission::set_volatiles(Bot* b, Emulator* f) {
}

Fill::Fill(Diff nd)
: nd(nd)
{
	// TODO: report wrong command
	//assert(nd.is_near());
}

void Fill::execute(Bot* b, Emulator* f) {
	// TODO
}

void Fill::set_volatiles(Bot* b, Emulator* f) {
}
