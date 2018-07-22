#ifndef __LOGGER_H_INCLUDED__
#define __LOGGER_H_INCLUDED__

#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <memory>
#include <exception>


class Emulator;

class base_error : public std::runtime_error {
public:
	base_error(const char* m) : std::runtime_error(m) { }
};

class emulation_error : public base_error {
public:
	emulation_error(const char* m) : base_error(m) { }
	const char* what() const throw() override {
		return (std::string("Emulation error: ") + runtime_error::what()).c_str();
	};
};

class parser_error : public base_error {
public:
	parser_error(const char* m) : base_error(m) { }
	const char* what() const throw() override {
		return (std::string("Parser erro: ") + runtime_error::what()).c_str();
	};
};

class malfunc_error :  public base_error {
public:
	malfunc_error(const char* m) : base_error(m) { }
	const char* what() const throw() override {
		return (std::string("Emulator malfunction: ") + runtime_error::what()).c_str();
	};
};



class State;

class Logger {
public:
	std::string logfile;
	std::ofstream f;

	std::string problemname;
	std::string solutionname;
	std::string mode;
	//std::string tasktype;

	Emulator* em;

	std::chrono::high_resolution_clock::time_point t1;
	std::chrono::high_resolution_clock::time_point t2;

	Logger();
	void start();

	void logerror(std::string message);
	void logsuccess(int64_t energy);


	//void logstate();
	//void logstatistics

private:
	void logheader();
	
};

#endif