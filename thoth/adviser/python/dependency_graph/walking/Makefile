# Makefile for optimized in-memory dependency graph.
# 2019 Fridolin Pokorny <fridolin@redhat.com>

.PHONY:
all: libdependency_graph.so

.PHONY:
clean:
	rm -f test dependency_graph.o libdependency_graph.so

.PHONY:
clean-build:
	docker rmi thoth-libdependency-graph

.PHONY:
debug: clean
	g++ -std=c++17 -Wall -pedantic -O0 -ggdb -c -fPIC -o dependency_graph.o dependency_graph.cpp
	g++ -shared -Wl,-soname,libdependency_graph.so -o libdependency_graph.so dependency_graph.o

dependency_graph.o: dependency_graph.cpp
	g++ -std=c++11 -Wall -pedantic -c -fPIC -o $@ $^

libdependency_graph.so: dependency_graph.o
	g++ -shared -Wl,-soname,dependency_graph.so -o $@ $^

.PHONY:
build-container:
	docker build -t thoth-libdependency-graph .

.PHONY:
container-build: build-container
	$(eval id=$(shell sh -c "docker create thoth-libdependency-graph"))
	docker cp $(id):/home/buildroot/libdependency_graph.so ./libdependency_graph.so
	docker rm $(id)
