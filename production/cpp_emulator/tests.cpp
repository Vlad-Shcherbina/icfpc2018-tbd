#include "algo.h"
#include "tests.h"
#include <iostream>



bool test_cubicles() {
	// no center - no loss
	bool case_1[27] {0, 0, 1,	//  . . a
		             0, 0, 1,	//  . . a
		             1, 0, 0,	//  b . .

		             1, 0, 1,	//  c . a
  		             1, 0, 0,	//  c . .
		             0, 1, 0,	//  . d .

		             0, 0, 0,	//  . . .
		             1, 0, 1,	//  c . e
		             0, 0, 0};	//  . . .
	if (cubic_num_components(case_1) != 5) return false;
	if (!can_safely_remove_center(case_1)) return false;

	// disjoining
	bool case_2[27] {0, 0, 1,	//  . . a
		             0, 0, 1,	//  . . a
		             1, 0, 0,	//  b . .

		             1, 0, 1,	//  c . a
  		             1, 1, 0,	//  c c .
		             0, 1, 0,	//  . c .

		             0, 0, 0,	//  . . .
		             1, 0, 1,	//  c . d
		             0, 0, 0};	//  . . .

	if (cubic_num_components(case_2) != 4) return false;
	if (can_safely_remove_center(case_2)) return false;

	// not disjoining
	bool case_3[27] {1, 1, 1,	//  a a a
		             1, 0, 1,	//  a . a
		             0, 1, 1,	//  . a a

		             0, 0, 0,	//  . . .
  		             1, 1, 0,	//  a a .
		             0, 1, 0,	//  . a .

		             0, 0, 1,	//  . . b
		             1, 0, 0,	//  a . .
		             1, 1, 0};	//  a a .

	if (cubic_num_components(case_3) != 2) return false;
	if (!can_safely_remove_center(case_3)) return false;

	// again disjoining
	bool case_4[27] {0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .

		             0, 0, 0,	//  . . .
  		             0, 1, 1,	//  . a a
		             0, 1, 0,	//  . a .

		             0, 0, 0,	//  . . .
		             0, 1, 0,	//  . a .
		             0, 0, 0};	//  . . .

	if (cubic_num_components(case_4) != 1) return false;
	if (can_safely_remove_center(case_4)) return false;

	// can happen
	bool case_5[27] {0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .

		             0, 0, 0,	//  . . .
  		             0, 1, 0,	//  . a .
		             0, 0, 0,	//  . . .

		             0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .
		             0, 0, 0};  //  . . .

	bool case_6[27] {0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .

		             0, 0, 0,	//  . . .
  		             0, 0, 0,	//  . a .
		             0, 0, 0,	//  . . .

		             0, 0, 0,	//  . . .
		             0, 0, 0,	//  . . .
		             0, 0, 0};  //  . . .

	if (cubic_num_components(case_5) != 1) return false;
	if (can_safely_remove_center(case_5)) return false;
	
	return true;
}


bool run_tests() {
	if (!test_cubicles()) return false;

	return true;
}