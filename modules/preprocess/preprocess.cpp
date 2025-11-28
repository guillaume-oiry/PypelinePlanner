#include <iostream>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

int filter() {
  std::cout << "For now it's just a placeholder." << std::endl;
  return 0;
}

PYBIND11_MODULE(cpp_preprocess, m) { m.def("filter", &filter, "PLACEHOLDER"); }
