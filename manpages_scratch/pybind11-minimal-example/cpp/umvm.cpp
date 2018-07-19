#include <pybind11/stl.h>
#include <pybind11/pybind11.h>
#include <string>

using std::string;

// This is a function that shall be exported as is.
// Useful for helper functions.
const string top_level_test() {
  return "Look, it's not that scary outside!";
}

// Using `class` keyword is good for maintaining the
// state.
class UMVM{ 
public:

  // In Python, you shall be invoking the functions
  // within classes (I guess, even the static ones)
  // in the following fashion: 
  //
  // ```
  // xo = external.umvm() # construct an instance of umvm
  // result = external.umvm.test(xo)
  // ```
  const string test() {
    return "Look, it's not that scary inside!";
  }

  UMVM() {}
};

namespace py = pybind11;

// PLUGIN is the most flexible macro. Don't forget to
// return `m.ptr` after you're done building it.
//
// Also, I have no idea why does it need an argument,
// that's the last thing I don't understand about
// how this whole pyblind contraption works. I guess
// I should read the code / documentation. Shrug.
PYBIND11_PLUGIN(umvm) {

  // Let's instantiate and name our module
  py::module m("umvm");

  // Here's how you "export" and extern top-level function
  m.def("top_level_test", &top_level_test);

  // Here we define `UMVMc` that is a way to tell pybind
  // what do we want to export. The usage is as follows:
  py::class_<UMVM> UMVMc(m, "umvm");
  UMVMc . def(py::init<>())
        . def("test", &UMVM::test);

  // The most important part.
  return m.ptr();
}
