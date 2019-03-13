/*
 * thoth-adviser - Dependency Graph implementation in C++
 * Copyright(C) 2018 Fridolin Pokorny
 *
 * This program is free software: you can redistribute it and / or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include <iostream>
#include <limits>
#include <unistd.h>

#include "dependency_graph.h"
#include "stack_item.h"

/*
 * Declaration of static constants.
 */
const package_t DependencyGraph::STREAM_STOP = std::numeric_limits<package_t>::max();
const package_t DependencyGraph::STREAM_DELIMITER = DependencyGraph::STREAM_STOP - 1;

/*
 * Walk dependency graph and generate application stacks. The value returned is a flag signalizing whether
 * there are more stacks to be produced.
 */
bool DependencyGraph::walk(){
    while (this->traversal_stack.size() > 0 && ! this->is_final_state())
        this->expand_state();

    if (this->traversal_stack.size() != 0) {
        // The top of the traversal stack holds a stack in a final state, write it to the output stack stream.
        auto stack_item = this->traversal_stack_toppop();
        this->write_stack_item(stack_item);
        delete stack_item;
    }

    // Is there anything more to compute?
    bool is_end = this->traversal_stack.size() == 0;
    if (is_end)
        write(this->write_fd, &(DependencyGraph::STREAM_STOP), sizeof(DependencyGraph::STREAM_STOP));

    return ! is_end;
}

/*
 * Compute cartesian product on vector of vectors. Used to compute all the possible combinations for done during
 * resolution. The callee is responsible for freeing allocated vectors in the (pre-allocated) output vector passed as a pointer.
 */
void DependencyGraph::cartesian_product(std::vector<std::vector<package_t> *> * output_vector, const std::vector<std::vector<package_t>> & v) {
    long long reminder;
    long long quot;
    long long total_size = 1LL;

    for (auto it: v)
        total_size *= it.size();

    for (long long n = 0 ; n < total_size; ++n) {
        std::vector<package_t> * u = new std::vector<package_t>();
        quot = n;
        for(long long i = v.size() - 1 ; 0 <= i ; --i) {
            reminder = quot % v[i].size();
            quot = quot / v[i].size();
            u->push_back(v[i][reminder]);
        }
        output_vector->push_back(u);
    }
}

/*
 * Export for ctypes.
 */
extern "C" {
    package_t get_stream_delimiter() {
        return DependencyGraph::STREAM_DELIMITER;
    }

    package_t get_stream_stop() {
        return DependencyGraph::STREAM_STOP;
    }

    size_t get_item_size() {
        return sizeof(package_t);
    }

    DependencyGraph * DependencyGraph_new(
            package_t * direct_dependencies,
            std::size_t direct_dependencies_size,
            package_t ** dependencies_list,
            std::size_t dependencies_list_size,
            package_type_t * dependency_types,
            std::size_t size,
            int write_fd
    ) {
        auto graph = new DependencyGraph(
            direct_dependencies,
            direct_dependencies_size,
            dependencies_list,
            dependencies_list_size,
            dependency_types,
            size,
            write_fd
        );
        return graph;
    }

    bool DependencyGraph_walk(DependencyGraph * graph){
	    return graph->walk();
    }

    void DependencyGraph_walk_all(DependencyGraph * graph){
        while (graph->walk())
            ;
    }

    void DependencyGraph_delete(DependencyGraph * graph) {
        delete graph;
    }
}
