.PHONY: clean stats test

CC ?= gcc
CFLAGS += -Wall -pedantic -O3 -flto -static -mno-avx 

all: clean mlisp89 stats test

non-bsd: clean mlisp89-non-bsd stats test

micro-lisp: micro-lisp.c
	$(CC) $(CFLAGS) -o $@ $^

mlisp89: mlisp89.c
	$(CC) $(CFLAGS) -ansi -std=c89 -D_DEFAULT_SOURCE -o $@ $^

mlisp89-non-bsd: mlisp89.c
	$(CC) $(CFLAGS) -ansi -lbsd -std=c89 -D_DEFAULT_SOURCE -o mlisp89 $^ -L /usr/x86_64-linux-gnu/

stats: mlisp89.c
	wc $^

clean:
	@rm -fv micro-lisp mlisp89
