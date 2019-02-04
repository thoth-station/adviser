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
#include <utility>
#include <stack>
#include <vector>
#include <unistd.h>
#include <limits>

#include "dependency_graph.h"

const unsigned DependencyGraph::STREAM_STOP = std::numeric_limits<unsigned>::max();
const unsigned DependencyGraph::STREAM_DELIMITER = DependencyGraph::STREAM_STOP - 1;


/*
 * Walk dependency graph and generate application stacks. The value returned is a flag signalizing whether
 * there are more stacks to be produced.
 */
bool DependencyGraph::walk(){
    // Remove from the last run.
    /*
    if (this->is_valid_state()) {
        traversal_stack_item_t * item = this->traversal_stack_toppop();
        this->delete_item(item);
    }

    while (this->traversal_stack.size() > 0 && ! this->is_final_state())
        this->expand_state();

    if (this->traversal_stack.size() > 0) {
        traversal_stack_item_t * item = this->traversal_stack.top();
        return item->first->data();
    }
    */

    // We don't have any states to traverse left. Return NULL.
    //write(this->write_pipe_fd, &(DependencyGraph::STREAM_DELIMITER), sizeof(unsigned));
    //write(this->write_pipe_fd, &(DependencyGraph::STREAM_STOP), sizeof(unsigned));
    return false;
}


/*
 * Export for ctypes.
 */
extern "C" {
    unsigned get_stream_delimiter() {
        return DependencyGraph::STREAM_DELIMITER;
    }

    unsigned get_stream_stop() {
        return DependencyGraph::STREAM_STOP;
    }

    size_t get_item_size() {
        return sizeof(unsigned);
    }

    DependencyGraph * DependencyGraph_new(unsigned * direct_dependencies, unsigned ** dependencies_list, unsigned * dependency_types, std::size_t size, int write_pipe_fd) {
        auto graph = new DependencyGraph(direct_dependencies, dependencies_list, dependency_types, size, write_pipe_fd);
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
