#ifndef __COMMANDS_H_INCLUDED__
#define __COMMANDS_H_INCLUDED__

#include <string>
#include "coordinates.h"

class Bot;
class Emulator;


struct Command {
	virtual ~Command() = default;
	virtual void execute(Bot*, Emulator*) = 0;
	virtual void set_volatiles(Bot*, Emulator*) = 0;
	virtual std::string __str__() = 0;

	static Diff get_nd(unsigned char byte);
	static Diff get_lld(unsigned char a, unsigned char i);
	static Diff get_sld(unsigned char a, unsigned char i);
	static std::unique_ptr<Command> getnextcommand(Emulator* field);
};

struct Halt : Command {
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct Wait : Command {
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct Flip : Command {
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct SMove : Command {
	Diff lld;
	SMove(Diff d);
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct LMove : Command {
	Diff sld1, sld2;
	LMove(Diff d1, Diff d2);
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;

	std::string __str__() override;
};

struct FusionP : Command {
	Diff nd;

	FusionP(Diff nd);
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct FusionS : Command
{
	Diff nd;
	FusionS(Diff nd);
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct Fission : Command
{
	Diff nd;
	unsigned m;
	Fission(Diff nd, unsigned m);
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

struct Fill : Command
{	
	Diff nd;
	Fill(Diff nd);
	void execute(Bot* b, Emulator* f) override;
	void set_volatiles(Bot* b, Emulator* f) override;
	std::string __str__() override;
};

#endif