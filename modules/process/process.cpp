#include <iostream>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

py::array_t<double>
cut_raw_data_to_epochs(const py::array_t<double> &raw_data_np, int duration,
                       int sfreq) {

  auto raw_data = raw_data_np.unchecked<2>();

  int segment_size{duration * sfreq};
  int limit{raw_data.shape(1)};

  if (segment_size >= limit)
    throw std::invalid_argument("Not enough length for a single epoch.");

  // We initialize the matrix with the expected shape first to avoid unnecessary
  // reallocations
  int n_epochs{(limit - (limit % segment_size)) / segment_size};
  int n_channels{raw_data.shape(0)};

  py::array_t<double> epochs_matrix({n_epochs, n_channels, segment_size});
  auto epochs_matrix_buf = epochs_matrix.mutable_unchecked<3>();

  for (int i = 0; i < n_epochs; ++i) {
    for (int k = 0; k < segment_size; ++k) {
      for (int j = 0; j < n_channels; ++j) {
        epochs_matrix_buf(i, j, k) = raw_data(j, i * segment_size + k);
      }
    }
  }

  return epochs_matrix;
}

PYBIND11_MODULE(cpp_process, m) {
  m.def("cut_raw_data_to_epochs", &cut_raw_data_to_epochs,
        "Cut raw data into epochs data.", py::arg("data"), py::arg("duration"),
        py::arg("sfreq"));
}
