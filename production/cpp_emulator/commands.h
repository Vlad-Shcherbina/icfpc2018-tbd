#ifndef __COMMANDS_H_INCLUDED__
#define __COMMANDS_H_INCLUDED__

#include "coordinates.h"

#include <string>
#include <memory>
#include <assert.h>

class Bot;
class State;
class Emulator;

struct Command {
	virtual ~Command() = default;
	virtual void check_preconditions(Bot* b, State* S) = 0;
	virtual void set_volatiles(Bot* b, State* S) = 0;
	virtual void execute(Bot* b, State* S) = 0;
	virtual std::string __str__() = 0;
	virtual Diff move_offset() const {
		// should only be called for SMove and LMove
		assert(false);
		return Diff(0, 0, 0);
	}

	static Diff get_nd(uint8_t byte);
	static Diff get_lld(uint8_t a, uint8_t i);
	static Diff get_sld(uint8_t a, uint8_t i);
	static Diff get_fd(uint8_t a, uint8_t b, uint8_t c);
	static std::unique_ptr<Command> getnextcommand(Emulator* em);
};

struct Halt : Command {
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct Wait : Command {
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct Flip : Command {
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct SMove : Command {
	Diff lld;
	SMove(Diff d);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
	virtual Diff move_offset() const {
		return lld;
	}
};

struct LMove : Command {
	Diff sld1, sld2;
	LMove(Diff d1, Diff d2);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;

	std::string __str__() override;

	virtual Diff move_offset() const {
		return sld1 + sld2;
	}
};

struct FusionP : Command {
	Diff nd;

	FusionP(Diff nd);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct FusionS : Command
{
	Diff nd;
	FusionS(Diff nd);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct Fission : Command
{
	Diff nd;
	unsigned m;
	Fission(Diff nd, unsigned m);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct Fill : Command
{	
	Diff nd;
	Fill(Diff nd);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};

struct Void : Command
{
	Diff nd;
	Void(Diff nd);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};


struct GFill : Command
{
	Diff nd;
	Diff fd;
	GFill(Diff nd, Diff fd);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};


struct GVoid : Command
{
	Diff nd;
	Diff fd;
	GVoid(Diff nd, Diff fd);
	void execute(Bot* b, State* S) override;
	void check_preconditions(Bot* b, State* S) override;
	void set_volatiles(Bot* b, State* S) override;
	std::string __str__() override;
};


#endif