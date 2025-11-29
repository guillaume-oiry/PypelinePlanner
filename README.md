# PypelinePlanner


## The skippable intro

When I was working for a lab I had to do some data analysis. I loved it but what kept frustrating me is the amount of time dedicated to organize my code and modules and to adapt the pipeline structure whenever we needed a new kind of insight into the data. My hard drive would soon be cluttered by an ominous mess of folders and an agonizing script lurking shamefully in the background.

Well I understood quickly that I needed to make my script *modular*, but this was really redundant, this was not the part of programming that I liked. I had a brief glimpse of my future data analysis missions doing that again and again, and I wondered if I could do this only one last time and for all.

So here is my solution : **a python pipeline that organizes itself**. All the layout of the pipeline is organized from the parameters, so that you only have to code modules : the fun part (according to me). It can also implements multiprocessing automatically.

I'm pretty sure something like this already exists in some corner of github but at least I learned a lot in the process, and I hope my way of solving this problem could be helpful to other junior engineers like me.

**Check the jupyter notebook tutorial to learn how to apprehend this tool.**

NOTE : The multiprocessing feature is still a work-in-progress but it works to some extent (more details at the end of the jupyter notebook).


## Features

### Python pipeline planning

[Check the jupyter notebook tutorial.]


### C++ integration

If you want to optimize your code with c++, there is already cpp files for each step of the pipeline ready to compile and integrate with their respective python submodules.

(for this section we simply go over the [*pybind11* documentation](https://pybind11.readthedocs.io/en/stable/basics.html#creating-bindings-for-a-simple-function))

When you wrote your cpp module (here a filter function), add it to the PYBIND11_MODULE at the end of the file :

```
PYBIND11_MODULE(cpp_preprocess, m) {
  ...;
  m.def("<function_name>", &<function_name>, "<description>"");
}
```


```
PYBIND11_MODULE(cpp_preprocess, m) {
  m.def("filter", &filter, "Apply a low-pass and high-pass filter on a numpy matrix object.");
}
```

Then to compile :

```
c++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) <step>.cpp -o cpp_<step>$(python3 -m pybind11 --extension-suffix)
```

For example from the modules/preprocess/ directory:

```
c++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) preprocess.cpp -o cpp_prepocess$(python3 -m pybind11 --extension-suffix)
```

This will generates a .so file that can be imported in the preprocess python file with `from . import cpp_preproces` and access the various functions inside like any library : `data = cpp_preprocess.filter(...)`

