Intended workflow:
students run simulate.py with specified CPU paramteres. This launches Gem5 running the micro-lisp benchmark. This then runs gem5tomcpat.py on the output stats file, then launches mcpat with the generated input to attain the power usage.

Build gem5:

cd gem5

scons build/X86/gem5.fast --with-lto -j 8

Build mcpat:

cd mcpat

make -j 8

Build micro-lisp:

cd benchmarks/micro-lisp

make -j 8

Test micro-lisp:

./mlisp89 examples/

The argument specifies the directory containing the input lisp programs. You can add and remove these programs in this directory (or create a new directory) to change the simulation behaviour and runtime. 
