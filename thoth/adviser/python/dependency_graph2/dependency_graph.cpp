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

#include "dependency_graph.h"

extern "C" {
    //Thoth::DependencyGraph * DependencyGraph_new(unsigned **dependencies_list, unsigned *dependency_types){
    //    auto graph = new Thoth::DependencyGraph(dependencies_list, dependency_types);
    //    std::cout << graph << std::endl;
    //    return graph;
    //}

    Thoth::DependencyGraph * DependencyGraph_new(){
        auto graph = new Thoth::DependencyGraph();
        std::cout << graph << std::endl;
        return graph;
    }

    int DependencyGraph_walk(Thoth::DependencyGraph * graph){
        std::cout << graph << std::endl;
        return graph->walk();
    }
}


/* Traverse the given dependency graph. This function can be called multiple times on the same object, it will
 * generate a new software stack each time (the state is kept in the DependencyGraph object itself).
 */
int Thoth::DependencyGraph::walk(void) {
    std::cerr << "Hello, Dependency Graph!\n";
    //std::cerr << this->dependencies_list << std::endl;
    //std::cerr << this->dependency_types << std::endl;
    return 1;
}
