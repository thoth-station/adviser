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

#include "dependency_graph.h"

/*
 * Walk dependency graph and generate application stacks. The value returned is owned by DependencyGraph
 * implementation and it is responsible for cleaning it.
 */
unsigned * DependencyGraph::walk(){
    // Remove from the last run.
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

    // We don't have any states to traverse left. Return NULL.
    return nullptr;
}


/*
 * Export for ctypes.
 */
extern "C" {
    DependencyGraph * DependencyGraph_new(unsigned * direct_dependencies, unsigned ** dependencies_list, unsigned * dependency_types, std::size_t size) {
        auto graph = new DependencyGraph(direct_dependencies, dependencies_list, dependency_types, size);
        return graph;
    }

    unsigned * DependencyGraph_walk(DependencyGraph * graph){
	    return graph->walk();
    }

    void DependencyGraph_delete(DependencyGraph * graph) {
        delete graph;
    }
}
