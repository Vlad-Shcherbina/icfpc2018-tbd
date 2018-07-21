#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cassert>

using std::vector;
using std::string;
using std::unique_ptr;
using std::make_unique;


// ENERGY CONSTANTS




/*======================== DIFF =========================*/

class Diff {

public:
	int dx, dy, dz;

	Diff(int dx, int dy, int dz) {
		this->dx = dx;
		this->dy = dy;
		this->dz = dz;
	}

	int mlen() const { return abs(dx) + abs(dy) + abs(dz); }

	int clen() const {
		int x = abs(dx);
		int y = abs(dy);
		int z = abs(dz);
		return (x >= y && x >= z) ? x : ((y >= z) ? y : z);
	}

	bool is_adjacent() const { return mlen() == 1; }
	bool is_near() const { return (clen() == 1) && (mlen() == 1 || mlen() == 2); }
	bool is_linear() const { return ((dx == 0) + (dy == 0) + (dz == 0)) == 2; }
	bool is_short() const { return is_linear() && mlen() <= 5; }
	bool is_long() const {return is_linear() && mlen() <= 15; }
	bool operator==(const Diff& other) const { return dx == other.dx && dy == other.dy && dz == other.dz; }
	bool operator!=(const Diff& other) const { return !(*this == other); }

	string __str__() const {
		return "[" + std::to_string(dx) + ", " + std::to_string(dy) + ", " + std::to_string(dz) + "]";
	}

};


/*========================= POS =========================*/

class Pos {
public:
	int x, y, z;

	Pos (int x, int y, int z) {
		this->x = x;
		this->y = y;
		this->z = z;
	}

	bool is_inside(int R) const { return x >= 0 && x < R && y >= 0 && y < R && z >= 0 && z < R; }
	Diff operator-(const Pos& other) const { return Diff(x - other.x, y - other.y, z - other.z); }
	Pos operator+(const Diff& d) const { return Pos(x + d.dx, y + d.dy, z + d.dz); }
	Pos operator-(const Diff& d) const { return Pos(x - d.dx, y - d.dy, z - d.dz); }
	bool operator==(const Pos& other) const { return x == other.x && y == other.y && z == other.z; }
	bool operator!=(const Pos& other) const { return !(*this == other); }
	
	Pos& operator+= (const Diff& d) {
		x += d.dx;
		y += d.dy;
		z += d.dz;
		return *this;
	}

	Pos& operator-= (const Diff& d) {
		x -= d.dx;
		y -= d.dy;
		x -= d.dz;
		return *this;
	}

	string __str__() const {
		return "[" + std::to_string(x) + ", " + std::to_string(y) + ", " + std::to_string(z) + "]";
	}

};


int region_dimension(const Pos& a, const Pos& b) {
	Diff d = b - a;
	return (d.dx != 0) + (d.dy != 0) + (d.dz != 0);
}


/*====================== COMMANDS =======================*/

class Bot;
class Emulator;

struct Command {
	virtual ~Command() = default;
	virtual void execute(Bot*, Emulator*) = 0;
	virtual void set_volatiles(Bot*, Emulator*) = 0;
	static unique_ptr<Command> getnextcommand(Emulator* field);	// defined after Emulator

	static Diff get_nd(unsigned char byte) {
		byte >>= 3;
		int dz = byte % 3 - 1;
		byte /= 3;
		int dy = byte % 3 - 1;
		byte /= 3;
		int dx = byte % 3 - 1;
		return Diff(dx, dy, dz);
	}

	static Diff get_lld(unsigned char a, unsigned char i) {
		a &= 3;
		int d = (int)(i &= 31) - 15;
		if (a == 1) return Diff(d, 0, 0);
		if (a == 2) return Diff(0, d, 0);
		if (a == 3) return Diff(0, 0, d);
		// TODO: report ill-formed model
	}

	static Diff get_sld(unsigned char a, unsigned char i) {
		a &= 3;
		int d = (int)(i &= 15) - 5;
		if (a == 1) return Diff(d, 0, 0);
		if (a == 2) return Diff(0, d, 0);
		if (a == 3) return Diff(0, 0, d);
		// TODO: report ill-formed model
	}

};

struct Halt : Command {
	void execute(Bot* b, Emulator* f) {
		// TODO
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct Wait : Command {
	void execute(Bot* b, Emulator* f) {}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct Flip : Command {
	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct SMove : Command {
	Diff lld;

	SMove(Diff d)
	: lld(d)
	{
		// TODO: report wrong command
		//assert (lld.is_long());
	}

	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct LMove : Command {
	Diff sld1, sld2;
	LMove(Diff d1, Diff d2)
	: sld1(d1)
	, sld2(d2)
	{
		// TODO: report wrong command
		// assert (sld1.is_short() && sld2.is_short());
	}

	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct FusionP : Command {
	Diff nd;

	FusionP(Diff nd)
	: nd(nd)
	{
		// TODO: report wrong command
		//assert(nd.is_near());
	}

	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct FusionS : Command
{
	Diff nd;

	FusionS(Diff nd)
	: nd(nd)
	{
		// TODO: report wrong command
		//assert(nd.is_near());
	}

	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct Fission : Command
{
	Diff nd;
	unsigned short m;
	Fission(Diff nd, unsigned short m)
	: nd(nd)
	, m(m)
	{
		// TODO: report wrong command
		//assert(nd.is_near());
	}

	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

struct Fill : Command
{	Diff nd;

	Fill(Diff nd)
	: nd(nd)
	{
		// TODO: report wrong command
		//assert(nd.is_near());
	}

	void execute(Bot* b, Emulator* f) {
	}

	void set_volatiles(Bot* b, Emulator* f) {
	}
};

/*======================== BOT ==========================*/

class Bot {
public:
	int pid;
	Pos position;
	vector<int> seeds;

	Bot(int pid, Pos position, vector<int> seeds)
	: pid(pid)
	, position(position)
	, seeds(seeds)
	{ }

	Bot()
	: pid(1)
	, position(Pos(0, 0, 0)) {
		for (int i = 2; i <= 20; i++) this-> seeds.push_back(i);
	}
};


/*====================== EMULATOR =======================*/

class Emulator {
public:
	int energy;
	bool high_harmonics;
	vector<unsigned char> matrix;
	int R;
	vector<Bot> bots;

	vector<unsigned char> trace;
	int tracepointer;
	int time_step;

	vector<unsigned char> floating;
	vector<unsigned char> model;
	vector<unsigned char> volatiles;
	bool volatile_violation;

	Emulator() {
		energy = 0;
		high_harmonics = false;
		R = 0;
		bots.push_back(Bot());
		tracepointer = 0;
		volatile_violation = false;
		time_step = 0;
	}

	~Emulator() {

	}


	void read_model(string filename) {
		std::ifstream f(filename, std::ios::binary);
		unsigned char c;
		f >> c;
		R = (int)c;
		while (f >> c) model.push_back(c);
		f.close();

		int bytes = (R * R * R + 7) / 8;
		matrix = vector<unsigned char>(bytes, 0);
		floating = vector<unsigned char>(bytes, 0);
		volatiles = vector<unsigned char>(bytes, 0);
	}

	void read_trace(string filename) {
		std::ifstream f(filename, std::ios::binary);
		unsigned char c;
		while (f >> c) {
			trace.push_back(c);
		}
		f.close();
	}

	unsigned char tracebyte() {
		return trace[tracepointer++];
	}

	bool getbit(const Pos& p, const vector<unsigned char>& v) const {
		int w = p.x*R*R + p.y*R + p.z;
		// TODO: TEST!
		return v[w / 8] & (1 << (w % 8));
	}

	void setbit(const Pos& p, vector<unsigned char>& v, bool bit) {
		int w = p.x*R*R + p.y*R + p.z;
		// TODO: TEST!
		v[w / 8] ^= (getbit(p, v) == bit) << (w % 8);
	}


	void run(string modelfile, string tracefile) {
		// test run
		read_model(modelfile);
		read_trace(tracefile);
		for (int i = 0; i < 20; i++) {
			unique_ptr<Command> c = Command::getnextcommand(this);
		}
	}
};


/*===================== FUNCTIONS =======================*/

unique_ptr<Command> Command::getnextcommand(Emulator* field) {
	unsigned char byte = field->tracebyte();
	if (byte == 255) return make_unique<Halt>(Halt());
	if (byte == 254) return make_unique<Wait>(Wait());
	if (byte == 253) return make_unique<Flip>(Flip());
	unsigned char tail = byte & 7;
	if (tail == 3) return make_unique<Fill>(Fill(get_nd(byte)));
	if (tail == 6) return make_unique<FusionS>(FusionS(get_nd(byte)));
	if (tail == 7) return make_unique<FusionP>(FusionP(get_nd(byte)));

	unsigned char byte2 = field->tracebyte();
	if (tail == 5) return make_unique<Fission>(Fission(get_nd(byte), byte2));
	if (tail == 4) {
		if (byte & 8) return make_unique<LMove>(LMove(get_sld(byte>>6, byte2>>4),
											   		  get_sld(byte>>4, byte2)));
		else		  return make_unique<SMove>(SMove(get_lld(byte>>4, byte2)));
	}
	// TODO: report ill-formed model
	return unique_ptr<Command>(nullptr);
}

/*====================== BINDING ========================*/

namespace py = pybind11;
PYBIND11_MODULE(emulator, m) {
	m.doc() = "C++ Emulator";

	py::class_<Diff> DiffClass(m, "Diff");
	DiffClass
		.def(py::init<int, int, int>())
		.def("mlen", &Diff::mlen)
		.def("clen", &Diff::clen)
		.def("is_linear", &Diff::is_linear)
		.def("is_short_linear", &Diff::is_short)
		.def("is_long_linear", &Diff::is_long)
		.def("is_near", &Diff::is_near)
		.def(py::self == py::self)
		.def(py::self != py::self)
		.def("__str__", &Diff::__str__)
	;

	py::class_<Pos> PosClass(m, "Pos");
	PosClass
		.def(py::init<int, int, int>())
		.def(py::self - py::self)
		.def("is_inside_matrix", &Pos::is_inside)
		.def("__add__", &Pos::operator+, py::is_operator())
		.def("__iadd__", &Pos::operator+=, py::is_operator())
		// .def("__sub__", &Pos::operator-<DiffClass>, py::is_operator())
		// .def("__isub__", &Pos::operator-=<Diff>, py::is_operator())
		.def(py::self == py::self)
		.def(py::self != py::self)
		.def("__str__", &Pos::__str__)
	;

	py::class_<Emulator> EmClass(m, "Emulator");
	EmClass
		.def(py::init<>())
		.def("run", &Emulator::run)
	;

	m.def("region_dimension", &region_dimension);
}
