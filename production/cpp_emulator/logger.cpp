#include "logger.h"

using std::string;

/** Logger class
	Logs emulation error or statistics if run is successful.

	Problem name and solution name can be set throw Emulator class
	to identify problem. If loaded from file, filename is used.

	logfile : should be passed; if not, no logging occures.

	mode : auto if the whole trace is loaded (Emulator::run_all)
	       interactive if partial trace is given (Emulator::run_given)

	tasktype : ! not supported yet !
			   assembly, disassembly, reassambly for auto mode
	           empty for interactive mode

  */

Logger::Logger() {
	problemname = "";
	solutionname = "";
	mode = "unknown";
	//tasktype = ""
	logfile = "";
}


void Logger::start() {
	t1 = std::chrono::high_resolution_clock::now();
}


void Logger::logsuccess(int64_t energy) {
	if (logfile == "") return;
	t2 = std::chrono::high_resolution_clock::now();
	f = std::ofstream(logfile, std::ios::app);
	logheader();
	f << "SUCCESS : " << energy << "\n\n";
	f.close();
}


void Logger::logerror(std::string message) {
	if (logfile == "") return;
	t2 = std::chrono::high_resolution_clock::now();
	f = std::ofstream(logfile, std::ios::app);
	logheader();
	f << "ERROR : " << message << "\n\n";
	f.close();
}


void Logger::logheader() {
	f << "Problem:  " << problemname 
	  << "\nSolution: " << solutionname 
	  << "\nMode:     " << mode << "\n"
	  << "time elapsed: " 
	  << std::chrono::duration_cast<std::chrono::microseconds> (t2 - t1).count()
	  << " microseconds\n";
}

// void Logger::logstate(State* S)
// void logstatistics


void setproblemname(Logger* l, std::string name) { l->problemname = name; }
void setsolutionname(Logger* l, std::string name) { l->solutionname = name; }
void setfilename(Logger* l, std::string name) { l->logfile = name; }

