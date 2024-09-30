Intended workflow:
students run simulate.py with specified CPU paramteres. This launches Gem5 running the micro-lisp benchmark. This then runs gem5tomcpat.py on the output stats file, then launches mcpat with the generated input to attain the power usage.

Currently simulate.py is unimplemented, and the conversion of gem5 output to mcpat input isn't working due to version mismatches. This'll hopefully be fixed soon!

In the meantime, the benchmark can be build and run with (relies on newest gcc version 11, newer than that emits instructions umimplemented in Gem5):

make 

./mlisp89 examples/

The argument specifies the directory containing the input lisp programs. You can add and remove these programs in this directory (or create a new directory) to change the simulation behaviour and runtime. 

Gem5 can be build and run with:

scons build/X86/gem5.fast --with-lto

./build/X86/gem5.fast configs/deprecated/examples/se.py --cpu-type=DerivO3CPU --caches --l2cache -c ../benchmarks/micro-lisp/mlisp89 --options="../benchmarks/micro-lisp/examples/"

