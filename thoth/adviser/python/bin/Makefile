# Makefile for optimized in-memory dependency graph.
# 2019 Fridolin Pokorny <fridolin@redhat.com>

.PHONY:
all: libdependency_graph.so

.PHONY:
clean:
	rm -f test dependency_graph.o libdependency_graph.so

.PHONY:
debug: clean
	g++ -std=c++17 -Wall -pedantic -O0 -ggdb -c -fPIC -o dependency_graph.o dependency_graph.cpp
	g++ -shared -Wl,-soname,dependency_graph.so -o dependency_graph.so dependency_graph.o

dependency_graph.o: dependency_graph.cpp
	g++ -std=c++17 -Wall -pedantic -c -fPIC -o $@ $^

libdependency_graph.so: dependency_graph.o
	g++ -shared -Wl,-soname,dependency_graph.so -o $@ $^

