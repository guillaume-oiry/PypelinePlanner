When I was working for a lab I had to do some data analysis. I loved it but what kept frustrating me is the amount of time dedicated to organize my code and modules and to adapt the pipeline structure whenever we needed a new kind of insight into the data. My hard drive would soon be cluttered by an ominous mess of folders and an agonizing script lurking shamefully in the background.

Well I understood quickly that I needed to make my script *modular*, but this was really redundant, this was not the part of programming that I liked. I had a brief glimpse of my future data analysis missions doing that again and again, and I wondered if I could do this only one last time and for all.

So here is my solution : **a meta-pipeline that organizes itself**. All the layout of the pipeline is organized from the parameters, so that you only have to code modules : the fun part (according to me). It also implements multiprocessing automatically (but you might not benefit much from it if the libraries you use are already well optimized, like numpy or tensorflow).

I'm pretty sure something like this already exists in some corner of github but at least I learned a lot in the process, and I hope my way of solving this problem could be helpful to other junior engineers like me.

DISCLAIMER : This is WORK IN PROGRESS.

NOTE : The multiprocessing part only works on Linux systems. I may switch to the *spawn* multiprocessing method in the future to make it work on Windows and MACOS too.

